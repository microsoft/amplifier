'use client'

import React, { createContext, useContext, useCallback, ReactNode } from 'react'
import { useStudioStore } from '@/state/store'

interface SelectionContextType {
  selectedIds: Set<string>
  isSelected: (id: string) => boolean
  selectArtifact: (id: string, modifiers?: { cmd?: boolean; shift?: boolean }) => void
  clearSelection: () => void
  selectAll: () => void
  selectedCount: number
}

const SelectionContext = createContext<SelectionContextType | undefined>(undefined)

export const SelectionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const selection = useStudioStore((state) => state.selection)
  const selectArtifact = useStudioStore((state) => state.selectArtifact)
  const clearSelection = useStudioStore((state) => state.clearSelection)
  const selectAll = useStudioStore((state) => state.selectAll)
  const isSelected = useStudioStore((state) => state.isSelected)

  const handleSelectArtifact = useCallback(
    (id: string, modifiers?: { cmd?: boolean; shift?: boolean }) => {
      selectArtifact(id, modifiers)
    },
    [selectArtifact]
  )

  const value: SelectionContextType = {
    selectedIds: selection.ids,
    isSelected,
    selectArtifact: handleSelectArtifact,
    clearSelection,
    selectAll,
    selectedCount: selection.ids.size,
  }

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>
}

export const useSelection = () => {
  const context = useContext(SelectionContext)
  if (!context) {
    throw new Error('useSelection must be used within a SelectionProvider')
  }
  return context
}