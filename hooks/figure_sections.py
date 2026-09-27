"""Lay out "heading + text + image" sections as two columns.

Pages opt in with `figure_sections: true` in their front matter. In each
`##` section that contains exactly one image-only paragraph, the heading and
text go in one column and the image in the other, vertically centered. The
Markdown order decides the side: image after the text sits on the right,
image right after the heading sits on the left. The Markdown itself stays
plain, so it renders cleanly anywhere.
"""

import re

SECTION_SPLIT = re.compile(r"(?=<h2[\s>])")
HEADING = re.compile(r"^<h2[\s>].*?</h2>", re.S)
IMAGE_PARAGRAPH = re.compile(r"<p>\s*<img[^>]*>\s*</p>")
FOOTNOTES = '<div class="footnote">'


def _layout(section):
    images = IMAGE_PARAGRAPH.findall(section)
    if not section.startswith("<h2") or len(images) != 1:
        return section
    image = images[0]
    before, after = section.split(image)
    heading = HEADING.match(before).group(0)
    image_left = not before[len(heading):].strip()
    columns = [f"<div>{before + after}</div>", image]
    if image_left:
        columns.reverse()
    return f'<div class="figure-text">{"".join(columns)}</div>'


def on_page_content(html, page, config, files):
    if not page.meta.get("figure_sections"):
        return html
    body, sep, footnotes = html.partition(FOOTNOTES)
    body = "".join(_layout(section) for section in SECTION_SPLIT.split(body))
    return body + sep + footnotes
