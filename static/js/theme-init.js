/* Apply the saved visual theme before the stylesheet is painted. */
(function () {
    "use strict";
    let theme = "light";
    try {
        const saved = localStorage.getItem("taskflow-theme");
        if (saved === "dark" || saved === "light") theme = saved;
    } catch (_) {
        // Storage may be unavailable in private or restricted browsing contexts.
    }
    document.documentElement.dataset.theme = theme;
}());
