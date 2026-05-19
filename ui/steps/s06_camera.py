"""
TecoQC - Paso 6: Prueba de cámara (OpenCV si disponible)
"""

import tkinter as tk
import threading
import time
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, CAMERA_MIN_WIDTH, CAMERA_MIN_HEIGHT, CAMERA_MIN_FPS


class Step(BaseStep):
    TITLE = "Prueba de Cámara"
    DESCRIPTION = "Detecte y verifique las cámaras del equipo. Revise vista previa y FPS mínimos."
    STEP_NUM = 6

    def build_ui(self, parent):
        self._cv2 = None
        self._cap = None
        self._running = False
        self._camera_idx = 0
        self._cameras_found = []
        self._frame_times = []

        # Camera list
        top = tk.Frame(parent, bg=theme.BG_BASE)
        top.pack(fill=tk.X, pady=(0, 12))

        tk.Label(top, text="Cámaras detectadas:",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(side=tk.LEFT)

        self._cam_var = tk.IntVar(value=0)
        self._cam_selector_frame = tk.Frame(top, bg=theme.BG_BASE)
        self._cam_selector_frame.pack(side=tk.LEFT, padx=12)

        # Main area: preview + controls
        main = tk.Frame(parent, bg=theme.BG_BASE)
        main.pack(fill=tk.BOTH, expand=True)

        # Preview canvas
        preview_wrapper = tk.Frame(main, bg=theme.BG_CRUST,
                                    highlightthickness=2,
                                    highlightbackground=theme.BG_SURFACE2)
        preview_wrapper.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        self._canvas = tk.Canvas(preview_wrapper, bg=theme.BG_CRUST,
                                  highlightthickness=0, width=480, height=320)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self._no_cam_lbl = tk.Label(
            self._canvas,
            text="Sin vista previa\n\nSe requiere OpenCV (cv2)\npara mostrar video en vivo",
            bg=theme.BG_CRUST, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
        )
        self._no_cam_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Controls
        ctrl = tk.Frame(main, bg=theme.BG_BASE, width=220)
        ctrl.pack(side=tk.LEFT, fill=tk.Y)
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="Controles",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 8))

        tk.Button(ctrl, text="▶  Iniciar cámara",
                   command=self._start_camera, **theme.BTN_PRIMARY).pack(fill=tk.X, pady=4)
        tk.Button(ctrl, text="■  Detener cámara",
                   command=self._stop_camera, **theme.BTN_SECONDARY).pack(fill=tk.X, pady=4)

        tk.Frame(ctrl, height=16, bg=theme.BG_BASE).pack()

        self._status_lbl = tk.Label(
            ctrl, text="● Esperando inicio",
            bg=theme.BG_BASE, fg=theme.TEXT_MUTED, font=theme.FONT_BODY,
            wraplength=200, justify="left",
        )
        self._status_lbl.pack(anchor="w")

        # Camera metrics card
        tk.Frame(ctrl, height=12, bg=theme.BG_BASE).pack()
        metrics_frame = tk.Frame(ctrl, bg=theme.BG_SURFACE0,
                                  highlightthickness=1,
                                  highlightbackground=theme.BG_SURFACE1)
        metrics_frame.pack(fill=tk.X)
        tk.Label(metrics_frame, text="Métricas detectadas",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", padx=8, pady=(6, 2))

        self._res_lbl = tk.Label(metrics_frame, text="Resolución: —",
                                  bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                  font=theme.FONT_SMALL)
        self._res_lbl.pack(anchor="w", padx=8)

        self._fps_lbl = tk.Label(metrics_frame, text="FPS: —",
                                  bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                  font=theme.FONT_SMALL)
        self._fps_lbl.pack(anchor="w", padx=8, pady=(0, 6))

        # Thresholds info
        tk.Label(ctrl, text=f"Mínimos: {CAMERA_MIN_WIDTH}×{CAMERA_MIN_HEIGHT} px, ≥{CAMERA_MIN_FPS} FPS",
                 bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
                 font=theme.FONT_SMALL, wraplength=200).pack(anchor="w", pady=(8, 0))

        # Camera info label
        tk.Frame(ctrl, height=8, bg=theme.BG_BASE).pack()
        self._cam_info_lbl = tk.Label(ctrl, text="N/D",
                                       bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
                                       font=theme.FONT_SMALL, wraplength=200,
                                       justify="left")
        self._cam_info_lbl.pack(anchor="w")

        # WMI camera list
        self.run_in_thread(self._detect_cameras_wmi,
                            on_done=self._show_camera_list)

    def _detect_cameras_wmi(self):
        cameras = []
        try:
            import wmi
            c = wmi.WMI()
            devices = c.Win32_PnPEntity()
            for d in devices:
                name = (d.Name or "").lower()
                if ("camera" in name or "webcam" in name or
                        "cam" in name or "imaging" in name):
                    cameras.append({
                        "name": d.Name,
                        "manufacturer": d.Manufacturer or "N/D",
                        "device_id": d.DeviceID or "",
                        "status": d.Status or "",
                    })
        except Exception as e:
            cameras.append({"name": f"Error WMI: {e}", "manufacturer": "",
                             "device_id": "", "status": ""})
        return cameras

    def _show_camera_list(self, cameras):
        self._cameras_wmi = cameras

        for widget in self._cam_selector_frame.winfo_children():
            widget.destroy()

        if cameras:
            for i, cam in enumerate(cameras):
                rb = tk.Radiobutton(
                    self._cam_selector_frame,
                    text=cam.get("name", f"Cámara {i}")[:40],
                    variable=self._cam_var,
                    value=i,
                    bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                    selectcolor=theme.BG_SURFACE0,
                    font=theme.FONT_SMALL,
                    activebackground=theme.BG_BASE,
                    activeforeground=theme.TEXT_PRIMARY,
                )
                rb.pack(side=tk.LEFT, padx=4)

            cam_info = cameras[0]
            info_text = (
                f"Nombre: {cam_info.get('name', 'N/D')}\n"
                f"Fabricante: {cam_info.get('manufacturer', 'N/D')}\n"
                f"Estado: {cam_info.get('status', 'N/D')}"
            )
            self._cam_info_lbl.configure(text=info_text, fg=theme.TEXT_SECONDARY)
        else:
            tk.Label(self._cam_selector_frame,
                     text="No se detectaron cámaras",
                     bg=theme.BG_BASE, fg=theme.WARNING,
                     font=theme.FONT_SMALL).pack(side=tk.LEFT)

    def _start_camera(self):
        try:
            import cv2
            self._cv2 = cv2
        except ImportError:
            self._status_lbl.configure(
                text="⚠ OpenCV no instalado.\nInstale 'opencv-python' para\nver vista previa.",
                fg=theme.WARNING,
            )
            self._set_detail("OpenCV no disponible - verificación manual requerida")
            return

        self._camera_idx = self._cam_var.get()
        self._frame_times = []
        try:
            cap = cv2.VideoCapture(self._camera_idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self._camera_idx)
            if not cap.isOpened():
                self._status_lbl.configure(
                    text=f"✗ No se pudo abrir cámara {self._camera_idx}",
                    fg=theme.ERROR,
                )
                self.set_status(STATUS_FAILED, f"No se pudo abrir cámara {self._camera_idx}")
                return

            # Request higher resolution (camera will use best available)
            for res_w, res_h in [(1920, 1080), (1280, 720), (1024, 768)]:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, res_w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res_h)
                got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                if got_w >= res_w - 10:
                    break

            # Request maximum FPS
            cap.set(cv2.CAP_PROP_FPS, 30)

            # Read actual resolution from camera
            cam_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cam_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._cam_width = cam_w
            self._cam_height = cam_h

            res_ok = cam_w >= CAMERA_MIN_WIDTH and cam_h >= CAMERA_MIN_HEIGHT
            res_color = theme.SUCCESS if res_ok else theme.WARNING
            self._res_lbl.configure(text=f"Resolución: {cam_w}×{cam_h} px",
                                     fg=res_color)

            self._cap = cap
            self._running = True
            self._no_cam_lbl.place_forget()
            self._status_lbl.configure(text="► Cámara activa — midiendo FPS...",
                                        fg=theme.ACCENT_BLUE)
            threading.Thread(target=self._update_frame, daemon=True).start()
        except Exception as e:
            self._status_lbl.configure(text=f"Error: {e}", fg=theme.ERROR)

    def _update_frame(self):
        import cv2
        try:
            from PIL import Image, ImageTk
        except ImportError:
            self.after(0, lambda: self._status_lbl.configure(
                text="Error: Pillow no instalado", fg=theme.ERROR))
            return

        frame_times = []
        evaluated = False

        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret:
                break

            t_now = time.time()
            frame_times.append(t_now)
            # Keep 3-second sliding window
            frame_times = [t for t in frame_times if t_now - t <= 3.0]
            measured_fps = len(frame_times) / 3.0 if len(frame_times) >= 3 else None

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            canvas_w = self._canvas.winfo_width() or 480
            canvas_h = self._canvas.winfo_height() or 320
            scale = min(canvas_w / w, canvas_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
            img = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(img)

            _eval = (not evaluated and len(frame_times) >= 20)
            if _eval:
                evaluated = True

            def update(p=photo, fps=measured_fps, do_eval=_eval, ft_len=len(frame_times)):
                cw = self._canvas.winfo_width()
                ch = self._canvas.winfo_height()
                self._canvas.delete("all")
                self._canvas.create_image(cw // 2, ch // 2, image=p, anchor="center")
                self._canvas._photo = p
                if fps is not None:
                    fps_ok = fps >= CAMERA_MIN_FPS
                    fps_color = theme.SUCCESS if fps_ok else theme.WARNING
                    self._fps_lbl.configure(
                        text=f"FPS: {fps:.1f} {'✓' if fps_ok else '⚠'}",
                        fg=fps_color)
                    if do_eval:
                        cam_w = getattr(self, "_cam_width", 0)
                        cam_h = getattr(self, "_cam_height", 0)
                        res_ok = cam_w >= CAMERA_MIN_WIDTH and cam_h >= CAMERA_MIN_HEIGHT
                        if res_ok and fps_ok:
                            self._status_lbl.configure(
                                text=f"✓ Cámara OK — {cam_w}×{cam_h} @ {fps:.1f} FPS",
                                fg=theme.SUCCESS)
                            self.set_status(STATUS_PASSED,
                                             f"{cam_w}×{cam_h} px @ {fps:.1f} FPS")
                        else:
                            issues = []
                            if not res_ok:
                                issues.append(f"resolución {cam_w}×{cam_h} baja")
                            if not fps_ok:
                                issues.append(f"FPS {fps:.1f} insuficiente")
                            self._status_lbl.configure(
                                text=f"⚠ Cámara con problemas: {', '.join(issues)}",
                                fg=theme.WARNING)
                            self.set_status(STATUS_FAILED, ", ".join(issues))

            self.after(0, update)
            # Cap UI updates at ~30fps to avoid flooding Tk event loop
            time.sleep(0.033)

        self.after(0, lambda: self._status_lbl.configure(
            text="■ Cámara detenida", fg=theme.TEXT_MUTED))

    def _stop_camera(self):
        self._running = False
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._canvas.delete("all")
        self._no_cam_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._status_lbl.configure(text="■ Cámara detenida", fg=theme.TEXT_MUTED)

    def on_leave(self):
        super().on_leave()
        self._stop_camera()
