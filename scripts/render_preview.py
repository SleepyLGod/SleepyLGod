#!/usr/bin/env python3
"""Build a standalone animated README preview with Pandoc and local images."""

import argparse
import base64
import mimetypes
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PROFILE_CACHE_URL = "https://raw.githubusercontent.com/SleepyLGod/SleepyLGod/profile-assets/assets/profile/"
BASE_CSS = """
.markdown-body { font: 16px/1.6 -apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;
  color: #1f2328; background: #fff; overflow-wrap: break-word; }
.markdown-body a { color: #0969da; text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }
.markdown-body img { max-width: 100%; height: auto; vertical-align: middle; }
.markdown-body h2 { font-size: 24px; line-height: 1.35; margin: 28px 0 18px;
  padding-bottom: 8px; border-bottom: 1px solid #d1d9e0; }
.markdown-body p { margin: 16px 0; }
.markdown-body li { margin: 7px 0; }
.markdown-body ul { padding-left: 28px; }
.markdown-body summary { cursor: pointer; }
.markdown-body hr { height: 2px; border: 0; background: #d1d9e0; margin: 24px 0; }
@media (prefers-color-scheme: dark) {
  .markdown-body { color: #e6edf3; background: #0d1117; }
  .markdown-body a { color: #58a6ff; }
  .markdown-body h2 { border-color: #30363d; }
  .markdown-body hr { background: #30363d; }
}
"""
LAYOUT_CSS = """
body { margin: 0; background: #f6f8fa; padding: 28px 16px; }
.preview-label { max-width: 880px; margin: 0 auto 12px; color: #656d76;
  font: 12px/1.6 system-ui,sans-serif; }
.markdown-body { max-width: 880px; box-sizing: border-box; margin: auto; padding: 36px 40px;
  border: 1px solid #d1d9e0; border-radius: 10px; }
@media (prefers-color-scheme: dark) {
  body { background: #010409; } .markdown-body { border-color: #30363d; }
  .preview-label { color: #9198a1; }
}
@media (max-width: 600px) {
  body { padding: 16px 8px; } .markdown-body { padding: 22px 16px; }
}
"""


def embed(match):
    attribute, relative = match.groups()
    if relative.startswith(PROFILE_CACHE_URL):
        # Use the reviewed local snapshot when building an offline preview.
        relative = "./assets/profile/" + relative.removeprefix(PROFILE_CACHE_URL)
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Preview images must stay inside the repository")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f'{attribute}="data:{mime};base64,{encoded}"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/sleepylgod-profile.html"))
    parser.add_argument("--css", type=Path, help="Optional github-markdown-css stylesheet")
    args = parser.parse_args()
    body = subprocess.check_output([
        "pandoc", "--from=gfm", "--to=html5", str(ROOT / "README.md")], text=True)
    # Archived blocks remain in README.md but must not load images in the preview.
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    image_paths = r'\./[^\"]+|' + re.escape(PROFILE_CACHE_URL) + r'code-atlas(?:-mobile)?-(?:dark|light)\.svg'
    body = re.sub(r'\b(src|srcset)="(' + image_paths + r')"', embed, body)
    if re.search(r'\b(?:src|srcset)="https?://', body):
        raise ValueError("README still embeds an external image")
    css = args.css.read_text() if args.css else BASE_CSS
    page = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>SleepyLGod · README preview</title><style>' + css + LAYOUT_CSS +
            '</style></head><body><div class="preview-label">README preview · '
            'All images are included in this file</div><article class="markdown-body">' +
            body + '</article></body></html>')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    print(f"Standalone preview saved: {args.output}")


if __name__ == "__main__":
    main()
