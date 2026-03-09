/**
 * LifeLineFill — rendu présence mémoire (issue #105)
 *
 * Nuance visuelle à l’intérieur de la ligne : zones peu remplies = plus discrètes,
 * zones riches = plus lumineuses. La forme de la ligne ne change pas.
 * Réf. docs/life-line-prototype-v0.md, docs/life-line-design-tokens.md
 */

import { useEffect, useMemo, useState } from 'react'
import type { YearDensity } from '../data/mockDensity'

const FILL_LOW_VAR = '--lifeline-fill-low'
const FILL_MID_VAR = '--lifeline-fill-mid'
const FILL_HIGH_VAR = '--lifeline-fill-high'

interface Rgba {
  r: number
  g: number
  b: number
  a: number
}

function parseHex(value: string): Rgba | null {
  const trimmed = value.trim().replace(/^#/, '')
  if (trimmed.length !== 6) return null
  const n = parseInt(trimmed, 16)
  if (Number.isNaN(n)) return null
  return {
    r: (n >> 16) & 0xff,
    g: (n >> 8) & 0xff,
    b: n & 0xff,
    a: 1,
  }
}

function parseRgba(value: string): Rgba | null {
  const trimmed = value.trim()
  if (trimmed.startsWith('#')) return parseHex(trimmed)
  const rgba = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$/.exec(
    trimmed
  )
  if (!rgba) return null
  return {
    r: Number(rgba[1]),
    g: Number(rgba[2]),
    b: Number(rgba[3]),
    a: rgba[4] !== undefined ? Number(rgba[4]) : 1,
  }
}

function mix(c1: Rgba, c2: Rgba, t: number): string {
  const u = Math.max(0, Math.min(1, t))
  return `rgba(${Math.round(c1.r + (c2.r - c1.r) * u)}, ${Math.round(
    c1.g + (c2.g - c1.g) * u
  )}, ${Math.round(c1.b + (c2.b - c1.b) * u)}, ${c1.a + (c2.a - c1.a) * u})`
}

/** Courbe pour mieux séparer visuellement low / mid / high (sans changer les données). */
function visualDensity(d: number): number {
  const t = Math.max(0, Math.min(1, d))
  return t ** 0.64
}

function densityToColor(density: number, low: Rgba, mid: Rgba, high: Rgba): string {
  const d = visualDensity(density)
  if (d <= 0.5) return mix(low, mid, d / 0.5)
  return mix(mid, high, (d - 0.5) / 0.5)
}

/* Aligné thème clair (fine-tuning hiérarchie low / mid / high) */
const FALLBACK_FILL: { low: Rgba; mid: Rgba; high: Rgba } = {
  low: { r: 183, g: 197, b: 211, a: 1 },
  mid: { r: 136, g: 196, b: 232, a: 1 },
  high: { r: 85, g: 223, b: 242, a: 1 },
}

function getFillColors(): { low: Rgba; mid: Rgba; high: Rgba } {
  if (typeof document === 'undefined') return FALLBACK_FILL
  const style = getComputedStyle(document.documentElement)
  const low = parseRgba(style.getPropertyValue(FILL_LOW_VAR).trim())
  const mid = parseRgba(style.getPropertyValue(FILL_MID_VAR).trim())
  const high = parseRgba(style.getPropertyValue(FILL_HIGH_VAR).trim())
  if (!low || !mid || !high) return FALLBACK_FILL
  return { low, mid, high }
}

export interface LifeLineFillProps {
  data: readonly YearDensity[]
}

export function LifeLineFill({ data }: LifeLineFillProps) {
  const [colors, setColors] = useState<{ low: Rgba; mid: Rgba; high: Rgba }>(
    FALLBACK_FILL
  )

  useEffect(() => {
    setColors(getFillColors())
  }, [])

  const gradient = useMemo(() => {
    if (data.length === 0) return undefined
    const n = data.length
    const stops = data
      .map((entry, i) => {
        const position = n > 1 ? (i / (n - 1)) * 100 : 50
        const color = densityToColor(
          entry.density,
          colors.low,
          colors.mid,
          colors.high
        )
        return `${color} ${position}%`
      })
      .join(', ')
    return `linear-gradient(to right, ${stops})`
  }, [data, colors])

  if (!gradient) return null

  return (
    <div className="lifeline__fill" aria-hidden role="presentation">
      <div
        className="lifeline__fill-inner"
        style={{ background: gradient }}
      />
    </div>
  )
}
