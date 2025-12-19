import { useState } from "react";
import { ChatList } from "@/components/ChatList";
import { ChatPanel } from "@/components/ChatPanel";
import { WebsitePanel } from "@/components/WebsitePanel";

function App() {
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedWebsiteId, setSelectedWebsiteId] = useState<string | null>(null);
  const [websiteRefresh, setWebsiteRefresh] = useState(0);

  const handleChatCreated = (chatId: string) => {
    setSelectedChatId(chatId);
  };

  const handleWebsiteGenerated = (websiteId: string) => {
    setSelectedWebsiteId(websiteId);
    setWebsiteRefresh((prev) => prev + 1);
  };

  return (
    <div className="flex h-screen">
      {/* Left Sidebar - Chat List */}
      <div className="w-64 flex-shrink-0">
        <ChatList
          selectedChatId={selectedChatId}
          onSelectChat={setSelectedChatId}
          onChatCreated={handleChatCreated}
        />
      </div>

      {/* Center - Chat Panel */}
      <div className="flex-1">
        <ChatPanel
          chatId={selectedChatId}
          onWebsiteGenerated={handleWebsiteGenerated}
        />
      </div>

      {/* Right Sidebar - Website Panel */}
      <div className="w-80 flex-shrink-0">
        <WebsitePanel
          selectedWebsiteId={selectedWebsiteId}
          onSelectWebsite={setSelectedWebsiteId}
          refreshTrigger={websiteRefresh}
        />
      </div>
    </div>
  );
}

export default App;
