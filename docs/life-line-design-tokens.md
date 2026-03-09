# Design tokens — Ligne de vie (prototype v0)

Proposition de variables visuelles pour le prototype de la Life Line. Alignée sur `docs/life-line-prototype-v0.md`. Exploitable pour le lab `apps/lifeline-lab/`.

**Contraintes respectées :** ligne droite, épaisse, continue, stable, extrémités arrondies ; présence mémoire traduite par une nuance interne (remplissage) ; pas de variation d’épaisseur pour la densité ; pas de logique centrée sur l’impulsion ; lisibilité immédiate ; possibilité de tester un thème clair et un thème sombre sobre.

---

## 1. Principes des tokens

- **Forme constante** : une seule épaisseur de ligne (hauteur), pas de min/max d’épaisseur pour la densité.
- **Extrémités arrondies** : rayon d’arrondi défini (cap ou border-radius selon implémentation).
- **Remplissage mémoire** : trois niveaux (faible / moyen / fort) pour la nuance interne (couleur / luminosité), sans changer la forme.
- **Glow** : très léger ou optionnel, pas au cœur du concept.
- **Fond** : tokens pour fond clair et fond sombre sobre, pour permettre la comparaison.

---

## 2. Tableau des tokens

### Thème clair (fond clair / blanc / très clair)

| Token | Valeur | Rôle |
|-------|--------|------|
| **Fond** | | |
| `--lifeline-bg-light` | `#ffffff` | Fond de la scène (blanc). Variante possible : `#f8f9fa`. |
| **Ligne de base** | | |
| `--lifeline-baseline-light` | `rgba(0, 0, 0, 0.08)` | Ligne visible sur toute la longueur lorsque le remplissage est minimal ; discrète, ne disparaît jamais. |
| **Remplissage mémoire** | | |
| `--lifeline-fill-low-light` | `rgba(0, 0, 0, 0.12)` | Zones peu remplies : plus discrètes, moins lumineuses. |
| `--lifeline-fill-mid-light` | `rgba(0, 0, 0, 0.25)` | Zones de présence moyenne. |
| `--lifeline-fill-high-light` | `rgba(0, 0, 0, 0.45)` | Zones riches : plus lumineuses / plus pleines à l’intérieur de la ligne. |
| **Texte** | | |
| `--lifeline-text-primary-light` | `#1a1a1a` | Texte principal (ex. phrase explicative). |
| `--lifeline-text-secondary-light` | `rgba(0, 0, 0, 0.5)` | Repères temporels (Naissance, 20 ans, etc.), discrets. |
| **Glow (optionnel)** | | |
| `--lifeline-glow-color-light` | `rgba(0, 0, 0, 0.06)` | Halo très léger autour de la ligne, optionnel. |
| `--lifeline-glow-blur` | `12px` | Flou du glow ; rester discret. |

### Thème sombre sobre

| Token | Valeur | Rôle |
|-------|--------|------|
| **Fond** | | |
| `--lifeline-bg-dark` | `#0e1419` | Fond sombre (aligné univers ECHO). |
| **Ligne de base** | | |
| `--lifeline-baseline-dark` | `rgba(255, 255, 255, 0.12)` | Ligne visible sur toute la longueur ; discrète. |
| **Remplissage mémoire** | | |
| `--lifeline-fill-low-dark` | `rgba(255, 255, 255, 0.18)` | Zones peu remplies. |
| `--lifeline-fill-mid-dark` | `rgba(255, 255, 255, 0.35)` | Zones de présence moyenne. |
| `--lifeline-fill-high-dark` | `rgba(255, 255, 255, 0.65)` | Zones riches : plus lumineuses à l’intérieur. |
| **Texte** | | |
| `--lifeline-text-primary-dark` | `#f0f0f0` | Texte principal. |
| `--lifeline-text-secondary-dark` | `rgba(255, 255, 255, 0.5)` | Repères temporels. |
| **Glow (optionnel)** | | |
| `--lifeline-glow-color-dark` | `rgba(255, 255, 255, 0.08)` | Halo très léger, optionnel. |
| `--lifeline-glow-blur` | `12px` | Flou du glow. |

### Communs (forme de la ligne)

| Token | Valeur | Rôle |
|-------|--------|------|
| **Forme** | | |
| `--lifeline-height` | `12px` | Hauteur (épaisseur) de la ligne. Constante sur toute la longueur. |
| `--lifeline-radius` | `6px` | Rayon des extrémités arrondies (demi-hauteur pour caps pleins, ou border-radius si rectangle). |
| `--lifeline-min-width` | `320px` | Largeur minimale de la ligne (responsive). |

---

## 3. Bloc CSS prêt à l’emploi

À placer dans `apps/lifeline-lab/src/index.css` (ou fichier tokens dédié) lors de la création du lab.

```css
/* -------------------------
   Life Line — design tokens (prototype v0)
   Réf. docs/life-line-design-tokens.md
   ------------------------- */
:root {
  /* Communs : forme de la ligne */
  --lifeline-height: 12px;
  --lifeline-radius: 6px;
  --lifeline-min-width: 320px;
  --lifeline-glow-blur: 12px;

  /* Thème clair */
  --lifeline-bg-light: #ffffff;
  --lifeline-baseline-light: rgba(0, 0, 0, 0.08);
  --lifeline-fill-low-light: rgba(0, 0, 0, 0.12);
  --lifeline-fill-mid-light: rgba(0, 0, 0, 0.25);
  --lifeline-fill-high-light: rgba(0, 0, 0, 0.45);
  --lifeline-text-primary-light: #1a1a1a;
  --lifeline-text-secondary-light: rgba(0, 0, 0, 0.5);
  --lifeline-glow-color-light: rgba(0, 0, 0, 0.06);

  /* Thème sombre sobre */
  --lifeline-bg-dark: #0e1419;
  --lifeline-baseline-dark: rgba(255, 255, 255, 0.12);
  --lifeline-fill-low-dark: rgba(255, 255, 255, 0.18);
  --lifeline-fill-mid-dark: rgba(255, 255, 255, 0.35);
  --lifeline-fill-high-dark: rgba(255, 255, 255, 0.65);
  --lifeline-text-primary-dark: #f0f0f0;
  --lifeline-text-secondary-dark: rgba(255, 255, 255, 0.5);
  --lifeline-glow-color-dark: rgba(255, 255, 255, 0.08);
}

/* Sélecteur optionnel pour basculer thème (ex. [data-theme="dark"]) */
[data-theme="dark"] {
  --lifeline-bg: var(--lifeline-bg-dark);
  --lifeline-baseline: var(--lifeline-baseline-dark);
  --lifeline-fill-low: var(--lifeline-fill-low-dark);
  --lifeline-fill-mid: var(--lifeline-fill-mid-dark);
  --lifeline-fill-high: var(--lifeline-fill-high-dark);
  --lifeline-text-primary: var(--lifeline-text-primary-dark);
  --lifeline-text-secondary: var(--lifeline-text-secondary-dark);
  --lifeline-glow-color: var(--lifeline-glow-color-dark);
}

[data-theme="light"],
:root {
  --lifeline-bg: var(--lifeline-bg-light);
  --lifeline-baseline: var(--lifeline-baseline-light);
  --lifeline-fill-low: var(--lifeline-fill-low-light);
  --lifeline-fill-mid: var(--lifeline-fill-mid-light);
  --lifeline-fill-high: var(--lifeline-fill-high-light);
  --lifeline-text-primary: var(--lifeline-text-primary-light);
  --lifeline-text-secondary: var(--lifeline-text-secondary-light);
  --lifeline-glow-color: var(--lifeline-glow-color-light);
}
```

---

## 4. Justification des choix

### Forme constante

- **Une seule hauteur** (`12px`) : la ligne ne varie pas d’épaisseur. La « densité » ou présence mémoire est rendue uniquement par la **nuance interne** (opacité / luminosité du remplissage), pas par l’épaisseur.
- **Rayon** (`6px` = demi-hauteur) : extrémités arrondies cohérentes avec une barre horizontale type pill.

### Remplissage mémoire (nuance interne)

- **Faible / moyen / fort** : interpolation possible entre ces trois niveaux selon la valeur mock (0–1) par année. La ligne de base reste visible ; le remplissage se superpose ou se fond à l’intérieur sans changer le contour.
- **Thème clair** : progression du noir avec opacité croissante (0.08 → 0.12 → 0.25 → 0.45) pour garder une bonne lisibilité sur fond blanc.
- **Thème sombre** : progression du blanc (0.12 → 0.18 → 0.35 → 0.65) pour le même principe sur fond sombre.

### Glow

- **Très léger et optionnel** : blur 12px, opacité faible. Ne doit pas devenir l’élément central ni rappeler un rendu « signal » ou néon.

### Fond

- **Clair** : blanc ou très clair pour maximiser la lisibilité et la compréhension rapide (aligné avec le cadrage « fond clair possible »).
- **Sombre** : `#0e1419` pour cohérence avec l’univers ECHO, en version sobre.

---

## 5. Utilisation dans le prototype

- **Interpolation** : pour une densité `d` dans [0, 1], interpoler la **couleur / opacité du remplissage** entre `--lifeline-fill-low`, `--lifeline-fill-mid` et `--lifeline-fill-high`. Ne pas interpoler l’épaisseur.
- **Forme** : utiliser `--lifeline-height` et `--lifeline-radius` pour le tracé SVG (rectangle avec border-radius ou path avec caps ronds).
- **Glow** : si utilisé, appliquer `--lifeline-glow-color` et `--lifeline-glow-blur` (filtre SVG ou box-shadow), de façon optionnelle.
- **Thème** : utiliser les variables dérivées `--lifeline-bg`, `--lifeline-baseline`, etc. selon `data-theme` pour comparer fond clair et fond sombre.

Aucun fichier du lab n’est créé dans le cadre de ce document ; ce document et le bloc CSS ci-dessus constituent le livrable, prêt à être repris dans le lab.
