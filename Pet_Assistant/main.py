import json
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from app_config import BASE_DIR, load_config
from command_executor import configure_commands, process_command
from logging_setup import setup_logging
from speech_engine import SpeechEngine
from single_instance import SingleInstance
from ui_pet import PetWindow
from voice_engine import VoiceEngine


STATE_PATH = os.path.join(BASE_DIR, "catvis_state.json")
MUTEX_NAME = "Local\\CatvisVoiceAssistant"


def main():
    config = load_config()
    logger = setup_logging(config["logs_dir"])
    instance = SingleInstance(MUTEX_NAME)

    if not instance.acquire():
        _show_already_running_message()
        return

    stop_event = threading.Event()
    message_queue = queue.Queue()
    configure_commands(
        commands=config.get("commands", {}),
        apps=config.get("apps", {}),
        intents=config.get("intents", {}),
        allow_windows_app_search=config.get("allow_windows_app_search", True),
        focus_existing_apps=config.get("focus_existing_apps", True),
    )
    speech_config = config.get("speech", {})
    speech_engine = SpeechEngine(
        enabled=speech_config.get("enabled", True),
        rate=speech_config.get("rate", 155),
        volume=speech_config.get("volume", 0.85),
        preferred_voices=speech_config.get("preferred_voices"),
        require_preferred_voice=speech_config.get("require_preferred_voice", True),
        logger=logger,
    )

    shutdown_started = {"value": False}
    idle_after_id = {"value": None}
    position = _load_position()
    ui_config = config.get("ui", {})

    pet = PetWindow(
        image_paths=ui_config.get("images", {}),
        width=ui_config.get("width", 150),
        height=ui_config.get("height", 150),
        x=position.get("x", ui_config.get("x", 1700)),
        y=position.get("y", ui_config.get("y", 900)),
        transparent_color=ui_config.get("transparent_color", "black"),
    )

    voice_engine = VoiceEngine(
        config["model_path"],
        message_queue,
        stop_event=stop_event,
        wake_words=config.get("wake_words", ["catvis"]),
        command_timeout_seconds=config.get("command_timeout_seconds", 5),
        mic_retry_seconds=config.get("mic_retry_seconds", 5),
        max_mic_retries=config.get("max_mic_retries", 5),
    )

    def set_idle_later():
        if shutdown_started["value"]:
            return
        if idle_after_id["value"] is not None:
            pet.after_cancel(idle_after_id["value"])
        idle_after_id["value"] = pet.after(
            config.get("talking_duration_ms", 2000),
            lambda: pet.update_state("idle"),
        )

    def handle_message(message):
        if not isinstance(message, dict):
            logger.info("Ignoring legacy queue message: %s", message)
            return

        message_type = message.get("type")
        data = message.get("data")

        if message_type == "status":
            logger.info("Voice status: %s", data)
            _apply_status(pet, data)
            if data == "ready" and speech_config.get("speak_ready", False):
                speech_engine.say("Estoy lista")
            elif data == "listening":
                speech_engine.say("Dime")
            return

        if message_type == "error":
            logger.error("Voice error: %s detail=%s", data, message.get("detail"))
            pet.update_state("error")
            speech_engine.say("No puedo usar el micrófono")
            return

        if message_type == "transcript":
            logger.info("Transcript: %s", data)
            return

        if message_type != "command":
            logger.warning("Unknown queue message: %s", message)
            return

        text = str(data or "")
        logger.info("Recognized command candidate: %s", text)
        result = process_command(text, logger=logger)
        if result is None:
            pet.update_state("idle")
            if speech_config.get("speak_unrecognized", False):
                speech_engine.say("No tengo ese comando")
            return

        if result.ok:
            logger.info("Executed command: %s action=%s", result.command, result.action)
        else:
            logger.error(
                "Command failed: %s action=%s message=%s",
                result.command,
                result.action,
                result.message,
            )
            pet.update_state("error")
            speech_engine.say("No pude hacerlo")
            return

        if result.action == "shutdown":
            speech_engine.say("Hasta luego")
            shutdown()
            return

        speech_engine.say(result.message or "Hecho")
        pet.update_state("talking")
        set_idle_later()

    def poll_queue():
        if shutdown_started["value"]:
            return

        try:
            while True:
                handle_message(message_queue.get_nowait())
        except queue.Empty:
            pass

        pet.after(config.get("poll_interval_ms", 100), poll_queue)

    def toggle_mic(muted):
        voice_engine.set_muted(muted)
        logger.info("Microphone muted: %s", muted)

    def shutdown():
        if shutdown_started["value"]:
            return

        shutdown_started["value"] = True
        logger.info("Shutting down Catvis")
        _save_position(pet.get_position())
        stop_event.set()
        voice_engine.stop()
        speech_engine.stop()

        if voice_engine.thread and voice_engine.thread.is_alive():
            logger.warning("Voice thread did not stop within timeout")

        instance.release()
        pet.destroy()

    pet.on_exit = shutdown
    pet.on_toggle_mic = toggle_mic

    speech_engine.start()
    voice_engine.start()
    pet.after(config.get("poll_interval_ms", 100), poll_queue)
    pet.mainloop()


def _apply_status(pet, status):
    state_map = {
        "loading": "waking_up",
        "ready": "idle",
        "listening": "listening",
        "muted": "muted",
    }
    pet.update_state(state_map.get(status, "idle"))


def _load_position():
    if not os.path.exists(STATE_PATH):
        return {}

    try:
        with open(STATE_PATH, "r", encoding="utf-8") as state_file:
            return json.load(state_file)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_position(position):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as state_file:
            json.dump(position, state_file, indent=2)
    except OSError:
        pass


def _show_already_running_message():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Catvis", "Catvis ya se está ejecutando.")
    root.destroy()


if __name__ == "__main__":
    main()
