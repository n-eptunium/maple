import type { ReactNode } from 'react'
import '../theme.css'
import './Scene.css'
import { cx } from './cx'

export interface SceneScreenProps {
  title: string
  emoji?: string
  /** White pills (PillButton surface="scene"). */
  children?: ReactNode
  /** Fill the nearest positioned parent instead of the window (Playground). */
  contained?: boolean
}

/** Full-screen scene blue: welcome and "Posted!" only. */
export function SceneScreen({ title, emoji, children, contained }: SceneScreenProps) {
  return (
    <div className={cx('scene-screen pop-in', contained && 'is-contained')}>
      {emoji && (
        <div className="scene-emoji" aria-hidden>
          {emoji}
        </div>
      )}
      <h1 className="scene-title">{title}</h1>
      {children && <div className="scene-actions">{children}</div>}
    </div>
  )
}
