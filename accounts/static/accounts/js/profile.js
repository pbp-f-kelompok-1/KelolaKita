document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-profile-form]");
    if (!form || !window.fetch || !window.FormData) return;

    const submitButton = form.querySelector('button[type="submit"]');
    const feedback = form.querySelector("[data-profile-message]");
    if (!submitButton || !feedback) return;

    const errorContainers = new Map(
        Array.from(form.querySelectorAll("[data-error-for]"), (element) => [
            element.dataset.errorFor,
            element,
        ])
    );
    const originalButtonText = submitButton.textContent;

    function showFeedback(text, type) {
        feedback.textContent = text;
        feedback.hidden = !text;
        feedback.classList.toggle("flash--success", type === "success");
        feedback.classList.toggle("flash--error", type === "error");
    }

    function clearErrors() {
        for (const [key, container] of errorContainers) {
            container.replaceChildren();
            container.hidden = true;

            if (key.includes(".")) {
                const field = form.elements.namedItem(key.split(".")[1]);
                field?.removeAttribute("aria-invalid");
            }
        }
    }

    function appendErrors(container, errors) {
        if (!container || !Array.isArray(errors)) return;

        for (const error of errors) {
            const item = document.createElement("p");
            item.setAttribute("role", "alert");
            item.textContent = String(error);
            container.append(item);
        }
        if (errors.length) container.hidden = false;
    }

    function showErrors(payload) {
        const generalErrors = [
            ...(payload.non_field_errors?.user || []),
            ...(payload.non_field_errors?.profile || []),
        ];

        for (const group of ["user", "profile"]) {
            for (const [name, errors] of Object.entries(payload.errors?.[group] || {})) {
                const container = errorContainers.get(`${group}.${name}`);
                if (!container) {
                    generalErrors.push(...errors);
                    continue;
                }

                appendErrors(container, errors);
                const field = form.elements.namedItem(name);
                if (errors.length) field?.setAttribute("aria-invalid", "true");
            }
        }
        appendErrors(errorContainers.get("non_field"), generalErrors);
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (submitButton.disabled) return;

        clearErrors();
        showFeedback("", null);
        submitButton.disabled = true;
        submitButton.textContent = "Menyimpan...";
        form.setAttribute("aria-busy", "true");

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json",
                },
                credentials: "same-origin",
            });
            const payload = await response.json();

            if (response.ok && payload.success === true) {
                showFeedback(payload.message, "success");

                const fullName = document.querySelector("[data-profile-full-name]");
                if (fullName && typeof payload.full_name === "string") {
                    fullName.textContent = payload.full_name;
                }

                const updatedAt = document.querySelector("[data-profile-updated-at]");
                if (updatedAt && typeof payload.updated_at_display === "string") {
                    updatedAt.textContent = payload.updated_at_display;
                }
            } else if (response.status === 400 && payload.success === false) {
                showErrors(payload);
                showFeedback("Periksa kembali isian yang ditandai.", "error");
            } else {
                throw new Error("Unexpected response");
            }
        } catch {
            showFeedback(
                "Perubahan belum tersimpan. Periksa koneksi atau sesi akun Anda, lalu coba lagi.",
                "error"
            );
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            form.removeAttribute("aria-busy");
        }
    });

    form.noValidate = true;
});
