#!/usr/bin/env bash
# ==============================================================================
# Linux Performance Kit - Multi-Distro Abstraction Layer
# ==============================================================================

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
        DISTRO_LIKE="${ID_LIKE:-$DISTRO_ID}"
    else
        DISTRO_ID="unknown"
        DISTRO_LIKE="unknown"
    fi
}

detect_bootloader() {
    BOOTLOADER="unknown"
    if [ -f /etc/default/limine ] || [ -f /boot/limine.conf ] || [ -f /boot/limine/limine.conf ]; then
        BOOTLOADER="limine"
    elif [ -d /boot/loader/entries ]; then
        BOOTLOADER="systemd-boot"
    elif [ -f /etc/default/grub ]; then
        BOOTLOADER="grub"
    fi
}

# Modificar cmdline de mitigaciones según el bootloader detectado
set_cmdline_param() {
    local action="$1" # "add" o "remove"
    local param="$2"  # e.g. "mitigations=off"

    detect_bootloader

    case "$BOOTLOADER" in
        limine)
            if [ -f /etc/default/limine ]; then
                local current_conf
                current_conf=$(cat /etc/default/limine)
                if [ "$action" = "add" ]; then
                    if ! grep -q "$param" /etc/default/limine; then
                        echo "Añadiendo '$param' a /etc/default/limine..."
                        sed -i "s/KERNEL_CMDLINE\[default\]+=\"/KERNEL_CMDLINE[default]+=\"$param /" /etc/default/limine
                    fi
                elif [ "$action" = "remove" ]; then
                    echo "Removiendo '$param' de /etc/default/limine..."
                    sed -i "s/$param //g; s/$param//g" /etc/default/limine
                fi
                if command -v limine-update >/dev/null 2>&1; then
                    limine-update
                fi
            fi
            ;;
        grub)
            if [ -f /etc/default/grub ]; then
                if [ "$action" = "add" ]; then
                    if ! grep -q "$param" /etc/default/grub; then
                        echo "Añadiendo '$param' a /etc/default/grub..."
                        sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/GRUB_CMDLINE_LINUX_DEFAULT=\"$param /" /etc/default/grub
                    fi
                elif [ "$action" = "remove" ]; then
                    echo "Removiendo '$param' de /etc/default/grub..."
                    sed -i "s/$param //g; s/$param//g" /etc/default/grub
                fi
                if command -v grub-mkconfig >/dev/null 2>&1; then
                    grub-mkconfig -o /boot/grub/grub.cfg
                elif command -v update-grub >/dev/null 2>&1; then
                    update-grub
                fi
            fi
            ;;
        systemd-boot)
            echo "Ajustando systemd-boot loader entries..."
            for entry in /boot/loader/entries/*.conf; do
                [ -f "$entry" ] || continue
                if [ "$action" = "add" ]; then
                    if ! grep -q "$param" "$entry"; then
                        sed -i "/^options / s/$/ $param/" "$entry"
                    fi
                elif [ "$action" = "remove" ]; then
                    sed -i "s/ $param//g; s/$param//g" "$entry"
                fi
            done
            ;;
        *)
            echo "Aviso: No se detectó un bootloader estándar automáticamente ($BOOTLOADER)."
            echo "Por favor añade o remueve manualmente '$param' en los parámetros de tu kernel."
            ;;
    esac
}
