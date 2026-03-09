/**
 * Life Line — orchestrateur (prototype v0)
 *
 * Axe horizontal : ligne droite, épaisse, continue, stable, extrémités arrondies.
 * Remplissage mémoire (nuance interne) par année — issue #105.
 * Réf. docs/life-line-prototype-v0.md, docs/life-line-design-tokens.md
 */

import { LifeLineAxis } from './LifeLineAxis'
import { LifeLineFill } from './LifeLineFill'
import { LifeLineLabels } from './LifeLineLabels'
import { BIRTH_YEAR, CURRENT_YEAR, MOCK_DENSITY } from '../data/mockDensity'

export function LifeLine() {
  return (
    <div
      className="lifeline"
      role="img"
      aria-label="Ligne de vie — de la naissance à aujourd'hui"
    >
      <LifeLineAxis>
        <LifeLineFill data={MOCK_DENSITY} />
      </LifeLineAxis>
      <LifeLineLabels birthYear={BIRTH_YEAR} currentYear={CURRENT_YEAR} />
    </div>
  )
}
