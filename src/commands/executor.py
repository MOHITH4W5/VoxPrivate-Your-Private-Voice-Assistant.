"""
src/commands/executor.py
Executes system actions based on recognized intent.
"""

import os
import sys
import platform
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Callable


SYSTEM = platform.system()  # 'Windows', 'Linux', 'Darwin'


class CommandExecutor:
    """
    Maps intents to system actions and returns a spoken response string.
    """

    HELP_TEXT = (
        "I can help you with: "
        "telling the time, today's date, opening the terminal, "
        "taking a screenshot, creating a file, opening the browser, "
        "playing music, adjusting the volume, and shutting down the computer."
    )

    def __init__(self, config, tts_engine=None):
        self.config = config
        self.tts = tts_engine
        # Optional callback to notify GUI of actions
        self.action_callback: Optional[Callable[[str], None]] = None

    def execute(self, intent: str, metadata: dict) -> str:
        """
        Execute the action for a given intent.
        Returns the spoken response string.
        """
        handlers = {
            "time": self._handle_time,
            "date": self._handle_date,
            "open_terminal": self._handle_open_terminal,
            "screenshot": self._handle_screenshot,
            "create_file": self._handle_create_file,
            "open_browser": self._handle_open_browser,
            "play_music": self._handle_play_music,
            "volume_up": self._handle_volume_up,
            "volume_down": self._handle_volume_down,
            "mute": self._handle_mute,
            "shutdown": self._handle_shutdown,
            "restart": self._handle_restart,
            "sleep": self._handle_sleep,
            "calculator": self._handle_calculator,
            "notepad": self._handle_notepad,
            "help": self._handle_help,
            "stop": self._handle_stop,
            "unknown": self._handle_unknown,
        }
        handler = handlers.get(intent, self._handle_unknown)
        try:
            response = handler(metadata)
        except Exception as e:
            response = f"Sorry, I encountered an error: {str(e)}"

        if self.action_callback:
            self.action_callback(response)
        return response

    # ── Individual Handlers ───────────────────────────────────────────────────

    def _handle_time(self, _) -> str:
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."

    def _handle_date(self, _) -> str:
        today = datetime.date.today()
        return f"Today is {today.strftime('%A, %B %d, %Y')}."

    def _handle_open_terminal(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("start cmd", shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            for term in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
                try:
                    subprocess.Popen([term])
                    break
                except FileNotFoundError:
                    continue
        return "Opening the terminal."

    def _handle_screenshot(self, _) -> str:
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot_dir = Path.home() / "Pictures"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            filepath = screenshot_dir / filename
            pyautogui.screenshot(str(filepath))
            return f"Screenshot saved to {filepath}."
        except Exception as e:
            return f"Could not take screenshot: {e}"

    def _handle_create_file(self, metadata: dict) -> str:
        filename = metadata.get("filename", "new_file.txt")
        filepath = Path.home() / "Desktop" / filename
        try:
            filepath.touch(exist_ok=True)
            return f"Created file {filename} on your Desktop."
        except Exception as e:
            return f"Could not create file: {e}"

    def _handle_open_browser(self, _) -> str:
        import webbrowser
        webbrowser.open("https://www.google.com")
        return "Opening your web browser."

    def _handle_play_music(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("start wmplayer", shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", "Music"])
        else:
            for player in ["rhythmbox", "banshee", "clementine", "vlc"]:
                try:
                    subprocess.Popen([player])
                    return f"Opening {player}."
                except FileNotFoundError:
                    continue
        return "Opening music player."

    def _handle_volume_up(self, _) -> str:
        if SYSTEM == "Windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
                return "Volume increased."
            except ImportError:
                import pyautogui
                for _ in range(5):
                    pyautogui.press("volumeup")
                return "Volume increased."
        return "Increasing volume."

    def _handle_volume_down(self, _) -> str:
        try:
            import pyautogui
            for _ in range(5):
                pyautogui.press("volumedown")
        except Exception:
            pass
        return "Volume decreased."

    def _handle_mute(self, _) -> str:
        try:
            import pyautogui
            pyautogui.press("volumemute")
        except Exception:
            pass
        return "Muted."

    def _handle_shutdown(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("shutdown /s /t 30", shell=True)
            return "Shutting down in 30 seconds. Say 'stop' to cancel."
        elif SYSTEM == "Darwin":
            subprocess.Popen(["sudo", "shutdown", "-h", "+1"])
        else:
            subprocess.Popen(["shutdown", "-h", "+1"])
        return "Shutdown initiated."

    def _handle_restart(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("shutdown /r /t 30", shell=True)
            return "Restarting in 30 seconds."
        return "Restart command issued."

    def _handle_sleep(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["pmset", "sleepnow"])
        else:
            subprocess.Popen(["systemctl", "suspend"])
        return "Going to sleep."

    def _handle_calculator(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("calc", shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
        else:
            for calc in ["gnome-calculator", "kcalc", "xcalc"]:
                try:
                    subprocess.Popen([calc])
                    break
                except FileNotFoundError:
                    continue
        return "Opening calculator."

    def _handle_notepad(self, _) -> str:
        if SYSTEM == "Windows":
            subprocess.Popen("notepad", shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", "TextEdit"])
        else:
            for editor in ["gedit", "kate", "nano", "mousepad"]:
                try:
                    subprocess.Popen([editor])
                    break
                except FileNotFoundError:
                    continue
        return "Opening text editor."

    def _handle_help(self, _) -> str:
        return self.HELP_TEXT

    def _handle_stop(self, _) -> str:
        return "Goodbye! See you next time."

    def _handle_unknown(self, _) -> str:
        return "Sorry, I didn't understand that. Say 'help' to hear what I can do."
