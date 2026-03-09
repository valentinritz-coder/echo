# Ligne de vie — Prototype v0 (Echo)

Document de cadrage pour le prototype « Life Line » : vision, périmètre, direction visuelle, échelle temporelle, règle UX, critères de réussite, design tokens, structure du composant, issues et plan d’implémentation. Aucune intégration backend ni données réelles ; prototype autonome dans le lab dédié.

---

## 1. Vision

La **Life Line** d’ECHO est une représentation visuelle de la vie de l’utilisateur, de la naissance à aujourd’hui.

**Principes non négociables :**

- **Une ligne horizontale unique** : droite, épaisse, continue, stable.
- **Extrémités arrondies** : la ligne se termine en caps arrondis, sans angle vif.
- **Forme constante** : pas de vague, pas de bosse, pas de pulsation comme principe central. La ligne ne se déforme pas.
- **Vie complète** : elle représente la vie de l’utilisateur de la **naissance** jusqu’à **aujourd’hui**.
- **Présence mémoire à l’intérieur** : les souvenirs ne déforment pas la forme. Ils se lisent par une **nuance visuelle sobre** à l’intérieur de la ligne : zones peu remplies = plus discrètes / moins lumineuses ; zones riches = plus lumineuses / plus pleines. La ligne reste toujours visible sur toute sa longueur.
- **Aucun point, cercle ni icône sur la ligne** : pas de points, cercles, anneaux, icônes ou marqueurs posés sur la ligne elle-même.
- **Symbolique** : la ligne représente la **continuité d’une vie**, pas une courbe de données. Pas de rendu ECG, waveform ou analytique.

**À éviter** : effet signal, visualisation de données, esthétique organique / filament vivant comme axe principal, impulsion lumineuse comme cœur du concept, variation d’épaisseur pour traduire la densité.

---

## 2. Phrase explicative obligatoire

Cette phrase est une **clé de lecture** du concept et doit figurer dans le cadrage produit / design / UX :

> **« Votre vie, de la naissance à aujourd’hui. Les zones plus lumineuses contiennent davantage de souvenirs. »**

Elle sert de référence pour la copy, les tooltips d’aide et la validation de la compréhension utilisateur.

---

## 3. Repères temporels

Les repères le long de la ligne sont **neutres, universels et sobres**. On ne veut pas de libellés interprétatifs (ex. « Enfance », « Jeune adulte »).

**Exemples de repères attendus :**

- Naissance  
- 20 ans  
- 40 ans  
- 60 ans  
- Aujourd’hui  

Ils doivent être **discrets mais lisibles**, pour ancrer le sens gauche = passé, droite = présent, sans surcharger l’interface.

---

## 4. Accessibilité et UX

Le concept doit être **compréhensible très vite**, y compris pour un public vieillissant.

**Objectifs :**

- L’utilisateur comprend **immédiatement** que la ligne représente sa vie.
- La **gauche** = passé (naissance).
- La **droite** = aujourd’hui.
- Certaines **zones contiennent plus de souvenirs** que d’autres (nuance interne : plus lumineux = plus de souvenirs).

La poésie visuelle est autorisée, mais **ne doit jamais nuire à la compréhension**. Le sens ne doit pas dépendre uniquement d’un effet subtil. La **lisibilité prime** sur l’ambiance.

**Règle UX** : la Life Line doit être compréhensible en **moins de 2 secondes**. Tout rendu qui nécessite une explication pour être compris doit être simplifié.

---

## 5. Fond clair / fond sombre

Le concept peut être validé sur **fond clair** comme sur fond sombre. Une image de référence a montré que le concept fonctionne très bien sur **fond blanc**, avec extrémités arrondies.

**Position de cadrage :**

- Le concept de la ligne peut être **validé sur fond clair**.
- La compréhension pure semble **meilleure sur fond clair / blanc / très clair**.
- Une **version sombre sobre** peut rester envisageable pour cohérence avec l’univers ECHO.
- Le **fond ne doit jamais prendre le dessus sur la ligne** : la ligne est l’élément identitaire central.
- **La lisibilité prime sur l’ambiance.**

Les documents et le backlog **n’imposent pas** un fond sombre comme obligation absolue. Ils **autorisent la comparaison** entre une version claire et une version sombre sobre. La décision finale (fond clair vs sombre) peut être prise après validation du prototype.

---

## 6. Périmètre phase 1

**Objectif** : valider le rendu visuel et les micro-interactions avant toute intégration produit.

**Contraintes du prototype (explicites) :**

- **Prototype autonome** : aucun branchement sur le reste du produit Echo.
- **Données mock uniquement** : pas d’API, pas de modèles métier, pas de données réelles.
- **Lab dédié** : tout le travail se fait dans `apps/lifeline-lab/` (Vite + React + TypeScript + SVG).
- **Aucune intégration backend** : pas de modification du backend, des apps existantes ni des vrais souvenirs.

---

## 7. Concept visuel (synthèse)

- **Une ligne horizontale** : droite, épaisse, continue, stable, extrémités arrondies.
- **Forme constante** : pas de variation d’épaisseur pour la densité, pas de vague, pas de pulsation centrale.
- **Présence mémoire** : traduite par une **nuance interne** (couleur / luminosité) : zones peu remplies = plus discrètes ; zones riches = plus lumineuses. La ligne reste toujours visible sur toute sa longueur.
- **Repères temporels** : discrets, sobres (Naissance, 20 ans, 40 ans, 60 ans, Aujourd’hui).
- **Interactions prototype** : hover → détection de zone + état actif ; tooltip → année + densité mock ; click → callback mock ou log. Pas de navigation métier.

---

## 8. Échelle temporelle

- La ligne représente la **vie complète** : de la **naissance** jusqu’à **aujourd’hui**.
- Pour le **prototype v0**, la **granularité de base est l’année** : les données mock sont structurées **par année**, et la présence mémoire (remplissage) est **calculée par année**.
- Une évolution future vers un zoom (année → mois) est envisageable ; ce n’est **pas** le périmètre du prototype actuel.

**Exemple de structure conceptuelle des données mock (année → densité, 0–1) :**

| Année | Densité (remplissage) |
|-------|------------------------|
| 1990  | 0.1                    |
| 1991  | 0.0                    |
| 1992  | 0.4                    |
| 1993  | 0.8                    |

Cette granularité annuelle est figée pour le v0 afin d’éviter toute ambiguïté technique.

---

## 9. Critères de réussite du prototype

Pour considérer le prototype comme réussi :

- La **ligne est compréhensible en moins de 2 secondes** (aligné avec la règle UX).
- L’utilisateur perçoit **sans effort** : gauche = passé, droite = aujourd’hui, zones plus lumineuses = plus de souvenirs.
- La **forme de la ligne reste constante** : pas de déformation, pas de rendu type signal ou waveform.
- La **phrase explicative** (« Votre vie, de la naissance à aujourd’hui… ») peut accompagner le rendu sans contredire la perception visuelle.

---

## 10. Design tokens

Les variables visuelles sont documentées dans **`docs/life-line-design-tokens.md`**. Elles couvrent notamment :

- Fond clair et fond sombre sobre
- Ligne de base (épaisseur constante, extrémités arrondies)
- Remplissage mémoire : faible / moyen / fort (nuance interne)
- Hauteur de ligne, rayon d’arrondi
- Texte principal, texte secondaire / repères
- Glow léger optionnel (sans en faire le cœur du concept)

**Livrable** : bloc de variables CSS ou tokens documentés (dans le lab, ex. `src/index.css` ou fichier dédié).

---

## 11. Structure du composant

Architecture indicative pour un code lisible et maintenable.

**Composant principal :**

- **LifeLine** : orchestrateur global ; gère les données (mock), les interactions et la coordination des sous-composants.

**Sous-composants possibles :**

- **LifeLineAxis** : rendu SVG principal de l’axe (ligne droite, épaisse, continue, extrémités arrondies).
- **LifeLineFill** (ou équivalent) : rendu du remplissage mémoire à l’intérieur de la ligne (nuance visuelle par zone), sans modifier la forme extérieure.
- **LifeLineTooltip** : affichage d’information au survol (année, densité mock).
- **LifeLineLabels** (ou équivalent) : repères temporels discrets (Naissance, 20 ans, 40 ans, 60 ans, Aujourd’hui).

Cette structure est **indicative** : l’objectif est de séparer les responsabilités (orchestration, rendu axe/remplissage, repères, feedback hover) sans imposer une découpe figée. Aucun sous-composant dédié à une « impulsion » ou à une animation centrale n’est requis pour le cœur du concept.

---

## 12. Vue de comparaison de variantes

Possibilité de **comparer plusieurs rendus** de la Life Line côte à côte avec le **même dataset mock**, dans le cadre de la **même direction visuelle** (ligne stable, nuance interne).

Exemples de variantes cohérentes :

- Ligne très sobre vs ligne avec un peu plus de contraste
- **Fond clair vs fond sombre sobre** (comparaison explicite autorisée par le cadrage)
- Glow très léger vs sans glow

**But** : choisir la meilleure déclinaison (fond, contraste, glow optionnel) avant de figer la direction design. Les variantes ne doivent pas réintroduire des directions divergentes (organique, impulsion centrale, épaisseur variable).

---

## 13. Performance

Contraintes techniques pour le prototype :

- Le prototype doit rester **fluide** avec environ **80 années simulées** (ordre de grandeur d’une vie complète).
- Éviter un **DOM trop lourd** : privilégier un **SVG simple** et des **interactions sobres** (pas de multiplication d’éléments par année si un rendu agrégé suffit).

---

## 14. Milestone GitHub

**Nom :** `ECHO — Life Line Prototype v0`

**Description (texte du milestone) :**

> Prototype visuel autonome de la Life Line : une ligne horizontale unique, droite, épaisse, continue et stable, avec extrémités arrondies, représentant la vie de l’utilisateur de la naissance à aujourd’hui. La présence mémoire est traduite par une nuance visuelle sobre à l’intérieur de la ligne (zones plus lumineuses = plus de souvenirs), sans déformer sa forme. Repères temporels discrets et sobres (Naissance, 20 ans, 40 ans, 60 ans, Aujourd’hui). Prototype autonome dans le lab dédié : aucune intégration backend, aucune donnée réelle, données mock uniquement. Objectif : valider le rendu visuel et la lisibilité (compréhension en moins de 2 secondes), y compris sur fond clair et fond sombre sobre.

---

## 15. Découpage des issues (référence)

Voir le document **Recadrage des issues** (livrable 4) pour le détail : quelles issues garder, renommer, réécrire, fermer ou mettre en parking, et quelles nouvelles issues créer. Le tableau ci-dessous est une **référence cible** alignée avec la nouvelle direction.

| # | Titre | Objectif |
|---|--------|----------|
| — | Composant SVG — axe horizontal de base | Ligne horizontale unique, droite, épaisse, continue, extrémités arrondies, responsive. Forme constante. |
| — | Rendu présence mémoire (nuance interne) | À l’intérieur de la ligne : zones peu remplies = plus discrètes ; zones riches = plus lumineuses. Pas de variation d’épaisseur. |
| — | Repères temporels | Libellés discrets et sobres : Naissance, 20 ans, 40 ans, 60 ans, Aujourd’hui. Pas de libellés interprétatifs. |
| — | Fond et lisibilité (clair / sombre) | Fond cohérent avec la ligne ; comparaison fond clair vs fond sombre sobre autorisée. La ligne reste l’élément central. |
| — | Hover et sélection de zone | Détection de zone au survol, état actif, click (callback mock). |
| — | Tooltip / overlay d’information | Année et densité mock au survol ; phrase explicative possible. |
| — | Vue de comparaison de variantes | Variantes cohérentes (fond clair/sombre, contraste, glow optionnel), même direction visuelle. |
| — | Documentation finale et décision | Doc : lancement du lab, choix retenus, respect règle UX et critères de réussite, décision « prêt pour phase 2 » ou itérations. |

**Definition of done (commune)** : pas de régression sur l’existant ; pas de modification du backend ni des modèles métier ; pas de branchement sur les vrais souvenirs.

---

## 16. Fichiers principaux (lab, phase suivante)

- `apps/lifeline-lab/package.json`, `index.html`, `tsconfig.json`, `vite.config.ts`
- `apps/lifeline-lab/src/main.tsx`, `App.tsx`, `index.css` (design tokens)
- `apps/lifeline-lab/src/components/LifeLine.tsx` (et sous-composants : LifeLineAxis, LifeLineFill, LifeLineLabels, LifeLineTooltip)
- `apps/lifeline-lab/src/data/mockDensity.ts`

Aucune modification dans `apps/web-static/`, `services/` ou ailleurs. Le lab se lance seul : `cd apps/lifeline-lab && npm i && npm run dev`.
