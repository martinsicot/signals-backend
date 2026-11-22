# INFRA-011 — Backups PostgreSQL + snapshots serveur (T9.2, T9.3 backlog)

## Statut
⬜ TODO

## Priorité
🟢 IMPORTANT (sécurité des données)

## Tâches

### T9.2 — Backups PostgreSQL automatiques

**Via Render.com** (natif) :
- Dans le dashboard Render → PostgreSQL → Backups
- Les backups quotidiens sont automatiques sur le plan payant
- Rétention : 7 jours (plan Starter) ou 30 jours (plan Standard)
- Téléchargement possible depuis le dashboard

**Option script externe** :
```bash
pg_dump $DATABASE_URL | gzip > signals_$(date +%Y%m%d).sql.gz
```

### T9.3 — Snapshot infrastructure

- Render.com gère la résilience infra (pas de snapshot VPS à gérer)
- Penser à exporter périodiquement un dump PostgreSQL vers un stockage externe (S3, Cloudflare R2)

## Test de restauration

Vérifier une fois après configuration que la restauration fonctionne :
1. Télécharger le dernier backup PostgreSQL
2. Restaurer dans une base locale
3. Vérifier l'intégrité des données

## Acceptance criteria

- Backup PostgreSQL automatique actif et vérifié
- Au moins un snapshot serveur créé
- Procédure de restauration documentée (même brièvement dans le README)
