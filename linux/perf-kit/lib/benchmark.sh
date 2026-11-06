#!/usr/bin/env bash
# ==============================================================================
# Linux Performance Kit - Micro-Benchmark Suite
# Mide: Syscall overhead, compresión zstd, latencia I/O de disco y estado de RAM
# ==============================================================================

run_benchmark() {
    echo "============================================================"
    echo "       LINUX PERFORMANCE KIT - BENCHMARK DE RENDIMIENTO     "
    echo "============================================================"
    local tmp_dir
    tmp_dir=$(mktemp -d /tmp/perf-bench-XXXXXX)

    # 1. Syscall / Kernel Context Switch Overhead (Sensible a Mitigaciones PTI/Retpolines)
    echo -n "[1/4] Evaluando latencia de syscalls (200,000 getpid / context switches)... "
    local syscall_time
    if command -v python3 >/dev/null 2>&1; then
        syscall_time=$(python3 -c '
import os, time
t0 = time.perf_counter()
for _ in range(200000):
    os.getpid()
t1 = time.perf_counter()
print(f"{(t1 - t0)*1000:.2f} ms")
' 2>/dev/null)
        echo "$syscall_time"
    else
        echo "N/A (python3 no disponible)"
    fi

    # 2. CPU Single-Core Hash / Compresión
    echo -n "[2/4] Evaluando compresión zstd multinúcleo (100MB datos mixtos)... "
    dd if=/dev/urandom of="$tmp_dir/test.raw" bs=1M count=20 status=none 2>/dev/null
    for i in {1..4}; do cat "$tmp_dir/test.raw" >> "$tmp_dir/test_100M.dat"; done
    local comp_start comp_end comp_ms
    comp_start=$(date +%s%N)
    zstd -1 -q -c "$tmp_dir/test_100M.dat" > "$tmp_dir/test.zst"
    comp_end=$(date +%s%N)
    comp_ms=$(( (comp_end - comp_start) / 1000000 ))
    echo "${comp_ms} ms"

    # 3. I/O Latency de Almacenamiento (Direct I/O sync en disco)
    echo -n "[3/4] Evaluando latencia de escritura síncrona en disco (50MB)... "
    local io_start io_end io_ms
    io_start=$(date +%s%N)
    dd if=/dev/zero of="$tmp_dir/sync_io.tmp" bs=1M count=50 oflag=sync status=none 2>/dev/null
    io_end=$(date +%s%N)
    io_ms=$(( (io_end - io_start) / 1000000 ))
    echo "${io_ms} ms"

    # 4. Estado de Memoria y Disco
    echo "------------------------------------------------------------"
    echo "[4/4] Resumen de Recursos Actuales:"
    free -h | awk 'NR==1{print "       "$0} NR==2{print "RAM:   "$0} NR==3{print "Swap:  "$0}'
    echo -n "Espacio libre en /: "
    df -h / | awk 'NR==2{print $4 " libres (usado " $5 ")"}'
    echo -n "ZRAM: "
    if command -v zramctl >/dev/null 2>&1; then
        zramctl --output NAME,ALGORITHM,DISKSIZE,DATA,COMPR,TOTAL --noheadings 2>/dev/null || echo "Inactivo"
    else
        echo "N/A"
    fi
    echo "============================================================"
    rm -rf "$tmp_dir"
}
