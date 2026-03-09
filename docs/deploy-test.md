# Exposer l’app pour un test externe (tunnel)

Cette page décrit comment permettre à une personne **hors de votre machine** d’accéder à l’interface Echo (par ex. pour un test utilisateur V1), sans déployer en production.

---

## Précautions

- **Environnement de test uniquement** : ne pas utiliser pour de la production. Les identifiants du compte test sont partagés avec le testeur.
- **Compte test** : utilisez un mot de passe dédié dans `.env` (`ADMIN_PASSWORD`) et communiquez-le de façon sécurisée au testeur. En production, le seed de ce compte est désactivé (`APP_ENV=production`).
- **Réseau** : le tunnel rend l’app accessible sur Internet pendant qu’il est actif. Arrêtez-le dès que le test est terminé.

---

## Option 1 : Tunnel avec ngrok

[ngrok](https://ngrok.com/) expose un service local via une URL publique HTTPS.

### Prérequis

- L’app tourne en local (Docker) : `docker compose up -d`, migrations appliquées.
- Un compte ngrok (gratuit) et le binaire `ngrok` installé.

### Étapes

1. **Démarrer l’app** (si ce n’est pas déjà fait) :
   ```bash
   docker compose up -d
   docker compose exec api alembic upgrade head
   ```

2. **Exposer le port du frontend** (Streamlit écoute sur 8501) :
   ```bash
   ngrok http 8501
   ```
   ngrok affiche une URL publique du type `https://xxxx-xx-xx-xx-xx.ngrok-free.app`.

3. **Partager l’URL avec le testeur** : il ouvre cette URL dans son navigateur. L’interface Echo s’affiche ; il peut se connecter avec les identifiants du compte test (`ADMIN_EMAIL` / `ADMIN_PASSWORD` de votre `.env`), créer un souvenir et consulter la liste.

4. **Arrêter le tunnel** : `Ctrl+C` dans le terminal ngrok une fois le test terminé.

**Note** : L’API (port 8000) est appelée par le serveur Streamlit depuis votre machine, pas depuis le navigateur du testeur. Il suffit d’exposer le port 8501.

---

## Option 2 : Autres tunnels

D’autres outils (ex. [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/), [localtunnel](https://localtunnel.github.io/www/)) permettent d’exposer un port local. Même principe : exposer le port **8501** (service web), laisser l’app et l’API tourner en local avec Docker.

---

## Option 3 : Déploiement minimal sur un serveur

Pour un accès plus durable (plusieurs jours, pas de tunnel à garder ouvert), vous pouvez déployer le stack Docker sur un VPS (ex. une petite instance sur un cloud). Dans ce cas :

- Utilisez les mêmes commandes (`docker compose up`, migrations) sur le serveur.
- Configurez un reverse proxy (ex. nginx ou Caddy) avec HTTPS devant le port 8501 (et éventuellement 8000 si besoin d’accès direct à l’API).
- Respectez les précautions ci-dessus : compte test avec mot de passe dédié, pas de données sensibles, `APP_ENV=development` ou un environnement dédié au test.

Le parcours utilisateur (connexion → créer un souvenir → consulter la liste) est décrit dans [Tests et vérifications](testing.md) ; seuls l’URL d’accès et la façon de l’obtenir changent (tunnel ou URL du serveur).
