import { create } from 'zustand'
import type { Platform } from '../components/safeZones'

interface UiState {
  safeZones: Record<Platform, boolean>
  toggleSafeZone: (p: Platform) => void
}

export const useUi = create<UiState>((set) => ({
  safeZones: { tiktok: true, shorts: false },
  toggleSafeZone: (p) => set((s) => ({ safeZones: { ...s.safeZones, [p]: !s.safeZones[p] } })),
}))
