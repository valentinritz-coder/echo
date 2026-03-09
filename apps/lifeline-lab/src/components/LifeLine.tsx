/**
 * Life Line — axe horizontal, signal de mémoire (prototype v0)
 * Réf. docs/life-line-prototype-v0.md, docs/life-line-design-tokens.md
 *
 * Rendu informatif : variations issues des données de densité (pas d’oscillation régulière).
 * Halo discret qui suit la densité ; corps lisible (zones pauvres / riches / transition en < 2 s).
 * Filament lumineux organique, sobre — signature visuelle Echo.
 */

import { MOCK_DENSITY } from '../data/mockDensity'

const VIEWBOX_MIN_X = -18
const VIEWBOX_WIDTH = 162
const VIEWBOX_HEIGHT = 10
const LINE_Y = VIEWBOX_HEIGHT / 2
const LINE_X_START = 12
const LINE_X_END = 126
const LINE_SPAN = LINE_X_END - LINE_X_START

/** Nombre de points par intervalle annuel pour lisser les transitions d’épaisseur. */
const SUBDIV = 32

/** Demi-épaisseur viewBox : min et max (densité 0 et 1). Profil « petites montagnes » bien marqué. */
const HALF_THICKNESS_MIN = 0.03
const HALF_THICKNESS_MAX = 4.0

/** Couleurs densité : contraste marqué pour lisibilité zones (pauvre / transition / riche). */
const DENSITY_LOW = { r: 96, g: 144, b: 178, a: 0.2 }
const DENSITY_MID = { r: 144, g: 178, b: 200, a: 0.55 }
const DENSITY_HIGH = { r: 189, g: 213, b: 230, a: 0.92 }

/** Courbe densité → épaisseur : exposant > 1 pour réduire le mid, garder les pics bien marqués. */
const THICKNESS_CURVE = 2.0

function densityToHalfThickness(density: number): number {
  const d = Math.max(0, Math.min(1, density))
  const t = Math.pow(d, THICKNESS_CURVE)
  return HALF_THICKNESS_MIN + (HALF_THICKNESS_MAX - HALF_THICKNESS_MIN) * t
}

/**
 * Densité → couleur avec passage par mid. Pas d’arrondi RGB pour limiter le banding à 100% zoom.
 */
function smoothstep(t: number): number {
  const s = Math.max(0, Math.min(1, t))
  return s * s * (3 - 2 * s)
}

function densityToColor(density: number): string {
  const d = Math.max(0, Math.min(1, density))
  let r: number, g: number, b: number, a: number
  if (d <= 0.5) {
    const t = smoothstep(d / 0.5)
    r = DENSITY_LOW.r + (DENSITY_MID.r - DENSITY_LOW.r) * t
    g = DENSITY_LOW.g + (DENSITY_MID.g - DENSITY_LOW.g) * t
    b = DENSITY_LOW.b + (DENSITY_MID.b - DENSITY_LOW.b) * t
    a = DENSITY_LOW.a + (DENSITY_MID.a - DENSITY_LOW.a) * t
  } else {
    const t = smoothstep((d - 0.5) / 0.5)
    r = DENSITY_MID.r + (DENSITY_HIGH.r - DENSITY_MID.r) * t
    g = DENSITY_MID.g + (DENSITY_HIGH.g - DENSITY_MID.g) * t
    b = DENSITY_MID.b + (DENSITY_HIGH.b - DENSITY_MID.b) * t
    a = DENSITY_MID.a + (DENSITY_HIGH.a - DENSITY_MID.a) * t
  }
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

/** Halo : même teinte que le corps, opacité très faible — suit la densité sans dominer. */
function densityToHaloColor(density: number): string {
  const d = Math.max(0, Math.min(1, density))
  let r: number, g: number, b: number, a: number
  if (d <= 0.5) {
    const t = smoothstep(d / 0.5)
    r = DENSITY_LOW.r + (DENSITY_MID.r - DENSITY_LOW.r) * t
    g = DENSITY_LOW.g + (DENSITY_MID.g - DENSITY_LOW.g) * t
    b = DENSITY_LOW.b + (DENSITY_MID.b - DENSITY_LOW.b) * t
    a = 0.04 + 0.05 * t
  } else {
    const t = smoothstep((d - 0.5) / 0.5)
    r = DENSITY_MID.r + (DENSITY_HIGH.r - DENSITY_MID.r) * t
    g = DENSITY_MID.g + (DENSITY_HIGH.g - DENSITY_MID.g) * t
    b = DENSITY_MID.b + (DENSITY_HIGH.b - DENSITY_MID.b) * t
    a = 0.09 + 0.06 * t
  }
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

/**
 * Construit les points (x, density) avec sous-division.
 */
function buildSubdividedPoints(
  data: readonly { year: number; density: number }[],
): { x: number; density: number }[] {
  const n = data.length
  const points: { x: number; density: number }[] = []
  for (let j = 0; j < n - 1; j++) {
    const dStart = data[j].density
    const dEnd = data[j + 1].density
    for (let k = 0; k < SUBDIV; k++) {
      const t = k / SUBDIV
      const x = LINE_X_START + ((j + t) / (n - 1)) * LINE_SPAN
      const density = dStart + (dEnd - dStart) * t
      points.push({ x, density })
    }
  }
  points.push({
    x: LINE_X_END,
    density: data[n - 1].density,
  })
  return points
}

/** Rayon de lissage : faible pour que les variations viennent des données, pas d’effet « vague » régulière. */
const SMOOTH_RADIUS = 6

/**
 * Lisse légèrement les densités pour continuité visuelle, sans écraser les transitions réelles.
 */
function smoothDensities(points: { x: number; density: number }[]): { x: number; density: number }[] {
  const n = points.length
  return points.map((p, i) => {
    let sum = 0
    let count = 0
    for (let j = Math.max(0, i - SMOOTH_RADIUS); j <= Math.min(n - 1, i + SMOOTH_RADIUS); j++) {
      sum += points[j].density
      count += 1
    }
    return { x: p.x, density: sum / count }
  })
}

/**
 * Construit le path SVG fermé (bordure haute puis basse) pour une ligne continue lissée.
 */
function buildSmoothPathD(
  points: { x: number; density: number }[],
): string {
  const top = points.map((p) => `${p.x},${LINE_Y - densityToHalfThickness(p.density)}`)
  const bottom = points
    .slice()
    .reverse()
    .map((p) => `${p.x},${LINE_Y + densityToHalfThickness(p.density)}`)
  const pathPoints = [...top, ...bottom]
  if (pathPoints.length < 2) return ''
  return `M ${pathPoints[0]} L ${pathPoints.slice(1).join(' L ')} Z`
}

export function LifeLine() {
  const data = MOCK_DENSITY
  const points = smoothDensities(buildSubdividedPoints(data))
  const pathD = buildSmoothPathD(points)

  return (
    <div className="lifeline" role="img" aria-label="Ligne de vie — axe temporel avec densité">
      <svg
        className="lifeline-axis"
        viewBox={`${VIEWBOX_MIN_X} 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        width="100%"
        height="32"
      >
        <defs>
          <filter
            id="lifeline-halo"
            x="-35%"
            y="-120%"
            width="170%"
            height="340%"
            filterUnits="objectBoundingBox"
          >
            <feGaussianBlur in="SourceGraphic" stdDeviation="0.95" />
          </filter>
          <filter
            id="lifeline-soft"
            x="-20%"
            y="-80%"
            width="140%"
            height="260%"
            filterUnits="objectBoundingBox"
          >
            <feGaussianBlur in="SourceGraphic" stdDeviation="0.15" />
          </filter>
          <linearGradient
            id="lifeline-gradient"
            gradientUnits="userSpaceOnUse"
            x1={LINE_X_START}
            y1={0}
            x2={LINE_X_END}
            y2={0}
          >
            {points.map((p, i) => (
              <stop
                key={i}
                offset={(p.x - LINE_X_START) / LINE_SPAN}
                stopColor={densityToColor(p.density)}
              />
            ))}
          </linearGradient>
          <linearGradient
            id="lifeline-halo-gradient"
            gradientUnits="userSpaceOnUse"
            x1={LINE_X_START}
            y1={0}
            x2={LINE_X_END}
            y2={0}
          >
            {points.map((p, i) => (
              <stop
                key={`halo-${i}`}
                offset={(p.x - LINE_X_START) / LINE_SPAN}
                stopColor={densityToHaloColor(p.density)}
              />
            ))}
          </linearGradient>
        </defs>
        <path
          className="lifeline-halo"
          d={pathD}
          fill="url(#lifeline-halo-gradient)"
          filter="url(#lifeline-halo)"
        />
        <path
          className="lifeline-shape"
          d={pathD}
          fill="url(#lifeline-gradient)"
          filter="url(#lifeline-soft)"
        />
      </svg>
    </div>
  )
}
