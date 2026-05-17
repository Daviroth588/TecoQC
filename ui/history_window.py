"""
TecoQC - Ventana de historial de inspecciones
"""

import tkinter as tk
from tkinter import ttk
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING


STATUS_FG = {
    STATUS_PASSED:  theme.SUCCESS,
    STATUS_FAILED:  theme.ERROR,
    STATUS_SKIPPED: theme.WARNING,
    STATUS_PENDING: theme.TEXT_MUTED,
}

STATUS_LABELS = {
    STATUS_PASSED:  "✓ Aprobado",
    STATUS_FAILED:  "✗ Fallido",
    STATUS_SKIPPED: "⊘ Omitido",
    STATUS_PENDING: "● Pendiente",
}


class HistoryWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("TecoQC — Historial de Inspecciones")
        self.geometry("1100x620")
        self.configure(bg=theme.BG_BASE)
        self.resizable(True, True)

        self._selected_id = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Top stats bar
        stats_bar = tk.Frame(self, bg=theme.BG_MANTLE,
                              highlightthickness=1,
                              highlightbackground=theme.BG_SURFACE2)
        stats_bar.pack(fill=tk.X)

        self._stats_lbl = tk.Label(stats_bar,
                                    text="Cargando estadísticas...",
                                    bg=theme.BG_MANTLE, fg=theme.TEXT_SECONDARY,
                                    font=theme.FONT_BODY, padx=16, pady=8)
        self._stats_lbl.pack(side=tk.LEFT)

        # Search bar
        search_frame = tk.Frame(stats_bar, bg=theme.BG_MANTLE)
        search_frame.pack(side=tk.RIGHT, padx=16, pady=6)
        tk.Label(search_frame, text="Buscar S/N:",
                 bg=theme.BG_MANTLE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(side=tk.LEFT, padx=(0, 6))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._on_search())
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                 width=20, **theme.ENTRY_STYLE)
        search_entry.pack(side=tk.LEFT)

        # Main split: list left, detail right
        main = tk.Frame(self, bg=theme.BG_BASE)
        main.pack(fill=tk.BOTH, expand=True)

        # Left: inspection list
        left = tk.Frame(main, bg=theme.BG_MANTLE, width=520,
                         highlightthickness=1, highlightbackground=theme.BG_SURFACE2)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        list_hdr = tk.Frame(left, bg=theme.BG_SURFACE1)
        list_hdr.pack(fill=tk.X)
        for col, w in [("S/N", 110), ("Modelo", 120), ("Técnico", 100),
                        ("Fecha", 85), ("Estado", 85)]:
            tk.Label(list_hdr, text=col, bg=theme.BG_SURFACE1,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     width=w//7, anchor="w", padx=6, pady=5).pack(side=tk.LEFT)

        # Scrollable list
        list_wrapper = tk.Frame(left, bg=theme.BG_MANTLE)
        list_wrapper.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_wrapper, bg=theme.BG_MANTLE, highlightthickness=0)
        vsb = tk.Scrollbar(list_wrapper, orient="vertical", command=canvas.yview)
        self._list_inner = tk.Frame(canvas, bg=theme.BG_MANTLE)
        self._list_inner.bind("<Configure>",
                               lambda e: canvas.configure(
                                   scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all("<MouseWheel>",
                         lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Right: inspection detail
        self._detail_frame = tk.Frame(main, bg=theme.BG_BASE)
        self._detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._detail_placeholder = tk.Label(
            self._detail_frame,
            text="Seleccione una inspección para ver el detalle",
            bg=theme.BG_BASE, fg=theme.TEXT_MUTED, font=theme.FONT_BODY)
        self._detail_placeholder.pack(expand=True)

        self._all_inspections = []

    def _load_data(self):
        try:
            from data.db import init_db, get_recent_inspections, get_stats
            init_db()
            self._all_inspections = get_recent_inspections()
            stats = get_stats()
            self._stats_lbl.configure(
                text=f"Total: {stats['total']}  |  "
                     f"✓ Aprobados: {stats['passed']}  |  "
                     f"✗ Fallidos: {stats['failed']}  |  "
                     f"Hoy: {stats['today']}")
        except Exception as e:
            self._stats_lbl.configure(text=f"Error cargando DB: {e}", fg=theme.ERROR)
            self._all_inspections = []
        self._render_list(self._all_inspections)

    def _on_search(self):
        term = self._search_var.get().strip().lower()
        if not term:
            self._render_list(self._all_inspections)
        else:
            filtered = [i for i in self._all_inspections
                        if term in (i.get("serial_number") or "").lower()
                        or term in (i.get("model") or "").lower()
                        or term in (i.get("technician") or "").lower()]
            self._render_list(filtered)

    def _render_list(self, inspections):
        for w in self._list_inner.winfo_children():
            w.destroy()

        if not inspections:
            tk.Label(self._list_inner, text="Sin inspecciones registradas.",
                     bg=theme.BG_MANTLE, fg=theme.TEXT_MUTED,
                     font=theme.FONT_BODY, pady=20).pack()
            return

        for i, insp in enumerate(inspections):
            bg = theme.BG_SURFACE0 if i % 2 == 0 else theme.BG_MANTLE
            status = insp.get("overall_status", STATUS_PENDING)
            fg_status = STATUS_FG.get(status, theme.TEXT_MUTED)

            row = tk.Frame(self._list_inner, bg=bg, cursor="hand2")
            row.pack(fill=tk.X)

            sn = (insp.get("serial_number") or "—")[:14]
            model = (insp.get("model") or "—")[:16]
            tech = (insp.get("technician") or "—")[:13]
            date = (insp.get("date") or "")[:10]
            status_lbl = STATUS_LABELS.get(status, status)

            for text, fg, w in [
                (sn, theme.TEXT_PRIMARY, 110),
                (model, theme.TEXT_SECONDARY, 120),
                (tech, theme.TEXT_MUTED, 100),
                (date, theme.TEXT_MUTED, 85),
                (status_lbl, fg_status, 85),
            ]:
                lbl = tk.Label(row, text=text, bg=bg, fg=fg,
                                font=theme.FONT_SMALL, width=w//7,
                                anchor="w", padx=6, pady=5)
                lbl.pack(side=tk.LEFT)
                lbl.bind("<Button-1>",
                          lambda e, iid=insp["id"]: self._show_detail(iid))

            row.bind("<Button-1>",
                      lambda e, iid=insp["id"]: self._show_detail(iid))
            row.bind("<Enter>",
                      lambda e, r=row, b=bg: r.configure(bg=theme.SIDEBAR_ITEM_HOVER))
            row.bind("<Leave>",
                      lambda e, r=row, b=bg: r.configure(bg=b))

    def _show_detail(self, inspection_id):
        for w in self._detail_frame.winfo_children():
            w.destroy()

        try:
            from data.db import get_inspection_steps, get_recent_inspections
            insp = next((i for i in self._all_inspections if i["id"] == inspection_id), None)
            if not insp:
                return
            steps = get_inspection_steps(inspection_id)
        except Exception as e:
            tk.Label(self._detail_frame, text=f"Error: {e}",
                     bg=theme.BG_BASE, fg=theme.ERROR,
                     font=theme.FONT_BODY).pack()
            return

        status = insp.get("overall_status", STATUS_PENDING)
        fg_status = STATUS_FG.get(status, theme.TEXT_MUTED)
        status_lbl = STATUS_LABELS.get(status, status)

        # Header
        hdr = tk.Frame(self._detail_frame, bg=theme.BG_SURFACE0,
                        highlightthickness=1, highlightbackground=theme.BG_SURFACE2)
        hdr.pack(fill=tk.X, pady=(0, 8))

        tk.Label(hdr, text=f"S/N: {insp.get('serial_number', '—')}",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", padx=12, pady=(8, 2))

        info_row = tk.Frame(hdr, bg=theme.BG_SURFACE0)
        info_row.pack(fill=tk.X, padx=12, pady=(0, 8))
        for text in [
            f"Modelo: {insp.get('model', '—')}",
            f"Técnico: {insp.get('technician', '—')}",
            f"Fecha: {insp.get('date', '—')}",
        ]:
            tk.Label(info_row, text=text, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(hdr, text=status_lbl,
                 bg=theme.BG_SURFACE0, fg=fg_status,
                 font=(theme.FONT_FAMILY, 14, "bold")).pack(anchor="w", padx=12, pady=(0, 8))

        # Steps table
        tk.Label(self._detail_frame, text="Resultados por componente:",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(0, 4))

        tbl_frame = tk.Frame(self._detail_frame, bg=theme.BG_SURFACE0,
                              highlightthickness=1, highlightbackground=theme.BG_SURFACE1)
        tbl_frame.pack(fill=tk.BOTH, expand=True)

        # Table header
        thdr = tk.Frame(tbl_frame, bg=theme.BG_SURFACE1)
        thdr.pack(fill=tk.X)
        for col, w in [("#", 30), ("Componente", 150), ("Estado", 100), ("Detalles", 300)]:
            tk.Label(thdr, text=col, bg=theme.BG_SURFACE1, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL, width=w//7, anchor="w",
                     padx=8, pady=5).pack(side=tk.LEFT)

        for step in steps:
            snum = step.get("step_num", 0)
            sname = step.get("step_name", "")
            sstatus = step.get("status", STATUS_PENDING)
            sdetails = (step.get("details") or "")[:45]
            sfg = STATUS_FG.get(sstatus, theme.TEXT_MUTED)
            slbl = STATUS_LABELS.get(sstatus, sstatus)
            bg = theme.BG_SURFACE0 if snum % 2 == 1 else theme.BG_MANTLE

            srow = tk.Frame(tbl_frame, bg=bg)
            srow.pack(fill=tk.X)
            for text, fg, w in [
                (str(snum), theme.TEXT_MUTED, 30),
                (sname, theme.TEXT_PRIMARY, 150),
                (slbl, sfg, 100),
                (sdetails or "—", theme.TEXT_SECONDARY, 300),
            ]:
                tk.Label(srow, text=text, bg=bg, fg=fg,
                          font=theme.FONT_SMALL, width=w//7,
                          anchor="w", padx=8, pady=4).pack(side=tk.LEFT)

        # Notes
        notes = insp.get("notes", "")
        if notes:
            tk.Label(self._detail_frame,
                     text=f"Observaciones: {notes}",
                     bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL).pack(anchor="w", pady=(8, 0))
