# Recadrage des issues — Life Line Prototype v0

Proposition de recadrage du backlog GitHub pour aligner les issues avec la nouvelle direction visuelle (ligne droite, épaisse, continue, stable ; présence mémoire par nuance interne ; repères sobres ; fond clair vs sombre). Prêt à reprendre dans GitHub.

---

## 1. Texte du milestone (copier-coller)

**Nom du milestone :** `ECHO — Life Line Prototype v0`

**Description du milestone :**

```
Prototype visuel autonome de la Life Line : une ligne horizontale unique, droite, épaisse, continue et stable, avec extrémités arrondies, représentant la vie de l'utilisateur de la naissance à aujourd'hui. La présence mémoire est traduite par une nuance visuelle sobre à l'intérieur de la ligne (zones plus lumineuses = plus de souvenirs), sans déformer sa forme. Repères temporels discrets et sobres (Naissance, 20 ans, 40 ans, 60 ans, Aujourd'hui). Prototype autonome dans le lab dédié : aucune intégration backend, aucune donnée réelle, données mock uniquement. Objectif : valider le rendu visuel et la lisibilité (compréhension en moins de 2 secondes), y compris sur fond clair et fond sombre sobre.
```

---

## 2. Issues existantes — décisions

| # | Titre actuel | Décision | Action |
|---|--------------|----------|--------|
| **#104** | Composant SVG — axe horizontal de base | **Garder** | **Renommer** et **réécrire** la description. |
| **#105** | Rendu densité (épaisseur + intensité) | **Garder** | **Réécrire en profondeur** (nuance interne, pas d’épaisseur variable). |
| **#106** | Background et ambiance lumineuse | **Garder** | **Renommer** et **réécrire** (fond clair vs sombre sobre, ligne centrale). |
| **#107** | Hover et sélection de zone | **Garder** | Ajuster la description si besoin (référence à la ligne stable). |
| **#108** | Tooltip / overlay d'information | **Garder** | Ajouter la phrase explicative obligatoire dans le périmètre. |
| **#109** | Vue de comparaison de variantes | **Garder** | **Réécrire** (variantes cohérentes : fond clair/sombre, contraste, glow optionnel). |
| **#110** | Documentation finale et décision | **Garder** | Mettre à jour pour refléter la nouvelle direction et les critères de réussite. |
| **#111** | Impulsion lumineuse bilatérale | **Fermer ou mettre en parking** | Non alignée avec la nouvelle direction ; ne plus en faire un objectif du v0. |

---

## 3. Détail des modifications par issue

### #104 — Composant SVG — axe horizontal de base

- **Nouveau titre (suggéré) :** `Composant SVG — axe horizontal de base (ligne droite, épaisse, extrémités arrondies)`
- **Description à utiliser :**  
  Rendre un axe horizontal unique en SVG : ligne **droite**, **épaisse**, **continue**, **stable**, avec **extrémités arrondies**. Pas de points, cercles ou marqueurs sur la ligne. Responsive. Utiliser les données mock par année ; structure prête pour le remplissage mémoire (nuance interne) selon la structure du composant (LifeLineAxis + LifeLineFill). La **forme** de la ligne est constante sur toute la longueur (même hauteur, pas de vague ni bosse).

---

### #105 — Rendu densité (épaisseur + intensité)

- **Nouveau titre (suggéré) :** `Rendu présence mémoire (nuance interne)`
- **Description à utiliser :**  
  Traduire la présence mémoire **à l’intérieur** de la ligne par une **nuance visuelle sobre** : zones peu remplies = plus discrètes / moins lumineuses ; zones riches = plus lumineuses / plus pleines. La **forme** de la ligne ne change pas (pas de variation d’épaisseur). La ligne reste **toujours visible** sur toute sa longueur. S’appuyer sur les tokens remplissage faible / moyen / fort (cf. `docs/life-line-design-tokens.md`). Pas de rendu type signal, waveform ou ECG.

---

### #106 — Background et ambiance lumineuse

- **Nouveau titre (suggéré) :** `Fond et lisibilité (clair / sombre sobre)`
- **Description à utiliser :**  
  Définir le fond de la scène pour que la **ligne reste l’élément central** et lisible. Le cadrage **n’impose pas** un fond sombre comme seule option : autoriser la **comparaison** entre une version **fond clair** (ex. blanc / très clair) et une version **fond sombre sobre** (ex. #0e1419). La lisibilité prime sur l’ambiance. Optionnel : glow très léger autour de la ligne, sans en faire le cœur du concept.

---

### #107 — Hover et sélection de zone

- **Conserver le titre** (ou légèrement préciser : « Hover et sélection de zone (Life Line) »).
- **Description :**  
  Détection de la zone temporelle (année) au survol, état actif, gestion du click (callback mock ou log). Pas de navigation métier. La ligne reste stable (pas de déformation au hover).

---

### #108 — Tooltip / overlay d'information

- **Conserver le titre.**
- **Description :**  
  Afficher année et densité (présence mémoire) mock au survol ; positionnement et style sobre. Peut inclure ou s’appuyer sur la **phrase explicative** : « Votre vie, de la naissance à aujourd’hui. Les zones plus lumineuses contiennent davantage de souvenirs. »

---

### #109 — Vue de comparaison de variantes

- **Nouveau titre (suggéré) :** `Vue de comparaison de variantes (fond clair / sombre, contraste, glow)`
- **Description à utiliser :**  
  Afficher plusieurs **variantes cohérentes** de la Life Line côte à côte avec le **même dataset mock** : même direction visuelle (ligne stable, nuance interne). Exemples : fond clair vs fond sombre sobre ; contraste plus ou moins marqué ; glow très léger vs sans glow. **But** : choisir la meilleure déclinaison avant de figer la direction design. Ne pas réintroduire des directions divergentes (organique, impulsion centrale, épaisseur variable).

---

### #110 — Documentation finale et décision

- **Conserver le titre.**
- **Description :**  
  Documenter : comment lancer le lab ; choix retenus (variante, palette, fond) ; respect de la règle UX (lisibilité < 2 s) et des critères de réussite (forme constante, phrase explicative, repères sobres) ; décision « prêt pour phase 2 » ou itérations. Référence : `docs/life-line-prototype-v0.md` et `docs/life-line-design-tokens.md`.

---

### #111 — Impulsion lumineuse bilatérale

- **Décision :** **Fermer** ou **mettre en parking** (label « parking » ou « hors périmètre v0 »).
- **Commentaire de clôture suggéré :**  
  « Hors périmètre du prototype v0 après recadrage de la direction visuelle. La Life Line repose désormais sur une ligne stable, sans pulsation comme principe central. Une animation légère pourra être reconsidérée en phase ultérieure si besoin, sans être au cœur du concept. »

---

## 4. Nouvelle issue à créer

### Repères temporels (libellés)

- **Titre :** `Repères temporels — libellés sobres (Naissance, 20 ans, 40 ans, 60 ans, Aujourd'hui)`
- **Description :**  
  Afficher des repères temporels **discrets mais lisibles** le long de la ligne (ou à proximité). Utiliser des libellés **neutres et universels** : **Naissance**, **20 ans**, **40 ans**, **60 ans**, **Aujourd’hui**. Pas de libellés interprétatifs (ex. « Enfance », « Jeune adulte »). Objectif : ancrer immédiatement le sens gauche = passé, droite = présent. Dépendances : axe horizontal de base (#104) et données mock (années de naissance / âge actuel).

---

## 5. Ordre recommandé du backlog (après recadrage)

1. #104 — Composant SVG — axe horizontal de base (ligne droite, épaisse, extrémités arrondies)
2. #105 — Rendu présence mémoire (nuance interne)
3. **Nouvelle** — Repères temporels — libellés sobres
4. #106 — Fond et lisibilité (clair / sombre sobre)
5. #107 — Hover et sélection de zone
6. #108 — Tooltip / overlay d'information
7. #109 — Vue de comparaison de variantes
8. #110 — Documentation finale et décision

**#111** : fermée ou en parking, à ne pas inclure dans le flux principal du v0.

---

## 6. Résumé

| Action | Issues |
|--------|--------|
| **Garder + renommer + réécrire** | #104, #105, #106, #109 |
| **Garder + ajuster description** | #107, #108, #110 |
| **Fermer ou parking** | #111 |
| **Créer** | 1 nouvelle issue : Repères temporels — libellés sobres |

Le milestone `ECHO — Life Line Prototype v0` doit être mis à jour avec le texte de la section 1 ci-dessus.
