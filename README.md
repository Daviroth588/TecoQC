# TecoQC — Sistema de Control de Calidad

**Tecology Quality Control v1.0.0**

Herramienta de inspección de hardware para técnicos. Guía paso a paso la revisión completa de un equipo: teclado, trackpad, pantalla, cámara, puertos USB, red, audio, CPU, GPU, RAM, almacenamiento y batería. Al finalizar genera un reporte PDF con los resultados.

---

## Requisitos

- **Windows 10 / 11** (64-bit)
- **Python 3.10 o superior** — [python.org](https://www.python.org/downloads/)
  - Al instalar Python, marcar **"Add Python to PATH"**
- **Permisos de Administrador** (necesarios para leer temperaturas de CPU/GPU)

---

## Instalación

### Opción A — Correr desde el código fuente

1. Clona o descarga este repositorio:
   ```
   git clone https://github.com/Daviroth588/TecoQC.git
   cd TecoQC
   ```

2. Ejecuta el instalador de dependencias:
   ```
   install.bat
   ```
   Esto instala automáticamente todos los paquetes de `requirements.txt`.

3. *(Opcional)* Para habilitar lectura de temperatura de CPU:
   - Descarga LibreHardwareMonitor desde su [página de releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
   - Extrae el ZIP y copia **`LibreHardwareMonitorLib.dll`** a la carpeta `assets/`

### Opción B — Usar el ejecutable compilado

Si tienes el archivo `TecoQC.exe` generado con `build.bat`:
- No necesitas instalar Python ni dependencias
- Simplemente ejecuta `TecoQC.exe` como Administrador

---

## Uso

### Desde el código fuente

```
run.bat
```

O directamente:
```
python main.py
```

Windows pedirá permisos de Administrador al iniciar (necesario para sensores de temperatura).

### Desde el ejecutable

Doble clic en `dist\TecoQC.exe`. Windows mostrará el diálogo UAC automáticamente.

---

## Pasos de inspección

TecoQC guía al técnico por **15 pasos** en orden:

| # | Paso | Qué verifica |
|---|------|-------------|
| 1 | Bienvenida | Datos del técnico y número de serie del equipo |
| 2 | Sistema | Información general del hardware (marca, modelo, SO) |
| 3 | Teclado | Detección de teclas — pulsa cada tecla para confirmar |
| 4 | Trackpad | Movimiento, clics y gestos multitáctiles |
| 5 | Pantalla | Resolución, brillo y prueba de píxeles muertos |
| 6 | Cámara | Vista en vivo, resolución mínima y FPS |
| 7 | Puertos USB | Detección de dispositivos conectados por puerto |
| 8 | Red | Conectividad WiFi/Ethernet y latencia |
| 9 | Audio | Prueba de bocinas y micrófono con tono de referencia |
| 10 | CPU | Uso, frecuencia, núcleos y temperatura en tiempo real |
| 11 | GPU | Adaptador, VRAM y temperatura (NVIDIA/AMD/Intel) |
| 12 | Memoria RAM | Capacidad, slots ocupados y velocidad |
| 13 | Almacenamiento | Velocidad de lectura/escritura y estado SMART |
| 14 | Batería | Capacidad, ciclos de carga y estado de salud |
| 15 | Reporte Final | Resumen de resultados + exportación PDF |

Cada paso puede marcarse como **Aprobado**, **Fallido** u **Omitido**.

---

## Compilar el ejecutable

Para generar `dist\TecoQC.exe`:

1. Asegúrate de haber corrido `install.bat` primero.

2. *(Opcional)* Coloca `LibreHardwareMonitorLib.dll` en `assets/` para incluir soporte de temperatura en el exe.

3. Ejecuta:
   ```
   build.bat
   ```

El ejecutable resultante estará en `dist\TecoQC.exe`. Incluye todas las dependencias — no requiere Python instalado en el equipo destino.

> **Nota:** El exe lleva manifiesto UAC (`requireAdministrator`), por lo que Windows siempre pedirá elevación al abrirlo.

---

## Modo USB

TecoQC detecta automáticamente si se ejecuta desde una unidad USB. En ese caso guarda los datos y reportes en una carpeta `TecoQC_Data/` junto al ejecutable, en lugar del directorio del usuario.

---

## Recuperación de sesión

Si la aplicación se cierra inesperadamente, al volver a abrirla ofrecerá continuar desde donde se quedó (técnico, número de serie y resultados previos).

---

## Estructura del proyecto

```
TecoQC/
├── main.py               # Punto de entrada
├── config.py             # Configuración global y umbrales
├── requirements.txt      # Dependencias Python
├── install.bat           # Instalador de dependencias
├── run.bat               # Lanzador rápido (código fuente)
├── build.bat             # Compilador PyInstaller → .exe
├── assets/
│   ├── logo.ico          # Ícono de la aplicación
│   └── LibreHardwareMonitorLib.dll  # (colocar manualmente)
├── hardware/             # Módulos de detección de hardware
│   ├── cpu.py
│   ├── gpu.py
│   ├── memory.py
│   ├── storage.py
│   ├── battery.py
│   ├── network.py
│   ├── bluetooth.py
│   ├── peripherals.py
│   └── ...
├── ui/
│   ├── wizard_manager.py # Controlador principal del wizard
│   ├── steps/            # Un archivo por paso (s01 a s15)
│   ├── components.py     # Widgets reutilizables
│   └── theme.py          # Colores y estilos
├── report/               # Generación de PDF y CSV
└── data/                 # Datos de sesión e historial (generado en uso)
```

---

## Dependencias principales

| Paquete | Uso |
|---------|-----|
| `psutil` | CPU, RAM, disco, batería |
| `WMI` | Hardware info vía Windows Management Instrumentation |
| `pywin32` | APIs nativas de Windows |
| `Pillow` | Imágenes en la UI y generación de reportes |
| `reportlab` | Exportación de reportes PDF |
| `opencv-python` | Vista en vivo de cámara |
| `sounddevice` | Prueba de audio y micrófono |
| `pythonnet` | Enlace a LibreHardwareMonitor.dll para temperaturas |

---

## Licencia

Uso interno — Tecology. Todos los derechos reservados.
