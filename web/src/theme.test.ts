import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const css = readFileSync(new URL('./theme.css', import.meta.url), 'utf8')

const TOKENS: Record<string, string> = {
  '--bg': '#e8eef6',
  '--panel': '#ffffff',
  '--ink': '#1f2940',
  '--muted': '#7d889e',
  '--line': '#d2dbe8',
  '--sel': '#19c3f0',
  '--accent': '#2f5bff',
  '--accent-d': '#1e3fc4',
  '--good': '#2ec76b',
  '--gold': '#ffd23f',
  '--stage': '#141c46',
  '--scene': '#2f7bff',
  '--font': "'Fredoka', system-ui, sans-serif",
}

describe('theme.css', () => {
  it.each(Object.entries(TOKENS))('defines %s', (name, value) => {
    const m = css.match(new RegExp(`${name}:\\s*([^;]+);`))
    expect(m?.[1].trim()).toBe(value)
  })

  it('bundles Fredoka locally', () => {
    expect(css).toMatch(/@font-face\s*{[^}]*font-family:\s*'Fredoka'[^}]*url\('\/fonts\/Fredoka\.ttf'\)/)
    expect(css).not.toMatch(/fonts\.googleapis|fonts\.gstatic/)
  })
})

describe('caption preview font', () => {
  const preview = readFileSync(new URL('./components/Preview.css', import.meta.url), 'utf8')
  it('loads the bundled Dosis-Bold.ttf, not Fredoka', () => {
    expect(preview).toMatch(/font-family:\s*'Dosis'[^}]*url\('\/fonts\/Dosis-Bold\.ttf'\)/)
    expect(preview).toMatch(/\.caption-text\s*{[^}]*font-family:\s*'Dosis'/)
  })
})
