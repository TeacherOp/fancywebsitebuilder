import { useEffect, useRef, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";
import type { Chat, Message } from "@/types";
import {
  getChat,
  sendMessageStream,
  uploadAsset,
  listAssets,
  updateBrandGuidelines,
  type Asset,
  type ProgressEvent,
} from "@/services/api";

interface ChatPanelProps {
  chatId: string | null;
  onWebsiteGenerated: (websiteId: string) => void;
}

export function ChatPanel({ chatId, onWebsiteGenerated }: ChatPanelProps) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [progressStatus, setProgressStatus] = useState<string>("");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [brandGuidelines, setBrandGuidelines] = useState("");
  const [brandGuidelinesOpen, setBrandGuidelinesOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!chatId) {
      setChat(null);
      setAssets([]);
      setBrandGuidelines("");
      return;
    }

    const loadChat = async () => {
      try {
        const data = await getChat(chatId);
        setChat(data);
        setBrandGuidelines(data.brand_guidelines || "");

        // Load assets
        const assetList = await listAssets(chatId);
        setAssets(assetList);
      } catch (error) {
        console.error("Failed to load chat:", error);
      }
    };

    loadChat();
  }, [chatId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages]);

  const handleProgressEvent = (event: ProgressEvent) => {
    switch (event.type) {
      case "agent_started":
        setProgressStatus("Starting website generation...");
        break;
      case "iteration_start":
        setProgressStatus(`Iteration ${event.iteration}/${event.max_iterations}`);
        break;
      case "tool_start":
        setProgressStatus(
          `Iteration ${event.iteration}/${30} - ${event.tool_details || event.tool_name}`
        );
        break;
      case "agent_completed":
        setProgressStatus(`Completed in ${event.iterations} iterations`);
        break;
      case "ping":
        // Keep alive, no status update needed
        break;
    }
  };

  const handleSend = async () => {
    if (!chatId || !input.trim() || sending) return;

    const userMessage = input.trim();
    setInput("");
    setSending(true);
    setProgressStatus("Thinking...");

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
      const response = await sendMessageStream(chatId, userMessage, handleProgressEvent);

      setChat((prev) => {
        if (!prev) return null;
        const messages = prev.messages.filter((m) => m.id !== "temp-user");
        return {
          ...prev,
          messages: [
            ...messages,
            response.user_message,
            response.assistant_message,
          ],
          website_id: response.website_id || prev.website_id,
        };
      });

      if (response.website_id) {
        onWebsiteGenerated(response.website_id);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      setChat((prev) =>
        prev
          ? {
              ...prev,
              messages: prev.messages.filter((m) => m.id !== "temp-user"),
            }
          : null
      );
    } finally {
      setSending(false);
      setProgressStatus("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!chatId || !e.target.files?.length) return;

    const file = e.target.files[0];
    setUploading(true);

    try {
      const result = await uploadAsset(chatId, file);
      // Create Asset from upload response
      const newAsset: Asset = {
        filename: result.filename,
        type: file.type.startsWith("image/") ? "image" : "text",
        status: "pending",
        url: result.url,
      };
      setAssets((prev) => [...prev, newAsset]);
    } catch (error) {
      console.error("Failed to upload file:", error);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleBrandGuidelinesBlur = async () => {
    if (!chatId) return;
    try {
      await updateBrandGuidelines(chatId, brandGuidelines);
      toast.success("Brand guidelines saved");
    } catch (error) {
      console.error("Failed to save brand guidelines:", error);
      toast.error("Failed to save brand guidelines");
    }
  };

  // Poll for asset status updates when any are processing
  const refreshAssets = useCallback(async () => {
    if (!chatId) return;
    try {
      const assetList = await listAssets(chatId);
      setAssets(assetList);
    } catch (error) {
      console.error("Failed to refresh assets:", error);
    }
  }, [chatId]);

  useEffect(() => {
    const hasProcessing = assets.some(
      (a) => a.status === "pending" || a.status === "processing"
    );
    if (!hasProcessing) return;

    const interval = setInterval(refreshAssets, 3000);
    return () => clearInterval(interval);
  }, [assets, refreshAssets]);

  const getMessageText = (message: Message): string => {
    if (typeof message.content === "string") {
      return message.content;
    }
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

      {/* Brand Guidelines - Collapsible */}
      <Collapsible
        open={brandGuidelinesOpen}
        onOpenChange={setBrandGuidelinesOpen}
        className="flex-shrink-0 border-b"
      >
        <CollapsibleTrigger asChild>
          <button className="flex w-full items-center justify-between px-4 py-2 text-sm hover:bg-muted/50">
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                />
              </svg>
              Brand Guidelines & Assets
              {(brandGuidelines || assets.length > 0) && (
                <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                  {assets.length > 0 && `${assets.length} files`}
                  {brandGuidelines && assets.length > 0 && " + "}
                  {brandGuidelines && "guidelines"}
                </span>
              )}
            </span>
            <svg
              className={`h-4 w-4 transition-transform ${brandGuidelinesOpen ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="space-y-4 p-4 pt-2">
            {/* Brand Guidelines Text */}
            <div>
              <label className="mb-1 block text-sm font-medium">
                Brand Guidelines
              </label>
              <Textarea
                value={brandGuidelines}
                onChange={(e) => setBrandGuidelines(e.target.value)}
                onBlur={handleBrandGuidelinesBlur}
                placeholder="Describe your brand: colors (e.g., primary: #3B82F6), fonts, style preferences, tone..."
                className="min-h-[80px] resize-none text-sm"
              />
            </div>

            {/* Asset Upload */}
            <div>
              <label className="mb-1 block text-sm font-medium">
                Images & Icons
              </label>
              <div className="flex flex-wrap gap-2">
                {assets.map((asset) => (
                  <div
                    key={asset.filename}
                    className="group relative h-16 w-16 overflow-hidden rounded border bg-muted"
                    title={
                      asset.status === "ready" && asset.brief_summary
                        ? asset.brief_summary
                        : asset.status === "processing"
                          ? "Analyzing..."
                          : asset.status === "error"
                            ? "Analysis failed"
                            : asset.filename
                    }
                  >
                    <img
                      src={`http://localhost:5000${asset.url}`}
                      alt={asset.filename}
                      className="h-full w-full object-cover"
                    />
                    {/* Status indicator overlay */}
                    {asset.status === "pending" || asset.status === "processing" ? (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                        <svg
                          className="h-6 w-6 animate-spin text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                          />
                        </svg>
                      </div>
                    ) : asset.status === "ready" ? (
                      <div className="absolute bottom-0 right-0 rounded-tl bg-green-500 p-0.5">
                        <svg
                          className="h-3 w-3 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    ) : asset.status === "error" ? (
                      <div className="absolute bottom-0 right-0 rounded-tl bg-red-500 p-0.5">
                        <svg
                          className="h-3 w-3 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </div>
                    ) : null}
                    {/* Hover overlay with filename */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                      <span className="max-w-full truncate px-1 text-xs text-white">
                        {asset.filename}
                      </span>
                    </div>
                  </div>
                ))}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="flex h-16 w-16 items-center justify-center rounded border-2 border-dashed border-muted-foreground/30 hover:border-muted-foreground/50"
                >
                  {uploading ? (
                    <svg
                      className="h-6 w-6 animate-spin text-muted-foreground"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="h-6 w-6 text-muted-foreground"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  )}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".png,.webp,.jpg,.jpeg,.svg,.ico"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                PNG, WebP, JPG, SVG, ICO
              </p>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>

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
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap">
                    {getMessageText(message)}
                  </p>
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5">
                    <ReactMarkdown>{getMessageText(message)}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-muted p-3">
                <div className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin text-muted-foreground"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  <p className="text-muted-foreground">
                    {progressStatus || "Thinking..."}
                  </p>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input - fixed at bottom */}
      <div className="absolute bottom-0 left-0 right-0 border-t bg-background p-4">
        <div className="flex items-end gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the website you want to build..."
            className="min-h-[60px] resize-none"
            disabled={sending}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="h-[60px] px-6"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
