/**
 * API client for SaralAI FastAPI backend.
 * Handles both standard REST calls and SSE streaming connections.
 */

// Hit FastAPI directly to avoid Next.js proxy timeout (default 30s).
// Model inference can take 30-60s on constrained hardware.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Extract fields from a document image via SSE stream.
 */
export async function extractDocument(
  imageBlob: Blob,
  docType: string = "aadhaar",
  onField: (field: { key: string; value: string; confidence: number }) => void,
  onDone: (summary: { total_fields: number; elapsed_ms: number }) => void,
  onError?: (error: string) => void,
  onRawText?: (text: string) => void,
): Promise<void> {
  const formData = new FormData();
  formData.append("image", imageBlob);
  formData.append("doc_type", docType);

  const response = await fetch(`${API_BASE}/api/extract-doc`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    onError?.(`Server error ${response.status}`);
    return;
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    onError?.("Failed to connect to extraction service");
    return;
  }

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6));
        if (currentEvent === "field") {
          onField(data);
        } else if (currentEvent === "raw_text") {
          onRawText?.(data.text);
        } else if (currentEvent === "done") {
          onDone(data);
        } else if (currentEvent === "error") {
          onError?.(data.message);
        }
      }
    }
  }
}

/**
 * Transcribe audio recording.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  language: string = "auto",
): Promise<{
  transcript: string;
  language_detected: string;
  confidence: number;
  duration_sec: number;
}> {
  const formData = new FormData();
  formData.append("audio", audioBlob);
  formData.append("language", language);

  const response = await fetch(`${API_BASE}/api/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Transcription failed: ${response.status}`;
    try {
      const errBody = await response.json();
      if (errBody?.detail) detail = String(errBody.detail);
      else if (errBody?.message) detail = String(errBody.message);
      else if (typeof errBody === "string") detail = errBody;
    } catch {
      // body was not JSON — keep the status-code message
    }
    throw new Error(detail);
  }
  return response.json();
}

/**
 * Find matching schemes via SSE stream.
 */
export async function findSchemes(
  profile: Record<string, any>,
  narrative: string,
  language: string,
  onThinking: (text: string) => void,
  onScheme: (scheme: Record<string, any>) => void,
  onDone: (summary: Record<string, any>) => void,
  onError?: (error: string) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/find-schemes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile, narrative, language }),
  });

  if (!response.ok) {
    onError?.(`Server error ${response.status}`);
    return;
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    onError?.("Failed to connect to scheme matching service");
    return;
  }

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (currentEvent === "thinking") {
            onThinking(data.text);
          } else if (currentEvent === "scheme") {
            onScheme(data);
          } else if (currentEvent === "done") {
            onDone(data);
          } else if (currentEvent === "error") {
            onError?.(data.message);
          }
        } catch (e) {
          // Skip malformed JSON
        }
      }
    }
  }
}

/**
 * Get full details for a single scheme.
 */
export async function getSchemeDetails(
  schemeId: string,
): Promise<Record<string, any>> {
  const response = await fetch(`${API_BASE}/api/scheme/${schemeId}`);
  if (!response.ok) throw new Error(`Scheme not found: ${response.status}`);
  return response.json();
}

/**
 * Generate a pre-filled PDF form.
 */
export async function generateForm(
  schemeId: string,
  userData: Record<string, any>,
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/generate-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scheme_id: schemeId, user_data: userData }),
  });

  if (!response.ok) throw new Error(`Form generation failed: ${response.status}`);
  return response.blob();
}

/**
 * Text-to-speech: get audio for a text string.
 */
export async function textToSpeech(
  text: string,
  language: string,
  voice: string = "female",
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language, voice }),
  });

  if (!response.ok) throw new Error(`TTS failed: ${response.status}`);
  return response.blob();
}
