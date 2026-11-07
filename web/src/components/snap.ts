import type { SnapLines } from './safeZones'

/** Caption box in frame fractions. x, y are the centre; w, h the size. */
export interface Box {
  x: number
  y: number
  w: number
  h: number
}

export type Handle = 'move' | 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw'

export const HANDLES: Exclude<Handle, 'move'>[] = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w']

export const SNAP_DIST = 0.015
export const MIN_W = 0.15
export const MIN_H = 0.05

interface Edges {
  l: number
  r: number
  t: number
  b: number
}

const toEdges = (b: Box): Edges => ({
  l: b.x - b.w / 2,
  r: b.x + b.w / 2,
  t: b.y - b.h / 2,
  b: b.y + b.h / 2,
})

const toBox = (e: Edges): Box => ({
  x: (e.l + e.r) / 2,
  y: (e.t + e.b) / 2,
  w: e.r - e.l,
  h: e.b - e.t,
})

/** Smallest offset that puts one of `points` on one of `lines`, if within SNAP_DIST. */
function nearest(points: number[], lines: number[]): { delta: number; line: number } | null {
  let best: { delta: number; line: number } | null = null
  for (const p of points)
    for (const line of lines) {
      const d = line - p
      if (Math.abs(d) <= SNAP_DIST && (!best || Math.abs(d) < Math.abs(best.delta)))
        best = { delta: d, line }
    }
  return best
}

export interface DragResult {
  box: Box
  /** Lines the box snapped to (for drawing guides). */
  snapped: SnapLines
}

/** Apply a drag of (dx, dy) frame fractions on `handle` to `start`, clamped and snapped. */
export function dragBox(start: Box, handle: Handle, dx: number, dy: number, lines: SnapLines): DragResult {
  const e = toEdges(start)
  const snapped: SnapLines = { xs: [], ys: [] }

  if (handle === 'move') {
    let { l, r, t, b } = e
    l += dx
    r += dx
    t += dy
    b += dy
    // Keep inside the frame.
    const sx = l < 0 ? -l : r > 1 ? 1 - r : 0
    const sy = t < 0 ? -t : b > 1 ? 1 - b : 0
    l += sx
    r += sx
    t += sy
    b += sy
    const nx = nearest([l, (l + r) / 2, r], lines.xs)
    if (nx) {
      l += nx.delta
      r += nx.delta
      snapped.xs.push(nx.line)
    }
    const ny = nearest([t, (t + b) / 2, b], lines.ys)
    if (ny) {
      t += ny.delta
      b += ny.delta
      snapped.ys.push(ny.line)
    }
    return { box: toBox({ l, r, t, b }), snapped }
  }

  const n = { ...e }
  const snapEdge = (v: number, ls: number[], out: number[]) => {
    const hit = nearest([v], ls)
    if (!hit) return v
    out.push(hit.line)
    return hit.line
  }
  if (handle.includes('w')) n.l = Math.min(Math.max(0, snapEdge(e.l + dx, lines.xs, snapped.xs)), e.r - MIN_W)
  if (handle.includes('e')) n.r = Math.max(Math.min(1, snapEdge(e.r + dx, lines.xs, snapped.xs)), e.l + MIN_W)
  if (handle.includes('n')) n.t = Math.min(Math.max(0, snapEdge(e.t + dy, lines.ys, snapped.ys)), e.b - MIN_H)
  if (handle.includes('s')) n.b = Math.max(Math.min(1, snapEdge(e.b + dy, lines.ys, snapped.ys)), e.t + MIN_H)
  return { box: toBox(n), snapped }
}
