"""
TecoQC - Paso 9: Prueba de audio (altavoces + micrófono)
"""

import tkinter as tk
import threading
import math
import struct
import wave
import io
import os

from ui.steps.base_step import BaseStep
from ui.components import Card
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, AUDIO_FREQUENCY, AUDIO_DURATION


class Step(BaseStep):
    TITLE = "Prueba de Audio"
    DESCRIPTION = "Prueba de altavoces (tono de prueba) y detección de micrófono."
    STEP_NUM = 9

    def build_ui(self, parent):
        cols = tk.Frame(parent, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # ── Speakers ──────────────────────────────────────────────────
        spk_card = Card(cols)
        spk_card.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        tk.Label(spk_card, text="Altavoces",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))

        tk.Frame(spk_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        spk_inner = tk.Frame(spk_card, bg=theme.BG_SURFACE0)
        spk_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(spk_inner,
                 text="Haga clic en 'Reproducir tono' para escuchar un tono de 440 Hz.\n"
                      "Pruebe con diferentes frecuencias para verificar el espectro de audio.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, wraplength=300, justify="left").pack(anchor="w", pady=(0, 12))

        # Frequency selector
        freq_frame = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        freq_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(freq_frame, text="Frecuencia:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(side=tk.LEFT)

        self._freq_var = tk.IntVar(value=AUDIO_FREQUENCY)
        freqs = [("200 Hz (Bajo)", 200), ("440 Hz (La)", 440),
                  ("1000 Hz (Medio)", 1000), ("4000 Hz (Alto)", 4000)]

        freq_sel = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        freq_sel.pack(fill=tk.X, pady=(0, 8))
        for label, val in freqs:
            tk.Radiobutton(
                freq_sel, text=label,
                variable=self._freq_var, value=val,
                bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                selectcolor=theme.BG_SURFACE1,
                font=theme.FONT_SMALL,
                activebackground=theme.BG_SURFACE0,
            ).pack(side=tk.LEFT, padx=4)

        # Play buttons
        btn_row = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        btn_row.pack(fill=tk.X, pady=(0, 12))

        tk.Button(btn_row, text="▶  Reproducir tono",
                   command=self._play_tone, **theme.BTN_PRIMARY).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(btn_row, text="▶▶  Tono continuo (3s)",
                   command=self._play_long_tone, **theme.BTN_SECONDARY).pack(side=tk.LEFT)

        self._spk_status_lbl = tk.Label(
            spk_inner, text="● Esperando prueba",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
        )
        self._spk_status_lbl.pack(anchor="w", pady=(4, 0))

        # Speaker device list
        tk.Label(spk_inner, text="Dispositivos de audio detectados:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(12, 4))

        self._spk_devices_lbl = tk.Label(
            spk_inner, text="Detectando...",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL, justify="left", anchor="w",
        )
        self._spk_devices_lbl.pack(anchor="w")

        # ── Microphone ────────────────────────────────────────────────
        mic_card = Card(cols)
        mic_card.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        tk.Label(mic_card, text="Micrófono",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))

        tk.Frame(mic_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        mic_inner = tk.Frame(mic_card, bg=theme.BG_SURFACE0)
        mic_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(mic_inner,
                 text="Detecte el micrófono del equipo e intente grabar\n"
                      "para verificar su funcionamiento.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, wraplength=280, justify="left").pack(anchor="w", pady=(0, 12))

        # Mic device list
        tk.Label(mic_inner, text="Micrófonos detectados:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 4))

        self._mic_devices_lbl = tk.Label(
            mic_inner, text="Detectando...",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL, justify="left", anchor="w",
            wraplength=280,
        )
        self._mic_devices_lbl.pack(anchor="w")

        # Level meter canvas
        tk.Label(mic_inner, text="Nivel de entrada (requiere sounddevice):",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(16, 4))

        self._level_canvas = tk.Canvas(mic_inner, height=24, bg=theme.BG_SURFACE1,
                                        highlightthickness=1,
                                        highlightbackground=theme.BG_SURFACE2)
        self._level_canvas.pack(fill=tk.X, pady=(0, 8))
        self._draw_level(0)

        mic_btn_row = tk.Frame(mic_inner, bg=theme.BG_SURFACE0)
        mic_btn_row.pack(fill=tk.X, pady=(4, 0))

        tk.Button(mic_btn_row, text="🎙 Probar micrófono (3s)",
                   command=self._test_mic, **theme.BTN_SECONDARY).pack(side=tk.LEFT, padx=(0, 8))

        self._mic_status_lbl = tk.Label(
            mic_inner, text="● Esperando prueba",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
        )
        self._mic_status_lbl.pack(anchor="w", pady=(8, 0))

        # Detect audio devices
        self.run_in_thread(self._get_audio_devices, on_done=self._show_audio_devices)

    def on_enter(self):
        pass

    def _get_audio_devices(self):
        speakers = []
        mics = []
        try:
            import wmi
            c = wmi.WMI()
            entities = c.Win32_PnPEntity()
            for e in entities:
                name = (e.Name or "").lower()
                pnp = (e.PNPClass or "").upper()
                if pnp in ("MEDIA", "SOUND"):
                    full_name = e.Name or "Dispositivo de audio"
                    if any(k in name for k in ("microphone", "micrófono", "mic", "input")):
                        mics.append(full_name)
                    else:
                        speakers.append(full_name)
        except Exception as ex:
            speakers.append(f"Error: {ex}")

        # Also try sounddevice
        sd_speakers = []
        sd_mics = []
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for d in devices:
                if d.get("max_output_channels", 0) > 0:
                    sd_speakers.append(d.get("name", ""))
                if d.get("max_input_channels", 0) > 0:
                    sd_mics.append(d.get("name", ""))
        except Exception:
            pass

        return {"speakers": speakers or sd_speakers, "mics": mics or sd_mics}

    def _show_audio_devices(self, data):
        speakers = data.get("speakers", [])
        mics = data.get("mics", [])

        spk_text = "\n".join(f"• {s[:45]}" for s in speakers[:5]) if speakers else "No detectados"
        mic_text = "\n".join(f"• {m[:45]}" for m in mics[:5]) if mics else "No detectados"

        self._spk_devices_lbl.configure(
            text=spk_text,
            fg=theme.TEXT_SECONDARY if speakers else theme.WARNING,
        )
        self._mic_devices_lbl.configure(
            text=mic_text,
            fg=theme.TEXT_SECONDARY if mics else theme.WARNING,
        )

    def _play_tone(self):
        freq = self._freq_var.get()
        self._spk_status_lbl.configure(
            text=f"► Reproduciendo {freq} Hz...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_play_tone,
                          args=(freq, AUDIO_DURATION // 1000),
                          daemon=True).start()

    def _play_long_tone(self):
        freq = self._freq_var.get()
        self._spk_status_lbl.configure(
            text=f"► Reproduciendo {freq} Hz (3s)...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_play_tone, args=(freq, 3), daemon=True).start()

    def _do_play_tone(self, frequency, duration_s):
        played = False

        # Try winsound
        try:
            import winsound
            winsound.Beep(frequency, duration_s * 1000)
            played = True
        except Exception:
            pass

        # Try sounddevice
        if not played:
            try:
                import sounddevice as sd
                import numpy as np
                sample_rate = 44100
                t = (1.0 / sample_rate) * \
                    (sample_rate * duration_s)
                samples = 0.5 * (
                    (lambda: __import__("numpy").sin(
                        2 * __import__("numpy").pi * frequency *
                        __import__("numpy").linspace(0, duration_s, int(sample_rate * duration_s))))()
                )
                sd.play(samples, sample_rate)
                sd.wait()
                played = True
            except Exception:
                pass

        # Write a WAV and open it
        if not played:
            try:
                sample_rate = 44100
                num_samples = int(sample_rate * duration_s)
                data = bytes([
                    int(127.5 * math.sin(2 * math.pi * frequency * t / sample_rate) + 127.5)
                    for t in range(num_samples)
                ])
                tmp_path = os.path.join(os.environ.get("TEMP", "."), "_tecoqc_tone.wav")
                with wave.open(tmp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(1)
                    wf.setframerate(sample_rate)
                    wf.writeframes(data)
                import subprocess
                subprocess.Popen(["start", tmp_path], shell=True)
                played = True
            except Exception:
                pass

        def update():
            if played:
                self._spk_status_lbl.configure(
                    text="✓ Tono reproducido — ¿Escuchó el tono?",
                    fg=theme.SUCCESS)
            else:
                self._spk_status_lbl.configure(
                    text="⚠ No se pudo reproducir audio automáticamente.\n"
                         "Pruebe manualmente reproduciendo un archivo de audio.",
                    fg=theme.WARNING)

        self.after(0, update)

    def _test_mic(self):
        self._mic_status_lbl.configure(
            text="🎙 Grabando 3 segundos...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_test_mic, daemon=True).start()

    def _do_test_mic(self):
        recorded = False
        level = 0

        try:
            import sounddevice as sd
            import numpy as np
            sample_rate = 44100
            duration = 3
            recording = sd.rec(int(duration * sample_rate),
                                samplerate=sample_rate, channels=1)
            sd.wait()
            level = float(np.abs(recording).mean()) * 1000
            recorded = True
        except ImportError:
            pass
        except Exception as e:
            self.after(0, lambda: self._mic_status_lbl.configure(
                text=f"Error de micrófono: {e}", fg=theme.ERROR))
            return

        def update():
            if recorded:
                self._draw_level(min(level * 100, 100))
                if level > 0.5:
                    self._mic_status_lbl.configure(
                        text=f"✓ Micrófono activo — Nivel: {level:.1f}",
                        fg=theme.SUCCESS)
                else:
                    self._mic_status_lbl.configure(
                        text="⚠ Nivel muy bajo — Hable más fuerte o verifique el micrófono",
                        fg=theme.WARNING)
            else:
                self._mic_status_lbl.configure(
                    text="⚠ sounddevice no disponible.\n"
                         "Instale: pip install sounddevice\n"
                         "Verificación manual requerida.",
                    fg=theme.WARNING)

        self.after(0, update)

    def _draw_level(self, pct):
        w = self._level_canvas.winfo_width() or 300
        h = 24
        self._level_canvas.delete("all")
        self._level_canvas.create_rectangle(0, 0, w, h,
                                              fill=theme.BG_SURFACE1, outline="")
        fill_w = int(w * max(0, min(pct, 100)) / 100)
        if fill_w > 0:
            color = (theme.SUCCESS if pct < 70
                      else theme.WARNING if pct < 90
                      else theme.ERROR)
            self._level_canvas.create_rectangle(0, 2, fill_w, h-2,
                                                  fill=color, outline="")
