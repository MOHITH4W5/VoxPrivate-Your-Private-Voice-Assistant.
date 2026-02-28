"""
src/gui/app.py
Beautiful dark-mode tkinter GUI for VoxPrivate.
Features: animated microphone button, live waveform, transcription log, status bar.
"""

import tkinter as tk
from tkinter import ttk, font
import threading
import math
import time
import queue


# ── Colour Palette ────────────────────────────────────────────────────────────
BG_DARK   = "#0d1117"   # deep background
BG_CARD   = "#161b22"   # card / panel background
BG_PANEL  = "#1c2333"   # secondary panels
ACCENT_C  = "#00e5ff"   # neon cyan accent
ACCENT_G  = "#00ff88"   # neon green (active/speaking)
ACCENT_R  = "#ff4444"   # red (error / muted)
TEXT_HI   = "#e6edf3"   # primary text
TEXT_MID  = "#8b949e"   # secondary text
TEXT_DIM  = "#484f58"   # dim text
BORDER    = "#30363d"   # subtle border
PULSE_ON  = "#00e5ff"   # mic pulse colour while listening
PULSE_OFF = "#30363d"   # mic off colour


class WaveformCanvas(tk.Canvas):
    """Live animated waveform display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, highlightthickness=0, **kwargs)
        self._amplitude = 0
        self._bars = 40
        self._animate()

    def set_amplitude(self, amp: int):
        self._amplitude = min(amp, 4000)  # clamp

    def _animate(self):
        self.delete("all")
        w = self.winfo_width() or 400
        h = self.winfo_height() or 60
        bar_w = w / self._bars
        t = time.time() * 6

        for i in range(self._bars):
            # Base wave shape
            wave = math.sin(t + i * 0.5) * 0.5 + 0.5
            energy_factor = self._amplitude / 4000
            bar_h = max(4, int((wave * 0.4 + energy_factor * 0.6) * h * 0.85))

            x1 = int(i * bar_w) + 2
            x2 = int((i + 1) * bar_w) - 2
            y1 = h // 2 - bar_h // 2
            y2 = h // 2 + bar_h // 2

            # Gradient colour: cyan at centre, dimmer at edges
            dist = abs(i - self._bars // 2) / (self._bars // 2)
            alpha = 1 - dist * 0.7
            # Approximate colour brightness via interpolation
            r = int(0x00 * alpha)
            g = int(0xe5 * alpha + 0x30 * (1 - alpha))
            bb = int(0xff * alpha + 0x36 * (1 - alpha))
            colour = f"#{r:02x}{g:02x}{bb:02x}"
            self.create_rectangle(x1, y1, x2, y2, fill=colour, outline="")

        self.after(40, self._animate)  # ~25 fps


class MicButton(tk.Canvas):
    """Animated pulsing microphone button."""

    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, bg=BG_DARK, highlightthickness=0,
                         width=90, height=90, **kwargs)
        self._command = command
        self._listening = False
        self._pulse_radius = 35
        self._pulse_dir = 1
        self._draw()
        self._animate()
        self.bind("<Button-1>", self._on_click)

    def set_listening(self, state: bool):
        self._listening = state
        self._draw()

    def _draw(self):
        self.delete("all")
        cx, cy = 45, 45
        r_outer = 40

        # Outer glow ring (only when listening)
        if self._listening:
            pr = self._pulse_radius
            self.create_oval(cx - pr, cy - pr, cx + pr, cy + pr,
                             outline=PULSE_ON, width=2, dash=(4, 3))

        # Main circle
        colour = ACCENT_C if self._listening else BORDER
        self.create_oval(cx - 30, cy - 30, cx + 30, cy + 30,
                         fill=BG_CARD, outline=colour, width=2)

        # Microphone icon (simple shapes)
        mic_colour = ACCENT_C if self._listening else TEXT_MID
        # Body
        self.create_rectangle(cx - 8, cy - 18, cx + 8, cy + 2,
                               fill=mic_colour, outline="", width=0)
        self.create_oval(cx - 8, cy - 26, cx + 8, cy - 10,
                         fill=mic_colour, outline="")
        # Stand arc
        self.create_arc(cx - 14, cy - 8, cx + 14, cy + 14,
                        start=0, extent=-180, style=tk.ARC,
                        outline=mic_colour, width=2)
        # Stem
        self.create_line(cx, cy + 14, cx, cy + 22, fill=mic_colour, width=2)
        self.create_line(cx - 8, cy + 22, cx + 8, cy + 22, fill=mic_colour, width=2)

    def _animate(self):
        if self._listening:
            self._pulse_radius += self._pulse_dir * 0.6
            if self._pulse_radius > 42 or self._pulse_radius < 33:
                self._pulse_dir *= -1
            self._draw()
        self.after(30, self._animate)

    def _on_click(self, _event):
        if self._command:
            self._command()


class VoxPrivateApp:
    """Main GUI application for VoxPrivate."""

    STATUS_IDLE      = ("⬤  Idle — Press the mic or Ctrl+Alt+V", TEXT_MID)
    STATUS_LISTENING = ("🎙  Listening…", ACCENT_C)
    STATUS_THINKING  = ("⚙  Processing…", ACCENT_G)
    STATUS_SPEAKING  = ("🔊  Speaking…", "#ff9800")
    STATUS_LOADING   = ("⏳  Loading model (first run)…", TEXT_MID)

    def __init__(self, assistant):
        self.assistant = assistant
        self._msg_queue: queue.Queue = queue.Queue()
        self._root = tk.Tk()
        self._root.title("VoxPrivate — Your Private Voice Assistant")
        self._root.geometry("800x580")
        self._root.minsize(680, 480)
        self._root.configure(bg=BG_DARK)
        self._root.resizable(True, True)

        self._build_ui()
        self._poll_messages()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self._root, bg=BG_CARD, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        tk.Label(header, text="🎙 VoxPrivate", font=title_font,
                 bg=BG_CARD, fg=ACCENT_C).pack(side=tk.LEFT, padx=18, pady=12)

        sub_font = font.Font(family="Segoe UI", size=9)
        tk.Label(header, text="100% Offline · Privacy-First",
                 font=sub_font, bg=BG_CARD, fg=TEXT_MID).pack(side=tk.LEFT, pady=16)

        # Status badge (top right)
        self._status_var = tk.StringVar(value=self.STATUS_IDLE[0])
        self._status_label = tk.Label(header, textvariable=self._status_var,
                                      font=sub_font, bg=BG_CARD, fg=TEXT_MID)
        self._status_label.pack(side=tk.RIGHT, padx=18)

        # Main content area
        content = tk.Frame(self._root, bg=BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Left panel — mic + waveform
        left = tk.Frame(content, bg=BG_DARK, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        mic_frame = tk.Frame(left, bg=BG_CARD, relief=tk.FLAT,
                              bd=0, padx=12, pady=12)
        mic_frame.pack(fill=tk.X, pady=(0, 8))

        self._mic_btn = MicButton(mic_frame, command=self._toggle_listening)
        self._mic_btn.pack()

        listen_font = font.Font(family="Segoe UI", size=9)
        tk.Label(mic_frame, text="Click to Toggle\nCtrl+Alt+V",
                 font=listen_font, bg=BG_CARD, fg=TEXT_DIM).pack(pady=(4, 0))

        # Waveform
        wave_frame = tk.Frame(left, bg=BG_CARD, relief=tk.FLAT, bd=0)
        wave_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(wave_frame, text="Audio Level", font=listen_font,
                 bg=BG_CARD, fg=TEXT_DIM).pack(pady=(6, 2))
        self._waveform = WaveformCanvas(wave_frame, height=80)
        self._waveform.pack(fill=tk.X, padx=6, pady=(0, 6))

        # Right panel — transcript + history
        right = tk.Frame(content, bg=BG_DARK)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Transcription card
        trans_frame = tk.Frame(right, bg=BG_CARD, relief=tk.FLAT, bd=0)
        trans_frame.pack(fill=tk.X, pady=(0, 8))

        label_font = font.Font(family="Segoe UI", size=9, weight="bold")
        tk.Label(trans_frame, text="LAST TRANSCRIPTION",
                 font=label_font, bg=BG_CARD, fg=TEXT_DIM).pack(
                     anchor=tk.W, padx=10, pady=(8, 2))

        trans_text_font = font.Font(family="Segoe UI", size=13)
        self._trans_var = tk.StringVar(value="Say something…")
        tk.Label(trans_frame, textvariable=self._trans_var,
                 font=trans_text_font, bg=BG_CARD, fg=TEXT_HI,
                 wraplength=500, justify=tk.LEFT).pack(
                     anchor=tk.W, padx=10, pady=(0, 10))

        # Response card
        resp_frame = tk.Frame(right, bg=BG_CARD, relief=tk.FLAT, bd=0)
        resp_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(resp_frame, text="ASSISTANT RESPONSE",
                 font=label_font, bg=BG_CARD, fg=TEXT_DIM).pack(
                     anchor=tk.W, padx=10, pady=(8, 2))

        self._resp_var = tk.StringVar(value="Awaiting your command…")
        tk.Label(resp_frame, textvariable=self._resp_var,
                 font=trans_text_font, bg=BG_CARD, fg=ACCENT_G,
                 wraplength=500, justify=tk.LEFT).pack(
                     anchor=tk.W, padx=10, pady=(0, 10))

        # History log
        log_frame = tk.Frame(right, bg=BG_CARD, relief=tk.FLAT, bd=0)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="COMMAND HISTORY",
                 font=label_font, bg=BG_CARD, fg=TEXT_DIM).pack(
                     anchor=tk.W, padx=10, pady=(8, 2))

        text_font = font.Font(family="Consolas", size=10)
        self._log_text = tk.Text(
            log_frame, font=text_font, bg=BG_PANEL, fg=TEXT_MID,
            relief=tk.FLAT, bd=0, state=tk.DISABLED, wrap=tk.WORD,
            insertbackground=ACCENT_C, selectbackground=ACCENT_C,
            padx=8, pady=4,
        )
        scrollbar = tk.Scrollbar(log_frame, command=self._log_text.yview,
                                  bg=BG_PANEL, troughcolor=BG_PANEL,
                                  activebackground=ACCENT_C)
        self._log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 8))

        # Footer
        footer = tk.Frame(self._root, bg=BG_CARD, height=28)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        footer_font = font.Font(family="Segoe UI", size=8)
        tk.Label(footer, text="🔒 No data leaves this device  |  VoxPrivate",
                 font=footer_font, bg=BG_CARD, fg=TEXT_DIM).pack(side=tk.LEFT, padx=12, pady=6)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _toggle_listening(self):
        if self.assistant:
            self.assistant.toggle_listening()

    def set_status(self, status_key: str):
        statuses = {
            "idle":      self.STATUS_IDLE,
            "listening": self.STATUS_LISTENING,
            "thinking":  self.STATUS_THINKING,
            "speaking":  self.STATUS_SPEAKING,
            "loading":   self.STATUS_LOADING,
        }
        text, colour = statuses.get(status_key, self.STATUS_IDLE)
        self._msg_queue.put(("status", text, colour))

    def set_transcription(self, text: str):
        self._msg_queue.put(("trans", text))

    def set_response(self, text: str):
        self._msg_queue.put(("resp", text))

    def set_listening(self, state: bool):
        self._msg_queue.put(("mic", state))

    def set_amplitude(self, amp: int):
        # Called from audio thread — use queue for thread safety
        self._msg_queue.put(("amp", amp))

    def log(self, line: str):
        self._msg_queue.put(("log", line))

    # ── Message pump (runs in main thread via after()) ────────────────────────

    def _poll_messages(self):
        try:
            while True:
                msg = self._msg_queue.get_nowait()
                self._dispatch_message(msg)
        except queue.Empty:
            pass
        self._root.after(50, self._poll_messages)

    def _dispatch_message(self, msg):
        kind = msg[0]
        if kind == "status":
            self._status_var.set(msg[1])
            self._status_label.configure(fg=msg[2])
        elif kind == "trans":
            self._trans_var.set(msg[1])
        elif kind == "resp":
            self._resp_var.set(msg[1])
        elif kind == "mic":
            self._mic_btn.set_listening(msg[1])
        elif kind == "amp":
            self._waveform.set_amplitude(msg[1])
        elif kind == "log":
            self._log_text.configure(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            self._log_text.insert(tk.END, f"[{timestamp}]  {msg[1]}\n")
            self._log_text.see(tk.END)
            self._log_text.configure(state=tk.DISABLED)

    def run(self):
        self._root.mainloop()
