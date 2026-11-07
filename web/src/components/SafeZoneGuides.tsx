import type { CSSProperties } from 'react'
import '../theme.css'
import './Preview.css'
import { SAFE_ZONES, type Platform } from './safeZones'

export interface SafeZoneGuidesProps {
  /** Which platforms' UI overlays to draw. */
  platforms: Partial<Record<Platform, boolean>>
}

/** Translucent red bands where TikTok / Shorts UI covers the video. */
export function SafeZoneGuides({ platforms }: SafeZoneGuidesProps) {
  const on = (Object.keys(SAFE_ZONES) as Platform[]).filter((p) => platforms[p])
  return (
    <div className="safe-zones" aria-hidden>
      {on.flatMap((p) => {
        const z = SAFE_ZONES[p]
        const mid = { top: `${z.top * 100}%`, bottom: `${z.bottom * 100}%` }
        const bands: CSSProperties[] = [
          { left: 0, right: 0, top: 0, height: `${z.top * 100}%` },
          { left: 0, right: 0, bottom: 0, height: `${z.bottom * 100}%` },
          { ...mid, left: 0, width: `${z.left * 100}%` },
          { ...mid, right: 0, width: `${z.right * 100}%` },
        ]
        return bands.map((style, i) => <div key={`${p}${i}`} className="safe-band" style={style} />)
      })}
    </div>
  )
}
