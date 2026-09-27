// Transparent videos (illustrations/globe_*.py): HEVC with alpha for Safari,
// VP9 with alpha elsewhere, since neither format keeps its transparency in
// every browser.
//
// A video names its file with data-name (hooks/alpha_videos.py), or has
// data-random to show one of the banner videos, picked once per page load
// so that every banner of the page shows the same one.
(function () {
    const BANNER = ["globe_seismes", "globe_maillage", "globe_satellites", "globe_magnetique"];
    const banner = BANNER[Math.floor(Math.random() * BANNER.length)];
    const safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    document.querySelectorAll("video.alpha-video").forEach(function (video) {
        const base = video.dataset.base.replace(/\/?$/, "/");
        const name = "random" in video.dataset ? banner : video.dataset.name;
        video.poster = base + name + ".png";
        video.src = base + name + (safari ? ".mov" : ".webm");
        video.play().catch(function () {});
    });
})();
