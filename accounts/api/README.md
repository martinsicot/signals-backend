# Authentification (JWT)

Endpoints d'authentification basés sur **SimpleJWT** (`rest_framework_simplejwt`).
Les tokens sont stateless : l'`access` s'utilise via l'en-tête `Authorization: Bearer <access>`.
Le `refresh` est stocké côté client et permet de renouveler l'`access` ; il est
blacklisté au logout (rotation + blacklist activées dans `SIMPLE_JWT`).

Schéma interactif : `/api/docs/` (Swagger) et `/api/redoc/`.

## Endpoints

| Méthode | URL | Auth | Description |
|---------|-----|------|-------------|
| POST | `/api/auth/register/` | — | Inscription → paire de tokens |
| POST | `/api/auth/login/` | — | Connexion → tokens + user |
| POST | `/api/auth/token/refresh/` | — | Renouvellement de l'`access` |
| POST | `/api/auth/logout/` | Bearer | Blacklist du `refresh` |
| POST | `/api/auth/password-reset/` | — | Envoi de l'email de réinitialisation |
| POST | `/api/auth/password-reset/confirm/` | — | Définition du nouveau mot de passe |
| GET  | `/api/auth/me/` | Bearer | Profil de l'utilisateur courant |
| GET  | `/api/account/me/` | Bearer | Profil client (nom, téléphone, adresse) |
| PATCH | `/api/account/me/` | Bearer | Modifier le profil client |

### POST `/api/auth/register/`
Requête :
```json
{ "first_name": "...", "last_name": "...", "email": "...",
  "password": "...", "password_confirm": "..." }
```
Réponse `201` :
```json
{ "access": "...", "refresh": "..." }
```
L'utilisateur est ajouté au groupe `customer` et un profil `Customer` est créé.

### POST `/api/auth/login/`
Requête : `{ "email": "...", "password": "..." }`
Réponse `200` :
```json
{ "access": "...", "refresh": "...",
  "user": { "id": 1, "email": "...", "first_name": "...",
            "last_name": "...", "groups": ["customer"] } }
```

### POST `/api/auth/token/refresh/`
Requête : `{ "refresh": "..." }` → Réponse `200` : `{ "access": "..." }`
(avec rotation : un nouveau `refresh` peut être renvoyé).

### POST `/api/auth/logout/`
En-tête `Authorization: Bearer <access>` + corps `{ "refresh": "..." }`.
Réponse `205` (No Content). Le `refresh` est blacklisté et ne peut plus être renouvelé.

### POST `/api/auth/password-reset/`
Requête : `{ "email": "..." }` → Réponse `200` **systématiquement**
(même si l'email est inconnu, pour éviter l'énumération de comptes).
Un email n'est envoyé que si le compte existe.

### POST `/api/auth/password-reset/confirm/`
Requête : `{ "uid": "...", "token": "...", "new_password": "..." }`
Réponse `200`. `uid`/`token` proviennent du lien envoyé par email.

### GET `/api/account/me/`
En-tête `Authorization: Bearer <access>`. Réservé aux comptes `customer`
(`403` pour un compte CRM/ops, `401` sans token).
Réponse `200` :
```json
{
  "id": 1,
  "email": "martin@example.com",
  "first_name": "Martin",
  "last_name": "Sicot",
  "phone": "0612345678",
  "default_shipping_address": {
    "line1": "12 rue des Acacias",
    "line2": "",
    "zip_code": "75001",
    "city": "Paris",
    "country": "FR"
  }
}
```
`default_shipping_address` vaut `null` si le client n'a aucune adresse.

### PATCH `/api/account/me/`
En-tête `Authorization: Bearer <access>`. Champs modifiables :
`first_name`, `last_name`, `phone`, `default_shipping_address`.
L'`email` est **en lecture seule** (une vérification séparée serait requise).
Mettre à jour `default_shipping_address` modifie (ou crée) l'adresse par défaut
du client.
Réponse `200` : le profil mis à jour (même format que le GET).

## Réponses d'erreur

Toutes les erreurs suivent l'un de ces deux formats :

- Erreur globale : `{ "detail": "..." }`
- Erreurs de validation par champ : `{ "<champ>": ["...", "..."] }`

| Endpoint | Statut | Corps | Cause |
|----------|--------|-------|-------|
| register | `400` | `{ "email": ["A user with this email already exists."] }` | Email déjà utilisé |
| register | `400` | `{ "password": ["Ensure this field has at least 8 characters."] }` | Mot de passe trop court |
| register | `400` | `{ "password_confirm": ["Passwords do not match."] }` | Mots de passe différents |
| register | `400` | `{ "<champ>": ["This field is required."] }` | Champ manquant |
| login | `401` | `{ "detail": "Invalid credentials." }` | Identifiants incorrects |
| logout | `400` | `{ "refresh": ["This field is required."] }` | `refresh` absent |
| logout | `400` | `{ "detail": "Invalid or expired token." }` | `refresh` invalide/expiré |
| logout | `401` | `{ "detail": "Authentication credentials were not provided." }` | `access` absent/invalide |
| token/refresh | `401` | `{ "detail": "Token is invalid or expired", "code": "token_not_valid" }` | `refresh` invalide/expiré/blacklisté |
| password-reset | `400` | `{ "email": ["This field is required."] }` | `email` absent |
| password-reset/confirm | `400` | `{ "detail": "uid, token and new_password are required." }` | Champ manquant |
| password-reset/confirm | `400` | `{ "detail": "Invalid reset link." }` | `uid` illisible |
| password-reset/confirm | `400` | `{ "detail": "Invalid or expired token." }` | `token` invalide/expiré |
| password-reset/confirm | `400` | `{ "new_password2": ["..."] }` | Nouveau mot de passe refusé par les validateurs |

## Configuration

- `SIMPLE_JWT` (durées de vie, rotation, blacklist) : `signals/settings/base.py`
- Email de réinitialisation : `templates/accounts/password_reset_email.html`
  et `templates/registration/password_reset_subject.txt`
  (backend email configurable via `EMAIL_BACKEND` ; `console` en dev).
