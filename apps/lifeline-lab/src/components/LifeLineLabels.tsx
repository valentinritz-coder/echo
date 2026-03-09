/**
 * LifeLineLabels — repères temporels (issue #114)
 *
 * Libellés sobres et neutres : Naissance, 20 ans, 40 ans, 60 ans, Aujourd'hui.
 * Discrets mais lisibles. Gauche = passé, droite = présent.
 * Réf. docs/life-line-prototype-v0.md (section Repères temporels).
 */

export interface LifeLineLabelsProps {
  birthYear: number
  currentYear: number
}

const REPERES: readonly { label: string; ageOffset: number }[] = [
  { label: 'Naissance', ageOffset: 0 },
  { label: '20 ans', ageOffset: 20 },
  { label: '40 ans', ageOffset: 40 },
  { label: '60 ans', ageOffset: 60 },
  { label: "Aujourd'hui", ageOffset: -1 }, // -1 = 100%
]

export function LifeLineLabels({ birthYear, currentYear }: LifeLineLabelsProps) {
  const span = Math.max(1, currentYear - birthYear)

  const items = REPERES.filter(({ ageOffset }) => {
    if (ageOffset < 0) return true // Aujourd'hui toujours affiché à 100 %
    const position = (ageOffset / span) * 100
    return position < 100 // n'afficher que les âges strictement avant aujourd'hui
  }).map(({ label, ageOffset }) => {
    const position =
      ageOffset < 0 ? 100 : (ageOffset / span) * 100
    return { label, position }
  })

  return (
    <div
      className="lifeline__labels"
      role="list"
      aria-label="Repères temporels de la ligne de vie"
    >
      {items.map(({ label, position }) => (
        <span
          key={label}
          className={`lifeline__label ${label === 'Naissance' || label === "Aujourd'hui" ? 'lifeline__label--endpoint' : ''}`}
          role="listitem"
          style={{ left: `${position}%` }}
        >
          {label}
        </span>
      ))}
    </div>
  )
}
