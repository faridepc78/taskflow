(function () {
    const board = document.getElementById("kanban-board");

    if (!board) {
        return;
    }

    let draggedCard = null;
    let sourceDropzone = null;

    const getCookie = (name) => {
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (const cookie of cookies) {
            const [key, ...valueParts] = cookie.trim().split("=");

            if (key === name) {
                return decodeURIComponent(valueParts.join("="));
            }
        }

        return null;
    };

    const refreshColumnState = () => {
        board.querySelectorAll(".kanban-column").forEach((column) => {
            const dropzone = column.querySelector(".kanban-dropzone");
            const cards = dropzone.querySelectorAll(".kanban-task-card");
            const counter = column.querySelector(".kanban-count");
            const emptyState = dropzone.querySelector(".kanban-empty");

            counter.textContent = cards.length;
            emptyState.hidden = cards.length > 0;
        });
    };

    const updateProjectProgress = (data) => {
        const bar = document.getElementById("project-progress-bar");
        const count = document.getElementById("project-progress-count");

        if (bar) {
            bar.style.width = `${data.progress_percentage}%`;
            bar.textContent = `${data.progress_percentage}%`;
        }

        if (count) {
            count.textContent = `${data.completed_tasks} / ${data.total_tasks} tasks`;
        }
    };

    const saveStatus = async (card, status) => {
        const formData = new FormData();
        formData.append("status", status);

        const response = await fetch(card.dataset.statusUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Unable to update task status.");
        }

        return data;
    };

    board.querySelectorAll(".kanban-task-card").forEach((card) => {
        card.addEventListener("dragstart", () => {
            draggedCard = card;
            sourceDropzone = card.closest(".kanban-dropzone");
            card.classList.add("is-dragging");
        });

        card.addEventListener("dragend", () => {
            card.classList.remove("is-dragging");
            board
                .querySelectorAll(".kanban-dropzone")
                .forEach((dropzone) => dropzone.classList.remove("is-drag-over"));
            draggedCard = null;
            sourceDropzone = null;
        });
    });

    board.querySelectorAll(".kanban-dropzone").forEach((dropzone) => {
        dropzone.addEventListener("dragover", (event) => {
            event.preventDefault();
            dropzone.classList.add("is-drag-over");
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("is-drag-over");
        });

        dropzone.addEventListener("drop", async (event) => {
            event.preventDefault();
            dropzone.classList.remove("is-drag-over");

            if (!draggedCard || !sourceDropzone) {
                return;
            }

            const newStatus = dropzone.dataset.status;
            const oldStatus = draggedCard.dataset.status;

            if (newStatus === oldStatus) {
                return;
            }

            const previousSibling = draggedCard.nextElementSibling;
            dropzone.appendChild(draggedCard);
            draggedCard.dataset.status = newStatus;
            refreshColumnState();

            try {
                const data = await saveStatus(draggedCard, newStatus);
                updateProjectProgress(data);

                const activeStatusFilter = board.dataset.activeStatusFilter;

                if (activeStatusFilter && activeStatusFilter !== newStatus) {
                    draggedCard.remove();
                }

                refreshColumnState();
            } catch (error) {
                draggedCard.dataset.status = oldStatus;

                if (previousSibling && previousSibling.parentElement === sourceDropzone) {
                    sourceDropzone.insertBefore(draggedCard, previousSibling);
                } else {
                    sourceDropzone.appendChild(draggedCard);
                }

                refreshColumnState();
                window.alert(error.message);
            }
        });
    });

    refreshColumnState();
})();
