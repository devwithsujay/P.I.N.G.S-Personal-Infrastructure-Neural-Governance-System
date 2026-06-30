import re
import html as html_mod


def markdown_to_odysseus_html(markdown_content: str, topic: str = "Research") -> str:
    body_lines: list[str] = []
    in_table = False
    table_rows: list[str] = []

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

        if stripped.startswith("# "):
            body_lines.append(f"<h1>{_md(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            body_lines.append(f"<h2>{_md(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            body_lines.append(f"<h3>{_md(stripped[4:])}</h3>")
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

h1 {{
  font-size: 1.75rem;
  font-weight: 700;
  color: #eef0f6;
  margin-bottom: 8px;
  line-height: 1.3;
  letter-spacing: -0.02em;
}}

h1 + .subtitle {{
  color: #6b7094;
  font-size: 0.8rem;
  margin-bottom: 28px;
}}

h2 {{
  font-size: 1.15rem;
  font-weight: 600;
  color: #a5b4fc;
  margin: 36px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(165, 180, 252, 0.12);
}}

h3 {{
  font-size: 1rem;
  font-weight: 600;
  color: #c4b5fd;
  margin: 24px 0 10px;
}}

p {{
  font-size: 0.9rem;
  color: #b0b6cc;
  margin-bottom: 14px;
  line-height: 1.8;
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

ul, ol {{
  padding-left: 22px;
  margin-bottom: 14px;
}}

li {{
  font-size: 0.88rem;
  color: #b0b6cc;
  margin-bottom: 10px;
  line-height: 1.7;
}}

li.numbered {{
  margin-bottom: 18px;
}}

strong {{
  color: #eef0f6;
  font-weight: 600;
}}

code {{
  background: rgba(129, 140, 248, 0.1);
  color: #c4b5fd;
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 0.82rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
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
  margin: 18px 0;
  font-size: 0.82rem;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(165, 180, 252, 0.1);
}}

thead th {{
  background: rgba(99, 102, 241, 0.12);
  color: #c4b5fd;
  font-weight: 600;
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(165, 180, 252, 0.1);
  white-space: nowrap;
}}

tbody td {{
  padding: 11px 16px;
  border-bottom: 1px solid rgba(165, 180, 252, 0.05);
  color: #b0b6cc;
  vertical-align: top;
  line-height: 1.5;
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
