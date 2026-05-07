/**
 * SSE (Server-Sent Events) helper utilities.
 */

export interface SSEEvent {
  event: string;
  data: any;
}

/**
 * Parse a raw SSE text chunk into structured events.
 */
export function parseSSEChunk(chunk: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  const lines = chunk.split("\n");

  let currentEvent = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      currentEvent = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      try {
        const data = JSON.parse(line.slice(6));
        events.push({ event: currentEvent || "message", data });
      } catch {
        events.push({ event: currentEvent || "message", data: line.slice(6) });
      }
      currentEvent = "";
    }
  }

  return events;
}

/**
 * Create an async iterator over SSE events from a fetch Response.
 */
export async function* streamSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const events = parseSSEChunk(part);
      for (const event of events) {
        yield event;
      }
    }
  }

  // Process remaining buffer
  if (buffer.trim()) {
    const events = parseSSEChunk(buffer);
    for (const event of events) {
      yield event;
    }
  }
}
