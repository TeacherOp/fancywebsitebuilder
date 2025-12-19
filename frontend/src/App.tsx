import { useState } from "react";
import { ChatList } from "@/components/ChatList";
import { ChatPanel } from "@/components/ChatPanel";
import { WebsitePanel } from "@/components/WebsitePanel";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";

function App() {
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [websiteRefresh, setWebsiteRefresh] = useState(0);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  const handleChatCreated = (chatId: string) => {
    setSelectedChatId(chatId);
  };

  const handleWebsiteGenerated = (_websiteId: string) => {
    setWebsiteRefresh((prev) => prev + 1);
    // Auto-open right sidebar when website is generated
    setRightSidebarOpen(true);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left Sidebar - Chat List */}
      <Collapsible
        open={leftSidebarOpen}
        onOpenChange={setLeftSidebarOpen}
        className="flex flex-shrink-0"
      >
        <CollapsibleContent className="w-64 h-full">
          <ChatList
            selectedChatId={selectedChatId}
            onSelectChat={setSelectedChatId}
            onChatCreated={handleChatCreated}
          />
        </CollapsibleContent>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-full rounded-none border-r px-2 hover:bg-muted"
          >
            {leftSidebarOpen ? "<" : ">"}
          </Button>
        </CollapsibleTrigger>
      </Collapsible>

      {/* Center - Chat Panel */}
      <div className="flex-1 min-w-0 h-full overflow-hidden">
        <ChatPanel
          chatId={selectedChatId}
          onWebsiteGenerated={handleWebsiteGenerated}
        />
      </div>

      {/* Right Sidebar - Website Panel */}
      <Collapsible
        open={rightSidebarOpen}
        onOpenChange={setRightSidebarOpen}
        className="flex flex-shrink-0"
      >
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-full rounded-none border-l px-2 hover:bg-muted"
          >
            {rightSidebarOpen ? ">" : "<"}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="w-72 h-full">
          <WebsitePanel refreshTrigger={websiteRefresh} />
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

export default App;
