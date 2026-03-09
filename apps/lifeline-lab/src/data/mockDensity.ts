/**
 * Modèle mock — densité temporelle (prototype v0)
 * Données par année pour la ligne de vie. Granularité = année.
 * Réf. docs/life-line-prototype-v0.md
 */

/** Une entrée année → densité (0 = aucune mémoire, 1 = très riche). */
export type YearDensity = {
  year: number
  density: number
}

/** Année de naissance simulée pour le dataset mock. */
export const BIRTH_YEAR = 1985

/** Année « actuelle » simulée pour le dataset mock. */
export const CURRENT_YEAR = 2025

/** Dataset mock : densité par année, de BIRTH_YEAR à CURRENT_YEAR (inclus). Contrastes marqués pour relief visuel. */
export const MOCK_DENSITY: readonly YearDensity[] = [
  { year: 1985, density: 0.0 },
  { year: 1986, density: 0.04 },
  { year: 1987, density: 0.08 },
  { year: 1988, density: 0.06 },
  { year: 1989, density: 0.12 },
  { year: 1990, density: 0.18 },
  { year: 1991, density: 0.14 },
  { year: 1992, density: 0.22 },
  { year: 1993, density: 0.28 },
  { year: 1994, density: 0.2 },
  { year: 1995, density: 0.35 },
  { year: 1996, density: 0.42 },
  { year: 1997, density: 0.38 },
  { year: 1998, density: 0.5 },
  { year: 1999, density: 0.58 },
  { year: 2000, density: 0.62 },
  { year: 2001, density: 0.48 },
  { year: 2002, density: 0.4 },
  { year: 2003, density: 0.52 },
  { year: 2004, density: 0.68 },
  { year: 2005, density: 0.78 },
  { year: 2006, density: 0.65 },
  { year: 2007, density: 0.5 },
  { year: 2008, density: 0.42 },
  { year: 2009, density: 0.38 },
  { year: 2010, density: 0.45 },
  { year: 2011, density: 0.55 },
  { year: 2012, density: 0.6 },
  { year: 2013, density: 0.55 },
  { year: 2014, density: 0.68 },
  { year: 2015, density: 0.75 },
  { year: 2016, density: 0.52 },
  { year: 2017, density: 0.48 },
  { year: 2018, density: 0.65 },
  { year: 2019, density: 0.82 },
  { year: 2020, density: 0.88 },
  { year: 2021, density: 0.72 },
  { year: 2022, density: 0.65 },
  { year: 2023, density: 0.78 },
  { year: 2024, density: 0.85 },
  { year: 2025, density: 0.92 },
] as const

/** Première année du dataset. */
export const MIN_YEAR = BIRTH_YEAR

/** Dernière année du dataset. */
export const MAX_YEAR = CURRENT_YEAR

/**
 * Ramène une valeur dans l’intervalle [0, 1] (densité).
 */
export function clampDensity(value: number): number {
  return Math.max(0, Math.min(1, value))
}

/**
 * Retourne la densité pour une année donnée, ou undefined si hors plage.
 */
export function getDensityForYear(year: number): number | undefined {
  const entry = MOCK_DENSITY.find((e) => e.year === year)
  return entry === undefined ? undefined : entry.density
}
