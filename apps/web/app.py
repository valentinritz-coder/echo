import os
from typing import Any

import requests
import streamlit as st

PROJECT_NAME = "echo-mvp"
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
ALLOWED_TYPES = ["mp3", "m4a", "mp4", "wav", "ogg"]
MIME_TO_EXT = {
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/webm": "webm",
    "audio/3gpp": "3gp",
}


st.set_page_config(page_title=PROJECT_NAME, layout="wide")
st.title("Echo MVP (capsule de vie)")

if "user_id" not in st.session_state:
    st.session_state.user_id = ""


with st.sidebar:
    st.header("Session")
    st.session_state.user_id = st.text_input("user_id", value=st.session_state.user_id)
    st.caption(f"API_BASE_URL: {API_BASE_URL}")


def api_json_error(response: requests.Response) -> str:
    try:
        payload = response.json()
        if "error" in payload:
            return payload["error"].get("message", str(payload["error"]))
        return str(payload)
    except ValueError:
        return response.text


def check_api_health() -> None:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        st.success("API connectée")
    except requests.RequestException as exc:
        st.error(f"API indisponible: {exc}")


def fetch_today_question() -> dict[str, Any] | None:
    try:
        response = requests.get(f"{API_BASE_URL}/questions/today", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Impossible de charger la question: {exc}")
        return None


def upload_entry(user_id: str, question_id: int, uploaded_file: Any) -> None:
    try:
        files = {"audio_file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"user_id": user_id, "question_id": str(question_id)}
        response = requests.post(f"{API_BASE_URL}/entries", data=data, files=files, timeout=30)
        if response.status_code >= 400:
            st.error(f"Upload refusé: {api_json_error(response)}")
            return
        st.success("Entrée créée avec succès")
    except requests.RequestException as exc:
        st.error(f"Erreur réseau pendant l'upload: {exc}")


def list_entries(user_id: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{API_BASE_URL}/entries", params={"user_id": user_id}, timeout=10)
        if response.status_code >= 400:
            st.error(f"Impossible de charger la bibliothèque: {api_json_error(response)}")
            return []
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Erreur réseau: {exc}")
        return []


@st.cache_data(show_spinner=False, max_entries=128)
def fetch_audio_bytes(entry_id: str) -> bytes:
    response = requests.get(f"{API_BASE_URL}/entries/{entry_id}/audio", timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(api_json_error(response))
    return response.content


def download_filename(entry: dict[str, Any]) -> str:
    mime = (entry.get("audio_mime") or "").lower()
    ext = MIME_TO_EXT.get(mime)
    if ext:
        return f"entry-{entry['id']}.{ext}"
    return f"entry-{entry['id']}"


def delete_entry(entry_id: str) -> None:
    try:
        response = requests.delete(f"{API_BASE_URL}/entries/{entry_id}", timeout=10)
        if response.status_code >= 400:
            st.error(f"Suppression impossible: {api_json_error(response)}")
            return
        fetch_audio_bytes.clear()
        st.success("Entrée supprimée")
    except requests.RequestException as exc:
        st.error(f"Erreur réseau: {exc}")


check_api_health()

tab_question, tab_library = st.tabs(["Question du jour", "Bibliothèque"])

with tab_question:
    st.subheader("Répondre à la question")
    if not st.session_state.user_id.strip():
        st.info("Renseignez un user_id dans la barre latérale pour continuer.")
    else:
        question = fetch_today_question()
        if question:
            st.markdown(f"**{question['text']}**")
            st.caption(f"Catégorie: {question['category']}")

            uploaded = st.file_uploader(
                "Ajoutez un audio (max 25MB)",
                type=ALLOWED_TYPES,
                accept_multiple_files=False,
            )
            if st.button("Envoyer", disabled=uploaded is None):
                if uploaded is None:
                    st.warning("Sélectionnez un fichier audio.")
                else:
                    upload_entry(st.session_state.user_id.strip(), question["id"], uploaded)

with tab_library:
    st.subheader("Mes entrées")
    if not st.session_state.user_id.strip():
        st.info("Renseignez un user_id pour afficher la bibliothèque.")
    else:
        entries = list_entries(st.session_state.user_id.strip())
        if not entries:
            st.write("Aucune entrée pour le moment.")
        for entry in entries:
            with st.container(border=True):
                st.write(f"Entry: `{entry['id']}`")
                st.write(f"Question ID: {entry['question_id']} · Taille: {entry['audio_size']} octets")
                if st.button("▶ Lire", key=f"play-{entry['id']}"):
                    try:
                        audio_bytes = fetch_audio_bytes(entry["id"])
                    except (requests.RequestException, RuntimeError) as exc:
                        st.error(f"Lecture impossible: {exc}")
                    else:
                        st.audio(audio_bytes, format=entry["audio_mime"])
                        st.download_button(
                            "Télécharger",
                            data=audio_bytes,
                            file_name=download_filename(entry),
                            mime=entry["audio_mime"],
                            key=f"download-{entry['id']}",
                        )
                if st.button("Supprimer", key=f"delete-{entry['id']}"):
                    delete_entry(entry["id"])
                    st.rerun()
