# Linux Performance Kit (`perf-kit`)

Kit modular, portable y 100% reversible para optimización de sistemas Linux de escritorio y desarrollo (ajustado para procesadores Intel de 4 núcleos, 8 GB de RAM con ZRAM y almacenamiento SSD SATA sin DRAM con Btrfs o ext4).

---

## Áreas de Optimización

1. **CPU e IPC (`mitigations=off` + BPF Scheduler)**:
   - Recupera entre un **15% y 25% de rendimiento** penalizado por mitigaciones de software (Meltdown PTI, Spectre v2 Retpolines, MDS buffers).
   - Activa el planificador BPF de baja latencia **`scx_bpfland`** mediante `scx_loader`: garantiza que el escritorio, el navegador y el cursor mantengan fluidez aunque la CPU esté al 100% compilando o indexando.
2. **Gestión de Memoria (8GB RAM + ZRAM `zstd`)**:
   - `vm.swappiness = 180` y `vm.page-cluster = 0`: prioriza comprimir páginas inactivas en ZRAM (ratio aprox. 3:1) en lugar de descartar la caché de disco y código.
   - **THP (Transparent Huge Pages)** en `madvise`: evita el desperdicio de memoria en sistemas de 8 GB.
   - **MGLRU (Multi-Gen LRU)** con `min_ttl_ms = 1000`: protege el conjunto de trabajo activo (ventanas en primer plano) contra vaciados abruptos.
3. **Almacenamiento SSD SATA (DRAM-less) y Btrfs**:
   - `vm.dirty_bytes = 128MB` y `vm.dirty_background_bytes = 32MB`: evita pausas de congelamiento al sincronizar memoria en SSDs sin DRAM integrada.
   - I/O Scheduler **`adios`** (o `mq-deadline` en distribuciones estándar) con `rq_affinity = 2` (completa interrupciones en el mismo núcleo de CPU que originó la petición).
   - Btrfs montado con `compress=zstd:1,ssd,commit=60`: compresión ultraligera que reduce desgaste del almacenamiento y uso de CPU.
   - Reducción del archivo de intercambio secundario a 4 GB para optimizar espacio útil en disco.
4. **Red de Baja Latencia**:
   - Algoritmo de control de congestión **BBR** + **Fair Queueing (`fq`)** + **TCP FastOpen (`3`)**, reduciendo el bufferbloat y acelerando conexiones web, descargas y APIs.

---

## Uso de la Herramienta CLI (`perf-kit`)

Dentro del directorio `linux/perf-kit`:

```bash
# Ver el estado actual del sistema (CPU, sched_ext, THP, ZRAM, I/O, BBR)
./bin/perf-kit status

# Ejecutar el benchmark integrado para medir latencia de syscalls, compresión e I/O
./bin/perf-kit benchmark

# Aplicar todas las optimizaciones al sistema (requiere permisos de superusuario)
./bin/perf-kit apply

# Activar o desactivar mitigaciones de CPU bajo demanda
./bin/perf-kit cpu-mitigations off
./bin/perf-kit cpu-mitigations on

# Revertir todo al estado original del sistema
./bin/perf-kit revert
```

---

## Portabilidad e Instalación en Otras Distribuciones

Este kit sigue el estándar **freedesktop / systemd drop-ins** en `/etc/`. Ningún archivo de paquetes de la distribución (`/usr/lib/`) es modificado directamente.

Para utilizarlo en **Fedora, Arch Linux, Debian, Ubuntu, openSUSE o Void**:

1. Copia el directorio `perf-kit` a la nueva instalación.
2. Accede al directorio y ejecuta:
   ```bash
   ./bin/perf-kit apply
   ```
3. El script detecta automáticamente el gestor de arranque activo (GRUB, Limine o systemd-boot), crea respaldos preventivos e instala los drop-ins correspondientes.
