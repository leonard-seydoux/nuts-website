// Transparent videos (illustrations/globe_*.py): HEVC with alpha for Safari,
// VP9 with alpha elsewhere, since neither format keeps its transparency in
// every browser.
//
// A video names its file with data-name (hooks/alpha_videos.py), or has
// data-random to show one of the banner videos, picked once per page load
// so that every banner of the page shows the same one.
//
// Browsers may refuse to autoplay even muted videos (iPhone in Low Power
// Mode, Firefox autoplay settings or energy saving), or pause them when the
// tab is hidden or the page comes back from the history cache. Playback is
// then retried on the first tap, click or key press, when the tab becomes
// visible again and when the page is shown again; meanwhile the poster
// image stays in place.
(function () {
    const BANNER = ["globe_seismes", "globe_maillage", "globe_satellites", "globe_magnetique"];
    const banner = BANNER[Math.floor(Math.random() * BANNER.length)];
    const safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    const videos = document.querySelectorAll("video.alpha-video");
    const GESTURES = ["touchend", "click", "keydown"];

    function playAll() {
        videos.forEach(function (video) {
            if (video.paused) {
                video.play().catch(waitForGesture);
            }
        });
    }

    function onGesture() {
        GESTURES.forEach(function (type) {
            document.removeEventListener(type, onGesture, true);
        });
        playAll();
    }

    function waitForGesture() {
        GESTURES.forEach(function (type) {
            document.addEventListener(type, onGesture, { capture: true, passive: true });
        });
    }

    videos.forEach(function (video) {
        const base = video.dataset.base.replace(/\/?$/, "/");
        const name = "random" in video.dataset ? banner : video.dataset.name;
        video.muted = true;  // as a property too: some browsers ignore the attribute
        video.poster = base + name + ".png";
        video.src = base + name + (safari ? ".mov" : ".webm");
    });
    playAll();

    document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible") playAll();
    });
    window.addEventListener("pageshow", playAll);
})();
