"""Hide both sidebars on every page.

The per-page table of contents and the navigation sidebar are hidden;
navigation happens through the header links and, for workshops, the cards
of the Workshops page.

Same as writing `hide: [toc, navigation]` in each page's front matter.
"""


def on_page_markdown(markdown, page, config, files):
    hide = page.meta.setdefault("hide", [])
    hide.extend(item for item in ("toc", "navigation") if item not in hide)
    return markdown
