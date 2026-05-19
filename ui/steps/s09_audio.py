"""
TecoQC - Paso 9: Prueba de audio (altavoces estéreo + micrófono con noise floor)
"""

import tkinter as tk
import threading
import math
import wave
import os

from ui.steps.base_step import BaseStep
from ui.components import Card
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, AUDIO_FREQUENCY, AUDIO_DURATION


class Step(BaseStep):
    TITLE = "Prueba de Audio"
    DESCRIPTION = "Prueba de altavoces estéreo (L/R) y micrófono con detección de nivel vs. ruido."
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
                 text="Reproduzca tonos para verificar los canales. "
                      "Confirme si escucha cada tono correctamente.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, wraplength=300, justify="left").pack(anchor="w", pady=(0, 10))

        # Frequency selector
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

        # Stereo channel buttons
        chan_frame = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        chan_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Button(chan_frame, text="◄ Canal Izquierdo",
                   command=lambda: self._play_channel("left"),
                   bg=theme.ACCENT_BLUE, fg=theme.BG_CRUST,
                   font=theme.FONT_BODY_BOLD, relief="flat",
                   cursor="hand2", padx=12, pady=6,
                   ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(chan_frame, text="Canal Derecho ►",
                   command=lambda: self._play_channel("right"),
                   bg=theme.ACCENT_LAVENDER, fg=theme.BG_CRUST,
                   font=theme.FONT_BODY_BOLD, relief="flat",
                   cursor="hand2", padx=12, pady=6,
                   ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(chan_frame, text="▶ Ambos canales",
                   command=self._play_tone, **theme.BTN_PRIMARY).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(chan_frame, text="▶▶ Continuo (3s)",
                   command=self._play_long_tone, **theme.BTN_SECONDARY).pack(side=tk.LEFT)

        # Channel status indicators
        chan_status_row = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        chan_status_row.pack(fill=tk.X, pady=(4, 0))
        self._left_lbl = tk.Label(chan_status_row, text="◄ Izq: pendiente",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                   font=theme.FONT_SMALL)
        self._left_lbl.pack(side=tk.LEFT, padx=(0, 16))
        self._right_lbl = tk.Label(chan_status_row, text="Der ►: pendiente",
                                    bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                    font=theme.FONT_SMALL)
        self._right_lbl.pack(side=tk.LEFT)

        self._spk_status_lbl = tk.Label(
            spk_inner, text="● Esperando prueba",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
        )
        self._spk_status_lbl.pack(anchor="w", pady=(8, 0))

        # Manual confirm buttons for stereo
        confirm_row = tk.Frame(spk_inner, bg=theme.BG_SURFACE0)
        confirm_row.pack(fill=tk.X, pady=(6, 0))
        tk.Label(confirm_row, text="¿Escuchó ambos canales?",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(confirm_row, text="✓ Sí",
                   command=lambda: self._confirm_speaker(True),
                   bg=theme.SUCCESS, fg=theme.BG_BASE,
                   font=theme.FONT_SMALL, relief="flat", padx=8, pady=3,
                   cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(confirm_row, text="✗ No",
                   command=lambda: self._confirm_speaker(False),
                   bg=theme.ERROR, fg=theme.BG_BASE,
                   font=theme.FONT_SMALL, relief="flat", padx=8, pady=3,
                   cursor="hand2").pack(side=tk.LEFT, padx=2)

        self._spk_confirmed = None

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
                 text="Primero mide el ruido de fondo (1s silencio), luego graba\n"
                      "3s hablando para verificar el nivel de voz.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, wraplength=280, justify="left").pack(anchor="w", pady=(0, 10))

        tk.Label(mic_inner, text="Micrófonos detectados:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 4))
        self._mic_devices_lbl = tk.Label(
            mic_inner, text="Detectando...",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL, justify="left", anchor="w", wraplength=280,
        )
        self._mic_devices_lbl.pack(anchor="w")

        tk.Label(mic_inner, text="Nivel de entrada:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(12, 2))

        self._noise_lbl = tk.Label(mic_inner, text="Ruido de fondo: —",
                                    bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                    font=theme.FONT_SMALL)
        self._noise_lbl.pack(anchor="w", pady=(0, 4))

        self._level_canvas = tk.Canvas(mic_inner, height=24, bg=theme.BG_SURFACE1,
                                        highlightthickness=1,
                                        highlightbackground=theme.BG_SURFACE2)
        self._level_canvas.pack(fill=tk.X, pady=(0, 8))
        self._draw_level(0)

        mic_btn_row = tk.Frame(mic_inner, bg=theme.BG_SURFACE0)
        mic_btn_row.pack(fill=tk.X, pady=(4, 0))

        tk.Button(mic_btn_row, text="🔇 Medir ruido (1s)",
                   command=self._measure_noise, **theme.BTN_NEUTRAL).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(mic_btn_row, text="🎙 Probar micrófono (3s)",
                   command=self._test_mic, **theme.BTN_SECONDARY).pack(side=tk.LEFT, padx=(0, 8))

        # Playback button — shown after recording exists
        self._playback_btn = tk.Button(mic_btn_row, text="▶ Reproducir",
                                        command=self._playback_recording,
                                        **theme.BTN_NEUTRAL)

        self._mic_status_lbl = tk.Label(
            mic_inner, text="● Esperando prueba",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
        )
        self._mic_status_lbl.pack(anchor="w", pady=(8, 0))

        self._noise_floor = 0.0
        self._last_recording = None   # numpy array of last mic recording

        # Detect audio devices
        self.run_in_thread(self._get_audio_devices, on_done=self._show_audio_devices)

    def on_enter(self):
        pass

    def _get_audio_devices(self):
        speakers, mics = [], []
        try:
            import wmi
            c = wmi.WMI()
            for e in c.Win32_PnPEntity():
                name = (e.Name or "").lower()
                pnp = (e.PNPClass or "").upper()
                if pnp in ("MEDIA", "SOUND"):
                    full_name = e.Name or "Dispositivo de audio"
                    if any(k in name for k in ("microphone", "micrófono", "mic", "input")):
                        mics.append(full_name)
                    else:
                        speakers.append(full_name)
        except Exception:
            pass
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            if not speakers:
                speakers = [d.get("name", "") for d in devices if d.get("max_output_channels", 0) > 0]
            if not mics:
                mics = [d.get("name", "") for d in devices if d.get("max_input_channels", 0) > 0]
        except Exception:
            pass
        return {"speakers": speakers, "mics": mics}

    def _show_audio_devices(self, data):
        speakers = data.get("speakers", [])
        mics = data.get("mics", [])
        self._spk_devices_lbl.configure(
            text="\n".join(f"• {s[:45]}" for s in speakers[:5]) if speakers else "No detectados",
            fg=theme.TEXT_SECONDARY if speakers else theme.WARNING)
        self._mic_devices_lbl.configure(
            text="\n".join(f"• {m[:45]}" for m in mics[:5]) if mics else "No detectados",
            fg=theme.TEXT_SECONDARY if mics else theme.WARNING)

    def _play_channel(self, channel):
        freq = self._freq_var.get()
        self._spk_status_lbl.configure(
            text=f"► {channel.capitalize()} — {freq} Hz...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_play_channel,
                          args=(freq, channel), daemon=True).start()

    def _do_play_channel(self, frequency, channel):
        played = False
        try:
            import sounddevice as sd
            import numpy as np
            sample_rate = 44100
            duration = 1.5
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            tone = (0.5 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
            stereo = np.zeros((len(tone), 2), dtype=np.float32)
            if channel == "left":
                stereo[:, 0] = tone
            elif channel == "right":
                stereo[:, 1] = tone
            else:
                stereo[:, 0] = tone
                stereo[:, 1] = tone
            sd.play(stereo, sample_rate)
            sd.wait()
            played = True
        except Exception:
            pass

        if not played:
            self._do_play_tone(frequency, 1)
            return

        def update(ch=channel, ok=played):
            lbl = self._left_lbl if ch == "left" else self._right_lbl
            prefix = "◄ Izq:" if ch == "left" else "Der ►:"
            lbl.configure(text=f"{prefix} reproducido ✓", fg=theme.SUCCESS)
            self._spk_status_lbl.configure(
                text=f"✓ Canal {ch} reproducido", fg=theme.SUCCESS)

        self.after(0, update)

    def _play_tone(self):
        freq = self._freq_var.get()
        self._spk_status_lbl.configure(
            text=f"► Reproduciendo {freq} Hz...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_play_tone,
                          args=(freq, AUDIO_DURATION // 1000), daemon=True).start()

    def _play_long_tone(self):
        freq = self._freq_var.get()
        self._spk_status_lbl.configure(
            text=f"► Reproduciendo {freq} Hz (3s)...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_play_tone, args=(freq, 3), daemon=True).start()

    def _do_play_tone(self, frequency, duration_s):
        played = False
        try:
            import winsound
            winsound.Beep(frequency, duration_s * 1000)
            played = True
        except Exception:
            pass
        if not played:
            try:
                import sounddevice as sd
                import numpy as np
                sample_rate = 44100
                t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
                samples = 0.5 * np.sin(2 * np.pi * frequency * t)
                sd.play(samples.astype(np.float32), sample_rate)
                sd.wait()
                played = True
            except Exception:
                pass
        if not played:
            try:
                sample_rate = 44100
                num_samples = int(sample_rate * duration_s)
                data = bytes([int(127.5 * math.sin(2 * math.pi * frequency * t / sample_rate) + 127.5)
                               for t in range(num_samples)])
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
                    text="✓ Tono reproducido — ¿Escuchó el tono?", fg=theme.SUCCESS)
            else:
                self._spk_status_lbl.configure(
                    text="⚠ No se pudo reproducir audio automáticamente.", fg=theme.WARNING)
        self.after(0, update)

    def _confirm_speaker(self, ok):
        self._spk_confirmed = ok
        if ok:
            self._spk_status_lbl.configure(text="✓ Altavoces confirmados por técnico",
                                            fg=theme.SUCCESS)
        else:
            self._spk_status_lbl.configure(text="✗ Técnico reporta fallo en altavoces",
                                            fg=theme.ERROR)
        self._evaluate_overall()

    def _measure_noise(self):
        self._mic_status_lbl.configure(text="🔇 Midiendo ruido de fondo (1s)...",
                                        fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_measure_noise, daemon=True).start()

    def _do_measure_noise(self):
        try:
            import sounddevice as sd
            import numpy as np
            recording = sd.rec(int(44100 * 1.0), samplerate=44100, channels=1)
            sd.wait()
            noise = float(np.abs(recording).mean()) * 1000
            self._noise_floor = noise

            def update(n=noise):
                self._noise_lbl.configure(
                    text=f"Ruido de fondo: {n:.2f}  (menor = mejor)",
                    fg=theme.TEXT_SECONDARY)
                self._mic_status_lbl.configure(
                    text="✓ Ruido medido — ahora pruebe el micrófono",
                    fg=theme.SUCCESS)
            self.after(0, update)
        except Exception as e:
            self.after(0, lambda: self._mic_status_lbl.configure(
                text=f"Error midiendo ruido: {e}", fg=theme.WARNING))

    def _test_mic(self):
        self._mic_status_lbl.configure(
            text="🎙 Grabando 3 segundos...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_test_mic, daemon=True).start()

    def _do_test_mic(self):
        recorded = False
        level = 0.0
        recording_data = None
        try:
            import sounddevice as sd
            import numpy as np
            recording = sd.rec(int(3 * 44100), samplerate=44100, channels=1)
            sd.wait()
            level = float(np.abs(recording).mean()) * 1000
            recording_data = recording.copy()
            recorded = True
        except ImportError:
            pass
        except Exception as e:
            self.after(0, lambda: self._mic_status_lbl.configure(
                text=f"Error de micrófono: {e}", fg=theme.ERROR))
            return

        def update(rec=recording_data):
            if recorded:
                self._last_recording = rec
                self._draw_level(min(level * 100, 100))
                noise = self._noise_floor
                threshold = max(noise * 3.0, 0.5)
                if level > threshold:
                    self._mic_status_lbl.configure(
                        text=f"✓ Micrófono activo — Nivel: {level:.2f} (ruido: {noise:.2f})",
                        fg=theme.SUCCESS)
                    self._evaluate_overall(mic_ok=True)
                else:
                    self._mic_status_lbl.configure(
                        text=f"⚠ Nivel bajo: {level:.2f} vs umbral {threshold:.2f} — Hable más fuerte",
                        fg=theme.WARNING)
                    self._evaluate_overall(mic_ok=False)
                # Show playback button in the button row
                self._playback_btn.pack(side=tk.LEFT)
            else:
                self._mic_status_lbl.configure(
                    text="⚠ sounddevice no disponible.\nInstale: pip install sounddevice",
                    fg=theme.WARNING)
        self.after(0, update)

    def _playback_recording(self):
        if self._last_recording is None:
            return
        self._playback_btn.configure(state=tk.DISABLED)
        def play():
            try:
                import sounddevice as sd
                sd.play(self._last_recording, samplerate=44100)
                sd.wait()
            except Exception:
                pass
            self.after(0, lambda: self._playback_btn.configure(state=tk.NORMAL))
        import threading
        threading.Thread(target=play, daemon=True).start()

    def _evaluate_overall(self, mic_ok=None):
        spk = self._spk_confirmed
        mic = mic_ok
        if spk is True and mic is True:
            self.set_status(STATUS_PASSED, "Altavoces ✓ | Micrófono ✓")
        elif spk is False or mic is False:
            issues = []
            if spk is False:
                issues.append("altavoces")
            if mic is False:
                issues.append("micrófono")
            self.set_status(STATUS_FAILED, f"Fallo en: {', '.join(issues)}")

    def _draw_level(self, pct):
        w = self._level_canvas.winfo_width() or 300
        h = 24
        self._level_canvas.delete("all")
        self._level_canvas.create_rectangle(0, 0, w, h, fill=theme.BG_SURFACE1, outline="")
        fill_w = int(w * max(0, min(pct, 100)) / 100)
        if fill_w > 0:
            color = (theme.SUCCESS if pct < 70
                      else theme.WARNING if pct < 90
                      else theme.ERROR)
            self._level_canvas.create_rectangle(0, 2, fill_w, h-2, fill=color, outline="")
