import re
import html as html_mod


def markdown_to_odysseus_html(markdown_content: str, topic: str = "Research") -> str:
    body_lines: list[str] = []
    in_table = False
    table_rows: list[str] = []
    section_count = 0

    for line in markdown_content.split("\n"):
        stripped = line.strip()

        if not stripped:
            if in_table:
                body_lines.append(_render_table(table_rows))
                in_table = False
                table_rows = []
            body_lines.append("<div class='spacer'></div>")
            continue

        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            is_sep = all(set(c.strip()) <= set("-: ") for c in cells)
            if is_sep:
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue

        if in_table:
            body_lines.append(_render_table(table_rows))
            in_table = False
            table_rows = []

        if stripped.startswith("# ") and not stripped.startswith("## "):
            body_lines.append(f"<h1>{_md(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            section_count += 1
            if section_count > 1:
                body_lines.append("<div class='section-divider'></div>")
            body_lines.append(f"<h2>{_md(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            body_lines.append(f"<h3>{_md(stripped[4:])}</h3>")
        elif stripped.startswith("#### "):
            body_lines.append(f"<h4>{_md(stripped[5:])}</h4>")
        elif stripped.startswith("---"):
            body_lines.append("<hr>")
        elif stripped.startswith("> "):
            body_lines.append(f"<blockquote>{_md(stripped[2:])}</blockquote>")
        elif stripped.startswith("* ") or stripped.startswith("- "):
            body_lines.append(f"<li>{_md(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            inner = re.sub(r"^\d+\.\s*", "", stripped)
            body_lines.append(f"<li class='numbered'>{_md(inner)}</li>")
        elif stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            body_lines.append(f"<p class='italic'>{_md(stripped.strip('*'))}</p>")
        else:
            body_lines.append(f"<p>{_md(stripped)}</p>")

    if in_table:
        body_lines.append(_render_table(table_rows))

    body_html = "\n".join(body_lines)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_mod.escape(topic)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0a0a12;
  color: #c8ccd8;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
}}

.container {{
  max-width: 780px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}}

/* Report typography hierarchy */
h1 {{
  font-size: 2rem;
  font-weight: 600;
  color: #a5b4fc;
  border-bottom: 2px solid #a5b4fc;
  padding-bottom: 0.5rem;
  margin: 2.5rem 0 1rem;
  line-height: 1.2;
}}

h1 + .subtitle {{
  color: #6b7094;
  font-size: 0.8rem;
  margin-bottom: 28px;
}}

h2 {{
  font-size: 1.5rem;
  font-weight: 600;
  color: #eef0f6;
  border-left: 3px solid #a5b4fc;
  padding-left: 0.75rem;
  margin: 2rem 0 0.75rem;
  line-height: 1.3;
}}

h3 {{
  font-size: 1.2rem;
  font-weight: 500;
  color: #c4b5fd;
  margin: 1.5rem 0 0.5rem;
}}

h4 {{
  font-size: 1rem;
  font-weight: 500;
  color: #8890b0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 1.25rem 0 0.4rem;
}}

p {{
  font-size: 0.95rem;
  line-height: 1.75;
  color: #b0b6cc;
  margin-bottom: 0.85rem;
}}

p.italic {{
  font-style: italic;
  color: #8890b0;
}}

blockquote {{
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.06));
  border-left: 3px solid #818cf8;
  border-radius: 0 10px 10px 0;
  padding: 18px 22px;
  margin: 18px 0;
  font-style: italic;
  color: #a5b4fc;
  font-size: 0.88rem;
  line-height: 1.7;
}}

hr {{
  border: none;
  border-top: 1px solid rgba(165, 180, 252, 0.08);
  margin: 28px 0;
}}

.section-divider {{
  height: 1px;
  background: rgba(165, 180, 252, 0.15);
  margin: 2rem 0;
  opacity: 0.4;
}}

ul, ol {{
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}}

li {{
  font-size: 0.95rem;
  line-height: 1.7;
  color: #b0b6cc;
  margin-bottom: 0.35rem;
}}

li.numbered {{
  margin-bottom: 18px;
}}

strong {{
  color: #eef0f6;
  font-weight: 600;
}}

code {{
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
  background: rgba(129, 140, 248, 0.1);
  color: #c4b5fd;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}}

pre {{
  background: rgba(129, 140, 248, 0.08);
  border: 1px solid rgba(165, 180, 252, 0.1);
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}}

pre code {{
  background: none;
  padding: 0;
  font-size: 0.875rem;
  line-height: 1.6;
}}

a {{
  color: #818cf8;
  text-decoration: none;
  transition: color 0.15s;
}}

a:hover {{
  color: #a5b4fc;
  text-decoration: underline;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1.25rem 0;
  font-size: 0.9rem;
}}

thead th {{
  background: rgba(99, 102, 241, 0.12);
  color: #a5b4fc;
  font-weight: 500;
  text-align: left;
  padding: 0.6rem 0.85rem;
  border: 1px solid rgba(165, 180, 252, 0.1);
  white-space: nowrap;
}}

tbody td {{
  padding: 0.55rem 0.85rem;
  border: 1px solid rgba(165, 180, 252, 0.05);
  color: #b0b6cc;
  vertical-align: top;
  line-height: 1.5;
}}

tbody tr:nth-child(even) td {{
  background: rgba(99, 102, 241, 0.03);
}}

tbody tr:last-child td {{
  border-bottom: none;
}}

tbody tr:hover {{
  background: rgba(99, 102, 241, 0.04);
}}

.spacer {{
  height: 8px;
}}

.prose li strong {{
  color: #eef0f6;
}}

/* Source badges at bottom */
.source-item {{
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
  padding: 0.4rem 0;
  border-bottom: 1px solid rgba(165, 180, 252, 0.05);
}}

.source-number {{
  color: #a5b4fc;
  font-weight: 500;
  font-size: 0.85rem;
  min-width: 2rem;
}}

.source-url {{
  color: #8890b0;
  font-size: 0.85rem;
  word-break: break-all;
}}
</style>
</head>
<body>
<div class="container">
{body_html}
</div>
</body>
</html>"""


def _md(text: str) -> str:
    escaped = html_mod.escape(text)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
    escaped = re.sub(r'`(.+?)`', r'<code>\1</code>', escaped)
    escaped = re.sub(
        r'\[(.+?)\]\((.+?)\)',
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        escaped,
    )
    return escaped


def _render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    out = ["<table><thead><tr>"]
    for cell in header:
        out.append(f"<th>{_md(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{_md(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)
