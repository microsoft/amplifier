import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Plus, 
  Settings, 
  Search, 
  Play, 
  Pause, 
  AlertCircle, 
  Clock, 
  DollarSign,
  Users,
  Brain,
  GitBranch,
  Activity,
  Zap,
  Shield,
  Bug,
  TestTube,
  Database,
  Eye,
  Lightbulb,
  Terminal,
  Folder,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  RotateCcw,
  Power,
  Code,
  FileText,
  BarChart3,
  Cpu,
  HardDrive,
  Network,
  MonitorSpeaker,
  Send,
  MessageSquare,
  Home,
  History,
  User,
  HelpCircle,
  LogOut,
  Moon,
  Sun,
  Trash2,
  Edit3,
  Archive,
  Star,
  MoreHorizontal,
  Check,
  X,
  Loader2,
  Wifi,
  WifiOff,
  Paperclip,
  Image,
  Smile,
  Bold,
  Italic,
  Link,
  List,
  Hash,
  Quote,
  Code2,
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles
} from 'lucide-react'
import './App.css'

// Agent definitions with icons
const agentDefinitions = {
  'zen-architect': { name: 'Zen Architect', icon: Brain, color: 'bg-blue-500' },
  'modular-builder': { name: 'Modular Builder', icon: GitBranch, color: 'bg-green-500' },
  'test-coverage': { name: 'Test Coverage', icon: TestTube, color: 'bg-purple-500' },
  'bug-hunter': { name: 'Bug Hunter', icon: Bug, color: 'bg-red-500' },
  'security-guardian': { name: 'Security Guardian', icon: Shield, color: 'bg-orange-500' },
  'performance-optimizer': { name: 'Performance Optimizer', icon: Zap, color: 'bg-yellow-500' },
  'database-architect': { name: 'Database Architect', icon: Database, color: 'bg-indigo-500' },
  'insight-synthesizer': { name: 'Insight Synthesizer', icon: Lightbulb, color: 'bg-pink-500' }
}

// API functions
const API_BASE = 'http://localhost:5000/api/amplifier'

async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('API call failed:', error)
    throw error
  }
}

function SessionListItem({ session, isActive, onClick, onDelete }) {
  const statusConfig = {
    active: { color: 'text-green-400', icon: '●' },
    idle: { color: 'text-yellow-400', icon: '●' },
    error: { color: 'text-red-400', icon: '●' }
  }

  const status = statusConfig[session.status] || statusConfig.idle
  const lastMessage = session.messages?.[session.messages.length - 1]

  return (
    <div 
      className={`group p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-accent/50 ${
        isActive ? 'bg-accent border-l-2 border-primary' : ''
      }`}
      onClick={() => onClick(session)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs ${status.color}`}>{status.icon}</span>
            <h3 className="font-medium text-sm truncate">{session.name}</h3>
          </div>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <GitBranch className="w-3 h-3" />
            <span className="truncate">{session.worktree}</span>
          </div>
          
          {lastMessage && (
            <p className="text-xs text-muted-foreground truncate">
              {lastMessage.content.substring(0, 50)}...
            </p>
          )}
        </div>
        
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs text-muted-foreground">{session.duration}m</span>
          <Button
            variant="ghost"
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity h-5 w-5 p-0"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(session.id)
            }}
          >
            <Trash2 className="w-3 h-3" />
          </Button>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {session.agents?.slice(0, 3).map(agentId => {
            const agent = agentDefinitions[agentId]
            return (
              <div key={agentId} className={`w-3 h-3 rounded-sm ${agent?.color || 'bg-gray-500'}`} title={agent?.name}></div>
            )
          })}
          {session.agents?.length > 3 && (
            <div className="w-3 h-3 rounded-sm bg-muted flex items-center justify-center text-[8px] font-bold">
              +{session.agents.length - 3}
            </div>
          )}
        </div>
        <span className="text-xs text-muted-foreground">${session.cost?.toFixed(2) || '0.00'}</span>
      </div>
    </div>
  )
}

function FileAttachment({ file, onRemove }) {
  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'py': return Code2
      case 'js': case 'jsx': case 'ts': case 'tsx': return Code2
      case 'md': return FileText
      case 'json': return Code2
      case 'html': case 'css': return Code2
      default: return FileText
    }
  }

  const FileIcon = getFileIcon(file.name)

  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
      <div className="flex items-center justify-center w-8 h-8 bg-primary/10 rounded">
        <FileIcon className="w-4 h-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">{file.name}</div>
        <div className="text-xs text-muted-foreground">{file.size}</div>
      </div>
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
          <Download className="w-3 h-3" />
        </Button>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
          <ExternalLink className="w-3 h-3" />
        </Button>
        {onRemove && (
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => onRemove(file.id)}>
            <X className="w-3 h-3" />
          </Button>
        )}
      </div>
    </div>
  )
}

function TaskProgress({ tasks, completedTasks }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Check className="w-4 h-4 text-green-400" />
        <span className="text-sm font-medium text-green-400">Task completed</span>
        <Badge variant="secondary" className="text-xs">
          {completedTasks}/{tasks} steps
        </Badge>
      </div>
      <div className="text-xs text-muted-foreground">
        All development tasks have been completed successfully
      </div>
    </div>
  )
}

function SuggestedFollowUp({ suggestion, onClick }) {
  return (
    <Card className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => onClick(suggestion.text)}>
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-primary/10 rounded-full">
            <MessageCircle className="w-4 h-4 text-primary" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium mb-1">{suggestion.title}</div>
            <div className="text-xs text-muted-foreground">{suggestion.description}</div>
          </div>
          <Sparkles className="w-4 h-4 text-yellow-400" />
        </div>
      </CardContent>
    </Card>
  )
}

function MessageBubble({ message, isUser, onRate, onCopy }) {
  const [showActions, setShowActions] = useState(false)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div 
          className={`rounded-lg p-4 ${
            isUser 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted border'
          }`}
          onMouseEnter={() => setShowActions(true)}
          onMouseLeave={() => setShowActions(false)}
        >
          <div className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</div>
          
          {/* File attachments */}
          {message.files && message.files.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.files.map(file => (
                <FileAttachment key={file.id} file={file} />
              ))}
              {message.files.length > 2 && (
                <Button variant="ghost" size="sm" className="text-xs">
                  View all files in this task
                </Button>
              )}
            </div>
          )}
          
          {/* Task progress */}
          {message.taskProgress && (
            <div className="mt-3 p-3 bg-background/50 rounded-lg">
              <TaskProgress 
                tasks={message.taskProgress.total} 
                completedTasks={message.taskProgress.completed} 
              />
            </div>
          )}
          
          {/* Message metadata */}
          <div className="flex items-center justify-between mt-3 text-xs opacity-70">
            <span>{message.timestamp}</span>
            <div className="flex items-center gap-2">
              {!isUser && message.status === 'completed' && (
                <Check className="w-3 h-3 text-green-400" />
              )}
              {showActions && !isUser && (
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={() => onCopy(message.content)}>
                    <Copy className="w-3 h-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={() => onRate(message.id, 'up')}>
                    <ThumbsUp className="w-3 h-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={() => onRate(message.id, 'down')}>
                    <ThumbsDown className="w-3 h-3" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Suggested follow-ups */}
        {message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-xs text-muted-foreground font-medium">Suggested follow-ups:</div>
            {message.suggestions.map((suggestion, index) => (
              <SuggestedFollowUp 
                key={index} 
                suggestion={suggestion} 
                onClick={(text) => {
                  // Handle suggestion click
                  console.log('Suggestion clicked:', text)
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function RichTextEditor({ value, onChange, onSend, disabled }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const textareaRef = useRef(null)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
      e.preventDefault()
      onSend()
    }
  }

  const insertFormatting = (before, after = '') => {
    const textarea = textareaRef.current
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = value.substring(start, end)
    
    const newValue = value.substring(0, start) + before + selectedText + after + value.substring(end)
    onChange(newValue)
    
    // Reset cursor position
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length)
    }, 0)
  }

  return (
    <div className="border rounded-lg bg-background">
      {/* Formatting toolbar */}
      <div className="flex items-center gap-1 p-2 border-b bg-muted/30">
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('**', '**')}>
          <Bold className="w-3 h-3" />
        </Button>
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('*', '*')}>
          <Italic className="w-3 h-3" />
        </Button>
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('`', '`')}>
          <Code2 className="w-3 h-3" />
        </Button>
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('[', '](url)')}>
          <Link className="w-3 h-3" />
        </Button>
        <Separator orientation="vertical" className="h-4" />
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('- ', '')}>
          <List className="w-3 h-3" />
        </Button>
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => insertFormatting('> ', '')}>
          <Quote className="w-3 h-3" />
        </Button>
        <div className="flex-1" />
        <Button 
          variant="ghost" 
          size="sm" 
          className="h-7 w-7 p-0" 
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
        </Button>
      </div>
      
      {/* Text input area */}
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask the agents to help with your development..."
        className={`border-0 resize-none focus-visible:ring-0 ${
          isExpanded ? 'min-h-32' : 'min-h-20'
        }`}
        disabled={disabled}
      />
      
      {/* Bottom toolbar */}
      <div className="flex items-center justify-between p-2 border-t bg-muted/30">
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
            <Paperclip className="w-3 h-3 mr-1" />
            Attach
          </Button>
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
            <Image className="w-3 h-3 mr-1" />
            Image
          </Button>
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
            <Code2 className="w-3 h-3 mr-1" />
            Code
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {value.length} characters
          </span>
          <Button 
            onClick={onSend} 
            disabled={!value.trim() || disabled}
            size="sm"
            className="px-4"
          >
            <Send className="w-4 h-4 mr-1" />
            Send
          </Button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [message, setMessage] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef(null)

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await apiCall('/health')
        setIsConnected(true)
        // Always load mock sessions to demonstrate the enhanced chat interface
        loadMockSessions()
      } catch (error) {
        setIsConnected(false)
        // Load mock data if backend is not available
        loadMockSessions()
      }
    }
    
    checkConnection()
    const interval = setInterval(checkConnection, 30000) // Check every 30 seconds
    
    return () => clearInterval(interval)
  }, [])

  // Set dark theme by default
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selectedSession?.messages])

  const loadSessions = async () => {
    try {
      const data = await apiCall('/sessions')
      setSessions(data)
      if (data.length > 0 && !selectedSession) {
        setSelectedSession(data[0])
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const loadMockSessions = () => {
    const mockSessions = [
      {
        id: '1',
        name: 'Feature Development',
        status: 'active',
        agents: ['zen-architect', 'modular-builder', 'test-coverage'],
        cost: 2.45,
        duration: 15,
        worktree: 'feature-auth',
        messages: [
          { 
            role: 'user', 
            content: 'Create a new authentication system with JWT tokens', 
            timestamp: '15:20:00' 
          },
          { 
            role: 'assistant', 
            content: 'I\'ll help you create a secure JWT authentication system. Let me start by analyzing your current project structure and implementing the necessary components.',
            timestamp: '15:20:15', 
            status: 'completed',
            files: [
              { id: '1', name: 'auth-middleware.py', size: '5.87 KB' },
              { id: '2', name: 'jwt-handler.js', size: '3.21 KB' }
            ],
            taskProgress: { completed: 4, total: 6 }
          },
          { 
            role: 'assistant', 
            content: 'I\'ve created the authentication middleware and JWT token handling. The system includes:\n\n- JWT token generation and validation\n- Secure password hashing with bcrypt\n- Session management\n- Protected route middleware\n\nWould you like me to add OAuth integration as well?',
            timestamp: '15:22:30', 
            status: 'completed',
            files: [
              { id: '3', name: 'auth-system.md', size: '10.71 KB' },
              { id: '4', name: 'test-auth.py', size: '7.43 KB' }
            ],
            taskProgress: { completed: 6, total: 6 },
            suggestions: [
              {
                title: 'Add OAuth Integration',
                description: 'Integrate Google and GitHub OAuth providers',
                text: 'Add OAuth integration with Google and GitHub providers'
              },
              {
                title: 'Create Test Suite',
                description: 'Generate comprehensive authentication tests',
                text: 'Create a comprehensive test suite for the authentication system'
              },
              {
                title: 'Add Rate Limiting',
                description: 'Implement rate limiting for login attempts',
                text: 'Add rate limiting and brute force protection'
              }
            ]
          }
        ]
      },
      {
        id: '2',
        name: 'Bug Investigation',
        status: 'idle',
        agents: ['bug-hunter', 'security-guardian'],
        cost: 1.20,
        duration: 8,
        worktree: 'bugfix-login',
        messages: [
          { role: 'user', content: 'There\'s a login issue where users can\'t authenticate', timestamp: '14:45:00' },
          { role: 'assistant', content: 'I\'ll investigate the login authentication issue. Let me check the authentication flow and identify potential problems.', timestamp: '14:45:10' },
          { 
            role: 'assistant', 
            content: 'Found the issue! The JWT token validation is failing due to a timezone mismatch in the expiration check. I\'ve fixed the token validation logic and added proper error handling.',
            timestamp: '14:47:25', 
            status: 'completed',
            taskProgress: { completed: 3, total: 3 }
          }
        ]
      }
    ]
    
    setSessions(mockSessions)
    setSelectedSession(mockSessions[0])
  }

  const createSession = async (sessionName) => {
    setIsLoading(true)
    try {
      if (isConnected) {
        const newSession = await apiCall('/sessions', {
          method: 'POST',
          body: JSON.stringify({
            name: sessionName,
            projectPath: '/home/ubuntu/amplifier'
          })
        })
        setSessions(prev => [...prev, newSession])
        setSelectedSession(newSession)
      } else {
        // Mock session creation
        const mockSession = {
          id: Date.now().toString(),
          name: sessionName,
          status: 'idle',
          agents: [],
          cost: 0,
          duration: 0,
          worktree: `session-${Date.now()}`,
          messages: [
            {
              role: 'assistant',
              content: `Session "${sessionName}" created! I'm ready to help you with development tasks. What would you like to work on?`,
              timestamp: new Date().toLocaleTimeString(),
              status: 'completed',
              suggestions: [
                {
                  title: 'Start Development',
                  description: 'Begin coding a new feature',
                  text: 'Help me start developing a new feature'
                },
                {
                  title: 'Debug Issues',
                  description: 'Investigate and fix bugs',
                  text: 'Help me debug issues in my code'
                },
                {
                  title: 'Code Review',
                  description: 'Review and improve existing code',
                  text: 'Please review my code and suggest improvements'
                }
              ]
            }
          ]
        }
        setSessions(prev => [...prev, mockSession])
        setSelectedSession(mockSession)
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateSession = () => {
    const sessionName = prompt('Enter session name:')
    if (sessionName?.trim()) {
      createSession(sessionName.trim())
    }
  }

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Are you sure you want to delete this session?')) return
    
    try {
      if (isConnected) {
        await apiCall(`/sessions/${sessionId}`, { method: 'DELETE' })
      }
      
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      if (selectedSession?.id === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId)
        setSelectedSession(remaining[0] || null)
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedSession || isSending) return
    
    setIsSending(true)
    
    const userMessage = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toLocaleTimeString()
    }
    
    // Add user message immediately
    const updatedSession = {
      ...selectedSession,
      messages: [...(selectedSession.messages || []), userMessage]
    }
    setSelectedSession(updatedSession)
    setSessions(prev => prev.map(s => s.id === selectedSession.id ? updatedSession : s))
    setMessage('')
    
    try {
      if (isConnected) {
        const response = await apiCall(`/sessions/${selectedSession.id}/chat`, {
          method: 'POST',
          body: JSON.stringify({ message: message.trim() })
        })
        
        const assistantMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toLocaleTimeString(),
          status: 'completed'
        }
        
        const finalSession = {
          ...updatedSession,
          messages: [...updatedSession.messages, assistantMessage]
        }
        setSelectedSession(finalSession)
        setSessions(prev => prev.map(s => s.id === selectedSession.id ? finalSession : s))
      } else {
        // Mock response with enhanced features
        setTimeout(() => {
          const assistantMessage = {
            role: 'assistant',
            content: `I received your message: "${userMessage.content}". I'm analyzing your request and will provide a comprehensive solution.\n\n(Demo mode - Backend not connected)`,
            timestamp: new Date().toLocaleTimeString(),
            status: 'completed',
            suggestions: [
              {
                title: 'Get More Details',
                description: 'Ask for more specific requirements',
                text: 'Can you provide more details about what you need?'
              },
              {
                title: 'Show Examples',
                description: 'Request code examples or demonstrations',
                text: 'Show me some examples of how this should work'
              }
            ]
          }
          
          const finalSession = {
            ...updatedSession,
            messages: [...updatedSession.messages, assistantMessage]
          }
          setSelectedSession(finalSession)
          setSessions(prev => prev.map(s => s.id === selectedSession.id ? finalSession : s))
        }, 1000)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSending(false)
    }
  }

  const handleCopyMessage = (content) => {
    navigator.clipboard.writeText(content)
    // Could add a toast notification here
  }

  const handleRateMessage = (messageId, rating) => {
    console.log('Rating message:', messageId, rating)
    // Could implement message rating functionality
  }

  const totalCost = sessions.reduce((sum, session) => sum + (session.cost || 0), 0)
  const activeSessions = sessions.filter(s => s.status === 'active').length

  return (
    <div className="h-screen flex bg-background text-foreground">
      {/* Left Sidebar - Session List */}
      <div className="w-80 border-r bg-card flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-lg font-bold">Amplifier UI</h1>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {isConnected ? (
                  <>
                    <Wifi className="w-3 h-3 text-green-400" />
                    <span>Connected to Amplifier</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 text-red-400" />
                    <span>Demo Mode</span>
                  </>
                )}
              </div>
            </div>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
          
          <Button 
            onClick={handleCreateSession} 
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4 mr-2" />
                New Session
              </>
            )}
          </Button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-hidden">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                Sessions ({sessions.length})
              </h2>
            </div>
            <ScrollArea className="h-full">
              <div className="space-y-1">
                {sessions.map(session => (
                  <SessionListItem
                    key={session.id}
                    session={session}
                    isActive={selectedSession?.id === session.id}
                    onClick={setSelectedSession}
                    onDelete={handleDeleteSession}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Footer Stats */}
        <div className="border-t p-4">
          <div className="grid grid-cols-2 gap-4 text-center text-sm">
            <div>
              <div className="font-bold text-green-400">{activeSessions}</div>
              <div className="text-xs text-muted-foreground">Active</div>
            </div>
            <div>
              <div className="font-bold text-blue-400">${totalCost.toFixed(2)}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="h-14 border-b bg-card px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold">
              {selectedSession ? selectedSession.name : 'Select a Session'}
            </h2>
            {selectedSession && (
              <div className="flex items-center gap-2">
                <Badge variant={selectedSession.status === 'active' ? 'default' : 'secondary'}>
                  {selectedSession.status}
                </Badge>
                {selectedSession.agents && selectedSession.agents.length > 0 && (
                  <Badge variant="outline">
                    {selectedSession.agents.length} agents
                  </Badge>
                )}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Activity className="w-4 h-4 mr-2" />
              Monitor
            </Button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-hidden">
          {selectedSession ? (
            <ScrollArea className="h-full p-6">
              <div className="max-w-4xl mx-auto">
                {selectedSession.messages?.map((msg, index) => (
                  <MessageBubble
                    key={index}
                    message={msg}
                    isUser={msg.role === 'user'}
                    onCopy={handleCopyMessage}
                    onRate={handleRateMessage}
                  />
                ))}
                {isSending && (
                  <div className="flex justify-start mb-6">
                    <div className="bg-muted border rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm text-muted-foreground">Agents are thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          ) : (
            <div className="flex-1 flex items-center justify-center text-center text-muted-foreground">
              <div>
                <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No Session Selected</h3>
                <p>Create a new session or select an existing one to start chatting with AI agents</p>
              </div>
            </div>
          )}
        </div>

        {/* Rich Text Input Area */}
        {selectedSession && (
          <div className="border-t bg-card p-4">
            <div className="max-w-4xl mx-auto">
              <RichTextEditor
                value={message}
                onChange={setMessage}
                onSend={handleSendMessage}
                disabled={isSending}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
