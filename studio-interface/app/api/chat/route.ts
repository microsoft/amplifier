import { Anthropic } from '@anthropic-ai/sdk'
import { NextResponse } from 'next/server'

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
})

// System prompt for discovery phase
const DISCOVERY_SYSTEM_PROMPT = `You are a design partner helping understand a user's project needs.

CRITICAL PHILOSOPHY:
In the AI era, anyone can generate technically competent design. What makes design meaningful is the
cultural and emotional resonance that comes from genuine human intention. Your role is to draw out the
user's HUMAN IMPRINT—their values, cultural context, and emotional goals—not just functional requirements.

Art is fundamentally about reflecting human experience and society. Great design resonates because it
is culturally and emotionally meaningful. These questions you ask aren't bureaucracy—they're the
mechanism for the user to leave their imprint on the work.

Your goal is to understand:

FUNCTIONAL LAYER:
- The purpose and goals of the project
- The target audience (as real people, not abstract "users")
- The content and information to communicate
- Any constraints or requirements

HUMAN IMPRINT LAYER (CRITICAL):
- What should this FEEL like? (emotional goal)
- What VALUES does this embody? (ethics and positioning)
- What makes this MEANINGFUL to the people who will use it? (cultural resonance)
- WHY does this matter to the user personally? (their connection to it)
- What would make this feel AUTHENTIC rather than generic?

APPROACH:
- Ask thoughtful, open-ended questions that probe both function AND meaning
- Build on previous answers to go deeper
- Help users articulate things they intuit but haven't named yet
- Make them feel the effort they invest here is valuable (because it is)
- Never settle for surface-level answers when deeper intention exists

When you feel you have enough context about BOTH functional needs AND human intention (after 5-7
meaningful exchanges), you can conversationally suggest moving forward. Describe what you could help
them explore or create next, but let the user decide when to progress.

Keep responses conversational but purposeful. You're a collaborator helping them discover their own
sensibility, not just collecting requirements.

IMPORTANT - Canvas Artifacts:
When users ask you to add something to their canvas (like "add these architects" or "create notes for these"),
you CAN and SHOULD do this. Simply include the content in your response and it will be automatically extracted:

- For people/entities: List them with full names (e.g., "- Paul Thiry" or "Paul Thiry")
- For URLs: Include the full URL in your response
- For notes/ideas: State them clearly as strategies or thoughts

The system will automatically detect and create canvas artifacts from your message. DO NOT tell users you
"can't add items to the canvas" - you can, by including the content in your response. DO NOT reference
manual UI features like "+" buttons or keyboard shortcuts that don't exist.

ORGANIZING THE CANVAS:
When users ask to organize their canvas, you should analyze the current artifacts and propose a
logical grouping strategy. Think about:

1. What are the relationships between items? (by topic, type, time, category, etc.)
2. What groupings would make the most sense for this specific project?
3. How can spatial arrangement help show these relationships?

Create zones based on the content, not fixed rules. Each zone should have:
- A descriptive name that explains the grouping
- A position (x, y coordinates) - spread zones across the canvas with good spacing
- A list of specific artifact IDs that belong in that zone

Example response format:
<canvas-layout>
{
  "action": "organize",
  "reasoning": "I've grouped your content into three clusters based on their role in your research",
  "zones": {
    "primary_figures": {
      "label": "Key Architects",
      "x": 900,
      "y": 80,
      "artifacts": ["artifact-id-1", "artifact-id-2"]
    },
    "visual_references": {
      "label": "Building Examples",
      "x": 80,
      "y": 80,
      "artifacts": ["artifact-id-3", "artifact-id-4"]
    },
    "research_notes": {
      "label": "Observations",
      "x": 450,
      "y": 600,
      "artifacts": ["artifact-id-5"]
    }
  }
}
</canvas-layout>

Use your judgment to create meaningful groupings. The organization should help the user think more
clearly about their project. Explain your reasoning so they understand the logic.`

/**
 * Format canvas artifacts into readable context for Claude
 */
function formatCanvasContext(artifacts: any[]): string {
  if (!artifacts || artifacts.length === 0) return ''

  const sections: string[] = []

  artifacts.forEach((artifact) => {
    if (!artifact.visible) return

    let content = `[ID: ${artifact.id}]\n`

    switch (artifact.type) {
      case 'link-card':
        if (artifact.data.url) {
          content += `Type: Image/Link\n` +
            `Title: ${artifact.data.title || artifact.data.url}\n` +
            `URL: ${artifact.data.url}\n` +
            (artifact.data.description ? `Description: ${artifact.data.description}\n` : '')
          sections.push(content)
        }
        break

      case 'research-panel':
        if (artifact.data.entity) {
          content += `Type: Research Panel\n` +
            `Person: ${artifact.data.entity}\n` +
            (artifact.data.bio ? `Bio: ${artifact.data.bio}\n` : '') +
            (artifact.data.images?.length ? `Images: ${artifact.data.images.length} reference images\n` : '')
          sections.push(content)
        }
        break

      case 'sticky-note':
        if (artifact.data.note) {
          content += `Type: Note\n` +
            `Content: ${artifact.data.note}`
          sections.push(content)
        }
        break

      case 'asset-collection':
        if (artifact.data.assets?.length) {
          content += `Type: Asset Collection\n` +
            `Name: ${artifact.data.collectionName || 'Images'}\n` +
            `Images: ${artifact.data.assets.length} images`
          sections.push(content)
        }
        break

      case 'strategy-card':
        if (artifact.data.strategy) {
          content += `Type: Strategy\n` +
            `Strategy: ${artifact.data.strategy}\n` +
            (artifact.data.channel ? `Channel: ${artifact.data.channel}\n` : '') +
            (artifact.data.goals?.length ? `Goals: ${artifact.data.goals.join(', ')}\n` : '')
          sections.push(content)
        }
        break
    }
  })

  if (sections.length === 0) return ''

  return '\n\n## CANVAS CONTEXT\nThe user has added the following to their project canvas:\n\n' + sections.join('\n---\n')
}

export async function POST(request: Request) {
  try {
    const { messages, canvasArtifacts } = await request.json()

    // Debug logging
    console.log('=== CHAT API DEBUG ===')
    console.log('Received canvasArtifacts:', JSON.stringify(canvasArtifacts, null, 2))
    console.log('Number of artifacts:', canvasArtifacts?.length || 0)

    // Format canvas context
    const canvasContext = formatCanvasContext(canvasArtifacts || [])
    console.log('Formatted context:', canvasContext)
    console.log('=====================')

    // Convert messages to Claude format
    const claudeMessages = messages.map((msg: { role: string; content: string }) => ({
      role: msg.role === 'ai' ? 'assistant' : 'user',
      content: msg.content,
    }))

    // Build system prompt with canvas context
    const systemPrompt = DISCOVERY_SYSTEM_PROMPT + canvasContext

    // Call Claude API
    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 1024,
      system: systemPrompt,
      messages: claudeMessages,
    })

    // Extract text content
    const textContent = response.content.find((block) => block.type === 'text')
    const aiMessage = textContent && 'text' in textContent ? textContent.text : 'I apologize, I had trouble responding. Could you try again?'

    // Check for canvas layout instructions
    const layoutMatch = aiMessage.match(/<canvas-layout>([\s\S]*?)<\/canvas-layout>/)
    let layoutInstructions = null
    let cleanMessage = aiMessage

    if (layoutMatch) {
      try {
        layoutInstructions = JSON.parse(layoutMatch[1].trim())
        // Remove layout instructions from visible message
        cleanMessage = aiMessage.replace(/<canvas-layout>[\s\S]*?<\/canvas-layout>/, '').trim()
      } catch (error) {
        console.error('Failed to parse layout instructions:', error)
      }
    }

    return NextResponse.json({
      message: cleanMessage,
      layoutInstructions,
      usage: response.usage,
    })
  } catch (error) {
    console.error('Claude API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate response' },
      { status: 500 }
    )
  }
}
