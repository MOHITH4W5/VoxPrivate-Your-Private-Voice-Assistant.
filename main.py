"""
main.py
Entry point for VoxPrivate — launches the GUI and starts the assistant.
"""

import sys
import os

# Ensure project root is in path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    from src.utils.config import Config
    from voiceprivate import VoiceAssistant

    config = Config.from_file()

    # Check if running in headless mode (no display / --headless flag)
    headless = "--headless" in sys.argv or "--cli" in sys.argv

    if headless:
        print("Running in headless/CLI mode.")
        assistant = VoiceAssistant(gui=None)
        assistant.listen()
    else:
        try:
            import tkinter as tk
            from src.gui.app import VoxPrivateApp
        except ImportError:
            print("tkinter not available. Falling back to headless mode.")
            assistant = VoiceAssistant(gui=None)
            assistant.listen()
            return

        # Create GUI first so we can wire callbacks
        gui = VoxPrivateApp(assistant=None)
        assistant = VoiceAssistant(gui=gui)
        gui.assistant = assistant  # wire assistant back

        # Show loading status
        gui.set_status("loading")
        gui.log("VoxPrivate starting up…")
        gui.log("Click the microphone or press Ctrl+Alt+V to start.")

        # Register global hotkey in background
        def _register_hotkey():
            try:
                import keyboard
                hotkey = config.get("hotkey", default="ctrl+alt+v")
                keyboard.add_hotkey(hotkey, assistant.toggle_listening)
                gui.log(f"Hotkey registered: {hotkey}")
            except Exception as e:
                gui.log(f"Hotkey not available: {e}")

        import threading
        threading.Thread(target=_register_hotkey, daemon=True).start()

        gui.set_status("idle")
        gui.log("Ready. Speak your command!")

        # Announce startup via TTS (in background so GUI opens first)
        def _announce():
            import time
            time.sleep(1.5)
            assistant._tts.speak("VoxPrivate is ready. Click the microphone to start.")

        threading.Thread(target=_announce, daemon=True).start()

        gui.run()


if __name__ == "__main__":
    main()
