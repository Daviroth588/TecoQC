"""
TecoQC - Paso 6: Prueba de cámara (OpenCV si disponible)
"""

import tkinter as tk
import threading
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Prueba de Cámara"
    DESCRIPTION = "Detecte y verifique las cámaras del equipo. Revise la vista previa en vivo."
    STEP_NUM = 6

    def build_ui(self, parent):
        self._cv2 = None
        self._cap = None
        self._running = False
        self._camera_idx = 0
        self._cameras_found = []

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

        # Camera info card
        tk.Frame(ctrl, height=12, bg=theme.BG_BASE).pack()
        tk.Label(ctrl, text="Información de cámara:",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w")

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
        try:
            cap = cv2.VideoCapture(self._camera_idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self._camera_idx)
            if not cap.isOpened():
                self._status_lbl.configure(
                    text=f"✗ No se pudo abrir cámara {self._camera_idx}",
                    fg=theme.ERROR,
                )
                return
            self._cap = cap
            self._running = True
            self._no_cam_lbl.place_forget()
            self._status_lbl.configure(text="► Cámara activa", fg=theme.SUCCESS)
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

        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to fit canvas
            h, w = frame.shape[:2]
            canvas_w = self._canvas.winfo_width() or 480
            canvas_h = self._canvas.winfo_height() or 320
            scale = min(canvas_w / w, canvas_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))

            img = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(img)

            def update(p=photo, pw=new_w, ph=new_h):
                cw = self._canvas.winfo_width()
                ch = self._canvas.winfo_height()
                self._canvas.delete("all")
                self._canvas.create_image(cw//2, ch//2, image=p, anchor="center")
                self._canvas._photo = p  # keep ref

            self.after(0, update)
            import time
            time.sleep(0.033)  # ~30 fps

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
