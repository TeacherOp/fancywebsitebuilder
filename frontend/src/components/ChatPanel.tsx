import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { Chat, Message } from "@/types";
import { getChat, sendMessage } from "@/services/api";

interface ChatPanelProps {
  chatId: string | null;
  onWebsiteGenerated: (websiteId: string) => void;
}

export function ChatPanel({ chatId, onWebsiteGenerated }: ChatPanelProps) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chatId) {
      setChat(null);
      return;
    }

    const loadChat = async () => {
      try {
        const data = await getChat(chatId);
        setChat(data);
      } catch (error) {
        console.error("Failed to load chat:", error);
      }
    };

    loadChat();
  }, [chatId]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages]);

  const handleSend = async () => {
    if (!chatId || !input.trim() || sending) return;

    const userMessage = input.trim();
    setInput("");
    setSending(true);

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: "temp-user",
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    };

    setChat((prev) =>
      prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : null
    );

    try {
      const response = await sendMessage(chatId, userMessage);

      // Update with real messages
      setChat((prev) => {
        if (!prev) return null;
        const messages = prev.messages.filter((m) => m.id !== "temp-user");
        return {
          ...prev,
          messages: [...messages, response.user_message, response.assistant_message],
          website_id: response.website_id || prev.website_id,
        };
      });

      // Notify if website was generated
      if (response.website_id) {
        onWebsiteGenerated(response.website_id);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // Remove optimistic message on error
      setChat((prev) =>
        prev
          ? { ...prev, messages: prev.messages.filter((m) => m.id !== "temp-user") }
          : null
      );
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getMessageText = (message: Message): string => {
    if (typeof message.content === "string") {
      return message.content;
    }
    // Handle content blocks
    return message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text || "")
      .join("\n");
  };

  if (!chatId) {
    return (
      <div className="flex h-full items-center justify-center bg-muted/10">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-muted-foreground">
            Welcome to Website Builder
          </h2>
          <p className="mt-2 text-muted-foreground">
            Select a chat or create a new one to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col">
      {/* Header */}
      <div className="flex-shrink-0 border-b p-4">
        <h2 className="font-semibold">{chat?.title || "Loading..."}</h2>
      </div>

      {/* Messages - scrollable area */}
      <div className="flex-1 overflow-y-auto p-4 pb-32">
        <div className="space-y-4">
          {chat?.messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap">{getMessageText(message)}</p>
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input - fixed at bottom */}
      <div className="absolute bottom-0 left-0 right-0 border-t bg-background p-4">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the website you want to build..."
            className="min-h-[60px] resize-none"
            disabled={sending}
          />
          <Button onClick={handleSend} disabled={!input.trim() || sending}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
