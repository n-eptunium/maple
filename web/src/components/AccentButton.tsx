import type { ButtonHTMLAttributes } from 'react'
import '../theme.css'
import './buttons.css'
import { cx } from './cx'
import type { DemoState } from './PillButton'

export interface AccentButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  demo?: DemoState
}

/** The one main action per screen ("Post", "Render"). */
export function AccentButton({ demo, className, type = 'button', ...rest }: AccentButtonProps) {
  return (
    <button type={type} className={cx('accent-btn', demo && `is-${demo}`, className)} {...rest} />
  )
}
