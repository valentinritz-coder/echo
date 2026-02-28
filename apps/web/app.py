from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import requests
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))

from api_client import API_BASE_URL, APIClient, ApiClientError

PROJECT_NAME = "echo-mvp"
ALLOWED_AUDIO_TYPES = ["mp3", "m4a", "wav", "ogg", "webm", "aac", "3gp"]
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]
PAGE_LIMIT = 10

st.set_page_config(page_title=PROJECT_NAME, layout="wide")
st.title("Echo MVP (capsule de vie)")

if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "login_email" not in st.session_state:
    st.session_state.login_email = ""
if "login_password" not in st.session_state:
    st.session_state.login_password = ""
if "entries_offset" not in st.session_state:
    st.session_state.entries_offset = 0
if "entries_limit" not in st.session_state:
    st.session_state.entries_limit = PAGE_LIMIT
if "last_page" not in st.session_state:
    st.session_state.last_page = False


@st.cache_data(show_spinner=False, max_entries=512)
def fetch_protected_bytes(url: str, token: str) -> bytes:
    return APIClient(token).fetch_bytes(url)


def format_created_at(value: str | None) -> str:
    if not value:
        return "Date inconnue"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return dt.strftime("%d/%m/%Y %H:%M")


def handle_api_error(exc: Exception) -> None:
    if isinstance(exc, ApiClientError) and exc.status_code == 401:
        st.error("Session expirée, merci de vous reconnecter.")
        st.session_state.access_token = ""
        fetch_protected_bytes.clear()
        st.rerun()
    st.error(str(exc))


def refresh_entries_page() -> None:
    fetch_protected_bytes.clear()
    st.rerun()


with st.sidebar:
    st.header("Session")
    st.session_state.login_email = st.text_input(
        "Email", value=st.session_state.login_email
    )
    st.session_state.login_password = st.text_input(
        "Mot de passe", value=st.session_state.login_password, type="password"
    )

    if st.button("Se connecter"):
        try:
            token = APIClient().login(
                st.session_state.login_email, st.session_state.login_password
            )
            st.session_state.access_token = token
            st.success("Connexion réussie")
        except (ApiClientError, requests.RequestException) as exc:
            st.error(f"Connexion refusée: {exc}")

    if st.session_state.access_token:
        st.success("Connecté")
        if st.button("Se déconnecter"):
            st.session_state.access_token = ""
            fetch_protected_bytes.clear()
            st.rerun()

    st.caption(f"ECHO_API_URL: {API_BASE_URL}")

if not st.session_state.access_token:
    st.info("Veuillez vous connecter")
    st.stop()

client = APIClient(st.session_state.access_token)

new_tab, list_tab = st.tabs(["New memory / Créer un souvenir", "List / Mes souvenirs"])

with new_tab:
    st.subheader("Créer un nouveau souvenir")
    try:
        question = client.get_today_question()
    except (ApiClientError, requests.RequestException) as exc:
        handle_api_error(exc)
        question = None

    if question:
        st.markdown(f"**{question.get('text', 'Question indisponible')}**")

        text_content = st.text_area(
            "Texte du souvenir", placeholder="Ajoutez un texte optionnel..."
        )
        audio_file = st.file_uploader(
            "Audio (optionnel)",
            type=ALLOWED_AUDIO_TYPES,
            accept_multiple_files=False,
        )
        image_files = st.file_uploader(
            "Images (optionnel)",
            type=ALLOWED_IMAGE_TYPES,
            accept_multiple_files=True,
        )

        if st.button("Save"):
            try:
                entry = client.create_entry(
                    question_id=question["id"],
                    text_content=text_content,
                    audio_file=audio_file,
                )
                entry_id = entry.get("id")
                if not entry_id:
                    raise ApiClientError("Réponse invalide: id d'entrée manquant")

                image_errors: list[str] = []
                for image in image_files or []:
                    try:
                        client.upload_image(entry_id, image)
                    except ApiClientError as image_exc:
                        if image_exc.status_code == 422:
                            image_errors.append(f"{image.name}: {image_exc}")
                        elif image_exc.status_code == 413:
                            image_errors.append(f"{image.name}: image trop volumineuse")
                        else:
                            image_errors.append(f"{image.name}: {image_exc}")

                if image_errors:
                    st.warning("Entrée créée, mais certaines images ont échoué :")
                    for err in image_errors:
                        st.write(f"- {err}")
                else:
                    st.success("Souvenir enregistré avec succès")

                refresh_entries_page()
            except (ApiClientError, requests.RequestException) as exc:
                handle_api_error(exc)

with list_tab:
    st.subheader("Mes souvenirs")

    left, right = st.columns([1, 2])
    with left:
        if st.button("Prev", disabled=st.session_state.entries_offset == 0):
            st.session_state.entries_offset = max(
                0, st.session_state.entries_offset - st.session_state.entries_limit
            )
            refresh_entries_page()
    with right:
        if st.button("Next", disabled=st.session_state.last_page):
            if not st.session_state.last_page:
                st.session_state.entries_offset += st.session_state.entries_limit
                refresh_entries_page()

    st.caption(
        f"offset={st.session_state.entries_offset} · limit={st.session_state.entries_limit}"
    )

    try:
        entries = client.list_entries(
            limit=st.session_state.entries_limit, offset=st.session_state.entries_offset
        )
    except (ApiClientError, requests.RequestException) as exc:
        handle_api_error(exc)
        entries = []

    st.session_state.last_page = len(entries) < st.session_state.entries_limit

    if not entries:
        st.write("Aucun souvenir sur cette page.")

    for entry in entries:
        with st.container(border=True):
            st.markdown(f"**{format_created_at(entry.get('created_at'))}**")
            text_content = entry.get("text_content")
            if text_content:
                st.write(text_content)

            assets = entry.get("assets") or []
            if assets:
                st.write("Images")
                cols = st.columns(3)
                for idx, asset in enumerate(assets):
                    download_url = asset.get("download_url")
                    if not download_url:
                        continue
                    with cols[idx % 3]:
                        try:
                            image_bytes = fetch_protected_bytes(
                                download_url, st.session_state.access_token
                            )
                            st.image(image_bytes, use_container_width=True)
                        except (ApiClientError, requests.RequestException) as exc:
                            st.error(f"Image indisponible: {exc}")

            audio_url = entry.get("audio_url")
            if audio_url:
                try:
                    audio_bytes = fetch_protected_bytes(
                        audio_url, st.session_state.access_token
                    )
                    st.audio(audio_bytes, format=entry.get("audio_mime") or None)
                except (ApiClientError, requests.RequestException) as exc:
                    st.error(f"Audio indisponible: {exc}")
