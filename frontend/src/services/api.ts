import type {
  Chat,
  ChatMeta,
  ChatsResponse,
  SendMessageResponse,
  Website,
  WebsiteMeta,
  WebsitesResponse,
} from "@/types";

const API_BASE = "http://localhost:5000/api";

// Generic fetch helper
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  return response.json();
}

// Chat API
export async function listChats(): Promise<ChatMeta[]> {
  const data = await fetchApi<ChatsResponse>("/chats");
  return data.chats;
}

export async function createChat(title?: string): Promise<Chat> {
  return fetchApi<Chat>("/chats", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function getChat(chatId: string): Promise<Chat> {
  return fetchApi<Chat>(`/chats/${chatId}`);
}

export async function deleteChat(chatId: string): Promise<void> {
  await fetchApi(`/chats/${chatId}`, { method: "DELETE" });
}

export async function sendMessage(
  chatId: string,
  message: string
): Promise<SendMessageResponse> {
  return fetchApi<SendMessageResponse>(`/chats/${chatId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

// Progress event types
export interface ProgressEvent {
  type: "agent_started" | "iteration_start" | "tool_start" | "agent_completed" | "complete" | "error" | "ping";
  iteration?: number;
  max_iterations?: number;
  tool_name?: string;
  tool_details?: string;
  website_id?: string;
  pages_created?: string[];
  iterations?: number;
  user_message?: Record<string, unknown>;
  assistant_message?: Record<string, unknown>;
  error?: string;
}

export async function sendMessageStream(
  chatId: string,
  message: string,
  onProgress: (event: ProgressEvent) => void
): Promise<SendMessageResponse> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: SendMessageResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event = JSON.parse(line.slice(6)) as ProgressEvent;
          onProgress(event);

          if (event.type === "complete") {
            finalResult = {
              user_message: event.user_message as unknown as SendMessageResponse["user_message"],
              assistant_message: event.assistant_message as unknown as SendMessageResponse["assistant_message"],
              website_id: event.website_id,
            };
          } else if (event.type === "error") {
            throw new Error(event.error || "Unknown error");
          }
        } catch (e) {
          if (e instanceof SyntaxError) {
            console.warn("Failed to parse SSE event:", line);
          } else {
            throw e;
          }
        }
      }
    }
  }

  if (!finalResult) {
    throw new Error("Stream ended without complete event");
  }

  return finalResult;
}

// Asset upload
export interface UploadAssetResponse {
  filename: string;
  url: string;
}

export interface Asset {
  filename: string;
  type: "image" | "text" | "unknown";
  status: "pending" | "processing" | "ready" | "error";
  url: string;
  brief_summary?: string;
  metadata?: Record<string, unknown>;
}

export async function uploadAsset(
  chatId: string,
  file: File
): Promise<UploadAssetResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/chats/${chatId}/assets`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `Upload failed: ${response.status}`);
  }

  return response.json();
}

export async function listAssets(chatId: string): Promise<Asset[]> {
  const data = await fetchApi<{ assets: Asset[] }>(`/chats/${chatId}/assets`);
  return data.assets;
}

export function getAssetUrl(chatId: string, filename: string): string {
  return `${API_BASE}/chats/${chatId}/assets/${filename}`;
}

// Brand guidelines
export async function getBrandGuidelines(chatId: string): Promise<string> {
  const data = await fetchApi<{ brand_guidelines: string }>(
    `/chats/${chatId}/brand-guidelines`
  );
  return data.brand_guidelines;
}

export async function updateBrandGuidelines(
  chatId: string,
  brandGuidelines: string
): Promise<void> {
  await fetchApi(`/chats/${chatId}/brand-guidelines`, {
    method: "PUT",
    body: JSON.stringify({ brand_guidelines: brandGuidelines }),
  });
}

// Website API
export async function listWebsites(): Promise<WebsiteMeta[]> {
  const data = await fetchApi<WebsitesResponse>("/websites");
  return data.websites;
}

export async function getWebsite(websiteId: string): Promise<Website> {
  return fetchApi<Website>(`/websites/${websiteId}`);
}

export function getWebsitePreviewUrl(websiteId: string): string {
  return `${API_BASE}/websites/${websiteId}/preview`;
}

export function getWebsiteFileUrl(websiteId: string, filepath: string): string {
  return `${API_BASE}/websites/${websiteId}/files/${filepath}`;
}
