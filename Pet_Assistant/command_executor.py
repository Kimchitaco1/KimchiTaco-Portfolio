import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

from text_utils import normalize_text


MEDIA_KEYS = {"next": 0xB0, "previous": 0xB1, "play_pause": 0xB3}
WINDOW_OPS = {"maximize": 3, "minimize": 2, "restore": 9}
WM_CLOSE = 0x0010
KEYEVENTF_KEYUP = 0x0002

INTENTS = {}
APPS = {}
ALLOW_APP_SEARCH = True
FOCUS_EXISTING = True


@dataclass
class CommandResult:
    command: str
    action: str
    ok: bool = True
    message: str = ""


def configure_commands(
    commands=None,
    apps=None,
    intents=None,
    allow_windows_app_search=True,
    focus_existing_apps=True,
):
    global APPS, INTENTS, ALLOW_APP_SEARCH, FOCUS_EXISTING
    APPS = {
        app_id: {
            **app,
            "id": app_id,
            "aliases": [normalize_text(a) for a in app.get("aliases", [app_id])],
        }
        for app_id, app in (apps or {}).items()
    }
    INTENTS = {
        intent: [normalize_text(phrase) for phrase in phrases]
        for intent, phrases in (intents or {}).items()
    }
    ALLOW_APP_SEARCH = allow_windows_app_search
    FOCUS_EXISTING = focus_existing_apps


def process_command(text, logger=None):
    command_text = normalize_text(text)
    try:
        result = process_dynamic(command_text)
        if result:
            return result
    except Exception as exc:
        if logger:
            logger.exception("Command failed: %s", command_text)
        return CommandResult(command_text, "unknown", ok=False, message=str(exc))

    if logger:
        logger.info("Ignored unrecognized command: %s", command_text)
    return None


def process_dynamic(command_text):
    app = resolve_app_alias(extract_launch_target(command_text) or command_text)
    if app:
        return launch_app(command_text, app)

    percent = extract_volume_percent(command_text)
    if percent is not None:
        return set_volume(command_text, percent)

    intent_actions = {
        "volume_up": lambda: change_volume(command_text, 10),
        "volume_down": lambda: change_volume(command_text, -10),
        "mute": lambda: set_mute(command_text, True),
        "unmute": lambda: set_mute(command_text, False),
        "media_next": lambda: media_key(command_text, "next"),
        "media_previous": lambda: media_key(command_text, "previous"),
        "media_play_pause": lambda: media_key(command_text, "play_pause"),
        "window_maximize": lambda: window_action(command_text, "maximize"),
        "window_minimize": lambda: window_action(command_text, "minimize"),
        "window_restore": lambda: window_action(command_text, "restore"),
        "window_close": lambda: window_action(command_text, "close"),
        "lock": lambda: lock_workstation(command_text),
        "shutdown": lambda: CommandResult(command_text, "shutdown"),
    }
    for intent, action in intent_actions.items():
        if command_text in INTENTS.get(intent, []):
            return action()
    return None


def extract_launch_target(command_text):
    for verb in INTENTS.get("launch_verbs", []):
        if command_text.startswith(f"{verb} "):
            return strip_articles(command_text[len(verb) :])
    return ""


def extract_volume_percent(command_text):
    for phrase in INTENTS.get("volume_set", []):
        if command_text.startswith(f"{phrase} "):
            return parse_percent(command_text[len(phrase) :])
    match = re.fullmatch(
        r"(?:pon|poner|ajusta|ajustar|sube|baja) (?:el )?volumen(?: al| a| en)? (.+)",
        command_text,
    )
    return parse_percent(match.group(1)) if match else None


def launch_app(command_text, app):
    if app.get("focus_existing", FOCUS_EXISTING):
        focused = focus_existing_app(command_text, app)
        if focused.ok:
            return focused

    errors = []
    for candidate in app.get("candidates", []):
        result = launch_candidate(command_text, candidate)
        if result.ok:
            result.message = f"Abriendo {app.get('name') or app.get('id') or 'app'}"
            return result
        errors.append(result.message)
    return CommandResult(command_text, "launch", ok=False, message="; ".join(errors))


def launch_candidate(command_text, candidate):
    candidate_type = candidate.get("type", "exe")
    if candidate_type in {"uri", "settings"}:
        return open_uri(command_text, candidate.get("uri"))
    if candidate_type == "app_id":
        return shell_open(command_text, "explorer.exe", [f"shell:AppsFolder\\{candidate.get('target')}"])
    if candidate_type == "shortcut":
        shortcut = find_shortcut(candidate.get("name"))
        return open_file(command_text, shortcut) if shortcut else fail(command_text, f"No encontré acceso directo: {candidate.get('name')}")
    if candidate_type == "exe":
        target = candidate.get("target")
        opened = shell_open(command_text, target, candidate.get("args"))
        if opened.ok:
            return opened
        executable = resolve_executable(target)
        return popen(command_text, executable, candidate.get("args")) if executable else fail(command_text, f"No encontré {target}")
    return fail(command_text, f"Tipo no soportado: {candidate_type}")


def shell_open(command_text, target, args=None):
    if not target:
        return fail(command_text, "Ejecutable vacío")
    import ctypes

    params = " ".join(str(arg) for arg in (args or [])) or None
    code = ctypes.windll.shell32.ShellExecuteW(None, "open", str(target), params, None, 1)
    return CommandResult(command_text, "launch", message="Abriendo") if code > 32 else fail(command_text, f"ShellExecute falló: {target}")


def popen(command_text, executable, args=None):
    subprocess.Popen(
        [executable, *[str(arg) for arg in (args or [])]],
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return CommandResult(command_text, "launch", message="Abriendo")


def open_uri(command_text, uri):
    if not uri or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9+.-]*:.*", uri):
        return fail(command_text, "URI inválida", "open_uri")
    result = shell_open(command_text, uri)
    result.action = "open_uri"
    return result if result.ok else open_file(command_text, uri, "open_uri")


def open_file(command_text, path, action="launch"):
    try:
        os.startfile(path)
        return CommandResult(command_text, action, message="Abriendo")
    except OSError as exc:
        return fail(command_text, str(exc), action)


def change_volume(command_text, delta):
    endpoint = endpoint_volume()
    level = max(0.0, min(1.0, endpoint.GetMasterVolumeLevelScalar() + float(delta) / 100))
    endpoint.SetMasterVolumeLevelScalar(level, None)
    endpoint.SetMute(0 if level > 0 else 1, None)
    return CommandResult(command_text, "volume", message="Volumen ajustado")


def set_volume(command_text, percent):
    endpoint = endpoint_volume()
    endpoint.SetMasterVolumeLevelScalar(max(0.0, min(1.0, percent / 100)), None)
    endpoint.SetMute(0 if percent > 0 else 1, None)
    return CommandResult(command_text, "volume", message=f"Volumen al {percent} por ciento")


def set_mute(command_text, muted):
    endpoint_volume().SetMute(1 if muted else 0, None)
    return CommandResult(command_text, "mute", message="Silenciado" if muted else "Sonido activado")


def media_key(command_text, key):
    import ctypes

    virtual_key = MEDIA_KEYS.get(key)
    if not virtual_key:
        return fail(command_text, "Tecla multimedia desconocida", "media_key")
    ctypes.windll.user32.keybd_event(virtual_key, 0, 0, 0)
    ctypes.windll.user32.keybd_event(virtual_key, 0, KEYEVENTF_KEYUP, 0)
    return CommandResult(command_text, "media_key", message="Listo")


def window_action(command_text, operation):
    import ctypes

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return fail(command_text, "No hay ventana activa", "window")
    if operation == "close":
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    elif operation in WINDOW_OPS:
        ctypes.windll.user32.ShowWindow(hwnd, WINDOW_OPS[operation])
    else:
        return fail(command_text, "Operación desconocida", "window")
    return CommandResult(command_text, "window", message="Listo")


def lock_workstation(command_text):
    import ctypes

    if not ctypes.windll.user32.LockWorkStation():
        raise ctypes.WinError()
    return CommandResult(command_text, "lock", message="Bloqueando equipo")


def focus_existing_app(command_text, app):
    hwnd = find_window_by_executable(executable_names(app))
    if not hwnd:
        return fail(command_text, "No hay ventana abierta", "focus")
    import ctypes

    ctypes.windll.user32.ShowWindow(hwnd, WINDOW_OPS["restore"])
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    return CommandResult(command_text, "focus", message=f"Mostrando {app.get('name') or app.get('id')}")


def find_window_by_executable(names):
    if not names:
        return None
    import ctypes
    from ctypes import wintypes

    found = []
    user32 = ctypes.windll.user32
    proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    names = {name.lower() for name in names}

    def visit(hwnd, _):
        if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd):
            path = process_path(hwnd)
            if path and os.path.basename(path).lower() in names:
                found.append(hwnd)
                return False
        return True

    user32.EnumWindows(proc_type(visit), 0)
    return found[0] if found else None


def process_path(hwnd):
    import ctypes
    from ctypes import wintypes

    process_id = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, process_id.value)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        return buffer.value if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)) else None
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def resolve_app_alias(target):
    target = strip_articles(target)
    for app in APPS.values():
        if target in app.get("aliases", []):
            return app
    return discover_windows_app(target) if ALLOW_APP_SEARCH else None


def discover_windows_app(name):
    if not name:
        return None
    candidates = []
    exe = name if name.endswith(".exe") else f"{name}.exe"
    if resolve_executable(exe):
        candidates.append({"type": "exe", "target": exe})
    if find_shortcut(name):
        candidates.append({"type": "shortcut", "name": name})
    start_app = find_start_app(name)
    if start_app:
        candidates.append({"type": "app_id", "target": start_app["AppID"]})
    return {"id": name, "name": start_app["Name"] if start_app else name.title(), "aliases": [name], "candidates": candidates} if candidates else None


def find_start_app(name):
    env = {**os.environ, "CATVIS_APP_QUERY": name}
    command = (
        "$q=$env:CATVIS_APP_QUERY; Get-StartApps | "
        "Where-Object { ($_.Name -ieq $q) -or ($_.Name -like \"*$q*\") } | "
        "Select-Object -First 1 Name,AppID | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=3,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        data = json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else {}
        return data if isinstance(data, dict) and data.get("AppID") else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def find_shortcut(name):
    roots = [
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    ]
    name = normalize_text(name)
    for root in filter(os.path.isdir, roots):
        for current_dir, _, files in os.walk(root):
            for file_name in files:
                shortcut_name = normalize_text(os.path.splitext(file_name)[0])
                if file_name.lower().endswith(".lnk") and (name == shortcut_name or name in shortcut_name):
                    return os.path.join(current_dir, file_name)
    return None


def executable_names(app):
    return [
        os.path.basename(candidate.get("target", "")).lower()
        for candidate in app.get("candidates", [])
        if candidate.get("type", "exe") == "exe" and candidate.get("target")
    ]


def resolve_executable(target):
    if not target:
        return None
    if os.path.isabs(target) and os.path.exists(target):
        return target
    return shutil.which(target) or app_path(target)


def app_path(target):
    try:
        import winreg
    except ImportError:
        return None
    subkey = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{target}"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, subkey) as key:
                path, _ = winreg.QueryValueEx(key, None)
                return path if path and os.path.exists(path) else None
        except OSError:
            pass
    return None


def parse_percent(text):
    text = strip_articles(normalize_text(text).replace("%", "").replace("por ciento", "").replace("porciento", ""))
    if text.isdigit():
        value = int(text)
        return value if 0 <= value <= 100 else None
    return {
        "cero": 0, "uno": 1, "cinco": 5, "diez": 10, "quince": 15,
        "veinte": 20, "veinticinco": 25, "treinta": 30, "cuarenta": 40,
        "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80,
        "noventa": 90, "cien": 100,
    }.get(text)


def strip_articles(text):
    text = normalize_text(text)
    for prefix in ("el ", "la ", "los ", "las ", "al ", "a ", "en "):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def endpoint_volume():
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    speakers = AudioUtilities.GetSpeakers()
    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def fail(command_text, message, action="launch"):
    return CommandResult(command_text, action, ok=False, message=message)
