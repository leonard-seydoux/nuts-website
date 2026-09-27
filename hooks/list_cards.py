"""Turn a page's top-level bullet lists into a grid of cards, or a timeline.

Pages opt in through their front matter:

    list_cards: true              # every top-level list on the page
    list_cards: [objectifs]       # only lists under these `##` sections (ids)
    numbered_cards: true          # number the cards (01, 02, ...)
    timeline: true                # top-level lists as a vertical timeline
    timeline: [historique]        # (or only under these sections, as above)

Each top-level `<ul>` is wrapped in Material's `grid cards` container, so the
Markdown stays a plain list.
"""

import re

LIST_TAG = re.compile(r"<(/?)ul\b[^>]*>")
SECTION_SPLIT = re.compile(r"(?=<h2[\s>])")
SECTION_ID = re.compile(r'^<h2[^>]*\bid="([^"]+)"')


def _wrap_top_level_lists(html, classes):
    out, depth, last = [], 0, 0
    for tag in LIST_TAG.finditer(html):
        closing = tag.group(1) == "/"
        if not closing:
            if depth == 0:
                out.append(html[last:tag.start()])
                out.append(f'<div class="{classes}">')
                last = tag.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                out.append(html[last:tag.end()])
                out.append("</div>")
                last = tag.end()
    out.append(html[last:])
    return "".join(out)


def on_page_content(html, page, config, files):
    if page.meta.get("timeline"):
        sections, classes = page.meta["timeline"], "timeline"
    else:
        sections = page.meta.get("list_cards")
        classes = "grid cards" + (" numbered" if page.meta.get("numbered_cards") else "")
    if not sections:
        return html
    if sections is True:
        return _wrap_top_level_lists(html, classes)

    def layout(section):
        match = SECTION_ID.match(section)
        if match and match.group(1) in sections:
            return _wrap_top_level_lists(section, classes)
        return section

    return "".join(layout(section) for section in SECTION_SPLIT.split(html))
