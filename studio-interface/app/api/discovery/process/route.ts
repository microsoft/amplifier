import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { randomUUID } from 'crypto';

/**
 * POST /api/discovery/process
 *
 * Processes content items (images, documents, URLs) for the Discovery canvas.
 * Uses the Python amplifier tool in the background.
 *
 * Request body:
 * {
 *   contentType: 'image' | 'document' | 'url' | 'canvas_drawing',
 *   fileName: string,
 *   mimeType?: string,
 *   fileData?: string (base64 for files),
 *   url?: string (for URL content)
 * }
 *
 * Response:
 * {
 *   success: boolean,
 *   sessionId: string,
 *   result?: ProcessingResult
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { contentType, fileName, mimeType, fileData, url } = body;

    // Validate input
    if (!contentType || !fileName) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: contentType, fileName' },
        { status: 400 }
      );
    }

    const sessionId = randomUUID();
    const uploadDir = join(process.cwd(), '.data', 'discovery', 'uploads');
    await mkdir(uploadDir, { recursive: true });

    let filePath: string;

    // Handle different content types
    if (contentType === 'url' && url) {
      // For URLs, we'll pass the URL directly to the processor
      filePath = url;
    } else if (fileData) {
      // Save uploaded file
      const buffer = Buffer.from(fileData, 'base64');
      filePath = join(uploadDir, `${sessionId}-${fileName}`);
      await writeFile(filePath, buffer);
    } else {
      return NextResponse.json(
        { success: false, error: 'Missing fileData or url' },
        { status: 400 }
      );
    }

    // Run Python processor
    const result = await runProcessor(filePath, sessionId, contentType);

    return NextResponse.json({
      success: true,
      sessionId,
      result,
    });
  } catch (error) {
    console.error('Error processing content:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * Run the Python discovery processor
 */
async function runProcessor(
  filePath: string,
  sessionId: string,
  contentType: string
): Promise<any> {
  return new Promise((resolve, reject) => {
    const pythonPath = 'python3';
    // Updated: discovery_processor now lives in amplified-design/ai_working/
    // (migrated from amplifier/ai_working/ on 2025-10-23)
    const modulePath = join(process.cwd(), '..');  // Points to amplified-design/ root
    const sessionFile = join(
      process.cwd(),
      '.data',
      'discovery',
      `session-${sessionId}.json`
    );

    const args = [
      '-m',
      'ai_working.discovery_processor.cli',  // Now resolves to amplified-design/ai_working/
      filePath,
      '--session-file',
      sessionFile,
      '--session-id',
      sessionId,
      '--output',
      join(process.cwd(), '.data', 'discovery', 'output'),
    ];

    const python = spawn(pythonPath, args, {
      cwd: modulePath,
      env: { ...process.env, PYTHONPATH: modulePath },  // Ensure module discovery
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log('[Discovery Processor]', data.toString());
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error('[Discovery Processor Error]', data.toString());
    });

    python.on('close', (code) => {
      if (code === 0) {
        // Parse result from session file
        // For now, return basic success info
        resolve({
          status: 'completed',
          contentType,
          message: 'Content processed successfully',
        });
      } else {
        reject(new Error(`Processor exited with code ${code}\n${stderr}`));
      }
    });

    python.on('error', (error) => {
      reject(error);
    });
  });
}
