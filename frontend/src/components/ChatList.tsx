import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { ChatMeta } from "@/types";
import { listChats, createChat, deleteChat } from "@/services/api";

interface ChatListProps {
  selectedChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onChatCreated: (chatId: string) => void;
}

export function ChatList({
  selectedChatId,
  onSelectChat,
  onChatCreated,
}: ChatListProps) {
  const [chats, setChats] = useState<ChatMeta[]>([]);
  const [loading, setLoading] = useState(true);

  const loadChats = async () => {
    try {
      const data = await listChats();
      setChats(data);
    } catch (error) {
      console.error("Failed to load chats:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChats();
  }, []);

  const handleNewChat = async () => {
    try {
      const chat = await createChat();
      setChats((prev) => [chat, ...prev]);
      onChatCreated(chat.id);
    } catch (error) {
      console.error("Failed to create chat:", error);
    }
  };

  const handleDeleteChat = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteChat(chatId);
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (selectedChatId === chatId) {
        onSelectChat("");
      }
    } catch (error) {
      console.error("Failed to delete chat:", error);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };

  return (
    <div className="flex h-full flex-col border-r bg-muted/30">
      <div className="p-4">
        <h2 className="mb-4 text-lg font-semibold">Chats</h2>
        <Button onClick={handleNewChat} className="w-full">
          + New Chat
        </Button>
      </div>

      <Separator />

      <ScrollArea className="flex-1">
        <div className="p-2">
          {loading ? (
            <p className="p-4 text-center text-muted-foreground">Loading...</p>
          ) : chats.length === 0 ? (
            <p className="p-4 text-center text-muted-foreground">
              No chats yet
            </p>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`group mb-1 cursor-pointer rounded-lg p-3 transition-colors hover:bg-accent ${
                  selectedChatId === chat.id ? "bg-accent" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{chat.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(chat.created_at)} - {chat.message_count} msgs
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteChat(chat.id, e)}
                    className="ml-2 hidden text-muted-foreground hover:text-destructive group-hover:block"
                  >
                    x
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
