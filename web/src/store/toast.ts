import { create } from 'zustand'

export type ToastKind = 'info' | 'done'

export interface ToastItem {
  id: number
  message: string
  kind: ToastKind
  emoji?: string
}

interface ToastState {
  toasts: ToastItem[]
  show: (message: string, opts?: { kind?: ToastKind; emoji?: string; ms?: number }) => void
  dismiss: (id: number) => void
}

let nextId = 1

export const useToasts = create<ToastState>((set, get) => ({
  toasts: [],
  show: (message, opts = {}) => {
    const id = nextId++
    const item: ToastItem = { id, message, kind: opts.kind ?? 'info', emoji: opts.emoji }
    set({ toasts: [...get().toasts, item] })
    window.setTimeout(() => get().dismiss(id), opts.ms ?? 2800)
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}))
