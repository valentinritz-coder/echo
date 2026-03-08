# Design tokens — Ligne de vie (prototype v0)

Proposition de variables visuelles pour le prototype de la ligne de vie. Alignée sur `docs/life-line-prototype-v0.md` et sur la palette Echo (`apps/web-static/styles.css`). Exploitable pour l’issue « Création du lab autonome » et les suivantes.

**Contraintes respectées :** fond sombre Echo, ligne discrète, densité = épaisseur + intensité, glow doux organique, pas de néon, lisibilité immédiate.

---

## 1. Tableau des tokens

| Token | Valeur | Rôle |
|-------|--------|------|
| **Fond** | | |
| `--lifeline-bg` | `#0e1419` | Couleur de fond de la scène (identique Echo). |
| **Ligne de base** | | |
| `--lifeline-baseline` | `rgba(96, 144, 178, 0.18)` | Couleur de la ligne lorsque la densité est nulle ou minimale ; discrète, même teinte que le halo Echo. |
| **Densité faible / moyenne / forte** | | |
| `--lifeline-density-low` | `rgba(96, 144, 178, 0.32)` | Zones pauvres en souvenirs : pâle, visible mais en retrait. |
| `--lifeline-density-mid` | `rgba(144, 178, 200, 0.58)` | Zones de densité moyenne ; transition lisible vers le bleu-gris accent. |
| `--lifeline-density-high` | `rgba(189, 213, 230, 0.85)` | Zones riches : lumineux, accent Echo (BDD5E6), sans effet néon. |
| **Glow** | | |
| `--lifeline-glow-color` | `rgba(96, 144, 178, 0.24)` | Couleur du halo autour de la ligne (organique, bioluminescent doux). |
| `--lifeline-glow-blur` | `20px` | Flou du glow ; reste contenu pour ne pas noyer l’écran. |
| **Épaisseur de la ligne** | | |
| `--lifeline-stroke-min` | `2px` | Épaisseur minimale (densité 0 ou très faible) ; reste visible sur tous les écrans. |
| `--lifeline-stroke-max` | `12px` | Épaisseur maximale (densité 1) ; contraste fort avec le min, sans dominer la vue. |
| **Impulsion lumineuse** | | |
| `--lifeline-pulse-duration` | `2.5s` | Durée de l’animation d’impulsion (par sens ou totale selon implémentation) ; lent, contemplatif. |
| `--lifeline-pulse-opacity` | `0.7` | Opacité maximale du trait d’impulsion ; visible mais non intrusive. |
| `--lifeline-pulse-color` | `rgba(189, 213, 230, 0.9)` | Couleur de l’impulsion ; alignée avec l’accent fort, légèrement plus vive que la ligne. |

---

## 2. Bloc CSS prêt à l’emploi

À placer dans `apps/lifeline-lab/src/index.css` (ou fichier tokens dédié) lors de la création du lab.

```css
/* -------------------------
   Life Line — design tokens (prototype v0)
   Réf. docs/life-line-design-tokens.md
   ------------------------- */
:root {
  /* Fond */
  --lifeline-bg: #0e1419;

  /* Ligne de base (densité nulle / minimale) */
  --lifeline-baseline: rgba(96, 144, 178, 0.18);

  /* Densité : faible → moyenne → forte */
  --lifeline-density-low: rgba(96, 144, 178, 0.32);
  --lifeline-density-mid: rgba(144, 178, 200, 0.58);
  --lifeline-density-high: rgba(189, 213, 230, 0.85);

  /* Glow (halo autour de la ligne) */
  --lifeline-glow-color: rgba(96, 144, 178, 0.24);
  --lifeline-glow-blur: 20px;

  /* Épaisseur de la ligne (stroke) */
  --lifeline-stroke-min: 2px;
  --lifeline-stroke-max: 12px;

  /* Impulsion lumineuse */
  --lifeline-pulse-duration: 2.5s;
  --lifeline-pulse-opacity: 0.7;
  --lifeline-pulse-color: rgba(189, 213, 230, 0.9);
}
```

---

## 3. Justification des choix

### Couleurs

- **Fond `#0e1419`** : identique à Echo pour une continuité visuelle forte et une ambiance déjà validée (sombre, calme).
- **Teinte bleu-gris (96, 144, 178) / (189, 213, 230)** : reprise de `--halo-soft` et des accents Echo ; évite toute couleur vive type néon et garde une lecture « filament vivant » / bioluminescence sobre.
- **Densité faible → forte** : progression d’opacité (0.18 → 0.32 → 0.58 → 0.85) et léger décalage de teinte vers le clair (144, 178, 200 puis 189, 213, 230) pour que les zones riches soient immédiatement identifiables sans être agressives.

### Plage d’épaisseurs (2px – 12px)

- **2px** : minimum lisible sur tous les écrans, y compris haute densité ; la ligne ne disparaît jamais.
- **12px** : contraste net avec les zones fines (rapport 1:6), suffisant pour « zones riches » sans que la ligne devienne un bandeau. Au-delà, risque de surcharge et de perte de lisibilité en < 2 s.

### Intensité du glow

- **0.24 + blur 20px** : légèrement plus marqué que le halo Echo (0.14) pour que la ligne ait une présence organique, tout en restant contenu pour ne pas éclairer toute la scène ni créer un effet néon.

### Vitesse d’animation (2.5s)

- **2.5s** : durée « lente et contemplative » ; l’impulsion reste perceptible sans attirer toute l’attention. Plus court = effet gadget ; plus long = risque d’être perçu comme lent ou bloqué.

### Opacité de l’impulsion (0.7)

- **0.7** : l’impulsion est bien visible sur le fond et sur la ligne, sans éblouir ni concurrencer le contenu principal (critère « animation douce et non intrusive »).

---

## 4. Utilisation dans le prototype

- **Interpolation** : pour une densité `d` dans [0, 1], le composant pourra interpoler linéairement entre `--lifeline-stroke-min` et `--lifeline-stroke-max` pour l’épaisseur, et entre `--lifeline-density-low`, `--lifeline-density-mid` et `--lifeline-density-high` (ou une interpolation continue) pour la couleur / opacité.
- **Impulsion** : utiliser `--lifeline-pulse-duration`, `--lifeline-pulse-opacity` et `--lifeline-pulse-color` pour l’animation bilatérale (CSS ou JS).
- **Glow** : optionnel ; si un halo le long de la ligne est ajouté, utiliser `--lifeline-glow-color` et `--lifeline-glow-blur` (ex. filtre SVG ou box-shadow).

Aucun fichier du lab n’est créé dans le cadre de cette issue ; ce document et le bloc CSS ci-dessus constituent le livrable, prêt à être repris à la création du lab.
