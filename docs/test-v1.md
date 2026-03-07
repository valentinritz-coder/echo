# Tester la V1 — Parcours utilisateur

Cette fiche permet à un testeur (sans connaissance du code) de lancer l’application et de vérifier le parcours : connexion → création d’un souvenir → consultation de la liste.

---

## Prérequis

- **Docker** et **Docker Compose** installés et fonctionnels.
- Un clone du dépôt à jour.

---

## 1. Préparer l’environnement

1. **Fichier `.env`**  
   À la racine du dépôt, copier `.env.example` vers `.env` :
   ```bash
   copy .env.example .env
   ```
   (Sous Linux/macOS : `cp .env.example .env`.)

2. **Compte test**  
   Dans `.env`, définir un email et un mot de passe pour le compte de test (créé automatiquement au premier démarrage de l’API en développement) :
   ```env
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=votre-mot-de-passe
   ```
   Vous vous connecterez à l’interface avec ces identifiants.

3. **Lancer les services**  
   À la racine du dépôt :
   ```bash
   docker compose up --build
   ```
   Laisser les conteneurs tourner (ou utiliser `docker compose up -d --build` pour lancer en arrière-plan).

4. **Appliquer les migrations**  
   Dans un autre terminal, à la racine du dépôt :
   ```bash
   docker compose exec api alembic upgrade head
   ```
   À faire une fois au premier run (et après chaque ajout de migration).

---

## 2. Accéder à l’application

Ouvrir dans un navigateur :

- **Interface utilisateur (web)** : [http://localhost:8501](http://localhost:8501)

L’API est disponible en arrière-plan (pas besoin d’y accéder directement pour ce parcours).

---

## 3. Se connecter

1. Dans la **barre latérale gauche**, saisir l’**email** et le **mot de passe** du compte test (ceux définis dans `.env` avec `ADMIN_EMAIL` et `ADMIN_PASSWORD`).
2. Cliquer sur **« Se connecter »**.
3. Un message « Connexion réussie » et « Connecté » confirme que vous êtes connecté.

---

## 4. Créer un souvenir

1. Ouvrir l’onglet **« New memory / Créer un souvenir »**.
2. Vous voyez la **question du jour**.
3. Renseigner au moins un des éléments suivants (tous optionnels mais au moins un requis) :
   - **Texte** : saisir du texte dans la zone prévue.
   - **Audio** : envoyer un fichier audio (formats acceptés : mp3, m4a, wav, ogg, etc.).
   - **Images** : ajouter une ou plusieurs images.
4. Cliquer sur **« Save »**.
5. Le souvenir est créé ; il apparaît dans la liste.

---

## 5. Consulter la bibliothèque

1. Ouvrir l’onglet **« List / Mes souvenirs »**.
2. La liste de vos souvenirs s’affiche (date, texte, images, lecteur audio).
3. Utiliser les boutons **Prev** / **Next** pour paginer si nécessaire.
4. Vous pouvez **écouter l’audio** et **voir les images** pour chaque souvenir.

---

## En cas de problème

- **« Connexion refusée »** : vérifier que les conteneurs sont bien démarrés (`docker compose ps`) et que `ADMIN_EMAIL` / `ADMIN_PASSWORD` sont bien définis dans `.env`, puis redémarrer l’API (`docker compose restart api`).
- **Page blanche ou erreur sur le web** : vérifier que les migrations ont été appliquées (`docker compose exec api alembic upgrade head`) et que l’API répond : `curl http://localhost:8000/api/v1/health` doit retourner `{"status":"ok"}`.
- **Aucune question du jour** : s’assurer que les migrations ont été exécutées (les questions sont créées automatiquement).

Pour plus de détails (structure du projet, autres commandes), voir le [README](../README.md) à la racine du dépôt.
