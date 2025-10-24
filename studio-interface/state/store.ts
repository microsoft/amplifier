import { create } from 'zustand'
import { projectsApi, messagesApi } from '@/lib/projects'
import type { Point, PlacementStrategy } from '@/utils/smartPlacement'

/**
 * Studio State Management
 * Based on spec: TODO-studio-spec-ai.md
 */

// Types
export type Corner = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
export type Edge = 'top' | 'right' | 'bottom' | 'left'

export interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  timestamp: number
}

// Canvas Artifacts - Progressive building during discovery
export type ArtifactType =
  | 'link-card'
  | 'research-panel'
  | 'sticky-note'
  | 'strategy-card'
  | 'asset-collection'

export interface CanvasArtifact {
  id: string
  type: ArtifactType
  position: { x: number; y: number }
  data: {
    // Link Card
    url?: string
    title?: string
    description?: string
    image?: string
    favicon?: string

    // Research Panel
    entity?: string
    bio?: string
    images?: string[]
    articles?: Array<{ title: string; url: string }>
    loading?: boolean

    // Sticky Note
    note?: string
    color?: string

    // Strategy Card
    strategy?: string
    channel?: string
    goals?: string[]

    // Asset Collection
    assets?: Array<{ url: string; source: string; caption?: string }>
    collectionName?: string

    // AI Processing metadata (for image/document processing)
    metadata?: {
      id?: string
      processing?: boolean
      analysis?: string
      insights?: string[]
      designElements?: Record<string, any>
      error?: string
    }
  }
  createdAt: number
  sourceMessageId?: string
  visible: boolean
}

export interface DesignVersion {
  id: string
  timestamp: number
  snapshot: unknown // Design state snapshot
  action: string // What changed
  userAction: boolean // User-initiated vs AI-generated
}

export interface DiscoveryContext {
  purpose?: string
  audience?: string
  industry?: string
  constraints?: string[]
}

// Rectangle type for marquee bounds
export interface Rect {
  x: number
  y: number
  width: number
  height: number
}

export interface Project {
  id: string
  name: string
  content: string
  context: DiscoveryContext
}

// Studio phases - 4-phase workflow
export type StudioPhase = 'empty' | 'discover' | 'explore' | 'express' | 'create'

// Phase readiness tracking
export interface PhaseReadiness {
  discover: boolean // Always true once project created
  explore: boolean // Unlocks when enough context gathered
  express: boolean // Unlocks when design direction chosen
  create: boolean // Unlocks when design system defined
}

// Context completeness tracking (replaces arbitrary message counts)
export interface ContextDimension {
  covered: boolean
  confidence: number // 0-100
  lastUpdated: number
}

export interface ContextCompleteness {
  purpose: ContextDimension      // Project goals, what it needs to accomplish
  audience: ContextDimension     // Target users, their needs
  content: ContextDimension      // What needs to be communicated
  constraints: ContextDimension  // Budget, timeline, technical limits
  feeling: ContextDimension      // Desired emotional response, brand personality
}

// Readiness assessment (Canvas Density + Context Completeness)
export interface ReadinessAssessment {
  canvasArtifactCount: number
  contextCompleteness: ContextCompleteness
  overallScore: number // 0-100, calculated
  readyToProgress: boolean
  missingDimensions: string[] // What still needs attention
  lastAssessed: number
}

export interface StudioState {
  // Current phase
  phase: StudioPhase
  setPhase: (phase: StudioPhase) => void
  phaseReadiness: PhaseReadiness
  updatePhaseReadiness: (phase: keyof PhaseReadiness, ready: boolean) => void

  // Selection state
  selection: {
    ids: Set<string>
    mode: 'single' | 'multi'
    lastId: string | null
  }
  selectArtifact: (id: string, modifiers?: { cmd?: boolean; shift?: boolean }) => void
  clearSelection: () => void
  selectAll: () => void
  getSelectedArtifacts: () => CanvasArtifact[]
  isSelected: (id: string) => boolean

  // Delete confirmation
  deleteConfirmation: {
    show: boolean
    ids: string[]
  }
  showDeleteConfirmation: (ids: string[]) => void
  hideDeleteConfirmation: () => void
  deleteArtifacts: (ids: string[]) => void

  // Marquee selection state
  marquee: {
    active: boolean
    start: Point | null
    end: Point | null
    modifiers: {
      shift: boolean  // Add to selection
      alt: boolean    // Subtract from selection
    }
  }
  setMarqueeStart: (point: Point, modifiers: { shift: boolean; alt: boolean }) => void
  setMarqueeEnd: (point: Point) => void
  clearMarquee: () => void
  getMarqueeRect: () => Rect | null
  getMarqueeIntersections: () => string[]  // Returns artifact IDs

  // Current project
  project: Project | null
  setProject: (project: Project) => void
  updateContext: (context: Partial<DiscoveryContext>) => void

  // Persistence
  saveProject: () => Promise<void>
  loadProject: (projectId: string) => Promise<void>

  // Design state
  currentDesign: DesignVersion | null
  designHistory: DesignVersion[]
  selectedElement: string | null
  setCurrentDesign: (design: DesignVersion) => void
  addDesignVersion: (design: DesignVersion) => void
  restoreVersion: (versionId: string) => void
  selectElement: (elementId: string | null) => void

  // Conversation
  messages: Message[]
  isGenerating: boolean
  suggestedQuestions: string[]
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  setIsGenerating: (generating: boolean) => void
  setSuggestedQuestions: (questions: string[]) => void
  clearMessages: () => void

  // UI state
  panels: {
    conversation: boolean
    properties: boolean
    history: boolean
    inspiration: boolean
  }
  devicePreview: 'desktop' | 'tablet' | 'mobile' | 'watch'
  previewMode: 'simulated' | 'live'
  theme: 'auto' | 'light' | 'dark'
  togglePanel: (panel: keyof StudioState['panels']) => void
  setDevicePreview: (device: StudioState['devicePreview']) => void
  setPreviewMode: (mode: StudioState['previewMode']) => void
  setTheme: (theme: 'auto' | 'light' | 'dark') => void

  // User sensibility (learned over time)
  sensibility: {
    confidence: number // 0-1
    preferences: Record<string, unknown>
  }
  updateSensibility: (updates: Partial<StudioState['sensibility']>) => void

  // Canvas artifacts (progressive building during discovery)
  canvasArtifacts: CanvasArtifact[]
  addArtifact: (artifact: Omit<CanvasArtifact, 'id' | 'createdAt'>) => string
  updateArtifact: (id: string, updates: Partial<CanvasArtifact>) => void
  removeArtifact: (id: string) => void
  clearArtifacts: () => void

  // Canvas layout mode
  canvasLayout: 'auto' | 'manual'
  setCanvasLayout: (layout: 'auto' | 'manual') => void

  // Placement configuration for smart artifact positioning
  placement: {
    strategy: PlacementStrategy
    gridSize: number
    lastPosition: Point
  }
  setPlacementStrategy: (strategy: PlacementStrategy) => void
  updateLastPosition: (position: Point) => void

  // Entrance animation queue
  entranceQueue: string[]
  addToEntranceQueue: (id: string) => void
  removeFromEntranceQueue: (id: string) => void
  getEntranceDelay: (id: string) => number
}

// Helper function for rectangle intersection
function rectanglesIntersect(rect1: Rect, rect2: Rect): boolean {
  return !(
    rect1.x + rect1.width < rect2.x ||
    rect2.x + rect2.width < rect1.x ||
    rect1.y + rect1.height < rect2.y ||
    rect2.y + rect2.height < rect1.y
  )
}

// Default artifact sizes for intersection calculation
const ARTIFACT_SIZES = {
  'link-card': { width: 280, height: 200 },
  'research-panel': { width: 320, height: 400 },
  'sticky-note': { width: 200, height: 200 },
  'strategy-card': { width: 280, height: 240 },
  'asset-collection': { width: 320, height: 280 },
}

export const useStudioStore = create<StudioState>((set, get) => ({
  // Initial phase
  phase: 'empty',
  setPhase: (phase) => set({ phase }),

  // Phase readiness - tracks which phases are unlocked
  phaseReadiness: {
    discover: false,
    explore: false,
    express: false,
    create: false,
  },
  updatePhaseReadiness: (phase, ready) =>
    set((state) => ({
      phaseReadiness: { ...state.phaseReadiness, [phase]: ready },
    })),

  // Selection state
  selection: {
    ids: new Set<string>(),
    mode: 'single' as const,
    lastId: null,
  },
  selectArtifact: (id, modifiers = {}) => {
    const state = get()
    const newIds = new Set(state.selection.ids)

    if (modifiers.cmd) {
      // Toggle selection with Cmd/Ctrl
      if (newIds.has(id)) {
        newIds.delete(id)
      } else {
        newIds.add(id)
      }
    } else {
      // Replace selection
      newIds.clear()
      newIds.add(id)
    }

    set({
      selection: {
        ids: newIds,
        mode: modifiers.cmd ? 'multi' : 'single',
        lastId: id,
      },
    })
  },
  clearSelection: () =>
    set({
      selection: {
        ids: new Set<string>(),
        mode: 'single',
        lastId: null,
      },
    }),
  selectAll: () => {
    const state = get()
    const allIds = new Set(state.canvasArtifacts.map((a) => a.id))
    set({
      selection: {
        ids: allIds,
        mode: 'multi',
        lastId: allIds.size > 0 ? Array.from(allIds).pop() || null : null,
      },
    })
  },
  getSelectedArtifacts: () => {
    const state = get()
    return state.canvasArtifacts.filter((a) => state.selection.ids.has(a.id))
  },
  isSelected: (id) => {
    const state = get()
    return state.selection.ids.has(id)
  },

  // Delete confirmation
  deleteConfirmation: {
    show: false,
    ids: [],
  },
  showDeleteConfirmation: (ids) =>
    set({ deleteConfirmation: { show: true, ids } }),
  hideDeleteConfirmation: () =>
    set({ deleteConfirmation: { show: false, ids: [] } }),
  deleteArtifacts: (ids) => {
    set((state) => ({
      canvasArtifacts: state.canvasArtifacts.filter((a) => !ids.includes(a.id)),
      selection: {
        ids: new Set<string>(),
        mode: 'single',
        lastId: null,
      },
      deleteConfirmation: { show: false, ids: [] },
    }))
  },

  // Marquee selection state
  marquee: {
    active: false,
    start: null,
    end: null,
    modifiers: { shift: false, alt: false }
  },
  setMarqueeStart: (point, modifiers) => {
    set({
      marquee: {
        active: true,
        start: point,
        end: point,
        modifiers
      }
    })
  },
  setMarqueeEnd: (point) => {
    set((state) => ({
      marquee: {
        ...state.marquee,
        end: point
      }
    }))
  },
  clearMarquee: () => {
    set({
      marquee: {
        active: false,
        start: null,
        end: null,
        modifiers: { shift: false, alt: false }
      }
    })
  },
  getMarqueeRect: () => {
    const state = get()
    const { start, end } = state.marquee

    if (!start || !end) return null

    return {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      width: Math.abs(end.x - start.x),
      height: Math.abs(end.y - start.y)
    }
  },
  getMarqueeIntersections: () => {
    const state = get()
    const marqueeRect = state.getMarqueeRect()

    if (!marqueeRect) return []

    // Check each visible artifact for intersection
    return state.canvasArtifacts
      .filter(a => a.visible)
      .filter(artifact => {
        // Get artifact bounds using default sizes
        const size = ARTIFACT_SIZES[artifact.type] || { width: 280, height: 200 }
        const artifactRect = {
          x: artifact.position.x,
          y: artifact.position.y,
          width: size.width,
          height: size.height
        }

        // Check if rectangles intersect
        return rectanglesIntersect(marqueeRect, artifactRect)
      })
      .map(a => a.id)
  },

  // Initial project state
  project: null,
  setProject: (project) => set({ project }),
  updateContext: (context) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            context: { ...state.project.context, ...context },
          }
        : null,
    })),

  // Persistence methods
  saveProject: async () => {
    const state = get()
    if (!state.project) return

    await projectsApi.saveState(state.project.id, {
      context: state.project.context,
      canvasArtifacts: state.canvasArtifacts,
      phase: state.phase,
      phaseReadiness: state.phaseReadiness,
      status:
        state.phase === 'discover' || state.phase === 'empty'
          ? 'discovery'
          : state.phase === 'express'
            ? 'expression'
            : 'completed',
    })
  },

  loadProject: async (projectId: string) => {
    const projectData = await projectsApi.get(projectId)
    if (!projectData) return

    const messages = await messagesApi.list(projectId)

    set({
      project: {
        id: projectData.id,
        name: projectData.name,
        content: '', // Legacy field
        context: projectData.context,
      },
      phase: (projectData.context.phase as StudioPhase) || 'discover',
      phaseReadiness: projectData.context.phaseReadiness
        ? {
            discover: projectData.context.phaseReadiness.discover || true,
            explore: projectData.context.phaseReadiness.explore || false,
            express: projectData.context.phaseReadiness.express || false,
            create: projectData.context.phaseReadiness.create || false,
          }
        : {
            discover: true,
            explore: false,
            express: false,
            create: false,
          },
      canvasArtifacts: projectData.context.canvasArtifacts || [],
      messages,
      entranceQueue: [], // Clear entrance queue on load
    })
  },

  // Initial design state
  currentDesign: null,
  designHistory: [],
  selectedElement: null,
  setCurrentDesign: (design) => set({ currentDesign: design }),
  addDesignVersion: (design) =>
    set((state) => ({
      currentDesign: design,
      designHistory: [...state.designHistory, design],
    })),
  restoreVersion: (versionId) => {
    const { designHistory } = get()
    const version = designHistory.find((v) => v.id === versionId)
    if (version) {
      set({ currentDesign: version })
    }
  },
  selectElement: (elementId) => set({ selectedElement: elementId }),

  // Initial conversation state
  messages: [],
  isGenerating: false,
  suggestedQuestions: [
    "What's the purpose of your project?",
    "Who is your audience?",
    "Tell me about your content",
  ],
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: Date.now(),
        },
      ],
    })),
  setIsGenerating: (generating) => set({ isGenerating: generating }),
  setSuggestedQuestions: (questions) => set({ suggestedQuestions: questions }),
  clearMessages: () => set({ messages: [] }),

  // Initial UI state
  panels: {
    conversation: true,
    properties: false,
    history: false,
    inspiration: false,
  },
  devicePreview: 'desktop',
  previewMode: 'simulated',
  theme: 'auto',
  togglePanel: (panel) =>
    set((state) => ({
      panels: {
        ...state.panels,
        [panel]: !state.panels[panel],
      },
    })),
  setDevicePreview: (device) => set({ devicePreview: device }),
  setPreviewMode: (mode) => set({ previewMode: mode }),
  setTheme: (theme) => {
    set({ theme })
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('studio-theme', theme)
    }
  },

  // Initial sensibility
  sensibility: {
    confidence: 0,
    preferences: {},
  },
  updateSensibility: (updates) =>
    set((state) => ({
      sensibility: {
        ...state.sensibility,
        ...updates,
      },
    })),

  // Initial canvas artifacts
  canvasArtifacts: [],
  addArtifact: (artifact) => {
    const id = crypto.randomUUID()

    set((state) => ({
      canvasArtifacts: [
        ...state.canvasArtifacts,
        {
          ...artifact,
          id,
          createdAt: Date.now(),
        },
      ],
      entranceQueue: [...state.entranceQueue, id]
    }))

    // Auto-remove from queue after animation completes (450ms = 400ms + buffer)
    setTimeout(() => {
      get().removeFromEntranceQueue(id)
    }, 450)

    return id
  },
  updateArtifact: (id, updates) =>
    set((state) => ({
      canvasArtifacts: state.canvasArtifacts.map((artifact) =>
        artifact.id === id ? { ...artifact, ...updates } : artifact
      ),
    })),
  removeArtifact: (id) =>
    set((state) => ({
      canvasArtifacts: state.canvasArtifacts.filter((artifact) => artifact.id !== id),
    })),
  clearArtifacts: () => set({ canvasArtifacts: [], entranceQueue: [] }),

  // Initial canvas layout
  canvasLayout: 'auto',
  setCanvasLayout: (layout) => set({ canvasLayout: layout }),

  // Initial placement configuration
  placement: {
    strategy: 'spiral' as PlacementStrategy,
    gridSize: 40,
    lastPosition: { x: 400, y: 300 },
  },
  setPlacementStrategy: (strategy) =>
    set((state) => ({
      placement: { ...state.placement, strategy },
    })),
  updateLastPosition: (position) =>
    set((state) => ({
      placement: { ...state.placement, lastPosition: position },
    })),

  // Entrance animation queue
  entranceQueue: [],
  addToEntranceQueue: (id) =>
    set((state) => ({
      entranceQueue: [...state.entranceQueue, id]
    })),
  removeFromEntranceQueue: (id) =>
    set((state) => ({
      entranceQueue: state.entranceQueue.filter(qId => qId !== id)
    })),
  getEntranceDelay: (id) => {
    const state = get()
    const index = state.entranceQueue.indexOf(id)
    if (index === -1) return 0

    // Stagger with 50ms delay, max 10 items (500ms)
    return Math.min(index * 50, 500)
  },
}))
