/**
 * Client API pour web-static : base URL, fetch avec token, gestion 401.
 * Usage : inclure avant app.js ; utiliser window.echoApi ou les fonctions exposées.
 */
(function () {
  "use strict";

  const API_PATH = "/api/v1";
  const STORAGE_KEY = "echo_access_token";
  const DEFAULT_BASE = "http://localhost:8000";

  function getApiBaseUrl() {
    const meta = document.querySelector('meta[name="echo-api-base"]');
    if (meta && meta.content && meta.content.trim()) {
      return meta.content.trim().replace(/\/+$/, "");
    }
    if (typeof window.ECHO_API_BASE_URL === "string" && window.ECHO_API_BASE_URL.trim()) {
      return window.ECHO_API_BASE_URL.trim().replace(/\/+$/, "");
    }
    return DEFAULT_BASE;
  }

  function getAccessToken() {
    try {
      return sessionStorage.getItem(STORAGE_KEY) || "";
    } catch {
      return "";
    }
  }

  function setAccessToken(token) {
    try {
      if (token) sessionStorage.setItem(STORAGE_KEY, token);
      else sessionStorage.removeItem(STORAGE_KEY);
    } catch (_) {}
  }

  function clearAccessToken() {
    setAccessToken("");
  }

  function buildUrl(path) {
    if (path.startsWith("http")) return path;
    const base = getApiBaseUrl();
    const p = path.startsWith("/") ? path : API_PATH + "/" + path;
    return base + (p.startsWith("/") ? p : "/" + p);
  }

  /**
   * Effectue un fetch vers l'API avec la base URL et le token.
   * En cas de 401 : appelle onUnauthorized (si fourni), supprime le token, puis redirige vers /login.html
   * sauf si onUnauthorized retourne true (pour éviter la redirection).
   *
   * @param {string} path - Chemin (ex: "/api/v1/auth/login", "/api/v1/entries")
   * @param {RequestInit & { onUnauthorized?: () => boolean | void }} options - Options fetch + onUnauthorized
   * @returns {Promise<Response>}
   */
  async function apiFetch(path, options = {}) {
    const { onUnauthorized, ...fetchOptions } = options;
    const url = buildUrl(path.startsWith(API_PATH) ? path : API_PATH + (path.startsWith("/") ? path : "/" + path));
    const token = getAccessToken();
    const headers = new Headers(fetchOptions.headers || {});
    if (token) headers.set("Authorization", "Bearer " + token);
    if (!headers.has("Content-Type") && fetchOptions.body && typeof fetchOptions.body === "string") {
      headers.set("Content-Type", "application/json");
    }
    const res = await fetch(url, { ...fetchOptions, headers });
    if (res.status === 401) {
      clearAccessToken();
      if (typeof onUnauthorized === "function") {
        const preventRedirect = onUnauthorized();
        if (preventRedirect === true) return res;
      }
      window.location.href = "/login.html";
      return res;
    }
    return res;
  }

  /**
   * Raccourci GET JSON.
   */
  async function apiGet(path, options = {}) {
    const res = await apiFetch(path, { ...options, method: "GET" });
    if (!res.ok) throw new ApiClientError(res.status, await res.text());
    const ct = res.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) return res.json();
    return res.text();
  }

  /**
   * Raccourci POST JSON.
   */
  async function apiPost(path, body, options = {}) {
    const res = await apiFetch(path, {
      ...options,
      method: "POST",
      body: typeof body === "string" ? body : JSON.stringify(body || {}),
    });
    if (!res.ok) throw new ApiClientError(res.status, await res.text());
    const ct = res.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) return res.json();
    return res.text();
  }

  function ApiClientError(statusCode, message) {
    this.name = "ApiClientError";
    this.statusCode = statusCode;
    this.message = message || "API error " + statusCode;
  }
  ApiClientError.prototype = Object.create(Error.prototype);

  window.echoApi = {
    getApiBaseUrl,
    getAccessToken,
    setAccessToken,
    clearAccessToken,
    apiFetch,
    apiGet,
    apiPost,
    ApiClientError,
    API_PATH,
  };
})();
