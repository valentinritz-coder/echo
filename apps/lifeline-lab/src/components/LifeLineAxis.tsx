/**
 * LifeLineAxis — axe horizontal de base (issue #104)
 *
 * Ligne droite, épaisse, continue, stable. Extrémités = demi-cercles de diamètre 12px
 * (hauteur de la barre). Pas de points, cercles ni marqueurs.
 * Les children (ex. LifeLineFill) sont rendus au-dessus du track.
 * Réf. docs/life-line-prototype-v0.md, docs/life-line-design-tokens.md
 */

import type { ReactNode } from 'react'

export interface LifeLineAxisProps {
  children?: ReactNode
}

export function LifeLineAxis({ children }: LifeLineAxisProps) {
  return (
    <div
      className="lifeline__axis"
      role="presentation"
      aria-hidden
    >
      <div className="lifeline__axis-track" />
      {children}
    </div>
  )
}
