import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "notepad.html"
USAGE = ROOT / "USAGE.md"
VENDOR = ROOT / "vendor"

USAGE_BLOCK = re.compile(
    r"/\* __WEB_NOTEPAD_USAGE_START__ \*/[\s\S]*?/\* __WEB_NOTEPAD_USAGE_END__ \*/"
)
SOURCE_BLOCK = re.compile(
    r"/\* __WEB_NOTEPAD_CLONE_SOURCE_START__ \*/[\s\S]*?/\* __WEB_NOTEPAD_CLONE_SOURCE_END__ \*/"
)
SOURCE_PLACEHOLDER = """/* __WEB_NOTEPAD_CLONE_SOURCE_START__ */
window.__WEB_NOTEPAD_CLONE_SOURCE__ = null;
/* __WEB_NOTEPAD_CLONE_SOURCE_END__ */"""

FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=Nanum+Gothic+Coding:wght@400;700&display=swap" rel="stylesheet">
"""
MARKED_TAG = '<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>'
PURIFY_TAG = '<script src="https://cdn.jsdelivr.net/npm/dompurify@3.2.6/dist/purify.min.js"></script>'


def script_json(value: str) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("/", "\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def usage_block(usage: str) -> str:
    return (
        "/* __WEB_NOTEPAD_USAGE_START__ */\n"
        f"const EMBEDDED_USAGE = {script_json(usage)};\n"
        "/* __WEB_NOTEPAD_USAGE_END__ */"
    )


def source_block(source: str) -> str:
    return (
        "/* __WEB_NOTEPAD_CLONE_SOURCE_START__ */\n"
        f"window.__WEB_NOTEPAD_CLONE_SOURCE__ = {script_json(source)};\n"
        "/* __WEB_NOTEPAD_CLONE_SOURCE_END__ */"
    )


def inline_script(name: str, code: str) -> str:
    return f"<!-- {name}: upstream distribution notice and license header preserved below. -->\n<script>\n{code.rstrip()}\n</script>"


def clone_base(canonical: str) -> str:
    marked = (VENDOR / "marked-12.0.2.min.js").read_text(encoding="utf-8")
    purify = (VENDOR / "dompurify-3.2.6.min.js").read_text(encoding="utf-8")
    clone = canonical.replace(FONT_LINKS, "")
    clone = clone.replace(
        '--sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", system-ui, sans-serif;',
        '--sans: "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", system-ui, sans-serif;',
    )
    clone = clone.replace(
        '--mono: "Nanum Gothic Coding", "D2Coding", Consolas, "SF Mono", Menlo, monospace;',
        '--mono: "D2Coding", Consolas, "SF Mono", Menlo, monospace;',
    )
    clone = clone.replace(MARKED_TAG, inline_script("marked 12.0.2 — MIT License", marked))
    clone = clone.replace(
        PURIFY_TAG,
        inline_script("DOMPurify 3.2.6 — Apache-2.0 OR MPL-2.0", purify),
    )
    if any(token in clone for token in ("fonts.googleapis.com", "fonts.gstatic.com", MARKED_TAG, PURIFY_TAG)):
        raise RuntimeError("clone source still contains an external runtime dependency")
    if "marked v12.0.2" not in clone or "@license DOMPurify 3.2.6" not in clone:
        raise RuntimeError("vendored library notices are missing")
    return clone


def build() -> str:
    current = APP.read_text(encoding="utf-8").replace("\r\n", "\n")
    usage = USAGE.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
    canonical, count = SOURCE_BLOCK.subn(SOURCE_PLACEHOLDER, current, count=1)
    if count != 1:
        raise RuntimeError("clone source marker is missing or duplicated")
    canonical, count = USAGE_BLOCK.subn(lambda _: usage_block(usage), canonical, count=1)
    if count != 1:
        raise RuntimeError("usage marker is missing or duplicated")
    base = clone_base(canonical)
    built, count = SOURCE_BLOCK.subn(lambda _: source_block(base), canonical, count=1)
    if count != 1:
        raise RuntimeError("could not embed clone source")
    APP.write_text(built, encoding="utf-8", newline="\n")
    print(f"배포용 HTML 생성: {APP} ({len(built.encode('utf-8')):,} bytes)")
    print(f"자체 포함 복제 템플릿: {len(base.encode('utf-8')):,} bytes")
    return built


if __name__ == "__main__":
    build()
