import type { HTMLAttributes } from 'react'
import '../theme.css'
import './Card.css'
import { cx } from './cx'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  selected?: boolean
  surface?: 'panel' | 'stage'
}

export function Card({ selected, surface = 'panel', className, ...rest }: CardProps) {
  return (
    <div
      className={cx('card', surface === 'stage' && 'on-stage', selected && 'is-selected', className)}
      {...rest}
    />
  )
}
