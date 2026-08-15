"""Generate stable academic PDFs from the repository Markdown without Node."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCUMENTS = (
    ("problem.md", "problem.pdf", "MPVRP-CC — Problem definition"),
    ("instance_format.md", "instance_format.pdf", "MPVRP-CC — Instance format"),
    ("solution_format.md", "solution_format.pdf", "MPVRP-CC — Solution format"),
)
KATEX_VERSION = "0.16.22"


def inline_markup(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
    value = re.sub(r"\[([^]]+)]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    return value


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code: list[str] = []
    index = 0

    def close_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markup(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            close_paragraph(); close_list()
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
                code.clear()
            in_code = not in_code
            index += 1
            continue
        if in_code:
            code.append(line)
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[index + 1]):
            close_paragraph(); close_list()
            headers = [cell.strip() for cell in stripped.strip("|").split("|")]
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            output.append("<table><thead><tr>" + "".join(f"<th>{inline_markup(cell)}</th>" for cell in headers) + "</tr></thead><tbody>")
            output.extend("<tr>" + "".join(f"<td>{inline_markup(cell)}</td>" for cell in row) + "</tr>" for row in rows)
            output.append("</tbody></table>")
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            close_paragraph(); close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
        elif stripped.startswith(">"):
            close_paragraph(); close_list()
            output.append(f"<blockquote>{inline_markup(stripped.lstrip('> '))}</blockquote>")
        elif match := re.match(r"^[-*]\s+(.+)$", stripped):
            close_paragraph()
            if list_type != "ul": close_list(); output.append("<ul>"); list_type = "ul"
            output.append(f"<li>{inline_markup(match.group(1))}</li>")
        elif match := re.match(r"^\d+\.\s+(.+)$", stripped):
            close_paragraph()
            if list_type != "ol": close_list(); output.append("<ol>"); list_type = "ol"
            output.append(f"<li>{inline_markup(match.group(1))}</li>")
        elif stripped in {"", "---"}:
            close_paragraph(); close_list()
        else:
            close_list(); paragraph.append(stripped)
        index += 1
    close_paragraph(); close_list()
    return "\n".join(output)


STYLE = """
@page { size: A4; margin: 18mm 17mm 19mm; }
* { box-sizing: border-box; } body { margin: 0; color: #1f2937; font: 10.5pt/1.55 Arial, sans-serif; }
h1,h2,h3 { color: #111827; line-height: 1.2; break-after: avoid; } h1 { margin: 0 0 8mm; padding-bottom: 4mm; border-bottom: 2px solid #047857; font-size: 23pt; }
h2 { margin: 7mm 0 3mm; font-size: 16pt; } h3 { margin: 5mm 0 2mm; color: #065f46; font-size: 12pt; }
p,ul,ol { margin: 0 0 3.5mm; } ul,ol { padding-left: 6mm; } code { background: #ecfdf5; color: #065f46; padding: 1px 3px; font: 9pt Consolas, monospace; }
pre { break-inside: avoid; border-left: 3px solid #059669; background: #f8fafc; padding: 4mm; font-size: 8.5pt; white-space: pre-wrap; } pre code { background: transparent; color: #111827; padding: 0; }
blockquote { margin: 4mm 0; border-left: 3px solid #059669; background: #ecfdf5; padding: 3mm 4mm; } table { width: 100%; margin: 4mm 0; border-collapse: collapse; break-inside: avoid; font-size: 9pt; }
th,td { border: 1px solid #cbd5e1; padding: 2mm; text-align: left; vertical-align: top; } th { background: #f1f5f9; } a { color: #047857; }
"""


def main() -> None:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise SystemExit("Google Chrome or Chromium is required to generate PDFs.")
    with tempfile.TemporaryDirectory(prefix="mpvrp-docs-") as temp:
        temporary = Path(temp)
        profile = temporary / "chrome-profile"
        for source_name, output_name, title in DOCUMENTS:
            body = markdown_to_html((DOCS / source_name).read_text(encoding="utf-8"))
            source = temporary / f"{source_name}.html"
            source.write_text(
                f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
                f'<title>{html.escape(title)}</title>'
                f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css">'
                f'<style>{STYLE}</style></head><body>{body}'
                f'<script src="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js"></script>'
                f'<script src="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js"></script>'
                '<script>renderMathInElement(document.body,{delimiters:['
                '{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}'
                '],throwOnError:false});</script></body></html>',
                encoding="utf-8",
            )
            subprocess.run([
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=5000",
                f"--user-data-dir={profile}", "--no-pdf-header-footer",
                f"--print-to-pdf={DOCS / output_name}", source.as_uri(),
            ], check=True)
            print(f"Generated docs/{output_name}")


if __name__ == "__main__":
    main()
