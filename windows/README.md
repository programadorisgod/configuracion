# Entorno de Terminal en Windows

Configuración de alto rendimiento para emulador de terminal en Windows basada en **Alacritty** (GPU accelerated) y el multiplexor **Zellij** (gestión de pestañas y paneles).

## Componentes

- **Alacritty v0.17+**: Renderizado por hardware con OpenGL, paleta Catppuccin Mocha, tipografía Cascadia Code con ligaduras y transparencia con desenfoque de ventana.
- **Zellij v0.45+**: Multiplexor de terminal en Rust que provee pestañas superiores, divisiones de paneles y soporte completo de ratón.
- **PowerShell**: Intérprete por defecto dentro de las sesiones.

## Instalación Rápida

Ejecuta el script de aprovisionamiento en una ventana de PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

O si necesitas instalar los paquetes desde cero mediante Windows Package Manager (`winget`):

```powershell
winget install Alacritty.Alacritty
winget install Zellij.Zellij
```

## Ubicaciones de Configuración

| Aplicación | Ruta de Configuración |
| :--- | :--- |
| **Alacritty** | `%APPDATA%\alacritty\alacritty.toml` |
| **Zellij** | `%APPDATA%\Zellij\config\config.kdl` |

## Atajos de Teclado Principales

### Pestañas (Zellij)
- `Alt + n`: Nueva pestaña
- `Alt + →` / `Alt + ←`: Cambiar entre pestañas
- `Ctrl + t` luego `x`: Cerrar pestaña actual
- `Ctrl + t` luego `r`: Renombrar pestaña

### Paneles Divididos (Splits)
- `Alt + r`: Dividir panel verticalmente (a la derecha)
- `Alt + d`: Dividir panel horizontalmente (abajo)
- `Alt + Flechas`: Mover foco entre paneles
- `Alt + f`: Alternar pantalla completa del panel actual
- `Alt + x`: Cerrar panel activo

### Alacritty
- `Ctrl + Shift + T` / `Ctrl + Shift + N`: Nueva ventana
- `Ctrl + Shift + C`: Copiar
- `Ctrl + Shift + V`: Pegar
- `Ctrl + [+]` / `Ctrl + [-]`: Aumentar o reducir tamaño de texto
- `Ctrl + Clic`: Abrir hipervínculo en el navegador web
