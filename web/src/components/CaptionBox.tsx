import { useState, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import '../theme.css'
import './Preview.css'
import { cx } from './cx'
import type { SnapLines } from './safeZones'
import { dragBox, HANDLES, type Box, type Handle } from './snap'

export interface CaptionBoxProps {
  value: Box
  onChange: (box: Box) => void
  /** Lines to snap to (centre lines and safe-zone edges). */
  lines?: SnapLines
  children?: ReactNode
}

const HANDLE_POS: Record<Exclude<Handle, 'move'>, [number, number]> = {
  nw: [0, 0], n: [50, 0], ne: [100, 0], e: [100, 50],
  se: [100, 100], s: [50, 100], sw: [0, 100], w: [0, 50],
}

/** Draggable, resizable caption box. Place inside a position:relative 9:16 frame. */
export function CaptionBox({ value, onChange, lines = { xs: [0.5], ys: [0.5] }, children }: CaptionBoxProps) {
  const [dragging, setDragging] = useState(false)
  const [snapped, setSnapped] = useState<SnapLines>({ xs: [], ys: [] })

  const begin = (handle: Handle) => (ev: ReactPointerEvent) => {
    const frame = (ev.currentTarget as HTMLElement).closest('.caption-box')?.parentElement
    if (!frame || ev.button !== 0) return
    ev.preventDefault()
    ev.stopPropagation()
    const rect = frame.getBoundingClientRect()
    const start = value
    const sx = ev.clientX
    const sy = ev.clientY
    setDragging(true)

    const move = (e: PointerEvent) => {
      const res = dragBox(start, handle, (e.clientX - sx) / rect.width, (e.clientY - sy) / rect.height, lines)
      setSnapped(res.snapped)
      onChange(res.box)
    }
    const up = () => {
      setDragging(false)
      setSnapped({ xs: [], ys: [] })
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      window.removeEventListener('pointercancel', up)
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
    window.addEventListener('pointercancel', up)
  }

  const pct = (v: number) => `${v * 100}%`
  return (
    <>
      {snapped.xs.map((x) => (
        <div key={`x${x}`} className="snap-line is-x" style={{ left: pct(x) }} />
      ))}
      {snapped.ys.map((y) => (
        <div key={`y${y}`} className="snap-line is-y" style={{ top: pct(y) }} />
      ))}
      <div
        className={cx('caption-box', dragging && 'is-dragging')}
        style={{ left: pct(value.x), top: pct(value.y), width: pct(value.w), height: pct(value.h) }}
        onPointerDown={begin('move')}
      >
        {children}
        {HANDLES.map((h) => (
          <div
            key={h}
            data-h={h}
            className="caption-handle"
            style={{ left: `${HANDLE_POS[h][0]}%`, top: `${HANDLE_POS[h][1]}%` }}
            onPointerDown={begin(h)}
          />
        ))}
      </div>
    </>
  )
}
