import type { HTMLAttributes } from 'react'
import '../theme.css'
import './Card.css'
import { cx } from './cx'

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  selected?: boolean
  gold?: boolean
}

export function Tag({ selected, gold, className, ...rest }: TagProps) {
  return (
    <span
      className={cx('tag', gold && 'is-gold', selected && 'is-selected', className)}
      {...rest}
    />
  )
}
