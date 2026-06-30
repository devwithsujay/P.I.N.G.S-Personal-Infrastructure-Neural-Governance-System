import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from core.agents.opencode_engine import run_opencode_task
from core.tools.file_tool import write_file

logger = logging.getLogger("pings.agents.report")

REPORT_SYSTEM_PROMPT = """You are a deep research report generation assistant. When generating reports:

1. Follow the EXACT template structure provided below — do not deviate.
2. NEVER include raw search strings, query artifacts, or "SearXNG results for:" lines.
3. Synthesize information across all sources into a single, cohesive narrative. Do NOT list sources one by one.
4. NEVER print raw URLs. Embed sources as markdown hyperlinks over descriptive titles.
5. Skip conversational introductions or conclusions. Output ONLY the finalized markdown report.
6. Do NOT use emojis or special unicode characters — use plain ASCII text only.
7. The report MUST contain these sections IN ORDER:
   - # Research Report: [Topic Title]
   - ## Executive Summary (2-3 sentence overview in a blockquote)
   - ## Core Capabilities & Technical Architecture (bullet points with key concepts)
   - ## Deep Comparison Matrix (markdown table)
   - ## Strategic Findings & Synthesis (numbered insights)
   - ## Verified Research Sources (hyperlinked source list)
"""


async def handle_report(message: str, persona: Optional[Dict[str, str]] = None) -> str:
    logger.info(f"Report processing: {message[:100]}")

    full_prompt = REPORT_SYSTEM_PROMPT
    if persona and persona.get("identity"):
        full_prompt = persona["identity"] + "\n\n" + REPORT_SYSTEM_PROMPT

    response = await run_opencode_task(
        task=(
            f"Generate a deep research report for: {message}. "
            "Follow the exact template: Executive Summary, Core Capabilities & Technical Architecture, "
            "Deep Comparison Matrix, Strategic Findings & Synthesis, Verified Research Sources. "
            "Return ONLY the finalized markdown report."
        ),
        system_context=full_prompt,
    )

    if response and not response.startswith("Agent error"):
        slug = re.sub(r'[^\w\s-]', '', message.lower().strip())
        slug = re.sub(r'[\s_]+', '-', slug)[:60].strip('-')
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{slug}-{timestamp}.md"
        result = await write_file(filename, response)
        if not result.startswith("Error"):
            response += f"\n\nReport saved to: {filename}"

    return response


async def generate_report_html(content: str, title: str = "Report") -> str:
    import html as html_mod

    def md_line_to_html(line: str) -> str:
        escaped = html_mod.escape(line)
        escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
        escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
        escaped = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:#818cf8;text-decoration:underline">\1</a>', escaped)
        escaped = re.sub(r'`(.+?)`', r'<code style="background:#1e1e2e;padding:2px 6px;border-radius:4px;font-size:0.9em">\1</code>', escaped)
        return escaped

    html_lines: list[str] = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append('<html><head><meta charset="utf-8">')
    html_lines.append(f"<title>{html_mod.escape(title)}</title>")
    html_lines.append("""<style>
body { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 40px 60px; line-height: 1.8; }
h1 { color: #e2e8f0; font-size: 1.8em; border-bottom: 2px solid #818cf8; padding-bottom: 12px; margin-top: 0; }
h2 { color: #93c5fd; font-size: 1.3em; margin-top: 32px; }
h3 { color: #a5b4fc; font-size: 1.1em; margin-top: 20px; }
blockquote { background: #161b22; border-left: 4px solid #818cf8; padding: 14px 20px; margin: 16px 0; border-radius: 0 8px 8px 0; font-style: italic; color: #9ca3af; }
hr { border: none; border-top: 1px solid #21262d; margin: 28px 0; }
a { color: #818cf8; text-decoration: none; } a:hover { text-decoration: underline; }
ul, ol { padding-left: 24px; } li { margin: 6px 0; }
table { border-collapse: collapse; width: 100%%; margin: 16px 0; }
th, td { border: 1px solid #21262d; padding: 10px 14px; text-align: left; }
th { background: #161b22; color: #93c5fd; font-weight: 600; }
td { background: #0d1117; }
code { background: #1e1e2e; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
</style></head><body>""")

    in_table = False
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            html_lines.append("<br>")
            continue

        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            is_separator = all(set(c.strip()) <= set("-: ") for c in cells)
            if is_separator:
                continue
            if not in_table:
                html_lines.append("<table>")
                in_table = True
                tag = "th"
            else:
                tag = "td"
            row = "".join(f"<{tag}>{md_line_to_html(c)}</{tag}>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
            continue

        if in_table:
            html_lines.append("</table>")
            in_table = False

        if stripped.startswith("# "):
            html_lines.append(f"<h1>{md_line_to_html(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{md_line_to_html(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{md_line_to_html(stripped[4:])}</h3>")
        elif stripped.startswith("---"):
            html_lines.append("<hr>")
        elif stripped.startswith("> "):
            html_lines.append(f"<blockquote>{md_line_to_html(stripped[2:])}</blockquote>")
        elif stripped.startswith("* ") or stripped.startswith("- "):
            html_lines.append(f"<li>{md_line_to_html(stripped[2:])}</li>")
        elif stripped[0:1].isdigit() and ". " in stripped[:5]:
            inner = stripped.split(". ", 1)[1] if ". " in stripped else stripped
            html_lines.append(f"<li>{md_line_to_html(inner)}</li>")
        else:
            html_lines.append(f"<p>{md_line_to_html(stripped)}</p>")

    if in_table:
        html_lines.append("</table>")

    html_lines.append("</body></html>")
    return "\n".join(html_lines)
