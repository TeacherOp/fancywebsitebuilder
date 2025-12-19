import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { WebsiteMeta } from "@/types";
import { listWebsites, getWebsitePreviewUrl } from "@/services/api";

interface WebsitePanelProps {
  refreshTrigger?: number;
}

export function WebsitePanel({ refreshTrigger }: WebsitePanelProps) {
  const [websites, setWebsites] = useState<WebsiteMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWebsite, setSelectedWebsite] = useState<WebsiteMeta | null>(
    null
  );
  const [previewOpen, setPreviewOpen] = useState(false);

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

  const handleWebsiteClick = (website: WebsiteMeta) => {
    setSelectedWebsite(website);
    setPreviewOpen(true);
  };

  const handleOpenInNewTab = () => {
    if (selectedWebsite) {
      window.open(getWebsitePreviewUrl(selectedWebsite.id), "_blank");
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
    <>
      <div className="flex h-full flex-col border-l bg-muted/30">
        <div className="flex-shrink-0 p-4">
          <h2 className="text-lg font-semibold">Websites</h2>
        </div>

        <Separator />

        {/* Website List */}
        <ScrollArea className="flex-1">
          <div className="p-2">
            {loading ? (
              <p className="p-4 text-center text-muted-foreground">
                Loading...
              </p>
            ) : websites.length === 0 ? (
              <p className="p-4 text-center text-muted-foreground">
                No websites yet
              </p>
            ) : (
              websites.map((website) => (
                <Card
                  key={website.id}
                  onClick={() => handleWebsiteClick(website)}
                  className="mb-2 cursor-pointer transition-colors hover:bg-accent"
                >
                  <CardHeader className="p-3">
                    <CardTitle className="text-sm">
                      <div className="flex items-start justify-between gap-2">
                        <span className="break-words">
                          {website.site_name || "Untitled Website"}
                        </span>
                        <span
                          className={`flex-shrink-0 rounded-full px-2 py-0.5 text-xs ${getStatusBadge(
                            website.status
                          )}`}
                        >
                          {website.status}
                        </span>
                      </div>
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
      </div>

      {/* Preview Modal */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="flex h-[95vh] w-[95vw] max-w-[95vw] sm:max-w-[95vw] flex-col gap-2 p-4">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center justify-between pr-8">
              <span>{selectedWebsite?.site_name || "Website Preview"}</span>
              <Button variant="outline" size="sm" onClick={handleOpenInNewTab}>
                Open in New Tab
              </Button>
            </DialogTitle>
          </DialogHeader>
          <div className="relative min-h-0 flex-1">
            {selectedWebsite && (
              <iframe
                src={getWebsitePreviewUrl(selectedWebsite.id)}
                className="absolute inset-0 h-full w-full rounded-md border bg-white"
                title="Website Preview"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
