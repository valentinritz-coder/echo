const memories = [
  {
    id: 1,
    date: "2026-01-10",
    text: "J'ai retrouvé une photo de famille ce matin.",
    audio: true,
    image: true,
  },
  {
    id: 2,
    date: "2026-01-05",
    text: "Promenade calme au parc.",
    audio: false,
    image: false,
  },
  {
    id: 3,
    date: "2025-12-28",
    text: "",
    audio: true,
    image: false,
  },
];

const imageSamples = [
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop stop-color='%233a5a74'/%3E%3Cstop offset='1' stop-color='%2392b4c8'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='640' height='360' fill='url(%23g)'/%3E%3Ccircle cx='190' cy='152' r='68' fill='%23ffffff22'/%3E%3C/svg%3E",
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='1' x2='1' y2='0'%3E%3Cstop stop-color='%23223a4a'/%3E%3Cstop offset='1' stop-color='%237ca0b5'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='640' height='360' fill='url(%23g)'/%3E%3Crect x='120' y='86' width='380' height='190' rx='16' fill='%23ffffff1e'/%3E%3C/svg%3E",
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='0'%3E%3Cstop stop-color='%2331424d'/%3E%3Cstop offset='1' stop-color='%235f7f93'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='640' height='360' fill='url(%23g)'/%3E%3Cpath d='M120 260l108-124 95 82 70-58 124 100z' fill='%23ffffff20'/%3E%3C/svg%3E",
];

let currentMemoryId = null;
let audioState = "idle";
let imageUrl = "";

const timelineList = document.getElementById("timeline-list");
const timelinePanel = document.querySelector(".timeline-panel");
const timelineToggle = document.getElementById("timeline-toggle");
const textInput = document.getElementById("memory-text");
const audioButton = document.getElementById("audio-action");
const audioStatus = document.getElementById("audio-status");
const imageAddBtn = document.getElementById("image-add");
const imageRemoveBtn = document.getElementById("image-remove");
const imagePreview = document.getElementById("image-preview");
const saveButton = document.getElementById("save-memory");

function formatDate(value) {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function getExcerpt(text) {
  const cleaned = (text || "").trim();
  if (!cleaned) return "Sans texte";
  return cleaned.length > 72 ? `${cleaned.slice(0, 72)}…` : cleaned;
}

function autosizeTextarea() {
  textInput.style.height = "auto";
  const maxHeight = parseFloat(window.getComputedStyle(textInput).maxHeight) || Infinity;
  const nextHeight = Math.min(textInput.scrollHeight, maxHeight);
  textInput.style.height = `${nextHeight}px`;
  textInput.style.overflowY = textInput.scrollHeight > maxHeight ? "auto" : "hidden";
}

function syncSaveState() {
  const hasText = textInput.value.trim().length > 0;
  const hasAudio = audioState === "recorded";
  const hasImage = Boolean(imageUrl);
  saveButton.disabled = !(hasText || hasAudio || hasImage);
}

function setAudioState(nextState) {
  audioState = nextState;

  if (audioState === "idle") {
    audioButton.textContent = "Enregistrer ma voix";
    audioStatus.textContent = "Aucun audio";
  } else if (audioState === "recording") {
    audioButton.textContent = "Stop (simulation)";
    audioStatus.textContent = "Enregistrement…";
  } else {
    audioButton.textContent = "Réenregistrer";
    audioStatus.textContent = "Audio ajouté";
  }

  syncSaveState();
}

function renderImagePreview() {
  if (!imageUrl) {
    imagePreview.innerHTML = "<p>Pas d'image ajoutée.</p>";
    imageRemoveBtn.disabled = true;
  } else {
    imagePreview.innerHTML = `<img src="${imageUrl}" alt="Aperçu de la photo du souvenir" />`;
    imageRemoveBtn.disabled = false;
  }

  syncSaveState();
}

function renderTimeline() {
  const sorted = [...memories].sort((a, b) => new Date(b.date) - new Date(a.date));

  timelineList.innerHTML = sorted
    .map((memory) => {
      const indicators = [memory.audio ? "🎙" : "", memory.image ? "🖼" : ""]
        .filter(Boolean)
        .join(" ");

      return `
        <button class="timeline-item ${memory.id === currentMemoryId ? "is-active" : ""}" data-id="${memory.id}" type="button">
          <p class="meta">${formatDate(memory.date)} ${indicators}</p>
          <p class="excerpt">${getExcerpt(memory.text)}</p>
        </button>
      `;
    })
    .join("");
}

function loadMemory(memoryId) {
  const memory = memories.find((item) => item.id === memoryId);
  if (!memory) return;

  currentMemoryId = memory.id;
  textInput.value = memory.text || "";
  setAudioState(memory.audio ? "recorded" : "idle");
  imageUrl = memory.image ? imageSamples[memory.id % imageSamples.length] : "";
  renderImagePreview();
  autosizeTextarea();
  renderTimeline();
}

function saveMemory() {
  const payload = {
    text: textInput.value.trim(),
    audio: audioState === "recorded",
    image: Boolean(imageUrl),
  };

  if (currentMemoryId) {
    const index = memories.findIndex((item) => item.id === currentMemoryId);
    if (index >= 0) {
      memories[index] = {
        ...memories[index],
        ...payload,
        date: new Date().toISOString().slice(0, 10),
      };
    }
  } else {
    const nextId = Math.max(0, ...memories.map((item) => item.id)) + 1;
    currentMemoryId = nextId;
    memories.push({
      id: nextId,
      ...payload,
      date: new Date().toISOString().slice(0, 10),
    });
  }

  renderTimeline();
}

textInput.addEventListener("input", () => {
  autosizeTextarea();
  syncSaveState();
});
window.addEventListener("resize", autosizeTextarea);

audioButton.addEventListener("click", () => {
  if (audioState === "idle") {
    setAudioState("recording");
  } else if (audioState === "recording") {
    setAudioState("recorded");
  } else {
    setAudioState("idle");
  }
});

imageAddBtn.addEventListener("click", () => {
  imageUrl = imageSamples[Math.floor(Math.random() * imageSamples.length)];
  renderImagePreview();
});

imageRemoveBtn.addEventListener("click", () => {
  imageUrl = "";
  renderImagePreview();
});

saveButton.addEventListener("click", saveMemory);

timelineList.addEventListener("click", (event) => {
  const item = event.target.closest(".timeline-item");
  if (!item) return;
  loadMemory(Number(item.dataset.id));
});

timelineToggle.addEventListener("click", () => {
  const open = timelinePanel.classList.toggle("is-open");
  timelineToggle.setAttribute("aria-expanded", String(open));
});

renderTimeline();
loadMemory(memories[0].id);
