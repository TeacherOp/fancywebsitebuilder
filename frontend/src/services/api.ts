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
