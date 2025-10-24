import { NextRequest } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

/**
 * GET /api/discovery/status?sessionId=xxx
 *
 * Returns the current processing status for a session.
 * Uses Server-Sent Events (SSE) for real-time updates.
 *
 * Query params:
 * - sessionId: string - Session ID to check status for
 *
 * Response (SSE stream):
 * data: {
 *   "status": "processing" | "completed" | "failed",
 *   "progress": number (0-100),
 *   "processed": number,
 *   "total": number,
 *   "results": ProcessingResult[]
 * }
 */
export async function GET(request: NextRequest) {
  const sessionId = request.nextUrl.searchParams.get('sessionId');

  if (!sessionId) {
    return new Response('Missing sessionId parameter', { status: 400 });
  }

  // Create a ReadableStream for SSE
  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();

      // Send initial connection message
      controller.enqueue(encoder.encode('event: connected\n'));
      controller.enqueue(encoder.encode(`data: {"sessionId":"${sessionId}"}\n\n`));

      // Poll session file for updates
      const sessionFile = join(
        process.cwd(),
        '.data',
        'discovery',
        `session-${sessionId}.json`
      );

      let lastUpdate = '';
      const pollInterval = 1000; // Poll every second
      const maxPolls = 300; // 5 minutes timeout

      for (let i = 0; i < maxPolls; i++) {
        try {
          const data = await readFile(sessionFile, 'utf-8');
          const session = JSON.parse(data);

          // Check if session data has changed
          if (data !== lastUpdate) {
            lastUpdate = data;

            const progress =
              session.total_items > 0
                ? (session.processed_items.length / session.total_items) * 100
                : 0;

            const status =
              session.processed_items.length === session.total_items
                ? 'completed'
                : 'processing';

            const update = {
              status,
              progress: Math.round(progress),
              processed: session.processed_items.length,
              total: session.total_items,
              results: session.results || [],
              failed: session.failed_items || [],
            };

            controller.enqueue(encoder.encode('event: progress\n'));
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(update)}\n\n`));

            // If completed, close the stream
            if (status === 'completed') {
              controller.enqueue(encoder.encode('event: complete\n'));
              controller.enqueue(encoder.encode(`data: ${JSON.stringify(update)}\n\n`));
              break;
            }
          }
        } catch (error) {
          // Session file doesn't exist yet or is invalid
          if (i === 0) {
            // First poll, session might not be created yet
            controller.enqueue(encoder.encode('event: waiting\n'));
            controller.enqueue(
              encoder.encode(`data: {"message":"Waiting for processing to start"}\n\n`)
            );
          }
        }

        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, pollInterval));
      }

      // Timeout reached
      controller.enqueue(encoder.encode('event: timeout\n'));
      controller.enqueue(
        encoder.encode(`data: {"message":"Status polling timed out"}\n\n`)
      );
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

/**
 * POST /api/discovery/status
 *
 * Get session status as a one-time JSON response (non-streaming).
 *
 * Request body:
 * {
 *   sessionId: string
 * }
 *
 * Response:
 * {
 *   success: boolean,
 *   status: 'processing' | 'completed' | 'failed',
 *   progress: number,
 *   results?: ProcessingResult[]
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const { sessionId } = await request.json();

    if (!sessionId) {
      return Response.json(
        { success: false, error: 'Missing sessionId' },
        { status: 400 }
      );
    }

    const sessionFile = join(
      process.cwd(),
      '.data',
      'discovery',
      `session-${sessionId}.json`
    );

    try {
      const data = await readFile(sessionFile, 'utf-8');
      const session = JSON.parse(data);

      const progress =
        session.total_items > 0
          ? (session.processed_items.length / session.total_items) * 100
          : 0;

      const status =
        session.processed_items.length === session.total_items
          ? 'completed'
          : 'processing';

      return Response.json({
        success: true,
        status,
        progress: Math.round(progress),
        processed: session.processed_items.length,
        total: session.total_items,
        results: session.results || [],
        failed: session.failed_items || [],
      });
    } catch (error) {
      return Response.json(
        {
          success: false,
          error: 'Session not found or processing not started',
        },
        { status: 404 }
      );
    }
  } catch (error) {
    console.error('Error checking status:', error);
    return Response.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
