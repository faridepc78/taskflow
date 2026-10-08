/* Presentation only. All form validation and authorization stay on the server. */
(function () {
    "use strict";
    const root = document.documentElement;

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        const label = () => button.setAttribute("aria-label", root.dataset.theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
        label();
        button.addEventListener("click", () => {
            root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
            try { localStorage.setItem("taskflow-theme", root.dataset.theme); } catch (_) { /* optional */ }
            label();
        });
    });

    const sidebar = document.getElementById("workspace-sidebar");
    const backdrop = document.querySelector(".sidebar-backdrop");
    const openButton = document.querySelector("[data-sidebar-open]");
    let previousFocus = null;
    const closeSidebar = (restoreFocus = true) => {
        if (!sidebar) return;
        sidebar.classList.remove("is-open");
        sidebar.inert = window.innerWidth <= 900;
        if (backdrop) backdrop.hidden = true;
        openButton?.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
        if (restoreFocus && previousFocus) previousFocus.focus();
    };
    openButton?.addEventListener("click", () => {
        previousFocus = document.activeElement;
        sidebar.inert = false;
        sidebar.classList.add("is-open");
        if (backdrop) backdrop.hidden = false;
        openButton.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
        sidebar.querySelector("a,button")?.focus();
    });
    document.querySelectorAll("[data-sidebar-close]").forEach((button) => button.addEventListener("click", () => closeSidebar()));
    sidebar?.querySelectorAll("a").forEach((anchor) => anchor.addEventListener("click", () => closeSidebar(false)));
    document.addEventListener("keydown", (event) => {
        if (!sidebar?.classList.contains("is-open")) return;
        if (event.key === "Escape") closeSidebar();
        if (event.key === "Tab") {
            const focusable = [...sidebar.querySelectorAll('a[href],button:not([disabled])')].filter((element) => element.offsetParent !== null);
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        }
    });
    if (sidebar) sidebar.inert = window.innerWidth <= 900;
    window.addEventListener("resize", () => {
        if (window.innerWidth > 900) closeSidebar(false);
        else if (sidebar && !sidebar.classList.contains("is-open")) sidebar.inert = true;
    });

    const dismiss = (element) => element?.closest(".toast")?.remove();
    document.querySelectorAll("[data-dismiss-toast]").forEach((button) => button.addEventListener("click", () => dismiss(button)));
    window.TaskFlowUI = {
        notify(message, type = "info") {
            const region = document.getElementById("toast-region");
            if (!region) return;
            const toast = document.createElement("div");
            toast.className = `toast toast-${["error", "success"].includes(type) ? type : "info"}`;
            toast.setAttribute("role", type === "error" ? "alert" : "status");
            const content = document.createElement("span");
            content.textContent = message;
            const button = document.createElement("button");
            button.type = "button";
            button.className = "icon-button toast-close";
            button.textContent = "\u00d7";
            button.setAttribute("aria-label", "Dismiss notification");
            button.addEventListener("click", () => toast.remove());
            toast.append(content, button);
            region.append(toast);
            // Errors stay until the user dismisses them.
            if (type !== "error") window.setTimeout(() => toast.remove(), 7000);
        },
    };

    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;
        button.hidden = false;
        button.addEventListener("click", () => {
            const visible = input.type === "password";
            input.type = visible ? "text" : "password";
            input.toggleAttribute("data-password-visible", visible);
            button.setAttribute("aria-pressed", String(visible));
            button.setAttribute("aria-label", visible ? "Hide password" : "Show password");
        });
    });

    document.querySelectorAll(".tf-form input[type='file']").forEach((input) => {
        let previewUrl = null;
        input.addEventListener("change", () => {
            const file = input.files?.[0];
            const label = input.closest("form")?.querySelector("[data-file-selection]");
            if (label) label.textContent = file ? `${file.name} \u00b7 ${(file.size / 1024).toFixed(0)} KB` : "";
            const target = document.querySelector("[data-avatar-preview]");
            if (input.name !== "avatar" || !target || !file?.type.startsWith("image/")) return;
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = URL.createObjectURL(file);
            const image = document.createElement("img");
            image.src = previewUrl;
            image.alt = "Selected avatar preview. Save your profile to apply.";
            image.addEventListener("load", () => { target.replaceChildren(image); }, { once: true });
        });
    });

    document.querySelectorAll("[data-date-picker]").forEach((button) => {
        const input = document.getElementById(button.dataset.datePicker);
        if (!input || input.type !== "date") return;
        button.addEventListener("click", () => {
            if (typeof input.showPicker === "function") {
                try { input.showPicker(); return; } catch (_) { /* Browser fallback */ }
            }
            input.focus();
            input.click();
        });
    });

    document.querySelectorAll("form[data-submit-state]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (form.dataset.submitted === "true") { event.preventDefault(); return; }
            form.dataset.submitted = "true";
            // Do not disable form fields or change their posted values.
            window.setTimeout(() => {
                form.querySelectorAll("button[type='submit']").forEach((button) => {
                    button.disabled = true;
                    button.classList.add("is-submitting");
                });
            }, 0);
        });
    });
    window.addEventListener("pageshow", () => {
        document.querySelectorAll("form[data-submit-state]").forEach((form) => {
            delete form.dataset.submitted;
            form.querySelectorAll(".is-submitting").forEach((button) => {
                button.disabled = false;
                button.classList.remove("is-submitting");
            });
        });
    });
}());
