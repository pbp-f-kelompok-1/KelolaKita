(() => {
    const card = document.querySelector("[data-education-form-card]");
    if (!card || !window.fetch) return;

    // The native form remains available for browsers without JavaScript.
    card.addEventListener("submit", async (event) => {
        const form = event.target.closest("[data-education-form]");
        if (!form) return;
        event.preventDefault();

        const button = form.querySelector('button[type="submit"]');
        if (button.disabled) return;
        const data = new FormData(form);
        button.disabled = true;
        card.setAttribute("aria-busy", "true");
        card.querySelector("[data-request-error]")?.remove();

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: data,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (response.redirected) {
                window.location.assign(response.url);
                return;
            }
            if (!response.ok && response.status !== 422) {
                throw new Error(response.status === 403
                    ? "Akses ditolak atau sesi kedaluwarsa. Muat ulang halaman."
                    : "Data belum dapat disimpan. Periksa kembali dan coba lagi.");
            }
            card.innerHTML = await response.text();
            card.querySelector('[aria-invalid="true"], [role="status"]')?.focus();
        } catch (error) {
            const feedback = document.createElement("p");
            feedback.className = "flash flash--error mb-4";
            feedback.setAttribute("role", "alert");
            feedback.setAttribute("data-request-error", "");
            feedback.textContent = error instanceof TypeError
                ? "Koneksi terputus. Periksa pengelolaan sebelum mengirim ulang."
                : error.message;
            card.prepend(feedback);
        } finally {
            card.removeAttribute("aria-busy");
            button.disabled = false;
        }
    });

    card.addEventListener("change", (event) => {
        const image = card.querySelector("#id_image");
        const clear = card.querySelector("#image-clear_id");
        if (!image || !clear) return;
        if (event.target === image && image.files.length) clear.checked = false;
        if (event.target === clear && clear.checked) image.value = "";
    });
})();
