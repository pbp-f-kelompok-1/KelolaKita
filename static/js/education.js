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

// Filter artikel: form GET tetap menjadi fallback tanpa JavaScript.
(() => {
    const form = document.querySelector("[data-article-filter]");
    const results = document.querySelector("[data-article-results]");
    if (!form || !results || !window.fetch || !window.URLSearchParams) return;

    let timer;
    let controller;

    const filterUrl = () => {
        const url = new URL(form.action, window.location.href);
        const params = new URLSearchParams(new FormData(form));
        for (const [key, value] of [...params]) {
            if (!value.trim()) params.delete(key);
        }
        url.search = params.toString() ? `?${params}` : "";
        return url;
    };

    const loadResults = async () => {
        if (controller) controller.abort();
        controller = new AbortController();
        const url = filterUrl();
        form.setAttribute("aria-busy", "true");
        results.setAttribute("aria-busy", "true");

        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: controller.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            results.innerHTML = await response.text();
            window.history.replaceState(null, "", url);
        } catch (error) {
            if (error.name === "AbortError") return;
            // Jika async gagal, gunakan navigasi GET biasa agar filter tetap dapat dipakai.
            window.location.assign(url);
        } finally {
            form.removeAttribute("aria-busy");
            results.removeAttribute("aria-busy");
        }
    };

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        window.clearTimeout(timer);
        loadResults();
    });

    const search = form.querySelector('input[name="q"]');
    if (search) {
        search.addEventListener("input", () => {
            window.clearTimeout(timer);
            timer = window.setTimeout(loadResults, 300);
        });
    }

    const category = form.querySelector('select[name="category"]');
    if (category) {
        category.addEventListener("change", () => {
            window.clearTimeout(timer);
            loadResults();
        });
    }
})();

// Hapus data dari dashboard tanpa reload.
// Tanpa JavaScript, tautan tetap menuju halaman konfirmasi biasa.
(() => {
    const links = document.querySelectorAll(".dash-action--danger");
    if (!links.length || !window.fetch) return;

    const feedback = document.querySelector("[data-dash-feedback]");
    const tokenInput = document.querySelector("[name=csrfmiddlewaretoken]");
    const token = tokenInput ? tokenInput.value : "";

    const showFeedback = (message) => {
        if (feedback) feedback.textContent = message;
    };

    links.forEach((link) => {
        link.addEventListener("click", async (event) => {
            event.preventDefault();
            if (!window.confirm("Hapus data ini secara permanen?")) return;

            link.setAttribute("aria-busy", "true");
            try {
                const response = await fetch(link.href, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": token,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (response.status === 403) {
                    showFeedback("Anda tidak berwenang menghapus data ini.");
                    return;
                }
                if (response.status === 404) {
                    showFeedback("Data sudah tidak ada. Muat ulang halaman bila perlu.");
                    return;
                }
                if (!response.ok || response.redirected) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                const item = link.closest(
                    ".dash-article, .dash-agenda__item, .dash-table tbody tr"
                );
                const parent = item ? item.parentElement : null;
                if (!item || !parent) {
                    window.location.assign(data.redirect || "/edukasi/kelola/");
                    return;
                }

                item.remove();
                if (!parent.children.length) {
                    window.location.assign(data.redirect || "/edukasi/kelola/");
                    return;
                }
                showFeedback(data.message || "Data berhasil dihapus.");
            } catch (error) {
                showFeedback("Gagal menghapus data. Silakan coba lagi.");
            } finally {
                link.removeAttribute("aria-busy");
            }
        });
    });
})();
