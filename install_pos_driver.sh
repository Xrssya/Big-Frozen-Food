#!/bin/bash
# ==============================================================================
# Script Install & Clean Reinstall Driver Printer Thermal OKAY 58D (Linux/Ubuntu)
# Big Frozen Food POS
# ==============================================================================

set -e

echo "========================================================================"
echo "          REINSTALL & SETUP DRIVER PRINTER THERMAL (OKAY 58D)          "
echo "========================================================================"

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Harap jalankan script ini dengan sudo!"
  echo "Penggunaan: sudo ./install_pos_driver.sh"
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARCH=$(uname -m)

DOWNLOAD_TAR="/home/adi-purwanto/Downloads/posdrv_linux_20180314.tar.gz"
PROJECT_TAR="$SCRIPT_DIR/posdrv_linux_20180314.tar.gz"

if [ -f "$DOWNLOAD_TAR" ]; then
    TAR_PATH="$DOWNLOAD_TAR"
elif [ -f "$PROJECT_TAR" ]; then
    TAR_PATH="$PROJECT_TAR"
else
    echo "[ERROR] File posdrv_linux_20180314.tar.gz tidak ditemukan di Downloads atau folder proyek!"
    exit 1
fi

echo "1. Menghapus (cleanup) antrean printer lama..."
lpadmin -x CX58D 2>/dev/null || true
rm -f /usr/lib/cups/filter/rastertopos

echo "2. Mengekstrak driver dari $TAR_PATH..."
cd "$SCRIPT_DIR"
tar -zxf "$TAR_PATH" -C "$SCRIPT_DIR"

echo "3. Memasang filter CUPS rastertopos ($ARCH)..."
if [ -d "$SCRIPT_DIR/posdrv_linux/filter/$ARCH" ]; then
    cp "$SCRIPT_DIR/posdrv_linux/filter/$ARCH/rastertopos" /usr/lib/cups/filter/
else
    echo "Arsitektur $ARCH tidak ditemukan secara khusus, menggunakan x86_64..."
    cp "$SCRIPT_DIR/posdrv_linux/filter/x86_64/rastertopos" /usr/lib/cups/filter/
fi

chmod 755 /usr/lib/cups/filter/rastertopos
chown root:root /usr/lib/cups/filter/rastertopos

echo "4. Memasang file PPD ke direktori CUPS model..."
mkdir -p /usr/share/cups/model/posdrv
cp "$SCRIPT_DIR/posdrv_linux/ppd/"*.ppd /usr/share/cups/model/posdrv/
chmod 644 /usr/share/cups/model/posdrv/*.ppd

echo "5. Merestart layanan CUPS..."
systemctl restart cups

echo "6. Mendaftarkan printer CX58D USB..."
USB_URI=$(lpinfo -v 2>/dev/null | grep -i "usb://HaoYin/CX58D" | head -n 1 | awk '{print $2}')
if [ -z "$USB_URI" ]; then
    USB_URI="usb://HaoYin/CX58D?serial=0.0"
fi

echo "   Menggunakan URI: $USB_URI"
lpadmin -p CX58D -E -v "$USB_URI" -i /usr/share/cups/model/posdrv/pos58.ppd -D "OKAY 58D Thermal Printer" -o PageSize=48mmx100mm
cupsenable CX58D
cupsaccept CX58D
lpadmin -d CX58D

echo "========================================================================"
echo " [BERHASIL] Driver & Printer CX58D berhasil dipasang dan diatur sebagai default!"
echo "========================================================================"
lpstat -p -d
