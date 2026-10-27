"""配布HTML/CSS専用の静的ガード。汎用サニタイザーではない。"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from .presets import PRESET_FILENAMES


_FORBIDDEN_ELEMENTS = {"script", "canvas", "svg", "iframe", "object", "embed"}
_RESOURCE_ATTRIBUTES = {
    "img": {"src", "srcset"},
    "source": {"src", "srcset"},
    "audio": {"src"},
    "video": {"src", "poster"},
    "iframe": {"src"},
    "embed": {"src"},
    "object": {"data"},
    "input": {"src", "formaction"},
    "button": {"formaction"},
    "form": {"action"},
    "base": {"href"},
}
_FETCHING_LINK_RELS = {
    "stylesheet", "icon", "preload", "prefetch", "modulepreload", "manifest",
    "preconnect", "dns-prefetch", "apple-touch-icon",
}
_URL_ATTRIBUTES = {
    "href", "src", "srcset", "action", "formaction", "poster", "data",
    "xlink:href", "ping",
}
_TEMPLATE_TOKEN = re.compile(
    r"\{\{[^{}]+\}\}|__[A-Z][A-Z0-9_]*__|@@[A-Z][A-Z0-9_]*@@"
    r"|<!--\s*(?:SAMPLES|POINTS|[A-Z]+_STEPS)\s*-->", re.IGNORECASE,
)
_CSS_URLS = re.compile(
    r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)|@import\s+(?:"([^"]*)"|'([^']*)')''',
    re.IGNORECASE,
)
_PAGES = (("index.html", 192), ("samples-96.html", 96), ("samples-384.html", 384), *((filename, 192) for filename in PRESET_FILENAMES))
_STYLES = ("style.css", "engine.css")


def _compact_url(value: str) -> str:
    # HTMLParser has already decoded character references in HTML attributes.
    return re.sub(r"[\x00-\x20\x7f]", "", value)


def _external_resource(value: str) -> bool:
    url = _compact_url(value)
    if url.lower().startswith("data:"):
        return False
    return url.startswith("//") or bool(re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I))


def _resource_candidates(value: str, attribute: str) -> list[str]:
    if attribute in {"srcset", "ping"}:
        # This project does not generate data-URL srcsets. Inspect every remote
        # candidate rather than only the first local image in the attribute.
        return [part for part in re.split(r"[\s,]+", value) if part]
    return [value]


def _inspect_css(css: str, errors: list[str]) -> None:
    source = re.sub(r"/\*[\s\S]*?\*/", "", css)
    for match in _CSS_URLS.finditer(source):
        value = next((part for part in match.groups() if part is not None), "")
        if _external_resource(value):
            errors.append(f"外部CSSリソース: {value.strip()}")
        compact = _compact_url(value).lower()
        if compact.startswith("javascript:"):
            errors.append("CSS内のjavascript: URL")
        if compact.startswith("data:image/svg+xml"):
            errors.append("CSS内のSVGデータURL")


def _unique(errors: list[str]) -> list[str]:
    return list(dict.fromkeys(errors))


def audit_css(css: str) -> dict:
    """CSSの外部リソース・禁止URLを検査し、ok/errorsを返す。"""
    if not isinstance(css, str):
        raise TypeError("css must be a string")
    errors: list[str] = []
    _inspect_css(css, errors)
    return {"ok": not errors, "errors": _unique(errors)}


class _HTMLAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.sample_count = 0
        self._style_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = [(name, value or "") for name, value in attrs]

        def first(name: str) -> str:
            return next((value for key, value in values if key == name), "")

        if tag in _FORBIDDEN_ELEMENTS:
            # Reject embedded documents regardless of local, remote, data: or
            # missing URLs. They are not part of this HTML/CSS application.
            self.errors.append(f"禁止された要素: <{tag}>")
        if tag == "i" and "sample" in first("class").split():
            self.sample_count += 1
        rels = set(first("rel").lower().split())

        for name, value in values:
            if name.startswith("on"):
                self.errors.append(f"イベントハンドラ属性: <{tag} {name}>")
            compact = _compact_url(value).lower()
            if name in _URL_ATTRIBUTES and compact.startswith("javascript:"):
                self.errors.append(f"javascript: URL: <{tag} {name}>")
            if name in _URL_ATTRIBUTES and compact.startswith("data:image/svg+xml"):
                self.errors.append(f"SVGデータURL: <{tag} {name}>")
            is_resource = (
                name in _RESOURCE_ATTRIBUTES.get(tag, set())
                or (tag == "link" and name == "href" and bool(rels & _FETCHING_LINK_RELS))
                or (tag == "a" and name == "ping")
            )
            if is_resource and any(
                _external_resource(candidate) for candidate in _resource_candidates(value, name)
            ):
                self.errors.append(f"外部実行時リソース: <{tag} {name}>")
            if name == "style":
                _inspect_css(value, self.errors)
            if tag == "iframe" and name == "srcdoc":
                self.errors.append("配布物ではiframe srcdocを使用しない")
        if tag == "meta" and first("http-equiv").lower() == "refresh":
            self.errors.append("配布物ではmeta refreshを使用しない")
        if tag == "style":
            self._style_parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._style_parts is not None:
            self._style_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self.finish_style()

    def finish_style(self) -> None:
        if self._style_parts is not None:
            _inspect_css("".join(self._style_parts), self.errors)
            self._style_parts = None


def audit_html(html: str, samples: int | None = None) -> dict:
    """HTMLを検査し、ok/errors/sample_countを返す。HTMLを書き換えない。"""
    if not isinstance(html, str):
        raise TypeError("html must be a string")
    if samples is not None and (type(samples) is not int or samples < 1):
        raise TypeError("samples must be a positive integer")
    parser = _HTMLAuditParser()
    if _TEMPLATE_TOKEN.search(html):
        parser.errors.append("未解決のテンプレートトークン")
    parser.feed(html)
    parser.close()
    parser.finish_style()
    if samples is not None and parser.sample_count != samples:
        parser.errors.append(
            f"サンプル数が不一致: expected {samples}, got {parser.sample_count}"
        )
    return {
        "ok": not parser.errors,
        "errors": _unique(parser.errors),
        "sample_count": parser.sample_count,
    }


def audit_directory(directory: Path) -> dict:
    """配布HTML / CSSの監査結果を集約する。欠落もerrorsとして返す。"""
    directory = Path(directory)
    files: list[dict] = []
    for filename, samples in (*_PAGES, *((filename, None) for filename in _STYLES)):
        try:
            source = (directory / filename).read_text(encoding="utf-8")
            result = audit_html(source, samples) if samples is not None else audit_css(source)
        except (OSError, UnicodeError) as error:
            result = {"ok": False, "errors": [f"ファイルを読み取れない: {error}"]}
        files.append({"path": filename, **result})
    errors = [f"{item['path']}: {error}" for item in files for error in item["errors"]]
    return {"ok": not errors, "errors": errors, "files": files}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="配布HTML/CSSの静的ガード")
    parser.add_argument(
        "directory", nargs="?", type=Path,
        default=Path(__file__).resolve().parents[1] / "build",
    )
    args = parser.parse_args(argv)
    result = audit_directory(args.directory)
    for item in result["files"]:
        if item["ok"]:
            detail = (
                f"{item['sample_count']} samples, HTML/CSS静的ガード"
                if "sample_count" in item else "CSS外部リソース静的ガード"
            )
            print(f"PASS {item['path']}: {detail}")
        else:
            print(f"FAIL {item['path']}", file=sys.stderr)
            for error in item["errors"]:
                print(f"  - {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
