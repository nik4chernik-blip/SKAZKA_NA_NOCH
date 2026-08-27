#!/usr/bin/env python3
"""Build a static GitHub Pages mirror from verified story manifests.

The builder is deterministic: it copies only local, already verified manifests
and media files; it never calls an LLM or a remote publisher.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path


def slug(value: str) -> str:
    out = []
    for ch in value.casefold():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "story"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render_article(manifest: dict, media_names: dict[str, str]) -> str:
    blocks: list[str] = []
    for block in manifest.get("blocks", []):
        kind = block.get("type")
        if kind == "image":
            local = block.get("local_path")
            name = media_names.get(str(local), "")
            if not name:
                raise RuntimeError(f"missing local image mapping: {local}")
            caption = str(block.get("caption") or "")
            block_html = f'<figure><img src="media/{esc(name)}" loading="lazy" alt="">'
            if caption:
                block_html += f"<figcaption>{esc(caption)}</figcaption>"
            blocks.append(block_html + "</figure>")
        else:
            rendered = str(block.get("html") or "")
            if rendered:
                blocks.append(rendered)
    title = esc(str(manifest.get("title") or "Без названия"))
    author = str(manifest.get("author") or "").strip()
    author_html = f'<p class="author"><em>{esc(author)}</em></p>' if author else ""
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Сказка на ночь</title><link rel="stylesheet" href="../style.css"></head>
<body><main class="story"><h1>{title}</h1>{author_html}
{''.join(blocks)}
<footer><a href="https://t.me/SKAZKA_NA_N0CH">Сказка на ночь</a></footer></main></body></html>'''


def build(source_dir: Path, output: Path, base_url: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    (output / "articles").mkdir(exist_ok=True)
    (output / "media").mkdir(exist_ok=True)
    rows = []
    for manifest_path in sorted(source_dir.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        title = str(manifest.get("title") or "").strip()
        content_hash = str(manifest.get("content_hash") or "")
        if not title or not content_hash:
            continue
        article_slug = slug(title) + "-" + content_hash[:10]
        media_names = {}
        for raw in manifest.get("image_paths") or []:
            src = Path(raw)
            if not src.is_file():
                raise RuntimeError(f"missing media: {src}")
            name = f"{content_hash[:10]}-{src.name}"
            shutil.copy2(src, output / "media" / name)
            media_names[str(src)] = name
        (output / "articles" / f"{article_slug}.html").write_text(
            render_article(manifest, media_names), encoding="utf-8"
        )
        url = base_url.rstrip("/") + "/articles/" + article_slug + ".html"
        rows.append({"title": title, "source_url": manifest.get("source_url"), "content_hash": content_hash, "url": url})
    cards = "\n".join(f'<li><a href="articles/{esc(slug(r["title"]) + "-" + r["content_hash"][:10])}.html">{esc(r["title"])}</a></li>' for r in rows)
    (output / "index.html").write_text(f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Сказка на ночь</title><link rel="stylesheet" href="style.css"></head><body><main class="story"><h1>Сказка на ночь</h1><p>Архив сказок.</p><ul>{cards}</ul></main></body></html>''', encoding="utf-8")
    (output / "articles.json").write_text(json.dumps({"articles": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"articles": len(rows), "base_url": base_url}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("site"))
    ap.add_argument("--base-url", required=True)
    args = ap.parse_args()
    print(json.dumps(build(args.source, args.output, args.base_url), ensure_ascii=False))
