// Reveal ringan saat section masuk viewport.
// Progressive enhancement: tanpa JS / reduced-motion, konten tetap terlihat.
(() => {
    const targets = document.querySelectorAll("[data-reveal]");
    if (!targets.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;

    document.documentElement.classList.add("js-reveal");

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
        });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    targets.forEach((target) => observer.observe(target));

    // Safety: jangan pernah meninggalkan konten tersembunyi bila observer tidak sempat jalan.
    window.setTimeout(() => {
        targets.forEach((target) => target.classList.add("is-visible"));
    }, 2500);
})();
