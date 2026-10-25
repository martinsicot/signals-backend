# INFRA-011 — Backups PostgreSQL + snapshots serveur (T9.2, T9.3 backlog)

## Priorité
🟢 IMPORTANT (sécurité des données)

## Tâches

### T9.2 — Backups PostgreSQL automatiques

**Option A — Via Coolify** (recommandée) :
- Configurer le backup automatique de la base PostgreSQL dans Coolify
- Destination : Hetzner Object Storage (S3-compatible, ~2€/mois pour 10 Go)
- Fréquence : quotidien à 3h du matin
- Rétention : 7 jours glissants

**Option B — Script cron** :
```bash
# Sur le VPS, via crontab
0 3 * * * pg_dump $DATABASE_URL | gzip > /backups/signals_$(date +%Y%m%d).sql.gz
```

### T9.3 — Snapshot serveur Hetzner

- Dans le dashboard Hetzner, activer les snapshots automatiques hebdomadaires
- Coût : ~20% du coût serveur/mois (CX22 → +~1€/mois)
- Permet une restauration complète du VPS en cas de panne grave

## Test de restauration

Vérifier une fois après configuration que la restauration fonctionne :
1. Télécharger le dernier backup PostgreSQL
2. Restaurer dans une base locale
3. Vérifier l'intégrité des données

## Acceptance criteria

- Backup PostgreSQL automatique actif et vérifié
- Au moins un snapshot serveur créé
- Procédure de restauration documentée (même brièvement dans le README)
