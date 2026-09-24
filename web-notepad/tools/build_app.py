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

CLONE_ONLY_BLOCKS = (
    "ORIGINAL_CLONE_BUTTON_CSS",
    "ORIGINAL_CLONE_DIALOG_CSS",
    "ORIGINAL_CLONE_RESPONSIVE_CSS",
    "ORIGINAL_CLONE_BUTTON",
    "ORIGINAL_CLONE_DIALOG",
    "ORIGINAL_CLONE_PROMPT",
    "ORIGINAL_CLONE_RUNTIME",
    "ORIGINAL_CLONE_EVENTS",
    "ORIGINAL_ABOUT_CSS",
    "ORIGINAL_ABOUT_MENU",
    "ORIGINAL_ABOUT_DIALOG",
    "ORIGINAL_ABOUT_RUNTIME",
    "ORIGINAL_ABOUT_COMMAND",
)


def script_json(value: str) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
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


def replace_marked_block(source: str, name: str, replacement: str = "") -> str:
    marker = re.compile(
        rf"[ \t]*(?:/\*|<!--) __WEB_NOTEPAD_{re.escape(name)}_START__ (?:\*/|-->)[ \t]*\n?"
        rf"[\s\S]*?"
        rf"[ \t]*(?:/\*|<!--) __WEB_NOTEPAD_{re.escape(name)}_END__ (?:\*/|-->)[ \t]*\n?"
    )
    updated, count = marker.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError(f"marked block is missing or duplicated: {name}")
    return updated


def clone_usage(usage: str) -> str:
    clone, count = re.subn(
        r"\n## 나만의 앱 만들기\n[\s\S]*?(?=\n## 편집 도구\n)",
        "\n",
        usage,
        count=1,
    )
    if count != 1:
        raise RuntimeError("clone-only usage section is missing or duplicated")
    clone = clone.replace(
        "- Vercel에 배포된 웹 메모장은 브라우저 로컬 저장 방식이라 기기 간 동기화를 제공하지 않아요.",
        "- 메모장은 브라우저 로컬 저장 방식이라 기기 간 동기화를 제공하지 않아요.",
    )
    clone = clone.replace(
        "- 원본 Vercel 화면은 외부 글꼴과 CDN 라이브러리를 사용하지만, 앱 복제 자료는 시스템 글꼴과 내부에 포함된 라이브러리를 사용해요.",
        "- 이 앱은 시스템 글꼴과 내부에 포함된 라이브러리를 사용해 외부 글꼴이나 CDN을 요청하지 않아요.",
    )
    clone = re.sub(
        r"\n- Gemini에서 Canvas 앱 미리보기를 제공하는지는[^\n]*",
        "",
        clone,
        count=1,
    )
    clone = clone.replace("## 라이선스와 문의", "## 라이선스")
    clone = re.sub(r"\n\*\*JOON\*\*[^\n]*\n2026\. 9\. 22\.?,?", "", clone, count=1)
    clone = clone.rstrip()
    if "앱 복제" in clone or "Gemini 열기" in clone:
        raise RuntimeError("clone usage still describes the original clone feature")
    if "eduedujoon@gmail.com" in clone or "2026. 9. 22" in clone:
        raise RuntimeError("clone usage still contains private author details")
    return clone


def clone_base(canonical: str, usage: str) -> str:
    marked = (VENDOR / "marked-12.0.2.min.js").read_text(encoding="utf-8")
    purify = (VENDOR / "dompurify-3.2.6.min.js").read_text(encoding="utf-8")
    clone = canonical
    for name in CLONE_ONLY_BLOCKS:
        clone = replace_marked_block(clone, name)
    clone = replace_marked_block(
        clone,
        "ORIGINAL_MODAL_GUARD",
        "  if (!$('dlgLayer').hidden) return;\n",
    )
    clone, count = SOURCE_BLOCK.subn("", clone, count=1)
    if count != 1:
        raise RuntimeError("clone source placeholder is missing or duplicated")
    clone, count = USAGE_BLOCK.subn(lambda _: usage_block(clone_usage(usage)), clone, count=1)
    if count != 1:
        raise RuntimeError("could not embed the clone-specific usage guide")
    clone = clone.replace(
        "  메모장\n  JOON <eduedujoon@gmail.com>\n  2026-09-22\n\n  MIT License\n\n  Copyright (c) 2026 JOON <eduedujoon@gmail.com>",
        "  메모장\n  MIT License\n\n  Copyright (c) 2026 JOON",
    )
    clone = clone.replace(
        '<meta name="author" content="JOON <eduedujoon@gmail.com>">',
        '<meta name="author" content="JOON">',
    )
    clone = clone.replace(
        '<meta name="copyright" content="(c) 2026 JOON, MIT License">',
        '<meta name="copyright" content="Copyright (c) 2026 JOON">',
    )
    clone = clone.replace(FONT_LINKS, "")
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
    forbidden = (
        'id="webClone"',
        'id="cloneLayer"',
        ".web-clone",
        ".clone-dialog",
        "cloneGemini",
        "cloneCopy",
        "cloneDownload",
        "buildCloneKit",
        "getCloneKit",
        "openClone",
        "copyCloneKit",
        "downloadCloneKit",
        "__WEB_NOTEPAD_CLONE_SOURCE__",
        "CLONE_PROMPT",
        "https://gemini.google.com/app",
        "앱 복제",
        "eduedujoon@gmail.com",
        "2026-09-22",
        "2026. 9. 22",
        "SIG_MAIL",
    )
    leaked = [token for token in forbidden if token in clone]
    if leaked:
        raise RuntimeError(f"clone source still contains original-only data: {leaked}")
    if "Copyright (c) 2026 JOON" not in clone:
        raise RuntimeError("project copyright notice is missing from clone source")
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
    base = clone_base(canonical, usage)
    built, count = SOURCE_BLOCK.subn(lambda _: source_block(base), canonical, count=1)
    if count != 1:
        raise RuntimeError("could not embed clone source")
    APP.write_text(built, encoding="utf-8", newline="\n")
    print(f"배포용 HTML 생성: {APP} ({len(built.encode('utf-8')):,} bytes)")
    print(f"자체 포함 복제 템플릿: {len(base.encode('utf-8')):,} bytes")
    return built


if __name__ == "__main__":
    build()
