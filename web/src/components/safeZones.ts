/** Platform UI overlays on a 9:16 frame, as fractions of frame width/height.
 * Approximate areas covered by each app's buttons, captions and header. */
export type Platform = 'tiktok' | 'shorts'

export interface Insets {
  top: number
  bottom: number
  left: number
  right: number
}

export const SAFE_ZONES: Record<Platform, Insets> = {
  tiktok: { top: 0.08, bottom: 0.2, left: 0.04, right: 0.14 },
  shorts: { top: 0.1, bottom: 0.19, left: 0.04, right: 0.16 },
}

export const PLATFORM_LABELS: Record<Platform, string> = {
  tiktok: 'TikTok',
  shorts: 'Shorts',
}

/** Union of the enabled platforms' insets (the strictest of each side). */
export function combinedInsets(enabled: Partial<Record<Platform, boolean>>): Insets | null {
  const on = (Object.keys(SAFE_ZONES) as Platform[]).filter((p) => enabled[p])
  if (on.length === 0) return null
  return on.reduce<Insets>(
    (acc, p) => ({
      top: Math.max(acc.top, SAFE_ZONES[p].top),
      bottom: Math.max(acc.bottom, SAFE_ZONES[p].bottom),
      left: Math.max(acc.left, SAFE_ZONES[p].left),
      right: Math.max(acc.right, SAFE_ZONES[p].right),
    }),
    { top: 0, bottom: 0, left: 0, right: 0 },
  )
}

export interface SnapLines {
  xs: number[]
  ys: number[]
}

/** Centre lines always; safe-zone edges for enabled platforms. */
export function snapLines(enabled: Partial<Record<Platform, boolean>>): SnapLines {
  const xs = [0.5]
  const ys = [0.5]
  const ins = combinedInsets(enabled)
  if (ins) {
    xs.push(ins.left, 1 - ins.right)
    ys.push(ins.top, 1 - ins.bottom)
  }
  return { xs, ys }
}
