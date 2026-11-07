import '../theme.css'
import './Toast.css'
import { useToasts, type ToastKind } from '../store/toast'
import { cx } from './cx'

export interface ToastProps {
  message: string
  /** Green only when it reports something done. */
  kind?: ToastKind
  emoji?: string
  onClick?: () => void
}

export function Toast({ message, kind = 'info', emoji, onClick }: ToastProps) {
  return (
    <div role="status" className={cx('toast', kind === 'done' && 'is-done')} onClick={onClick}>
      {emoji && <span aria-hidden>{emoji}</span>}
      {message}
    </div>
  )
}

/** Mount once per app; shows toasts from the store, bottom-centre. */
export function ToastHost() {
  const toasts = useToasts((s) => s.toasts)
  const dismiss = useToasts((s) => s.dismiss)
  return (
    <div className="toast-host">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onClick={() => dismiss(t.id)} />
      ))}
    </div>
  )
}
