/* Same status endpoint and payload; drag and keyboard/touch controls share one path. */
(function () {
    "use strict";
    const board = document.getElementById("kanban-board");
    if (!board) return;
    const validStatuses = new Set(["todo", "in_progress", "done"]);
    const liveRegion = document.getElementById("kanban-status");
    let draggedCard = null;
    let saving = false;

    const getCsrfToken = () => {
        for (const cookie of document.cookie.split(";")) {
            const [key, ...parts] = cookie.trim().split("=");
            if (key === "csrftoken") return decodeURIComponent(parts.join("="));
        }
        return document.querySelector("input[name='csrfmiddlewaretoken']")?.value || "";
    };
    const refreshColumns = () => {
        board.querySelectorAll(".kanban-column").forEach((column) => {
            const cards = column.querySelectorAll(".kanban-task-card");
            column.querySelector(".kanban-count").textContent = String(cards.length);
            column.querySelector(".kanban-empty").hidden = cards.length > 0;
        });
    };
    const refreshProgress = (data) => {
        const bar = document.getElementById("project-progress-bar");
        if (bar) {
            bar.style.width = `${data.progress_percentage}%`;
            bar.textContent = `${data.progress_percentage}%`;
            bar.parentElement?.setAttribute("aria-valuenow", String(data.progress_percentage));
        }
        const count = document.getElementById("project-progress-count");
        if (count) count.textContent = `${data.completed_tasks} / ${data.total_tasks} tasks`;
        const label = document.getElementById("project-progress-label");
        if (label) label.textContent = `${data.progress_percentage}%`;
    };
    const refreshDeadline = (card, status) => {
        const deadline = card.querySelector(".kanban-deadline");
        if (!deadline) return;
        const overdue = status !== "done" && card.dataset.dueState === "overdue";
        const today = status !== "done" && card.dataset.dueState === "today";
        card.classList.toggle("kanban-task-overdue", overdue);
        card.classList.toggle("kanban-task-due-today", today);
        deadline.classList.toggle("is-overdue", overdue);
        deadline.classList.toggle("is-due-today", today);
        deadline.textContent = `${overdue ? "Overdue \u00b7" : today ? "Due today \u00b7" : "Due"} ${card.dataset.dueDate}`;
    };
    const noLongerMatches = (newStatus) => Boolean(
        (board.dataset.activeStatusFilter && board.dataset.activeStatusFilter !== newStatus) ||
        (newStatus === "done" && ["overdue", "today", "upcoming"].includes(board.dataset.activeDeadlineFilter))
    );
    const setBusy = (state) => {
        saving = state;
        board.setAttribute("aria-busy", String(state));
        board.querySelectorAll("[data-move-task]").forEach((control) => { control.disabled = state; });
    };

    const moveTask = async (card, newStatus) => {
        if (saving || !card || !validStatuses.has(newStatus)) return;
        const oldStatus = card.dataset.status;
        if (oldStatus === newStatus) return;
        // Capture references before awaiting: dragend clears the global drag state.
        const oldZone = card.closest(".kanban-dropzone");
        const nextSibling = card.nextElementSibling;
        const newZone = board.querySelector(`.kanban-dropzone[data-status='${newStatus}']`);
        if (!oldZone || !newZone) return;
        setBusy(true);
        card.classList.add("is-saving");
        card.dataset.status = newStatus;
        newZone.insertBefore(card, newZone.querySelector(".kanban-empty"));
        refreshColumns();
        try {
            const body = new FormData();
            body.append("status", newStatus);
            const response = await fetch(card.dataset.statusUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "XMLHttpRequest" },
                body,
            });
            if (!response.headers.get("content-type")?.includes("application/json")) {
                throw new Error("Unable to update this task. Refresh the page and check that you are signed in.");
            }
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.message || "Unable to update task status.");
            refreshProgress(data);
            refreshDeadline(card, newStatus);
            const control = card.querySelector("[data-move-task]");
            if (control) control.value = newStatus;
            const message = `Task moved to ${data.status_label}.`;
            if (liveRegion) liveRegion.textContent = message;
            if (noLongerMatches(newStatus)) card.remove();
        } catch (error) {
            card.dataset.status = oldStatus;
            if (nextSibling?.parentElement === oldZone) oldZone.insertBefore(card, nextSibling);
            else oldZone.insertBefore(card, oldZone.querySelector(".kanban-empty"));
            const control = card.querySelector("[data-move-task]");
            if (control) control.value = oldStatus;
            const message = error instanceof Error ? error.message : "Unable to update task status.";
            if (liveRegion) liveRegion.textContent = message;
            window.TaskFlowUI?.notify(message, "error");
        } finally {
            card.classList.remove("is-saving", "is-dragging");
            setBusy(false);
            refreshColumns();
        }
    };

    board.querySelectorAll(".kanban-task-card").forEach((card) => {
        const control = card.querySelector("[data-move-task]");
        if (control) {
            control.hidden = false;
            control.addEventListener("change", () => moveTask(card, control.value));
        }
        card.addEventListener("dragstart", (event) => {
            if (saving) { event.preventDefault(); return; }
            draggedCard = card;
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", card.dataset.taskId);
            card.classList.add("is-dragging");
        });
        card.addEventListener("dragend", () => {
            card.classList.remove("is-dragging");
            board.querySelectorAll(".kanban-dropzone").forEach((zone) => zone.classList.remove("is-drag-over"));
            draggedCard = null;
        });
    });
    board.querySelectorAll(".kanban-dropzone").forEach((zone) => {
        zone.addEventListener("dragover", (event) => {
            if (!draggedCard || saving) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            zone.classList.add("is-drag-over");
        });
        zone.addEventListener("dragleave", (event) => {
            if (!zone.contains(event.relatedTarget)) zone.classList.remove("is-drag-over");
        });
        zone.addEventListener("drop", (event) => {
            event.preventDefault();
            zone.classList.remove("is-drag-over");
            const card = draggedCard;
            if (card) moveTask(card, zone.dataset.status);
        });
    });
    refreshColumns();
}());
