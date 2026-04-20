import os
import subprocess
from pathlib import Path
from uuid import uuid4

import requests
from PIL import Image


class TelegramBotLogic:
    AUDIO_TARGETS = {
        "audio_to_mp3": {"label": "MP3", "extension": "mp3", "mime": "audio/mpeg"},
        "audio_to_wav": {"label": "WAV", "extension": "wav", "mime": "audio/wav"},
        "audio_to_ogg": {"label": "OGG", "extension": "ogg", "mime": "audio/ogg"},
    }

    IMAGE_TARGETS = {
        "image_to_png": {"label": "PNG", "extension": "png", "pil_format": "PNG"},
        "image_to_jpg": {"label": "JPG", "extension": "jpg", "pil_format": "JPEG"},
        "image_to_webp": {"label": "WEBP", "extension": "webp", "pil_format": "WEBP"},
    }

    def __init__(self, token: str, workdir: str = "tmp"):
        self.token = token
        self.telegram_api = f"https://api.telegram.org/bot{token}"
        self.telegram_file_api = f"https://api.telegram.org/file/bot{token}"
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.user_states = {}

    def process_update(self, data: dict):
        if "message" in data:
            return self.handle_message(data["message"])
        if "callback_query" in data:
            return self.handle_callback_query(data["callback_query"])
        return "ignored"

    def handle_message(self, message: dict):
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        state = self.user_states.get(chat_id)

        if text == "/start":
            self.user_states.pop(chat_id, None)
            self.send_main_menu(chat_id)
            return "ok"

        if text == "/menu":
            self.send_main_menu(chat_id)
            return "ok"

        if state and state.get("mode") == "audio":
            if self.message_has_audio(message):
                return self.process_audio_message(chat_id, message, state)
            self.send_message(chat_id, "שלח קובץ שמע, הודעת קול או וידאו עם שמע כדי שאמיר אותו לפורמט שבחרת.")
            return "ok"

        if state and state.get("mode") == "image":
            if self.message_has_image(message):
                return self.process_image_message(chat_id, message, state)
            self.send_message(chat_id, "שלח תמונה או קובץ תמונה כדי שאמיר אותו לפורמט שבחרת.")
            return "ok"

        self.send_message(chat_id, "כדי להתחיל, לחץ על /start ובחר סוג המרה מהתפריט.")
        return "ok"

    def handle_callback_query(self, callback_query: dict):
        chat_id = callback_query["message"]["chat"]["id"]
        callback_data = callback_query["data"]
        callback_id = callback_query["id"]

        if callback_data == "menu_audio":
            self.send_audio_menu(chat_id)
            self.answer_callback_query(callback_id, "בחר פורמט יעד לשמע")
            return "ok"

        if callback_data == "menu_image":
            self.send_image_menu(chat_id)
            self.answer_callback_query(callback_id, "בחר פורמט יעד לתמונה")
            return "ok"

        if callback_data == "about":
            self.send_message(
                chat_id,
                "הבוט יודע להמיר קבצי שמע ותמונות. בחר סוג המרה, בחר פורמט יעד, ואז שלח את הקובץ המתאים.",
            )
            self.answer_callback_query(callback_id, "נשלח מידע על הבוט")
            return "ok"

        if callback_data == "back_to_main":
            self.send_main_menu(chat_id)
            self.answer_callback_query(callback_id, "חזרת לתפריט הראשי")
            return "ok"

        if callback_data in self.AUDIO_TARGETS:
            target = self.AUDIO_TARGETS[callback_data]
            self.user_states[chat_id] = {
                "mode": "audio",
                "target": target["extension"],
                "target_label": target["label"],
            }
            self.send_message(chat_id, f"מעולה. עכשיו שלח קובץ שמע ואמיר אותו ל-{target['label']}.")
            self.answer_callback_query(callback_id, f"פורמט היעד שנבחר: {target['label']}")
            return "ok"

        if callback_data in self.IMAGE_TARGETS:
            target = self.IMAGE_TARGETS[callback_data]
            self.user_states[chat_id] = {
                "mode": "image",
                "target": target["extension"],
                "target_label": target["label"],
            }
            self.send_message(chat_id, f"מעולה. עכשיו שלח תמונה ואמיר אותה ל-{target['label']}.")
            self.answer_callback_query(callback_id, f"פורמט היעד שנבחר: {target['label']}")
            return "ok"

        self.answer_callback_query(callback_id, "פעולה לא מזוהה")
        return "ok"

    def send_main_menu(self, chat_id: int):
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "המרת שמע", "callback_data": "menu_audio"},
                    {"text": "המרת תמונות", "callback_data": "menu_image"},
                ],
                [
                    {"text": "על הבוט", "callback_data": "about"},
                ],
            ]
        }
        self.send_message(chat_id, "בחר סוג המרה:", reply_markup=keyboard)

    def send_audio_menu(self, chat_id: int):
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "MP3", "callback_data": "audio_to_mp3"},
                    {"text": "WAV", "callback_data": "audio_to_wav"},
                    {"text": "OGG", "callback_data": "audio_to_ogg"},
                ],
                [
                    {"text": "חזרה", "callback_data": "back_to_main"},
                ],
            ]
        }
        self.send_message(chat_id, "בחר פורמט יעד לשמע:", reply_markup=keyboard)

    def send_image_menu(self, chat_id: int):
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "PNG", "callback_data": "image_to_png"},
                    {"text": "JPG", "callback_data": "image_to_jpg"},
                    {"text": "WEBP", "callback_data": "image_to_webp"},
                ],
                [
                    {"text": "חזרה", "callback_data": "back_to_main"},
                ],
            ]
        }
        self.send_message(chat_id, "בחר פורמט יעד לתמונה:", reply_markup=keyboard)

    def process_audio_message(self, chat_id: int, message: dict, state: dict):
        source = self.extract_audio_source(message)
        if not source:
            self.send_message(chat_id, "לא הצלחתי לזהות קובץ שמע. נסה לשלוח קובץ שמע, וידאו או הודעת קול.")
            return "ok"

        incoming_path = self.download_telegram_file(source["file_id"], source["filename"])
        output_path = incoming_path.with_suffix(f".{state['target']}")

        try:
            self.convert_audio(incoming_path, output_path)
            self.send_document(
                chat_id,
                output_path,
                caption=f"הנה קובץ השמע שלך בפורמט {state['target_label']}",
            )
        except Exception as exc:
            self.send_message(chat_id, f"המרת השמע נכשלה: {exc}")
        finally:
            self.cleanup_files(incoming_path, output_path)

        return "ok"

    def process_image_message(self, chat_id: int, message: dict, state: dict):
        source = self.extract_image_source(message)
        if not source:
            self.send_message(chat_id, "לא הצלחתי לזהות תמונה להמרה. נסה לשלוח תמונה או קובץ תמונה.")
            return "ok"

        incoming_path = self.download_telegram_file(source["file_id"], source["filename"])
        output_path = incoming_path.with_suffix(f".{state['target']}")

        try:
            self.convert_image(incoming_path, output_path, state['target'])
            self.send_document(
                chat_id,
                output_path,
                caption=f"הנה התמונה שלך בפורמט {state['target_label']}",
            )
        except Exception as exc:
            self.send_message(chat_id, f"המרת התמונה נכשלה: {exc}")
        finally:
            self.cleanup_files(incoming_path, output_path)

        return "ok"

    def message_has_audio(self, message: dict) -> bool:
        return any(key in message for key in ("audio", "voice", "video", "document"))

    def message_has_image(self, message: dict) -> bool:
        return "photo" in message or "document" in message

    def extract_audio_source(self, message: dict):
        if "audio" in message:
            audio = message["audio"]
            return {
                "file_id": audio["file_id"],
                "filename": audio.get("file_name") or f"audio_{uuid4().hex}.mp3",
            }

        if "voice" in message:
            voice = message["voice"]
            return {
                "file_id": voice["file_id"],
                "filename": f"voice_{uuid4().hex}.ogg",
            }

        if "video" in message:
            video = message["video"]
            return {
                "file_id": video["file_id"],
                "filename": video.get("file_name") or f"video_{uuid4().hex}.mp4",
            }

        if "document" in message:
            document = message["document"]
            mime_type = document.get("mime_type", "")
            filename = document.get("file_name") or f"audio_file_{uuid4().hex}"
            if mime_type.startswith("audio/") or filename.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".mp4")):
                return {"file_id": document["file_id"], "filename": filename}

        return None

    def extract_image_source(self, message: dict):
        if "photo" in message and message["photo"]:
            photo = message["photo"][-1]
            return {
                "file_id": photo["file_id"],
                "filename": f"photo_{uuid4().hex}.jpg",
            }

        if "document" in message:
            document = message["document"]
            mime_type = document.get("mime_type", "")
            filename = document.get("file_name") or f"image_file_{uuid4().hex}"
            if mime_type.startswith("image/") or filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff")):
                return {"file_id": document["file_id"], "filename": filename}

        return None

    def convert_audio(self, input_path: Path, output_path: Path):
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg failed")

    def convert_image(self, input_path: Path, output_path: Path, target_extension: str):
        image = Image.open(input_path)

        if target_extension == "jpg":
            image = image.convert("RGB")
        elif image.mode in ("P", "RGBA") and target_extension in {"png", "webp"}:
            image = image.convert("RGBA")

        target_format = self.IMAGE_TARGETS[f"image_to_{target_extension}"]["pil_format"]
        image.save(output_path, format=target_format)

    def download_telegram_file(self, file_id: str, filename: str) -> Path:
        response = requests.get(f"{self.telegram_api}/getFile", params={"file_id": file_id}, timeout=30)
        response.raise_for_status()
        file_path = response.json()["result"]["file_path"]

        safe_name = f"{uuid4().hex}_{Path(filename).name}"
        local_path = self.workdir / safe_name

        file_response = requests.get(f"{self.telegram_file_api}/{file_path}", timeout=60)
        file_response.raise_for_status()
        local_path.write_bytes(file_response.content)
        return local_path

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None):
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{self.telegram_api}/sendMessage", json=payload, timeout=30)

    def send_document(self, chat_id: int, file_path: Path, caption: str | None = None):
        with file_path.open("rb") as document_file:
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            requests.post(
                f"{self.telegram_api}/sendDocument",
                data=data,
                files={"document": document_file},
                timeout=120,
            )

    def answer_callback_query(self, callback_query_id: str, text: str):
        requests.post(
            f"{self.telegram_api}/answerCallbackQuery",
            json={
                "callback_query_id": callback_query_id,
                "text": text,
            },
            timeout=30,
        )

    def cleanup_files(self, *paths: Path):
        for path in paths:
            try:
                if path and path.exists():
                    path.unlink()
            except OSError:
                continue
