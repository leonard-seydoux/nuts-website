"""Turn the poster image of a transparent video into the video itself.

In Markdown, a transparent video from illustrations/ is referenced by its
poster image, so that the page stays plain Markdown and shows a still
anywhere else:

    ![Globe et satellites](videos/globe_satellites.png)

When videos/globe_satellites.webm exists next to that image, the image is
replaced at build time by a looping, muted video. javascripts/alpha_videos.js
then picks the file each browser can play with transparency.
"""

import re
from pathlib import Path

IMAGE = re.compile(r'<img\b[^>]*\bsrc="(?P<base>[^"]*videos/)(?P<name>[\w-]+)\.png"[^>]*>')
ALT = re.compile(r'\balt="([^"]*)"')


def on_page_content(html, page, config, files):
    videos = Path(config["docs_dir"]) / "videos"

    def replace(match):
        if not (videos / f"{match['name']}.webm").exists():
            return match.group(0)
        alt = ALT.search(match.group(0))
        label = f' aria-label="{alt.group(1)}"' if alt else ""
        return (f'<video class="alpha-video" autoplay muted loop playsinline{label}'
                f' poster="{match["base"]}{match["name"]}.png"'
                f' data-base="{match["base"]}" data-name="{match["name"]}"></video>')

    return IMAGE.sub(replace, html)
