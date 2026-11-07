import '../theme.css'
import './Scene.css'
import { PillButton } from './PillButton'

export interface EmptyStateProps {
  emoji: string
  title: string
  actionLabel?: string
  onAction?: () => void
}

/** Full-panel scene blue with one white pill action. */
export function EmptyState({ emoji, title, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="scene-emoji" aria-hidden>
        {emoji}
      </div>
      <h2 className="scene-title">{title}</h2>
      {actionLabel && (
        <PillButton surface="scene" onClick={onAction}>
          {actionLabel}
        </PillButton>
      )}
    </div>
  )
}
