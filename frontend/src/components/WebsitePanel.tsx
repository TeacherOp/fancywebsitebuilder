import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { WebsiteMeta } from "@/types";
import { listWebsites, getWebsitePreviewUrl } from "@/services/api";

interface WebsitePanelProps {
  selectedWebsiteId: string | null;
  onSelectWebsite: (websiteId: string | null) => void;
  refreshTrigger?: number;
}

export function WebsitePanel({
  selectedWebsiteId,
  onSelectWebsite,
  refreshTrigger,
}: WebsitePanelProps) {
  const [websites, setWebsites] = useState<WebsiteMeta[]>([]);
  const [loading, setLoading] = useState(true);

  const loadWebsites = async () => {
    try {
      const data = await listWebsites();
      setWebsites(data);
    } catch (error) {
      console.error("Failed to load websites:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWebsites();
  }, [refreshTrigger]);

  const handleOpenInNewTab = () => {
    if (selectedWebsiteId) {
      window.open(getWebsitePreviewUrl(selectedWebsiteId), "_blank");
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      ready: "bg-green-100 text-green-800",
      generating: "bg-yellow-100 text-yellow-800",
      planning: "bg-blue-100 text-blue-800",
      error: "bg-red-100 text-red-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="flex h-full flex-col border-l bg-muted/30">
      <div className="p-4">
        <h2 className="text-lg font-semibold">Websites</h2>
      </div>

      <Separator />

      {/* Website List */}
      <ScrollArea className="h-48 border-b">
        <div className="p-2">
          {loading ? (
            <p className="p-4 text-center text-muted-foreground">Loading...</p>
          ) : websites.length === 0 ? (
            <p className="p-4 text-center text-muted-foreground">
              No websites yet
            </p>
          ) : (
            websites.map((website) => (
              <Card
                key={website.id}
                onClick={() => onSelectWebsite(website.id)}
                className={`mb-2 cursor-pointer transition-colors hover:bg-accent ${
                  selectedWebsiteId === website.id ? "ring-2 ring-primary" : ""
                }`}
              >
                <CardHeader className="p-3">
                  <CardTitle className="flex items-center justify-between text-sm">
                    <span className="truncate">
                      {website.site_name || "Untitled Website"}
                    </span>
                    <span
                      className={`ml-2 rounded-full px-2 py-0.5 text-xs ${getStatusBadge(
                        website.status
                      )}`}
                    >
                      {website.status}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0">
                  <p className="text-xs text-muted-foreground">
                    {website.pages_created?.length || 0} pages
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Preview */}
      <div className="flex flex-1 flex-col">
        <div className="flex items-center justify-between border-b p-2">
          <span className="text-sm font-medium">Preview</span>
          {selectedWebsiteId && (
            <Button variant="outline" size="sm" onClick={handleOpenInNewTab}>
              Open in New Tab
            </Button>
          )}
        </div>

        <div className="flex-1 bg-white">
          {selectedWebsiteId ? (
            <iframe
              src={getWebsitePreviewUrl(selectedWebsiteId)}
              className="h-full w-full border-0"
              title="Website Preview"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Select a website to preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
