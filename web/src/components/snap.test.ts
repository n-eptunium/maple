import { describe, expect, it } from 'vitest'
import { snapLines } from './safeZones'
import { dragBox, MIN_W, type Box } from './snap'

const box: Box = { x: 0.5, y: 0.5, w: 0.4, h: 0.1 }
const lines = snapLines({ tiktok: true })

describe('dragBox', () => {
  it('snaps the centre to the centre line', () => {
    const r = dragBox(box, 'move', 0.01, 0, lines)
    expect(r.box.x).toBeCloseTo(0.5)
    expect(r.snapped.xs).toEqual([0.5])
  })

  it('snaps the bottom edge to the safe-zone edge', () => {
    // TikTok bottom inset 0.2 => line at 0.8; box bottom 0.55 dragged by 0.24 => 0.79.
    const r = dragBox(box, 'move', 0, 0.24, lines)
    expect(r.box.y + r.box.h / 2).toBeCloseTo(0.8)
  })

  it('keeps a minimum width when resizing', () => {
    const r = dragBox(box, 'e', -1, 0, lines)
    expect(r.box.w).toBeCloseTo(MIN_W)
  })

  it('stays inside the frame', () => {
    const r = dragBox(box, 'move', -2, -2, { xs: [], ys: [] })
    expect(r.box.x - r.box.w / 2).toBeCloseTo(0)
    expect(r.box.y - r.box.h / 2).toBeCloseTo(0)
  })
})
