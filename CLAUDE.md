# Website Builder

AI-powered website builder. Users chat with Claude to describe their website, then an agent generates complete HTML/CSS/JS files with AI-generated images.

## Status: v0.1 - MVP Complete
- [x] Flask backend with chat + website agent
- [x] React frontend with 3-panel layout
- [x] Claude Opus 4.5 integration
- [x] Gemini image generation integration
- [ ] Testing & refinements pending

## Tech Stack
- **Backend**: Flask (Python) - port 5000
- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn/ui - port 5173
- **LLM**: Claude Opus 4.5 (`claude-opus-4-5-20251101`)
- **Images**: Google Gemini (`gemini-3-pro-image-preview`)
- **Storage**: Local JSON files (no database)

## Architecture

```
User Chat -> Main Chat Service -> generate_website tool -> Website Agent -> Generated Files
```

**Main Chat**: Single tool (`generate_website`) - triggers agent when user is ready.

**Website Agent**: 7 tools, agentic loop (max 30 iterations):
- `plan_website` - Plan structure, pages, design
- `generate_website_image` - Generate images via Gemini
- `read_file`, `create_file`, `update_file_lines`, `insert_code` - File ops
- `finalize_website` - Termination tool

## Data Structure
```
backend/data/
  chats/
    index.json          # Chat list with metadata
    {chat_id}.json      # Chat messages
  agents/
    {execution_id}.json # Agent execution logs
  websites/
    {website_id}/
      metadata.json     # Website info
      index.html, styles.css, script.js
      assets/           # Generated images
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chats` | List chats |
| POST | `/api/chats` | Create chat |
| GET | `/api/chats/{id}` | Get chat + messages |
| POST | `/api/chats/{id}/messages` | Send message |
| GET | `/api/websites` | List websites |
| GET | `/api/websites/{id}/preview` | Preview in iframe |
| GET | `/api/websites/{id}/files/{path}` | Serve files |

## Running

**Backend:**
```bash
cd backend
source fancyenv/bin/activate
python run.py  # http://localhost:5000
```

**Frontend:**
```bash
cd frontend
npm run dev  # http://localhost:5173
```

## Project Structure
```
backend/
  app/
    routes/           # API endpoints
    services/         # Business logic
    tools/            # Tool definitions
    utils/            # Helpers
  data/               # JSON storage (gitignored)
  run.py

frontend/
  src/
    components/
      ui/             # shadcn components
      ChatList.tsx    # Left sidebar
      ChatPanel.tsx   # Center chat
      WebsitePanel.tsx # Right sidebar + preview
    services/api.ts   # Backend API calls
    types/index.ts    # TypeScript types
    App.tsx           # Main layout
```

## Key Files
- `backend/app/services/main_chat_service.py` - Chat orchestration
- `backend/app/services/website_agent_service.py` - Agentic website generation
- `backend/app/tools/tool_definitions.py` - All tool schemas + prompts
- `frontend/src/App.tsx` - Main 3-column layout
