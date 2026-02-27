"""
Backward-compatible entrypoint kept for imports from the API layer.

The actual implementation is now split into:
1) build_bulletin_context()  -> dict
2) render_charts(context)    -> images (base64 strings)
3) render_html(context, ...) -> html string
"""

from bulletin.context import build_bulletin_context
from bulletin.render import render_charts, render_html


def generate_bulletin_html() -> str:
    context = build_bulletin_context()
    images = render_charts(context)
    return render_html(context, images)


if __name__ == "__main__":
    print(generate_bulletin_html()[:500])
