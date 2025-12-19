// Chat types
export interface ChatMeta {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  website_id?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string | ContentBlock[];
  timestamp: string;
  model?: string;
  tokens?: { input_tokens: number; output_tokens: number };
  error?: boolean;
}

export interface ContentBlock {
  type: "text" | "tool_use" | "tool_result";
  text?: string;
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
  tool_use_id?: string;
  content?: string;
}

export interface Chat extends ChatMeta {
  messages: Message[];
}

// Website types
export interface WebsiteMeta {
  id: string;
  status: "generating" | "planning" | "ready" | "error";
  site_name?: string;
  created_at: string;
  pages_created: string[];
}

export interface Website extends WebsiteMeta {
  chat_id: string;
  summary?: string;
  features_implemented?: string[];
  images?: ImageInfo[];
  plan?: WebsitePlan;
}

export interface ImageInfo {
  purpose: string;
  filename: string;
  placeholder: string;
  url: string;
}

export interface WebsitePlan {
  site_type: string;
  site_name: string;
  pages: { filename: string; page_title: string; description: string }[];
  features: string[];
  design_system?: {
    primary_color?: string;
    secondary_color?: string;
    font_family?: string;
  };
}

// API response types
export interface ChatsResponse {
  chats: ChatMeta[];
}

export interface WebsitesResponse {
  websites: WebsiteMeta[];
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
  website_id?: string;
}
