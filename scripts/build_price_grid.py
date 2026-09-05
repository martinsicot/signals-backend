"""
Build a normalized price-grid JSON from the 'Signalisation Permanente' price book
(Apple Numbers export).

The source spreadsheet keys prices by (reference-group, size, class, RAL-backing).
Many regulatory sign refs share one price line, so we normalize into:

  price_schedules[]  : distinct price matrices (deduped by content)
  sign_references[]  : ref -> schedule + shape (the mapping / where shape lives)

Usage:
    uv run --with numbers-parser python scripts/build_price_grid.py \
        <source.numbers> <out.json>
"""

import hashlib
import json
import re
import sys
from collections import defaultdict

from numbers_parser import Document

# Column layout of Feuil1 / "Table 1-1" (0-indexed), derived from the 3 header rows.
COL = {
    "ref": 0,
    "size": 1,
    "brut_cl1_vente": 2,
    "brut_cl2_vente": 3,
    "epaisseur": 4,
    "poids": 5,
    "rails": 6,
    "brut_cl1_achat": 7,
    "brut_cl2_achat": 8,
    "delai_brut": 9,
    "ral_cl1_vente": 10,
    "ral_cl2_vente": 11,
    "ral_cl1_achat": 12,
    "ral_cl2_achat": 13,
    "delai_ral": 14,
    "transport_dpd": 15,
    "transport_palette": 16,
}
DATA_START = 4  # first data row after the 4 header rows

# Shape per source group, keyed by the leading ref token. French signage families.
SHAPE_BY_LEAD = {
    "A": "triangle",     # danger
    "AB1": "triangle", "AB2": "triangle", "AB25": "triangle",
    "AB3": "triangle",   # cédez (inverted triangle)
    "AB4": "octagon",    # STOP
    "AB6": "diamond", "AB7": "diamond",   # priority
    "B0": "round", "B1": "round", "B à": "round",  # interdiction/obligation
    "B6b": "square",
    "C": "square",       # indication
    "CE": "square",      # services
    "G": "directional",  # directional (quote)
    "J4": "rect", "J10": "rect",
}

REF_RE = re.compile(r"^[A-Z]{1,3}\d")  # a real ref token starts letters + a digit


def money(v):
    try:
        return None if v is None else round(float(v), 2)
    except (TypeError, ValueError):
        return None


def num(v):
    try:
        if v is None:
            return None
        f = round(float(v), 3)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return clean(v)  # keep non-numeric notes (e.g. poids "Au sol")


def dim(v):
    """Cleaned dimension string; 300.0 -> '300' but keep '150/300', '?' as-is."""
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return clean(v)


def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def parse_size(raw):
    """Return a size dict with a display label + parsed dimensions."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        n = int(round(raw))
        return {"kind": "single", "value_mm": n, "label": str(n)}
    s = str(raw).strip()
    low = s.lower()
    if low[:1] in ("o", "ø"):
        digits = re.sub(r"\D", "", s)
        if digits:
            return {"kind": "diameter", "diameter_mm": int(digits), "label": f"Ø{digits}"}
    if "x" in low:
        parts = re.split(r"x", low)
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            w, h = int(parts[0]), int(parts[1])
            return {"kind": "rect", "width_mm": w, "height_mm": h, "label": f"{w}x{h}"}
    return {"kind": "raw", "label": s}


def size_kind(size):
    if not size:
        return "single"
    return {"single": "single", "diameter": "diameter", "rect": "rect"}.get(size["kind"], "single")


def extract_refs(raw_label):
    """Split col-0 into clean ref tokens; return (refs, noise_tokens)."""
    tokens = re.split(r"\s+", raw_label.strip())
    refs, noise = [], []
    for t in tokens:
        t = t.strip()
        if not t or t in (":",):
            continue
        if REF_RE.match(t):
            refs.append(t)
        else:
            noise.append(t)
    return refs, noise


def shape_for(refs):
    lead = refs[0] if refs else ""
    for key in ("AB1", "AB2", "AB25", "AB3", "AB4", "AB6", "AB7", "B6b", "B à",
                "B0", "B1", "CE", "J4", "J10"):
        if lead.startswith(key):
            return SHAPE_BY_LEAD[key]
    return SHAPE_BY_LEAD.get(lead[:1], "unknown")


def main():
    src, out = sys.argv[1], sys.argv[2]
    doc = Document(src)
    table = doc.sheets[0].tables[1]  # Feuil1 / Table 1-1 (the master, 18 cols)
    rows = table.rows(values_only=True)

    # --- 1. split rows into source groups (a new group starts when col0 is set) ---
    groups = []  # {source_label, refs, noise, shape, rows:[...]}
    current = None
    for i in range(DATA_START, len(rows)):
        r = rows[i]
        ref_cell = clean(r[COL["ref"]])
        size = parse_size(r[COL["size"]])
        if ref_cell:
            refs, noise = extract_refs(ref_cell)
            current = {
                "source_label": ref_cell,
                "refs": refs,
                "noise": noise,
                "shape": shape_for(refs),
                "rows": [],
            }
            groups.append(current)
        if current is None or size is None:
            continue  # skip stray/empty lines

        def cell(key):
            return r[COL[key]]

        row = {
            "size": size,
            "specs": {
                "epaisseur_mm": num(cell("epaisseur")),
                "poids_kg": num(cell("poids")),
                "rails_mm": dim(cell("rails")),
                "delai_alu_brut": clean(cell("delai_brut")),
                "delai_ral": clean(cell("delai_ral")),
                "transport_dpd": clean(cell("transport_dpd")),
                "transport_palette": clean(cell("transport_palette")),
            },
            "prices": {
                "alu_brut": {
                    "CL1": {"vente": money(cell("brut_cl1_vente")), "achat": money(cell("brut_cl1_achat"))},
                    "CL2": {"vente": money(cell("brut_cl2_vente")), "achat": money(cell("brut_cl2_achat"))},
                },
                "ral": {
                    "CL1": {"vente": money(cell("ral_cl1_vente")), "achat": money(cell("ral_cl1_achat"))},
                    "CL2": {"vente": money(cell("ral_cl2_vente")), "achat": money(cell("ral_cl2_achat"))},
                },
            },
        }
        current["rows"].append(row)

    # --- 2. classify: priced vs quote-only (no prices at all) ---
    def has_price(g):
        for row in g["rows"]:
            for b in row["prices"].values():
                for c in b.values():
                    if c["vente"] is not None:
                        return True
        return False

    priced = [g for g in groups if has_price(g)]
    quote = [g for g in groups if not has_price(g)]

    # --- 3. dedupe priced groups by content hash (size+specs+prices) ---
    def content_hash(g):
        payload = json.dumps([{"size": r["size"], "specs": r["specs"], "prices": r["prices"]}
                              for r in g["rows"]], sort_keys=True, ensure_ascii=False)
        return hashlib.sha1(payload.encode()).hexdigest()

    by_hash = defaultdict(list)
    for g in priced:
        by_hash[content_hash(g)].append(g)

    schedules = []
    sign_references = []
    anomalies = []
    used_codes = set()

    def make_code(g):
        sk = size_kind(g["rows"][0]["size"])
        labels = [r["size"]["label"] for r in g["rows"]]
        base = {"single": "side", "diameter": "round", "rect": "rect"}.get(sk, "sched")
        code = f"{base}_{labels[0]}_{labels[-1]}".lower().replace("ø", "d")
        code = re.sub(r"[^a-z0-9_]", "", code)
        n, c = 2, code
        while c in used_codes:
            c = f"{code}_{n}"; n += 1
        used_codes.add(c)
        return c

    for members in by_hash.values():
        rep = members[0]
        code = make_code(rep)
        all_refs = []
        shapes = set()
        for g in members:
            all_refs.extend(g["refs"])
            shapes.add(g["shape"])
            for t in g["noise"]:
                anomalies.append({"type": "unparsed_ref_token", "schedule": code,
                                  "source_label": g["source_label"], "token": t})
        schedules.append({
            "code": code,
            "size_kind": size_kind(rep["rows"][0]["size"]),
            "member_count": len(all_refs),
            "rows": [{"size": r["size"]["label"], "dimensions": r["size"],
                      "specs": r["specs"], "prices": r["prices"]} for r in rep["rows"]],
        })
        for g in members:
            for ref in g["refs"]:
                sign_references.append({"ref": ref, "shape": g["shape"], "schedule": code})
        # anomaly: ral cheaper than brut (backing surcharge should be positive)
        for r in rep["rows"]:
            for cls in ("CL1", "CL2"):
                b = r["prices"]["alu_brut"][cls]["vente"]
                ral = r["prices"]["ral"][cls]["vente"]
                if b is not None and ral is not None and ral < b:
                    anomalies.append({"type": "ral_below_brut", "schedule": code,
                                      "size": r["size"]["label"], "class": cls,
                                      "alu_brut": b, "ral": ral})

    # quote-only refs
    for g in quote:
        for ref in g["refs"]:
            sign_references.append({"ref": ref, "shape": g["shape"],
                                    "schedule": None, "pricing": "quote"})

    doc_out = {
        "meta": {
            "domain": "signalisation_permanente",
            "currency": "EUR",
            "price_type": "HT",
            "backings": [
                {"code": "alu_brut", "label": "Dos alu brut", "default": True},
                {"code": "ral", "label": "Alu RAL au choix", "default": False},
            ],
            "classes": ["CL1", "CL2"],
            "source": src.split("/")[-1],
            "note": "vente/achat rounded to 2 decimals (EUR). specs shared per (schedule,size).",
        },
        "price_schedules": schedules,
        "sign_references": sorted(sign_references, key=lambda x: x["ref"]),
        "anomalies": anomalies,
    }

    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc_out, fh, ensure_ascii=False, indent=2)

    # --- report ---
    print(f"source groups: {len(groups)}  (priced={len(priced)}, quote-only={len(quote)})")
    print(f"distinct price schedules after dedupe: {len(schedules)}")
    for s in schedules:
        print(f"  {s['code']:24} rows={len(s['rows']):2} refs={s['member_count']}")
    print(f"sign references: {len(sign_references)}")
    print(f"anomalies: {len(anomalies)}")
    for a in anomalies:
        print("  -", a)


if __name__ == "__main__":
    main()
