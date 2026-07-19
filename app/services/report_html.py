import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HTML_STYLE = """
:root {
    --bg-color: #0b0f19;
    --text-color: #f3f4f6;
    --card-bg: #111827;
    --border-color: #374151;
    --primary-color: #6366f1;
    --primary-hover: #4f46e5;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --info-color: #3b82f6;
    --blockquote-border: #4f46e5;
    --table-header-bg: #1f2937;
}

body {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px 20px;
}

h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
    font-weight: 700;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 {
    font-size: 2.5rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 10px;
    margin-top: 2em;
}

h2 {
    font-size: 1.8rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
}

h3 {
    font-size: 1.4rem;
}

p {
    margin-bottom: 1.2em;
}

a {
    color: var(--primary-color);
    text-decoration: none;
    transition: color 0.2s;
}

a:hover {
    color: var(--primary-hover);
    text-decoration: underline;
}

code {
    font-family: 'Fira Code', 'Courier New', Courier, monospace;
    background-color: #1f2937;
    color: #f43f5e;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
}

pre {
    background-color: #111827;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
}

pre code {
    background-color: transparent;
    color: var(--text-color);
    padding: 0;
    border-radius: 0;
}

blockquote {
    border-left: 4px solid var(--blockquote-border);
    background-color: #1e1b4b;
    margin: 1.5em 0;
    padding: 12px 24px;
    border-radius: 0 8px 8px 0;
}

blockquote p {
    margin: 0;
    font-style: italic;
}

/* Callout blocks */
.callout {
    border-left: 4px solid var(--primary-color);
    background-color: #1e1b4b;
    margin: 1.5em 0;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
}

.callout.important {
    border-left-color: var(--danger-color);
    background-color: #451a1a;
}

.callout.note {
    border-left-color: var(--info-color);
    background-color: #172554;
}

.callout.tip {
    border-left-color: var(--success-color);
    background-color: #064e3b;
}

.callout-title {
    font-weight: bold;
    margin-bottom: 8px;
    color: #ffffff;
}

ul, ol {
    margin-bottom: 1.2em;
    padding-left: 2em;
}

li {
    margin-bottom: 0.4em;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 2em 0;
    background-color: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
}

th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: var(--table-header-bg);
    color: #ffffff;
    font-weight: 600;
}

tr:hover {
    background-color: #1f2937;
}

hr {
    border: 0;
    border-top: 1px solid var(--border-color);
    margin: 3em 0;
}

.footer {
    text-align: center;
    margin-top: 80px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
    font-size: 0.9rem;
    color: #9ca3af;
}
"""

def parse_markdown_to_html(md_text: str) -> str:
    """A simple line-based parser to compile Markdown to HTML without dependencies."""
    lines = md_text.splitlines()
    html_lines = []
    
    in_list = False
    list_type = None  # 'ul' or 'ol'
    in_table = False
    
    in_code_block = False
    code_content = []
    
    in_blockquote = False
    blockquote_content = []
    
    in_callout = False
    callout_type = None  # 'important', 'note', 'tip'
    callout_content = []

    def close_list():
        nonlocal in_list, list_type
        if in_list:
            html_lines.append(f"</{list_type}>")
            in_list = False
            list_type = None

    def close_table():
        nonlocal in_table
        if in_table:
            html_lines.append("</tbody></table>")
            in_table = False

    def close_blockquote():
        nonlocal in_blockquote, blockquote_content
        if in_blockquote:
            content = " ".join(blockquote_content)
            html_lines.append(f"blockquote><p>{content}</p></blockquote>")
            in_blockquote = False
            blockquote_content = []

    def close_callout():
        nonlocal in_callout, callout_type, callout_content
        if in_callout:
            content = "<br>".join(callout_content)
            html_lines.append(
                f"<div class=\"callout {callout_type}\">"
                f"<div class=\"callout-title\">{callout_type.upper()}</div>"
                f"{content}</div>"
            )
            in_callout = False
            callout_type = None
            callout_content = []

    for line in lines:
        stripped = line.strip()
        
        # 1. Code block handling
        if stripped.startswith("```"):
            if in_code_block:
                html_lines.append(f"<pre><code>{'<br>'.join(code_content)}</code></pre>")
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            # Escape HTML characters in code block
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_content.append(escaped)
            continue

        # 2. Callout / Alert blocks
        if stripped.startswith("> [!"):
            close_list()
            close_table()
            close_blockquote()
            close_callout()
            in_callout = True
            # Extract type
            match = re.match(r"^>\s*\[!(IMPORTANT|NOTE|TIP)\]", stripped, re.IGNORECASE)
            if match:
                callout_type = match.group(1).lower()
            else:
                callout_type = "note"
            continue

        if in_callout:
            if stripped.startswith(">"):
                # Clean prefix
                content_line = stripped[1:].strip()
                # Clean list items inside callouts if any
                if content_line.startswith("-"):
                    content_line = f"• {content_line[1:].strip()}"
                
                # Apply inline styles
                content_line = apply_inline_styles(content_line)
                callout_content.append(content_line)
                continue
            else:
                close_callout()

        # 3. Standard Blockquote handling
        if stripped.startswith(">") and not in_callout:
            close_list()
            close_table()
            close_callout()
            if not in_blockquote:
                in_blockquote = True
            content_line = stripped[1:].strip()
            content_line = apply_inline_styles(content_line)
            blockquote_content.append(content_line)
            continue
        elif in_blockquote:
            close_blockquote()

        # 4. Heading handling
        if stripped.startswith("#"):
            close_list()
            close_table()
            close_blockquote()
            close_callout()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped.lstrip("#").strip()
            
            # Extract possible anchor tag if manually written
            anchor_match = re.search(r'<a id="([^"]+)"></a>', title)
            if anchor_match:
                id_val = anchor_match.group(1)
                title = re.sub(r'<a id="[^"]+"></a>', "", title).strip()
            else:
                id_val = title.lower().replace(" ", "-").replace(",", "").replace(".", "")

            html_lines.append(f"<h{level} id=\"{id_val}\">{title}</h{level}>")
            continue

        # 5. Table handling
        if stripped.startswith("|"):
            close_list()
            close_blockquote()
            close_callout()
            
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            
            # Skip separator line (e.g. |---|---|)
            if all(re.match(r"^:?-+:?$", cell) for cell in cells):
                continue
                
            if not in_table:
                in_table = True
                html_lines.append("<table><thead><tr>")
                for cell in cells:
                    html_lines.append(f"<th>{apply_inline_styles(cell)}</th>")
                html_lines.append("</tr></thead><tbody>")
            else:
                html_lines.append("<tr>")
                for cell in cells:
                    html_lines.append(f"<td>{apply_inline_styles(cell)}</td>")
                html_lines.append("</tr>")
            continue
        elif in_table:
            close_table()

        # 6. List handling
        if stripped.startswith("- ") or stripped.startswith("* "):
            close_table()
            close_blockquote()
            close_callout()
            if not in_list or list_type != "ul":
                close_list()
                in_list = True
                list_type = "ul"
                html_lines.append("<ul>")
            content = apply_inline_styles(stripped[2:])
            html_lines.append(f"<li>{content}</li>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            close_table()
            close_blockquote()
            close_callout()
            if not in_list or list_type != "ol":
                close_list()
                in_list = True
                list_type = "ol"
                html_lines.append("<ol>")
            match = re.match(r"^\d+\.\s+(.*)", stripped)
            content = apply_inline_styles(match.group(1))
            html_lines.append(f"<li>{content}</li>")
            continue

        # 7. Blank lines / Paragraphs
        if not stripped:
            close_list()
            close_table()
            close_blockquote()
            close_callout()
            continue

        # Default paragraph line
        close_list()
        close_table()
        close_blockquote()
        close_callout()
        html_lines.append(f"<p>{apply_inline_styles(stripped)}</p>")

    # Final cleanup
    close_list()
    close_table()
    close_blockquote()
    close_callout()

    return "\n".join(html_lines)

def apply_inline_styles(text: str) -> str:
    """Replace Markdown inline tags (bold, italic, code, links) with HTML tags."""
    # 1. Bold: **text**
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # 2. Italic: *text*
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    # 3. Inline code: `code`
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    # 4. Markdown links: [text](#anchor)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text

class HTMLReportBuilder:
    def __init__(self, data_md: str, title: str):
        self.data_md = data_md
        self.title = title

    def build_html(self) -> str:
        """Converts Compiled Markdown text into styled HTML document."""
        body_content = parse_markdown_to_html(self.data_md)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code&display=swap" rel="stylesheet">
    <style>
        {HTML_STYLE}
    </style>
</head>
<body>
    <div class="container">
        {body_content}
        <div class="footer">
            Praxis Program Book &copy; {datetime.now(timezone.utc).year}. Compiled Headless.
        </div>
    </div>
</body>
</html>
"""
        return html
