const API_BASE = "/api";
const TOKEN_KEY = "tasklog_token";
const USER_KEY = "tasklog_user";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

/**
 * Wrapper around fetch() that adds the Authorization header, parses JSON,
 * and sends the user back to login if the token is missing/expired.
 * `path` is relative to /api, e.g. "/tasks" or "/tasks/3".
 */
async function apiRequest(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && path !== "/auth/login") {
    clearSession();
    window.location.href = "login.html";
    throw new Error("Session expired");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }

  return data;
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "login.html";
  }
}
