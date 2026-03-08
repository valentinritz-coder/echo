# Ligne de vie — Prototype v0 (Echo)

Document de cadrage pour la feature « ligne de vie » : vision, périmètre phase 1, échelle temporelle, règle UX, critères de réussite, design tokens, structure du composant, issues et plan d’implémentation. Aucune intégration backend ni données réelles ; prototype autonome dans le lab dédié.

---

## 1. Vision

La **ligne de vie** doit devenir une pièce maîtresse de l’interface Echo.

**Principes non négociables :**

- **Axe horizontal unique** : la ligne est un axe horizontal, jamais vertical, en cercles ou en arbre.
- **Vie complète** : elle représente la vie de l’utilisateur de la **naissance** jusqu’à l’**âge actuel**.
- **Densité = épaisseur + intensité** : la densité de mémoire est représentée uniquement par l’épaisseur du trait et l’intensité de la couleur (zones pauvres = fines, pâles ; zones riches = épaisses, lumineuses).
- **Aucun point, cercle ni icône sur la ligne** : pas de points, cercles, anneaux, icônes ou marqueurs sur la ligne elle-même.
- **Esthétique** : organique, vivante, légèrement bioluminescente — filament vivant / plante luminescente, sobre et élégant.

**À éviter** : effet néon agressif, waveform audio technique, visualisation analytique froide.

---

## 2. Périmètre phase 1

**Objectif** : valider le rendu visuel, les micro-interactions et l’impulsion lumineuse avant toute intégration produit.

**Contraintes du prototype (explicites) :**

- **Prototype autonome** : aucun branchement sur le reste du produit Echo.
- **Données mock uniquement** : pas d’API, pas de modèles métier, pas de données réelles.
- **Lab dédié** : tout le travail se fait dans `apps/lifeline-lab/` (Vite + React + TypeScript + SVG).
- **Aucune intégration backend** : pas de modification du backend, des apps existantes ni des vrais souvenirs.

---

## 3. Concept visuel

- Un **axe horizontal unique** ; pas de points, cercles, anneaux, icônes ou arbre sur la ligne.
- **Densité** = épaisseur du trait + intensité de la couleur.
- **Animation** : impulsion lumineuse douce qui peut parcourir la ligne ; sur « nouveau souvenir » simulé (année donnée), l’impulsion part de ce point vers la naissance et vers l’âge actuel. Lent, contemplatif.
- **Interactions prototype** : hover → détection de zone + état actif ; tooltip → année + densité mock ; click → callback mock ou log. Pas de navigation métier.

---

## 4. Échelle temporelle

- La ligne représente la **vie complète** de l’utilisateur : de la **naissance** jusqu’à l’**âge actuel**.
- Pour le **prototype v0**, la **granularité de base est l’année** : les données mock sont structurées **par année**, et la densité est **calculée par année**.
- Une évolution future vers un zoom (année → mois) est envisageable ; ce n’est **pas** le périmètre du prototype actuel.

**Exemple de structure conceptuelle des données mock (année → densité, 0–1) :**

| Année | Densité |
|-------|---------|
| 1990  | 0.1     |
| 1991  | 0.0     |
| 1992  | 0.4     |
| 1993  | 0.8     |

Cette granularité annuelle est figée pour le v0 afin d’éviter toute ambiguïté technique.

---

## 5. Règle UX

**Lisibilité immédiate** : la ligne de vie doit être **compréhensible en moins de 2 secondes**. Si l’utilisateur doit réfléchir pour comprendre l’axe, la densité ou l’animation, alors le design est trop complexe.

Cette règle sert de **critère de validation UX** du prototype : tout rendu ou interaction qui nécessite une explication pour être compris doit être simplifié.

---

## 6. Critères de réussite du prototype

Pour considérer le prototype comme réussi :

- La **ligne est compréhensible en moins de 2 secondes** (aligné avec la règle UX).
- La **densité est immédiatement perceptible** : l’utilisateur perçoit sans effort les zones riches et pauvres en souvenirs.
- L’**animation reste douce et non intrusive** : l’impulsion lumineuse ne distrait pas ni ne surcharge l’écran.

---

## 7. Design tokens

Avant de développer le composant, les **variables visuelles** sont figées dans une issue dédiée (« Design tokens — Life Line »). Exemples de paramètres à documenter :

- Couleur de fond
- Couleur de ligne de base
- Couleur densité faible / moyenne / forte
- Intensité du glow
- Épaisseur min / max de la ligne
- Vitesse d’impulsion

**Livrable** : bloc de variables CSS ou tokens documentés (dans le lab, ex. `src/index.css` ou fichier dédié).

---

## 8. Structure du composant

Architecture indicative pour éviter un composant monolithique et garder un code lisible et maintenable.

**Composant principal :**

- **LifeLine** : orchestrateur global ; gère les données (mock), les interactions et la coordination des sous-composants.

**Sous-composants possibles :**

- **LifeLineAxis** : rendu SVG principal de l’axe (conteneur de la ligne).
- **LifeLineSegment** : rendu visuel d’un segment temporel / une tranche de densité (épaisseur + intensité par année ou par groupe d’années).
- **LifeLinePulse** : animation d’impulsion lumineuse le long de la ligne.
- **LifeLineTooltip** : affichage d’information au survol (année, densité mock).

Cette structure est **indicative** : l’objectif est de séparer clairement les responsabilités (orchestration, rendu axe/segments, animation, feedback hover) sans imposer une découpe figée.

---

## 9. Vue de comparaison de variantes

Feature centrale pour Echo : pouvoir **comparer plusieurs rendus** de la ligne de vie côte à côte avec le **même dataset mock**.

Exemples de variantes :

- Ligne très sobre
- Ligne organique
- Ligne avec glow un peu plus marqué

**But** : choisir la meilleure représentation visuelle avant de figer la direction design.

---

## 10. Performance

Contraintes techniques pour encadrer les choix d’implémentation du prototype :

- Le prototype doit rester **fluide** avec environ **80 années simulées** (ordre de grandeur d’une vie complète).
- L’**animation d’impulsion** ne doit pas provoquer de **re-renders inutiles** (privilégier CSS ou une logique d’animation isolée).
- Éviter un **DOM trop lourd** : privilégier un **SVG simple** et des **interactions sobres** (pas de multiplication d’éléments par année si un rendu agrégé suffit).

---

## 11. Milestone GitHub

**Nom :** `ECHO — Life Line Prototype v0`

**Objectif :** Prototype visuel autonome de la ligne de vie (axe horizontal, densité = épaisseur + intensité, aspect organique/luminescent, impulsion bilatérale, interactions mock), sans intégration backend ni métier.

---

## 12. Découpage des issues

| # | Titre | Objectif | Dépendances |
|---|--------|----------|-------------|
| 1 | **Spec produit et direction visuelle** | Cadrer vision, périmètre, rendu visuel, animation et interactions pour le prototype. | — |
| 2 | **Design tokens — Life Line** | Définir les variables visuelles (couleur fond, ligne base, densité faible/moyenne/forte, glow, épaisseur min/max, vitesse impulsion). Livrable : bloc de variables CSS ou tokens documentés. | #1 |
| 3 | **Création du lab autonome** | Créer `apps/lifeline-lab/` avec Vite, React, TypeScript, une page unique et un fond inspiré Echo. | #1, #2 |
| 4 | **Modèle mock — densité temporelle** | Données factices structurées **par année** : une valeur de densité (0–1) par année. Structure lisible (tableau ou map année → densité), cohérente avec l’échelle temporelle v0. | #3 |
| 5 | **Composant SVG — axe horizontal de base** | Un axe horizontal unique (ligne SVG), sans points, responsive. Utilise les données mock par année ; structure prête pour segments (LifeLineAxis / LifeLineSegment) selon la structure du composant. | #3, #4 |
| 6 | **Rendu densité (épaisseur + intensité)** | Déduire de la densité mock par année : épaisseur du trait et intensité (opacité/couleur). Zones pauvres = fin/pâle, zones riches = épais/lumineux. Aspect organique. | #5 |
| 7 | **Background et ambiance lumineuse** | Fond cohérent Echo (#0e1419), halo doux (type halo-soft), pas néon. Optionnel : léger glow le long de la ligne. | #3 |
| 8 | **Hover et sélection de zone** | Détection de la zone temporelle (année) au survol, état actif, gestion du click (callback mock ou log). Pas de navigation métier. | #6 |
| 9 | **Tooltip / overlay d’information** | Afficher année et densité mock au survol ; positionnement et style sobre. | #8 |
| 10 | **Impulsion lumineuse bilatérale** | Animation douce : impulsion qui parcourt la ligne. Sur « nouveau souvenir » simulé (année donnée), impulsion part de ce point vers naissance et vers présent. Lent, contemplatif. Sans re-renders excessifs (voir contraintes performance). | #6 |
| 11 | **Vue de comparaison de variantes** | Afficher plusieurs versions de la ligne de vie côte à côte avec le même dataset mock (sobre, organique, glow plus marqué). Choisir la meilleure représentation visuelle. | #6, #7 |
| 12 | **Documentation finale et décision** | Doc : comment lancer le lab, choix retenus (variante, palette), respect de la règle UX (lisibilité &lt; 2 s) et des contraintes performance, décision « prêt pour phase 2 » ou itérations. | #1–#11 |

**Definition of done (commune)** : pas de régression sur l’existant ; pas de modification du backend ni des modèles métier ; pas de branchement sur les vrais souvenirs.

---

## 13. Ordre d’implémentation recommandé

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

- **#1–#2** : cadrage et tokens (aucun code lab).
- **#3** : création du lab (structure, pas encore la ligne).
- **#4–#6** : données mock par année, axe SVG, rendu densité.
- **#7** : background et ambiance.
- **#8–#9** : interactions (hover/sélection, tooltip).
- **#10** : impulsion lumineuse.
- **#11** : vue de comparaison des variantes.
- **#12** : documentation et décision.

---

## 14. Fichiers principaux (lab, phase suivante)

- `apps/lifeline-lab/package.json`, `index.html`, `tsconfig.json`, `vite.config.ts`
- `apps/lifeline-lab/src/main.tsx`, `App.tsx`, `index.css` (design tokens)
- `apps/lifeline-lab/src/components/LifeLine.tsx` (et sous-composants éventuels : LifeLineAxis, LifeLineSegment, LifeLinePulse, LifeLineTooltip)
- `apps/lifeline-lab/src/data/mockDensity.ts`

Aucune modification dans `apps/web-static/`, `services/` ou ailleurs. Le lab se lance seul : `cd apps/lifeline-lab && npm i && npm run dev`.
