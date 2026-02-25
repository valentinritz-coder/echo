import hashlib
import os
from pathlib import Path
from typing import Optional
import wave

from fastapi import HTTPException, UploadFile

CHUNK_SIZE = 1024 * 1024

ALLOWED_MIME_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "audio/3gpp": ".3gp",
    "audio/3gpp2": ".3g2",
    "audio/webm": ".webm",
    "audio/aiff": ".aiff",
}

ALLOWED_EXTENSIONS_BY_MIME = {
    "audio/mp4": {".m4a", ".mp4"},
    "audio/x-m4a": {".m4a", ".mp4"},
    "audio/ogg": {".ogg", ".oga"},
    "audio/aiff": {".aiff", ".aif"},
}

WAV_MIME_TYPES = {"audio/wav", "audio/x-wav"}
MP4_FAMILY_MIME_TYPES = {"audio/mp4", "audio/x-m4a", "audio/3gpp", "audio/3gpp2"}


def _has_mp3_signature(header: bytes) -> bool:
    if header.startswith(b"ID3"):
        return True
    if len(header) < 2:
        return False
    return header[0] == 0xFF and (header[1] & 0xE0) == 0xE0


def _has_wav_signature(header: bytes) -> bool:
    return len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WAVE"


def _has_ogg_signature(header: bytes) -> bool:
    return header.startswith(b"OggS")


def _has_mp4_signature(header: bytes) -> bool:
    return len(header) >= 8 and header[4:8] == b"ftyp"


def _has_webm_signature(header: bytes) -> bool:
    return header.startswith(b"\x1a\x45\xdf\xa3")


def _has_aac_adts_signature(header: bytes) -> bool:
    if len(header) < 2:
        return False
    if header[0] != 0xFF:
        return False
    return header[1] in {0xF1, 0xF9}


def has_valid_signature(header: bytes, mime_type: str) -> bool:
    if mime_type == "audio/mpeg":
        return _has_mp3_signature(header)
    if mime_type in WAV_MIME_TYPES:
        return _has_wav_signature(header)
    if mime_type == "audio/ogg":
        return _has_ogg_signature(header)
    if mime_type in MP4_FAMILY_MIME_TYPES:
        return _has_mp4_signature(header)
    if mime_type == "audio/webm":
        return _has_webm_signature(header)
    if mime_type == "audio/aac":
        return _has_aac_adts_signature(header)
    if mime_type == "audio/aiff":
        return (
            len(header) >= 12 and header.startswith(b"FORM") and header[8:12] == b"AIFF"
        )
    return False


def _try_get_wav_duration_ms(path: Path) -> Optional[int]:
    try:
        with wave.open(str(path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            if frame_rate <= 0:
                return None
            frames = wav_file.getnframes()
            return int((frames / frame_rate) * 1000)
    except (wave.Error, EOFError):
        return None


async def stream_upload_to_disk(
    upload: UploadFile,
    dst_path: Path,
    max_bytes: int,
    expected_mime: str,
    expected_ext: str,
) -> dict[str, Optional[int] | str]:
    suffix = Path(upload.filename or "").suffix.lower()
    allowed = ALLOWED_EXTENSIONS_BY_MIME.get(expected_mime, {expected_ext.lower()})
    if suffix not in allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_extension",
                "message": "Filename extension does not match MIME type",
            },
        )

    header = await upload.read(512)
    if not header or not has_valid_signature(header, expected_mime):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_signature",
                "message": "Audio signature does not match MIME type",
            },
        )

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dst_path.with_name(f"{dst_path.name}.{os.urandom(6).hex()}.tmp")
    size = 0
    digest = hashlib.sha256()

    try:
        with tmp_path.open("wb") as handle:
            size += len(header)
            if size > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "code": "payload_too_large",
                        "message": "Audio file exceeds upload size limit",
                    },
                )
            digest.update(header)
            handle.write(header)

            while True:
                to_read = min(CHUNK_SIZE, max(1, max_bytes - size + 1))
                chunk = await upload.read(to_read)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "code": "payload_too_large",
                            "message": "Audio file exceeds upload size limit",
                        },
                    )
                digest.update(chunk)
                handle.write(chunk)

        os.replace(tmp_path, dst_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    duration_ms = (
        _try_get_wav_duration_ms(dst_path) if expected_mime in WAV_MIME_TYPES else None
    )
    return {
        "sha256": digest.hexdigest(),
        "size": size,
        "duration_ms": duration_ms,
    }
