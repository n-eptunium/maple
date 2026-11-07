import type { ButtonHTMLAttributes } from 'react'
import '../theme.css'
import './buttons.css'
import { cx } from './cx'

export type DemoState = 'hover' | 'pressed'

export interface PillButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean
  /** Where the pill sits; picks the shadow colour. */
  surface?: 'panel' | 'scene' | 'stage'
  /** Force a visual state (Playground only). */
  demo?: DemoState
}

export function PillButton({
  selected,
  surface = 'panel',
  demo,
  className,
  type = 'button',
  ...rest
}: PillButtonProps) {
  return (
    <button
      type={type}
      aria-pressed={selected}
      className={cx(
        'pill',
        surface !== 'panel' && `on-${surface}`,
        selected && 'is-selected',
        demo && `is-${demo}`,
        className,
      )}
      {...rest}
    />
  )
}
