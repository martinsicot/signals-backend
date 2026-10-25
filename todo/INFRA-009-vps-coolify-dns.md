# INFRA-009 — Provisioning VPS + Coolify + DNS/SSL (T1.5, T1.6, T1.7 backlog)

## Priorité
🟡 IMPORTANT (requis avant mise en prod)

## Tâches

### T1.5 — Provisionner VPS Hetzner CX22

- Créer un VPS CX22 sur Hetzner Cloud (2 vCPU, 4 Go RAM, 40 Go SSD, ~5€/mois)
- Région recommandée : `nbg1` (Nuremberg) ou `fsn1` (Falkenstein) pour la latence France
- OS : Ubuntu 24.04 LTS
- Activer le firewall Hetzner : ouvrir ports 80, 443, 22

### T1.6 — Installer Coolify et connecter le repo

```bash
# Sur le VPS
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

- Créer un projet `signals` dans Coolify
- Ajouter le service Django (Dockerfile à la racine)
- Ajouter le service PostgreSQL 16
- Ajouter le service Redis
- Configurer les variables d'environnement depuis `.env.example`
- Premier déploiement et vérification `/health/`

### T1.7 — Config domaine + DNS + SSL

- Pointer `api.signals.fr` (ou domaine choisi) vers l'IP du VPS
- Configurer le domaine dans Coolify → Let's Encrypt automatique
- Vérifier HTTPS actif et redirection HTTP→HTTPS
- Tester `curl https://api.signals.fr/health/`

## Variables d'environnement à configurer en prod

```
DJANGO_SETTINGS_MODULE=signals.settings.prod
SECRET_KEY=<générer>
DATABASE_URL=postgres://...
REDIS_URL=redis://...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_BASE_URL=https://signals.fr
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.brevo.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

## Acceptance criteria

- `GET https://api.signals.fr/health/` retourne 200
- SSL valide (Let's Encrypt)
- Django Admin accessible via HTTPS
- Logs visibles dans Coolify
