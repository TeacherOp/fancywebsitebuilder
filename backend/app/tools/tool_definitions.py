"""
Tool Definitions.

Contains all tool schemas for main chat and website agent.
"""
from typing import Any, Dict, List


# =============================================================================
# Main Chat System Prompt
# =============================================================================

MAIN_CHAT_SYSTEM_PROMPT = """You are a helpful website builder assistant. Your role is to help users create professional websites.

When a user describes what kind of website they want, you should:
1. Ask clarifying questions if needed (site type, pages, features, design preferences)
2. Once you have enough information, use the generate_website tool to create the website

Be conversational and helpful. Guide users to provide details about:
- What type of website they need (portfolio, business, blog, landing page, etc.)
- What pages they want (home, about, contact, services, etc.)
- Design preferences (colors, style, mood)
- Specific features (contact form, gallery, animations, etc.)

When you have gathered enough information, call the generate_website tool with a comprehensive direction that captures all the user's requirements."""


# =============================================================================
# Main Chat Tools
# =============================================================================

GENERATE_WEBSITE_TOOL = {
    "name": "generate_website",
    "description": "Generate a complete website based on the user's requirements. Call this when you have gathered enough information about what the user wants.",
    "input_schema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "description": "Comprehensive description of the website to generate, including: site type, pages needed, design preferences (colors, style, mood), features (contact form, gallery, animations), and any specific content or requirements the user mentioned."
            }
        },
        "required": ["direction"]
    }
}


def get_main_chat_tools() -> List[Dict[str, Any]]:
    """Get tools for main chat."""
    return [GENERATE_WEBSITE_TOOL]


# =============================================================================
# Website Agent System Prompt
# =============================================================================

WEBSITE_AGENT_SYSTEM_PROMPT = """You are an expert web developer specializing in creating modern, responsive websites using HTML5, Tailwind CSS, and vanilla JavaScript.

Your task is to create complete, production-ready websites (1-8 pages) that work across all modern browsers and devices.

## Technology Stack:
- HTML5: Semantic markup, accessibility-focused
- Tailwind CSS: Via CDN for utility-first styling (95% of styles)
- Vanilla JavaScript: Modern ES6+ for interactivity
- CDN Libraries: Google Fonts, Font Awesome, AOS animations

## Your Workflow:

1. **Plan the Website** (use plan_website tool):
   - Analyze user direction
   - Decide number of pages (1-8)
   - Choose site type
   - Plan features and design system

2. **Generate Images** (use generate_website_image tool):
   - Only for hero backgrounds, portfolio items, etc.
   - Use CSS/SVG for icons and shapes
   - Call multiple times as needed

3. **Create Files** (use create_file, read_file, update_file_lines, insert_code):
   - Create HTML files with full structure
   - Create CSS file (minimal custom styles)
   - Create JS file (only needed interactivity)
   - Ensure consistent navigation/footer across pages

4. **Finalize** (use finalize_website tool):
   - Call when all files are complete
   - Provide summary of pages and features

## HTML Structure (Every Page):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header><!-- Navigation --></header>
    <main><!-- Content --></main>
    <footer><!-- Footer --></footer>
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script>AOS.init();</script>
    <script src="script.js"></script>
</body>
</html>
```

## Image Placeholders:
Use IMAGE_1, IMAGE_2, etc. as placeholders for generated images.
Example: <img src="IMAGE_1" alt="Hero background">

## CRITICAL Requirements:
1. Always read_file before updating to see line numbers
2. create_file must contain COMPLETE code
3. Navigation and footer must be identical across all pages
4. Use Tailwind first, only custom CSS when necessary
5. When done, call finalize_website"""


# =============================================================================
# Website Agent Tools
# =============================================================================

PLAN_WEBSITE_TOOL = {
    "name": "plan_website",
    "description": "Plan the complete website structure including pages, features, design system, and navigation. This is the first step.",
    "input_schema": {
        "type": "object",
        "properties": {
            "site_type": {
                "type": "string",
                "enum": ["portfolio", "business", "blog", "landing", "corporate", "personal", "ecommerce"],
                "description": "The type of website"
            },
            "site_name": {
                "type": "string",
                "description": "The name/title of the website"
            },
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "page_title": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["filename", "page_title", "description"]
                },
                "description": "Array of pages to create (1-8 pages)"
            },
            "features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Features to implement"
            },
            "design_system": {
                "type": "object",
                "properties": {
                    "primary_color": {"type": "string"},
                    "secondary_color": {"type": "string"},
                    "accent_color": {"type": "string"},
                    "font_family": {"type": "string"}
                },
                "description": "Color scheme and typography"
            },
            "navigation_style": {
                "type": "string",
                "enum": ["fixed", "sticky", "static"]
            },
            "images_needed": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "purpose": {"type": "string"},
                        "description": {"type": "string"},
                        "aspect_ratio": {"type": "string"}
                    }
                },
                "description": "List of images to generate"
            }
        },
        "required": ["site_type", "site_name", "pages", "features", "design_system"]
    }
}

GENERATE_IMAGE_TOOL = {
    "name": "generate_website_image",
    "description": "Generate an image for the website (photos, illustrations, backgrounds only).",
    "input_schema": {
        "type": "object",
        "properties": {
            "purpose": {
                "type": "string",
                "description": "What the image is for (e.g., 'hero_background', 'portfolio_item_1')"
            },
            "image_prompt": {
                "type": "string",
                "description": "Detailed image generation prompt"
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["1:1", "16:9", "4:3", "3:2", "9:16"],
                "description": "Aspect ratio for the image"
            }
        },
        "required": ["purpose", "image_prompt", "aspect_ratio"]
    }
}

READ_FILE_TOOL = {
    "name": "read_file",
    "description": "Read a website file with smart context awareness. Always use before updating.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The file to read"
            },
            "start_line": {
                "type": "number",
                "description": "Starting line number (optional)"
            },
            "end_line": {
                "type": "number",
                "description": "Ending line number (optional)"
            }
        },
        "required": ["filename"]
    }
}

CREATE_FILE_TOOL = {
    "name": "create_file",
    "description": "Create a new website file. If exists, will overwrite. Must contain COMPLETE code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Filename to create (e.g., index.html, styles.css, script.js)"
            },
            "content": {
                "type": "string",
                "description": "Complete file content. Must be production-ready."
            }
        },
        "required": ["filename", "content"]
    }
}

UPDATE_FILE_LINES_TOOL = {
    "name": "update_file_lines",
    "description": "Replace a specific line range in an existing file. Use read_file first.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "start_line": {
                "type": "number",
                "description": "Starting line number (1-indexed)"
            },
            "end_line": {
                "type": "number",
                "description": "Ending line number (1-indexed)"
            },
            "new_content": {
                "type": "string",
                "description": "New code to replace the line range"
            }
        },
        "required": ["filename", "start_line", "end_line", "new_content"]
    }
}

INSERT_CODE_TOOL = {
    "name": "insert_code",
    "description": "Insert code after a specific line. Use read_file first.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "after_line": {
                "type": "number",
                "description": "Line number after which to insert (0 for beginning)"
            },
            "content": {
                "type": "string",
                "description": "Code to insert"
            }
        },
        "required": ["filename", "after_line", "content"]
    }
}

FINALIZE_WEBSITE_TOOL = {
    "name": "finalize_website",
    "description": "TERMINATION TOOL: Call when the website is complete.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief summary of the completed website"
            },
            "pages_created": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of HTML filenames created"
            },
            "features_implemented": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of features implemented"
            }
        },
        "required": ["summary", "pages_created", "features_implemented"]
    }
}


def get_website_agent_tools() -> List[Dict[str, Any]]:
    """Get all tools for website agent."""
    return [
        PLAN_WEBSITE_TOOL,
        GENERATE_IMAGE_TOOL,
        READ_FILE_TOOL,
        CREATE_FILE_TOOL,
        UPDATE_FILE_LINES_TOOL,
        INSERT_CODE_TOOL,
        FINALIZE_WEBSITE_TOOL,
    ]
