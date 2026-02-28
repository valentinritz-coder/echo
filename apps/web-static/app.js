const API_BASE = localStorage.getItem("echo_api_base") || "http://localhost:8000";
const ACCESS_TOKEN_KEY = "echo_access_token";
const MAX_IMAGES_PER_ENTRY = 8;

const textarea = document.getElementById("echo-input");
const sidebarList = document.getElementById("sidebar-list");
const loadMoreBtn = document.getElementById("load-more-btn");
const composerForm = document.getElementById("composer-form");
const submitEntryBtn = document.getElementById("submit-entry-btn");
const composerHint = document.getElementById("composer-hint");

const imagesInput = document.getElementById("images-input");
const imagesPreview = document.getElementById("images-preview");

const micBtn = document.getElementById("audio-btn");
const audioPreview = document.getElementById("audio-preview");
const audioStatus = document.getElementById("audio-status");
const audioClear = document.getElementById("audio-clear");

const authToggle = document.getElementById("auth-toggle");
const loginModal = document.getElementById("login-modal");
const loginForm = document.getElementById("login-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginCancel = document.getElementById("login-cancel");
const toast = document.getElementById("toast");

const state = {
  entries: [],
  nextOffset: null,
  selectedImages: [],
  currentQuestionId: null,
  mediaRecorder: null,
  recordedAudioBlob: null,
  recordedMimeType: "audio/webm",
  audioBlobUrl: null,
  isSubmitting: false,
};

function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setTokens(payload) {
  localStorage.setItem(ACCESS_TOKEN_KEY, payload.access_token);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => toast.classList.remove("is-visible"), 2500);
}

function revokeEntryObjectUrls(entries) {
  for (const entry of entries || []) {
    if (entry._audioObjectUrl && entry._audioObjectUrlCreated) URL.revokeObjectURL(entry._audioObjectUrl);
    for (let i = 0; i < (entry._assetObjectUrls || []).length; i += 1) {
      if (entry._assetObjectUrlsCreated?.[i] && entry._assetObjectUrls[i]) {
        URL.revokeObjectURL(entry._assetObjectUrls[i]);
      }
    }
  }
}

function softLogout(message) {
  clearTokens();
  revokeEntryObjectUrls(state.entries);
  state.entries = [];
  state.nextOffset = null;
  renderSidebarList();
  updateAuthUi();
  if (message) showToast(message);
}

function authHeaders(headers = {}) {
  const token = getAccessToken();
  const next = { ...headers };
  if (token) next.Authorization = `Bearer ${token}`;
  return next;
}

function resolveApiPath(path) {
  if (typeof path !== "string") throw new Error("API path must be a string");
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (path.startsWith("/api/")) return `${API_BASE}${path}`;
  return `${API_BASE}/api/v1${path}`;
}

function formatApiErrorDetail(detail) {
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      const locParts = Array.isArray(item?.loc) ? item.loc.filter((part) => part !== "body" && part !== "query") : [];
      const loc = locParts.length ? locParts.join(".") : "field";
      const msg = item?.msg || "invalid value";
      return `${loc}: ${msg}`;
    });
    return messages.join(" | ");
  }
  if (detail && typeof detail === "object") {
    if (typeof detail.message === "string") return detail.message;
    if (typeof detail.detail === "string") return detail.detail;
  }
  if (typeof detail === "string") return detail;
  return null;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(resolveApiPath(path), {
    ...options,
    headers: authHeaders(options.headers || {}),
  });

  if (response.status === 401) {
    softLogout("Session expirée. Merci de vous reconnecter.");
    throw new Error("Session expirée. Merci de vous reconnecter.");
  }

  if (response.status === 403) {
    throw new Error("Accès refusé");
  }

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      const formattedDetail = formatApiErrorDetail(payload?.detail);
      errorMessage = formattedDetail || payload?.error?.message || errorMessage;
    } catch {
      // ignore
    }
    throw new Error(errorMessage);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  return response;
}

async function apiFetchBlob(path) {
  const response = await apiFetch(path);
  if (!(response instanceof Response)) throw new Error("Blob response expected");
  return response.blob();
}

function autosize(el) {
  if (!el) return;
  el.style.height = "auto";
  const maxH = Number.parseFloat(window.getComputedStyle(el).maxHeight) || Infinity;
  const nextH = Math.min(el.scrollHeight, maxH);
  el.style.height = `${nextH}px`;
  el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
}

function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(isoDate) {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return isoDate;
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function setComposerEnabled(enabled) {
  composerForm?.classList.toggle("is-disabled", !enabled);
  if (textarea) textarea.disabled = !enabled;
  if (micBtn) micBtn.disabled = !enabled;
  if (imagesInput) imagesInput.disabled = !enabled;
  if (submitEntryBtn) submitEntryBtn.disabled = !enabled;
  if (audioClear) audioClear.disabled = !enabled && !state.recordedAudioBlob;
}

function updateAuthUi() {
  const isLoggedIn = Boolean(getAccessToken());
  document.body.classList.toggle("is-logged-in", isLoggedIn);
  if (authToggle) authToggle.textContent = isLoggedIn ? "Log out" : "Log in";
  setComposerEnabled(isLoggedIn && !state.isSubmitting);
  if (composerHint) composerHint.textContent = isLoggedIn ? "" : "Log in requis pour enregistrer un souvenir.";
}

async function login(email, password) {
  const payload = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setTokens(payload);
}

function openLoginModal() {
  loginModal?.showModal?.();
  loginEmail?.focus();
}

function closeLoginModal() {
  loginModal?.close?.();
}

function pickRecorderMimeType() {
  const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg"];
  for (const candidate of preferred) {
    if (window.MediaRecorder?.isTypeSupported?.(candidate)) return candidate;
  }
  return "";
}

function setAudioUi({ recording = false, hasAudio = false, status = "Prêt." }) {
  micBtn?.classList.toggle("is-recording", recording);
  micBtn?.classList.toggle("has-audio", hasAudio);
  micBtn?.setAttribute("aria-pressed", recording ? "true" : "false");
  if (audioStatus) audioStatus.textContent = status;
  if (audioClear) audioClear.disabled = !hasAudio && !recording;
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setAudioUi({ status: "Micro non supporté." });
    return;
  }
  if (state.recordedAudioBlob) clearRecording();

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = pickRecorderMimeType();
  state.recordedMimeType = mimeType || "audio/webm";
  state.mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
  const chunks = [];

  state.mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) chunks.push(event.data);
  };

  state.mediaRecorder.onstop = () => {
    stream.getTracks().forEach((track) => track.stop());
    state.recordedAudioBlob = new Blob(chunks, { type: state.mediaRecorder?.mimeType || state.recordedMimeType });
    if (state.audioBlobUrl) URL.revokeObjectURL(state.audioBlobUrl);
    state.audioBlobUrl = URL.createObjectURL(state.recordedAudioBlob);
    if (audioPreview) {
      audioPreview.hidden = false;
      audioPreview.src = state.audioBlobUrl;
    }
    setAudioUi({ recording: false, hasAudio: true, status: "Audio prêt." });
  };

  state.mediaRecorder.start();
  setAudioUi({ recording: true, status: "Enregistrement…" });
}

function stopRecording() {
  if (state.mediaRecorder?.state === "recording") state.mediaRecorder.stop();
}

function clearRecording() {
  stopRecording();
  state.recordedAudioBlob = null;
  if (state.audioBlobUrl) URL.revokeObjectURL(state.audioBlobUrl);
  state.audioBlobUrl = null;
  if (audioPreview) {
    audioPreview.hidden = true;
    audioPreview.removeAttribute("src");
    audioPreview.load?.();
  }
  setAudioUi({ recording: false, hasAudio: false, status: "Prêt." });
}

function clearImagesPreview() {
  if (!imagesPreview) return;
  imagesPreview.innerHTML = "";
}

function addThumb(file) {
  if (!imagesPreview) return;
  const wrap = document.createElement("div");
  wrap.className = "thumb";
  const img = document.createElement("img");
  img.alt = "";
  wrap.appendChild(img);
  const url = URL.createObjectURL(file);
  img.src = url;
  img.onload = () => URL.revokeObjectURL(url);
  imagesPreview.appendChild(wrap);
}

async function getQuestionId() {
  if (state.currentQuestionId) return state.currentQuestionId;
  const question = await apiFetch("/questions/today");
  state.currentQuestionId = question.id;
  return question.id;
}

async function uploadImages(entryId, files) {
  for (let i = 0; i < files.length; i += 1) {
    const formData = new FormData();
    formData.append("file", files[i], files[i].name);
    await apiFetch(`/entries/${entryId}/assets`, { method: "POST", body: formData });
    showToast(`Upload image ${i + 1}/${files.length}`);
  }
}

async function createEntry() {
  const text = textarea?.value.trim() || "";
  const hasAudio = Boolean(state.recordedAudioBlob);
  const hasImages = state.selectedImages.length > 0;

  if (!text && !hasAudio) {
    if (composerHint) composerHint.textContent = hasImages
      ? "Ajoute du texte ou un audio avant d'uploader des images."
      : "Ajoute du texte ou un audio.";
    return;
  }

  state.isSubmitting = true;
  updateAuthUi();

  try {
    const questionId = await getQuestionId();
    const formData = new FormData();
    formData.append("question_id", String(questionId));
    if (text) formData.append("text", text);
    if (hasAudio) {
      const extension = state.recordedMimeType.includes("ogg") ? "ogg" : "webm";
      formData.append("audio_file", state.recordedAudioBlob, `recording.${extension}`);
    }

    const entry = await apiFetch("/entries", { method: "POST", body: formData });
    if (hasImages) await uploadImages(entry.id, state.selectedImages);

    if (textarea) {
      textarea.value = "";
      autosize(textarea);
    }
    clearRecording();
    state.selectedImages = [];
    if (imagesInput) imagesInput.value = "";
    clearImagesPreview();
    if (composerHint) composerHint.textContent = "";

    showToast("Souvenir enregistré.");
    await refreshTimeline();
  } catch (error) {
    showToast(`Erreur: ${error.message}`);
  } finally {
    state.isSubmitting = false;
    updateAuthUi();
  }
}

function dotSummary(entry) {
  const dots = [];
  if (entry.text_content) dots.push("•");
  if (entry.audio_url) dots.push("◍");
  if (entry.assets?.length) dots.push("◼︎");
  return dots.join(" ");
}

async function hydrateEntryMedia(entry) {
  const hydrated = {
    ...entry,
    _audioObjectUrl: null,
    _audioObjectUrlCreated: false,
    _assetObjectUrls: [],
    _assetObjectUrlsCreated: [],
  };

  if (entry.audio_url) {
    try {
      const blob = await apiFetchBlob(entry.audio_url);
      hydrated._audioObjectUrl = URL.createObjectURL(blob);
      hydrated._audioObjectUrlCreated = true;
    } catch {
      hydrated._audioObjectUrl = entry.audio_url;
      hydrated._audioObjectUrlCreated = false;
    }
  }

  for (const asset of entry.assets || []) {
    try {
      const blob = await apiFetchBlob(asset.download_url);
      hydrated._assetObjectUrls.push(URL.createObjectURL(blob));
      hydrated._assetObjectUrlsCreated.push(true);
    } catch {
      hydrated._assetObjectUrls.push(asset.download_url);
      hydrated._assetObjectUrlsCreated.push(false);
    }
  }

  return hydrated;
}

function renderEntryCard(entry) {
  if (!sidebarList) return;
  const li = document.createElement("li");
  li.className = "sidebar-item";

  const imageHtml = (entry._assetObjectUrls || [])
    .map((url) => `<img src="${escapeHtml(url)}" alt="asset" loading="lazy" class="sidebar-asset" />`)
    .join("");

  li.innerHTML = `
    <article class="sidebar-link sidebar-link--entry">
      <div class="sidebar-row">
        <span class="sidebar-date">${escapeHtml(formatDate(entry.created_at))}</span>
        <span class="sidebar-dots">${escapeHtml(dotSummary(entry))}</span>
      </div>
      ${entry.text_content ? `<div class="sidebar-text">${escapeHtml(entry.text_content)}</div>` : ""}
      ${entry._audioObjectUrl ? `<audio controls preload="none" src="${escapeHtml(entry._audioObjectUrl)}"></audio>` : ""}
      ${imageHtml ? `<div class="sidebar-assets">${imageHtml}</div>` : ""}
    </article>
  `;
  sidebarList.appendChild(li);
}

function renderSidebarList() {
  if (!sidebarList) return;
  sidebarList.innerHTML = "";
  state.entries.forEach(renderEntryCard);
}

async function loadEntries(offset = 0) {
  const payload = await apiFetch(`/entries?limit=50&offset=${offset}&sort=created_at_desc`);
  const hydratedItems = await Promise.all(payload.items.map(hydrateEntryMedia));
  state.nextOffset = payload.next_offset;

  if (offset === 0) {
    revokeEntryObjectUrls(state.entries);
    state.entries = hydratedItems;
  } else {
    state.entries = state.entries.concat(hydratedItems);
  }

  renderSidebarList();
  if (loadMoreBtn) loadMoreBtn.hidden = state.nextOffset === null || state.nextOffset === undefined;
}

async function refreshTimeline() {
  if (!getAccessToken()) {
    revokeEntryObjectUrls(state.entries);
    state.entries = [];
    state.nextOffset = null;
    renderSidebarList();
    if (loadMoreBtn) loadMoreBtn.hidden = true;
    return;
  }

  try {
    await loadEntries(0);
  } catch (error) {
    showToast(`Timeline indisponible: ${error.message}`);
  }
}

function bindEvents() {
  if (textarea) {
    autosize(textarea);
    textarea.addEventListener("input", () => autosize(textarea));
    window.addEventListener("resize", () => autosize(textarea));
  }

  authToggle?.addEventListener("click", async () => {
    if (getAccessToken()) {
      softLogout("Déconnecté.");
      return;
    }
    openLoginModal();
  });

  loginCancel?.addEventListener("click", closeLoginModal);
  loginModal?.addEventListener("click", (event) => {
    if (event.target === loginModal) closeLoginModal();
  });
  loginModal?.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeLoginModal();
  });

  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await login(loginEmail.value.trim(), loginPassword.value);
      closeLoginModal();
      updateAuthUi();
      showToast("Connexion réussie.");
      await refreshTimeline();
    } catch (error) {
      showToast(`Login failed: ${error.message}`);
    }
  });

  micBtn?.addEventListener("click", async () => {
    if (!getAccessToken()) return openLoginModal();
    try {
      if (state.mediaRecorder?.state === "recording") stopRecording();
      else await startRecording();
    } catch {
      setAudioUi({ recording: false, hasAudio: false, status: "Permission micro refusée." });
    }
  });

  audioClear?.addEventListener("click", clearRecording);

  imagesInput?.addEventListener("change", () => {
    const files = Array.from(imagesInput.files || []);
    if (files.length > MAX_IMAGES_PER_ENTRY) {
      showToast(`Maximum ${MAX_IMAGES_PER_ENTRY} images par entrée.`);
    }
    state.selectedImages = files.slice(0, MAX_IMAGES_PER_ENTRY);
    clearImagesPreview();
    state.selectedImages.slice(0, 9).forEach(addThumb);
  });

  composerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!getAccessToken()) return openLoginModal();
    await createEntry();
  });

  loadMoreBtn?.addEventListener("click", async () => {
    if (state.nextOffset === null || state.nextOffset === undefined) return;
    try {
      await loadEntries(state.nextOffset);
    } catch (error) {
      showToast(`Impossible de charger plus: ${error.message}`);
    }
  });
}

bindEvents();
updateAuthUi();
setAudioUi({ recording: false, hasAudio: false, status: "Prêt." });
refreshTimeline();
