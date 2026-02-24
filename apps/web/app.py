import os
from typing import Any

import requests
import streamlit as st

PROJECT_NAME = "echo-mvp"
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")
API_BASE_PATH = "/api/v1"
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

if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "login_email" not in st.session_state:
    st.session_state.login_email = os.getenv("ADMIN_EMAIL", "")
if "login_password" not in st.session_state:
    st.session_state.login_password = os.getenv("ADMIN_PASSWORD", "")


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
        response = requests.get(f"{API_BASE_URL}{API_BASE_PATH}/health", timeout=5)
        response.raise_for_status()
        st.success("API connectée")
    except requests.RequestException as exc:
        st.error(f"API indisponible: {exc}")


def auth_headers() -> dict[str, str]:
    if not st.session_state.access_token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def login() -> None:
    try:
        response = requests.post(
            f"{API_BASE_URL}{API_BASE_PATH}/auth/login",
            json={"email": st.session_state.login_email.strip(), "password": st.session_state.login_password},
            timeout=10,
        )
        if response.status_code >= 400:
            st.error(f"Connexion refusée: {api_json_error(response)}")
            return
        st.session_state.access_token = response.json().get("access_token", "")
        st.success("Connexion réussie")
    except requests.RequestException as exc:
        st.error(f"Erreur réseau pendant la connexion: {exc}")


def fetch_today_question() -> dict[str, Any] | None:
    try:
        response = requests.get(f"{API_BASE_URL}{API_BASE_PATH}/questions/today", headers=auth_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Impossible de charger la question: {exc}")
        return None


def upload_entry(question_id: int, uploaded_file: Any) -> None:
    try:
        files = {"audio_file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"question_id": str(question_id)}
        response = requests.post(
            f"{API_BASE_URL}{API_BASE_PATH}/entries",
            data=data,
            files=files,
            headers=auth_headers(),
            timeout=30,
        )
        if response.status_code >= 400:
            st.error(f"Upload refusé: {api_json_error(response)}")
            return
        st.success("Entrée créée avec succès")
    except requests.RequestException as exc:
        st.error(f"Erreur réseau pendant l'upload: {exc}")


def list_entries() -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{API_BASE_URL}{API_BASE_PATH}/entries", headers=auth_headers(), timeout=10)
        if response.status_code >= 400:
            st.error(f"Impossible de charger la bibliothèque: {api_json_error(response)}")
            return []
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Erreur réseau: {exc}")
        return []


@st.cache_data(show_spinner=False, max_entries=128)
def fetch_audio_bytes(entry_id: str, access_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    response = requests.get(f"{API_BASE_URL}{API_BASE_PATH}/entries/{entry_id}/audio", headers=headers, timeout=30)
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
        response = requests.delete(f"{API_BASE_URL}{API_BASE_PATH}/entries/{entry_id}", headers=auth_headers(), timeout=10)
        if response.status_code >= 400:
            st.error(f"Suppression impossible: {api_json_error(response)}")
            return
        fetch_audio_bytes.clear()
        st.success("Entrée supprimée")
    except requests.RequestException as exc:
        st.error(f"Erreur réseau: {exc}")


with st.sidebar:
    st.header("Session")
    st.session_state.login_email = st.text_input("Email", value=st.session_state.login_email)
    st.session_state.login_password = st.text_input("Mot de passe", value=st.session_state.login_password, type="password")
    if st.button("Se connecter"):
        login()
    if st.session_state.access_token:
        st.success("Connecté")
        if st.button("Se déconnecter"):
            st.session_state.access_token = ""
            fetch_audio_bytes.clear()
            st.rerun()
    st.caption(f"API_BASE_URL: {API_BASE_URL}")

check_api_health()

if not st.session_state.access_token:
    st.info("Veuillez vous connecter")
    st.stop()

tab_question, tab_library = st.tabs(["Question du jour", "Bibliothèque"])

with tab_question:
    st.subheader("Répondre à la question")
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
                upload_entry(question["id"], uploaded)

with tab_library:
    st.subheader("Mes entrées")
    entries = list_entries()
    if not entries:
        st.write("Aucune entrée pour le moment.")
    for entry in entries:
        with st.container(border=True):
            st.write(f"Entry: `{entry['id']}`")
            st.write(f"Question ID: {entry['question_id']} · Taille: {entry['audio_size']} octets")
            if st.button("▶ Lire", key=f"play-{entry['id']}"):
                try:
                    audio_bytes = fetch_audio_bytes(entry["id"], st.session_state.access_token)
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
