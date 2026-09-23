requireAuth();

const user = getStoredUser();
if (user) document.getElementById("username-display").textContent = user.username;

const grid = document.getElementById("task-grid");
const emptyState = document.getElementById("empty-state");
const errorBanner = document.getElementById("error-banner");

const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("status-filter");
const priorityFilter = document.getElementById("priority-filter");

const taskModal = document.getElementById("task-modal");
const taskForm = document.getElementById("task-form");
const taskFormError = document.getElementById("task-form-error");
const confirmModal = document.getElementById("confirm-modal");

let pendingDeleteId = null;

function showPageError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
}

function statusToClass(status) {
  return "status-" + status.toLowerCase().replace(/\s+/g, "-");
}

function priorityToClass(priority) {
  return "priority-" + priority.toLowerCase();
}

function formatDueDate(dueDate) {
  if (!dueDate) return "No due date";
  const d = new Date(dueDate + "T00:00:00");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

// ---------- Loading data ----------

async function loadStats() {
  const { stats } = await apiRequest("/tasks/stats");
  document.getElementById("stat-total").textContent = stats.total;
  document.getElementById("stat-pending").textContent = stats["Pending"] || 0;
  document.getElementById("stat-progress").textContent = stats["In Progress"] || 0;
  document.getElementById("stat-completed").textContent = stats["Completed"] || 0;
}

async function loadTasks() {
  const params = new URLSearchParams();
  if (statusFilter.value) params.set("status", statusFilter.value);
  if (priorityFilter.value) params.set("priority", priorityFilter.value);
  if (searchInput.value.trim()) params.set("search", searchInput.value.trim());

  const query = params.toString() ? `?${params.toString()}` : "";
  const { tasks } = await apiRequest(`/tasks${query}`);
  renderTasks(tasks);
}

function renderTasks(tasks) {
  grid.innerHTML = "";

  if (tasks.length === 0) {
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  for (const task of tasks) {
    const card = document.createElement("div");
    card.className = "task-card";
    card.innerHTML = `
      <h3></h3>
      <p></p>
      <div class="pill-row">
        <span class="pill ${statusToClass(task.status)}"></span>
        <span class="pill ${priorityToClass(task.priority)}"></span>
      </div>
      <div class="footer-row">
        <span class="due"></span>
        <div class="actions">
          <button class="btn-icon edit-btn" title="Edit" aria-label="Edit task">✎</button>
          <button class="btn-icon delete-btn" title="Delete" aria-label="Delete task">🗑</button>
        </div>
      </div>
    `;
    card.querySelector("h3").textContent = task.title;
    card.querySelector("p").textContent = task.description || "No description";
    card.querySelectorAll(".pill")[0].textContent = task.status;
    card.querySelectorAll(".pill")[1].textContent = task.priority + " priority";
    card.querySelector(".due").textContent = formatDueDate(task.due_date);

    card.querySelector(".edit-btn").addEventListener("click", () => openTaskModal(task));
    card.querySelector(".delete-btn").addEventListener("click", () => openConfirmModal(task.id));

    grid.appendChild(card);
  }
}

async function refreshAll() {
  try {
    await Promise.all([loadStats(), loadTasks()]);
  } catch (err) {
    showPageError(err.message);
  }
}

// ---------- Filters & search ----------

let searchTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadTasks, 300);
});
statusFilter.addEventListener("change", loadTasks);
priorityFilter.addEventListener("change", loadTasks);

// ---------- Task modal (create / edit) ----------

function openTaskModal(task = null) {
  taskForm.reset();
  taskFormError.classList.remove("visible");
  document.getElementById("task-id").value = task ? task.id : "";
  document.getElementById("task-modal-title").textContent = task ? "Edit task" : "New task";
  document.getElementById("task-title").value = task ? task.title : "";
  document.getElementById("task-description").value = task ? task.description : "";
  document.getElementById("task-status").value = task ? task.status : "Pending";
  document.getElementById("task-priority").value = task ? task.priority : "Medium";
  document.getElementById("task-due-date").value = task ? (task.due_date || "") : "";
  taskModal.classList.remove("hidden");
  document.getElementById("task-title").focus();
}

function closeTaskModal() {
  taskModal.classList.add("hidden");
}

document.getElementById("new-task-btn").addEventListener("click", () => openTaskModal());
document.getElementById("empty-new-task-btn").addEventListener("click", () => openTaskModal());
document.getElementById("task-cancel-btn").addEventListener("click", closeTaskModal);
taskModal.addEventListener("click", (e) => { if (e.target === taskModal) closeTaskModal(); });

taskForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  taskFormError.classList.remove("visible");

  const id = document.getElementById("task-id").value;
  const payload = {
    title: document.getElementById("task-title").value.trim(),
    description: document.getElementById("task-description").value.trim(),
    status: document.getElementById("task-status").value,
    priority: document.getElementById("task-priority").value,
    due_date: document.getElementById("task-due-date").value || null,
  };

  try {
    if (id) {
      await apiRequest(`/tasks/${id}`, { method: "PUT", body: payload });
    } else {
      await apiRequest("/tasks", { method: "POST", body: payload });
    }
    closeTaskModal();
    refreshAll();
  } catch (err) {
    taskFormError.textContent = err.message;
    taskFormError.classList.add("visible");
  }
});

// ---------- Delete confirmation ----------

function openConfirmModal(taskId) {
  pendingDeleteId = taskId;
  confirmModal.classList.remove("hidden");
}

function closeConfirmModal() {
  pendingDeleteId = null;
  confirmModal.classList.add("hidden");
}

document.getElementById("confirm-cancel-btn").addEventListener("click", closeConfirmModal);
confirmModal.addEventListener("click", (e) => { if (e.target === confirmModal) closeConfirmModal(); });

document.getElementById("confirm-delete-btn").addEventListener("click", async () => {
  try {
    await apiRequest(`/tasks/${pendingDeleteId}`, { method: "DELETE" });
    closeConfirmModal();
    refreshAll();
  } catch (err) {
    closeConfirmModal();
    showPageError(err.message);
  }
});

// ---------- Logout ----------

document.getElementById("logout-btn").addEventListener("click", async () => {
  try {
    await apiRequest("/auth/logout", { method: "POST" });
  } catch (err) {
    // Even if the request fails, still clear the local session below.
  }
  clearSession();
  window.location.href = "login.html";
});

// ---------- Close modals with Escape ----------

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeTaskModal();
    closeConfirmModal();
  }
});

refreshAll();
