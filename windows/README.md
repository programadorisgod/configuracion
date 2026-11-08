# 🪟 Entorno de Terminal en Windows

Configuración de alto rendimiento para terminal en Windows basada en **Alacritty** (acelerado por GPU mediante OpenGL) y el multiplexor **Zellij** (gestión de pestañas, divisiones de pantalla y sesiones).

---

## ✨ Componentes y Características

- **Alacritty v0.17+**:
  - Renderizado ultrarrápido por hardware (GPU OpenGL).
  - Paleta oficial **Catppuccin Mocha** (alto contraste, descanso visual).
  - Tipografía **Cascadia Code** con soporte nativo para ligaduras de programación (`=>`, `===`, `!=`).
  - Transparencia (94%) y efecto de desenfoque de ventana (*acrylic blur*).
  - Detección interactiva de hipervínculos (abre enlaces en tu navegador con `Ctrl + Clic`).
- **Zellij v0.45+**:
  - Multiplexor moderno escrito en Rust integrado como shell por defecto.
  - Barra de pestañas superior interactiva.
  - Creación ilimitada de paneles verticales y horizontales (*splits*).
  - Soporte completo de ratón (selección, clic para cambiar panel, scroll).
- **PowerShell**: Intérprete por defecto dentro de cada panel o sesión.

---

## 🚀 Instalación y Despliegue Rápido

### 1. Despliegue Automatizado (Recomendado)
Abre PowerShell en este directorio y ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

> [!TIP]
> Si aún no tienes Alacritty o Zellij instalados, puedes añadir el parámetro `-InstallPackages` para que el script los descargue e instale automáticamente mediante `winget`:
> ```powershell
> .\setup.ps1 -InstallPackages
> ```

### 2. Instalación Manual vía Windows Package Manager (`winget`)
Si prefieres instalar los binarios manualmente:

```powershell
winget install Alacritty.Alacritty
winget install Zellij.Zellij
```

---

## 📂 Estructura y Destinos de Configuración

```text
windows/
├── terminal/
│   ├── alacritty/
│   │   └── alacritty.toml         # Configuración Catppuccin Mocha + Cascadia Code
│   └── zellij/
│       └── config.kdl             # Configuración Catppuccin + Tabs + PowerShell
├── setup.ps1                      # Script de aprovisionamiento automatizado
└── README.md                      # Documentación del entorno Windows
```

| Aplicación | Origen en Repositorio | Destino en Windows |
| :--- | :--- | :--- |
| **Alacritty** | `terminal/alacritty/alacritty.toml` | `%APPDATA%\alacritty\alacritty.toml` |
| **Zellij** | `terminal/zellij/config.kdl` | `%APPDATA%\Zellij\config\config.kdl` |

---

## ⌨️ Atajos de Teclado Principales

### 📑 Pestañas (Zellij)
| Atajo | Acción |
| :--- | :--- |
| `Alt + n` | Crear nueva pestaña |
| `Alt + →` / `Alt + ←` | Cambiar entre pestañas |
| `Ctrl + t` luego `x` | Cerrar pestaña activa |
| `Ctrl + t` luego `r` | Renombrar pestaña activa |

### 🔲 Paneles Divididos (Splits en Zellij)
| Atajo | Acción |
| :--- | :--- |
| `Alt + r` | Dividir panel verticalmente (a la derecha) |
| `Alt + d` | Dividir panel horizontalmente (abajo) |
| `Alt + Flechas` | Mover foco entre paneles (`←`, `↑`, `↓`, `→`) |
| `Alt + f` | Alternar pantalla completa del panel actual |
| `Alt + x` | Cerrar panel activo |
| `Alt + +` / `Alt + -` | Aumentar / reducir tamaño del panel activo |

### 🖥️ Alacritty
| Atajo | Acción |
| :--- | :--- |
| `Ctrl + Shift + T` | Abrir nueva ventana |
| `Ctrl + Shift + N` | Abrir nueva ventana |
| `Ctrl + Shift + C` | Copiar selección al portapapeles |
| `Ctrl + Shift + V` | Pegar desde el portapapeles |
| `Ctrl + [+]` / `Ctrl + [-]` | Aumentar / disminuir tamaño de fuente |
| `Ctrl + [0]` | Restablecer tamaño de fuente original |
| `Ctrl + Clic Izquierdo` | Abrir hipervínculo en el navegador predeterminado |

---

## 🔍 Solución de Problemas

- **La terminal no arranca tras instalar Alacritty**:
  Asegúrate de que `zellij.exe` se encuentra en tu variable de entorno `PATH`. Tras la instalación de winget, se recomienda cerrar y reabrir la consola para refrescar el PATH del sistema.
- **Caracteres o iconos raros**:
  Verifica que tienes instalada la fuente `Cascadia Code` (incluida en Windows 10/11) o cualquier Nerd Font compatible.
