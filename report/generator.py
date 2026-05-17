"""
TecoQC - Generador de reporte HTML de control de calidad
"""

import os
import datetime


# Status color mapping
STATUS_COLORS = {
    "passed":  ("#a6e3a1", "#1a2e1a", "✓ Aprobado"),
    "failed":  ("#f38ba8", "#2e1a1a", "✗ Fallido"),
    "skipped": ("#f9e2af", "#2e2a1a", "⊘ Omitido"),
    "pending": ("#a6adc8", "#1e1e2e", "● Pendiente"),
}

STEP_NAMES = {
    1:  "Bienvenida",
    2:  "Información del Sistema",
    3:  "Teclado",
    4:  "Trackpad",
    5:  "Pantalla",
    6:  "Cámara",
    7:  "Puertos USB",
    8:  "Red",
    9:  "Audio",
    10: "CPU",
    11: "GPU",
    12: "Memoria RAM",
    13: "Almacenamiento",
    14: "Batería",
    15: "Reporte Final",
}


def generate_html_report(wizard_state: dict) -> str:
    """
    Genera un reporte HTML completo con los resultados del QC.
    Retorna la ruta del archivo generado.
    """
    tech_name = wizard_state.get("technician_name", "N/D")
    serial = wizard_state.get("device_serial", "sin_serial")
    report_date = wizard_state.get("report_date",
                                   datetime.date.today().isoformat())
    device_model = wizard_state.get("device_model", "N/D")
    company = wizard_state.get("company", "Tecology")
    step_results = wizard_state.get("step_results", {})
    system_info = wizard_state.get("system_info", {})

    # Calculate overall result
    statuses = [v.get("status", "pending") for v in step_results.values()]
    failed_count = statuses.count("failed")
    skipped_count = statuses.count("skipped")
    passed_count = statuses.count("passed")
    total_count = len(STEP_NAMES) - 1  # Exclude step 15 (report itself)

    overall_status = "Aprobado" if failed_count == 0 else "Fallido"
    overall_color = "#a6e3a1" if failed_count == 0 else "#f38ba8"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte QC - {serial} - {report_date}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            padding: 24px;
            min-height: 100vh;
        }}
        .report-container {{
            max-width: 960px;
            margin: 0 auto;
            background: #181825;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        }}
        .header {{
            background: linear-gradient(135deg, #11111b 0%, #1e1e2e 100%);
            padding: 36px 40px;
            border-bottom: 2px solid #313244;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: 700;
            color: #89b4fa;
            letter-spacing: 1px;
        }}
        .app-name {{
            font-size: 14px;
            color: #a6adc8;
            margin-top: 4px;
        }}
        .overall-badge {{
            background: {overall_color};
            color: #1e1e2e;
            font-size: 20px;
            font-weight: 700;
            padding: 10px 24px;
            border-radius: 8px;
        }}
        .report-title {{
            font-size: 22px;
            font-weight: 600;
            color: #cdd6f4;
            margin-top: 20px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 20px;
        }}
        .meta-item {{
            background: #313244;
            border-radius: 8px;
            padding: 12px 16px;
        }}
        .meta-label {{
            font-size: 11px;
            color: #6c7086;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .meta-value {{
            font-size: 15px;
            color: #cdd6f4;
            font-weight: 600;
        }}
        .summary-bar {{
            display: flex;
            gap: 16px;
            padding: 20px 40px;
            background: #11111b;
            border-bottom: 1px solid #313244;
        }}
        .summary-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .summary-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .content {{
            padding: 32px 40px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #89b4fa;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #313244;
        }}
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 32px;
        }}
        .results-table th {{
            background: #313244;
            color: #a6adc8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 10px 16px;
            text-align: left;
        }}
        .results-table td {{
            padding: 12px 16px;
            border-bottom: 1px solid #313244;
            font-size: 14px;
        }}
        .results-table tr:last-child td {{
            border-bottom: none;
        }}
        .results-table tr:hover td {{
            background: #252535;
        }}
        .status-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-passed  {{ background: #a6e3a1; color: #1a2e1a; }}
        .status-failed  {{ background: #f38ba8; color: #2e1a1a; }}
        .status-skipped {{ background: #f9e2af; color: #2e2a1a; }}
        .status-pending {{ background: #45475a; color: #cdd6f4; }}
        .sysinfo-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .sysinfo-card {{
            background: #313244;
            border-radius: 8px;
            padding: 16px;
        }}
        .sysinfo-card-title {{
            font-size: 13px;
            font-weight: 700;
            color: #89b4fa;
            margin-bottom: 10px;
        }}
        .sysinfo-row {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            padding: 4px 0;
            border-bottom: 1px solid #45475a;
        }}
        .sysinfo-row:last-child {{
            border-bottom: none;
        }}
        .sysinfo-label {{
            color: #a6adc8;
        }}
        .sysinfo-val {{
            color: #cdd6f4;
            font-weight: 500;
            text-align: right;
            max-width: 60%;
        }}
        .notes-box {{
            background: #252535;
            border-left: 3px solid #89b4fa;
            padding: 10px 14px;
            font-size: 13px;
            color: #a6adc8;
            margin-top: 4px;
            border-radius: 0 4px 4px 0;
            font-style: italic;
        }}
        .footer {{
            padding: 20px 40px;
            background: #11111b;
            border-top: 1px solid #313244;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #6c7086;
        }}
        @media print {{
            body {{ background: white; color: black; padding: 0; }}
            .report-container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
<div class="report-container">
    <div class="header">
        <div class="header-top">
            <div>
                <div class="company-name">{company}</div>
                <div class="app-name">TecoQC v1.0.0 — Sistema de Control de Calidad</div>
            </div>
            <div class="overall-badge">
                {'✓' if overall_status == 'Aprobado' else '✗'} {overall_status}
            </div>
        </div>
        <div class="report-title">Reporte de Control de Calidad</div>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Técnico</div>
                <div class="meta-value">{tech_name}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Número de Serie</div>
                <div class="meta-value">{serial}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Fecha</div>
                <div class="meta-value">{report_date}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Modelo</div>
                <div class="meta-value">{device_model}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Pruebas Aprobadas</div>
                <div class="meta-value" style="color:#a6e3a1">{passed_count} / {total_count}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Pruebas Fallidas</div>
                <div class="meta-value" style="color:{'#f38ba8' if failed_count > 0 else '#a6e3a1'}">{failed_count}</div>
            </div>
        </div>
    </div>

    <div class="summary-bar">
        <div class="summary-item">
            <div class="summary-dot" style="background:#a6e3a1"></div>
            <span>Aprobado: {passed_count}</span>
        </div>
        <div class="summary-item">
            <div class="summary-dot" style="background:#f38ba8"></div>
            <span>Fallido: {failed_count}</span>
        </div>
        <div class="summary-item">
            <div class="summary-dot" style="background:#f9e2af"></div>
            <span>Omitido: {skipped_count}</span>
        </div>
        <div class="summary-item">
            <div class="summary-dot" style="background:#45475a"></div>
            <span>Pendiente: {statuses.count('pending')}</span>
        </div>
    </div>

    <div class="content">
        {_build_sysinfo_section(system_info)}

        <div class="section-title">Resultados de Pruebas</div>
        <table class="results-table">
            <thead>
                <tr>
                    <th style="width:40px">#</th>
                    <th>Componente</th>
                    <th style="width:120px">Estado</th>
                    <th>Detalles</th>
                    <th>Notas</th>
                </tr>
            </thead>
            <tbody>
                {_build_results_rows(step_results)}
            </tbody>
        </table>
    </div>

    <div class="footer">
        <span>Generado por TecoQC v1.0.0 — {company}</span>
        <span>{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</span>
    </div>
</div>
</body>
</html>"""

    # Save to Desktop
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~")

    safe_serial = "".join(c if c.isalnum() or c in "-_" else "_" for c in serial)
    filename = f"TecoQC_Reporte_{safe_serial}_{report_date}.html"
    filepath = os.path.join(desktop, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        # Fallback: save to home dir
        filepath = os.path.join(os.path.expanduser("~"), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    return filepath


def _build_sysinfo_section(system_info: dict) -> str:
    if not system_info:
        return ""

    os_info = system_info.get("os", {})
    mb_info = system_info.get("motherboard", {})
    cpu_info = system_info.get("cpu", {})
    mem_info = system_info.get("memory", {})
    gpu_list = system_info.get("gpu", [])

    def row(label, val):
        return (f'<div class="sysinfo-row">'
                f'<span class="sysinfo-label">{label}</span>'
                f'<span class="sysinfo-val">{val or "N/D"}</span>'
                f'</div>')

    os_card = f"""
    <div class="sysinfo-card">
        <div class="sysinfo-card-title">Sistema Operativo</div>
        {row("OS", os_info.get("product_name", os_info.get("os_full", "N/D")))}
        {row("Versión", os_info.get("os_version", "N/D")[:50])}
        {row("Arquitectura", os_info.get("architecture", "N/D"))}
        {row("Hostname", os_info.get("hostname", "N/D"))}
    </div>"""

    hw_card = f"""
    <div class="sysinfo-card">
        <div class="sysinfo-card-title">Hardware</div>
        {row("Fabricante", mb_info.get("make", mb_info.get("manufacturer", "N/D")))}
        {row("Modelo", mb_info.get("model", mb_info.get("product", "N/D")))}
        {row("Placa Base", mb_info.get("product", "N/D"))}
        {row("S/N BIOS", system_info.get("bios", {}).get("serial_number", "N/D"))}
    </div>"""

    cpu_card = f"""
    <div class="sysinfo-card">
        <div class="sysinfo-card-title">Procesador</div>
        {row("Nombre", cpu_info.get("name", "N/D"))}
        {row("Núcleos físicos", cpu_info.get("cores_physical", "N/D"))}
        {row("Núcleos lógicos", cpu_info.get("cores_logical", "N/D"))}
        {row("Velocidad máx.", f"{cpu_info.get('freq_max_mhz', 0)} MHz")}
    </div>"""

    gpu_rows = ""
    if gpu_list:
        g = gpu_list[0]
        gpu_rows = (row("GPU", g.get("name", "N/D")) +
                    row("VRAM", f"{g.get('vram_total_mb', 0)} MB") +
                    row("Controlador", g.get("driver_version", "N/D")) +
                    row("Fabricante", g.get("vendor", "N/D")))
    gpu_card = f"""
    <div class="sysinfo-card">
        <div class="sysinfo-card-title">Tarjeta Gráfica</div>
        {gpu_rows or row("Estado", "No detectada")}
    </div>"""

    ram_gb = mem_info.get("total_gb", 0)
    mem_card = f"""
    <div class="sysinfo-card">
        <div class="sysinfo-card-title">Memoria RAM</div>
        {row("Total", f"{ram_gb} GB")}
        {row("Usada", f"{mem_info.get('used_gb', 0)} GB")}
        {row("Disponible", f"{mem_info.get('available_gb', 0)} GB")}
        {row("Uso", f"{mem_info.get('percent', 0):.1f}%")}
    </div>"""

    return f"""
    <div class="section-title">Especificaciones del Sistema</div>
    <div class="sysinfo-grid">
        {os_card}
        {hw_card}
        {cpu_card}
        {gpu_card}
        {mem_card}
    </div>"""


def _build_results_rows(step_results: dict) -> str:
    rows = []
    for step_num in range(1, 15):  # Steps 1-14 (skip 15=report)
        step_name = STEP_NAMES.get(step_num, f"Paso {step_num}")
        data = step_results.get(step_num, {})
        status = data.get("status", "pending")
        details = data.get("details", "")
        notes = data.get("notes", "")

        color_cls = f"status-{status}"
        label_map = {
            "passed": "✓ Aprobado",
            "failed": "✗ Fallido",
            "skipped": "⊘ Omitido",
            "pending": "● Pendiente",
        }
        status_label = label_map.get(status, status)

        notes_html = f'<div class="notes-box">{notes}</div>' if notes else "—"

        rows.append(f"""
        <tr>
            <td style="color:#6c7086;font-size:12px">{step_num:02d}</td>
            <td style="font-weight:500">{step_name}</td>
            <td><span class="status-badge {color_cls}">{status_label}</span></td>
            <td style="font-size:13px;color:#a6adc8">{details or "—"}</td>
            <td style="min-width:160px">{notes_html}</td>
        </tr>""")

    return "\n".join(rows)
