#!/bin/bash
# ==============================================================================
# SCRIPT PERBAIKAN BULLETPROOF PRINTER THERMAL CX58D - BIG FROZEN FOOD
# Memperbaiki NULL PPD File Pointer pada filter rastertopos, permissions 644,
# wrapper script, USB autosuspend, usblp blacklist & PPD MIME filters.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "========================================================================"
echo "    PERBAIKAN PERMANEN BULLETPROOF PRINTER THERMAL (OKAY 58D / CX58D)   "
echo "========================================================================"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Harap jalankan script ini dengan sudo!${NC}"
  echo "Penggunaan: sudo bash ./drivers/fix_printer.sh"
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
ARCH=$(uname -m)

# ------------------------------------------------------------------------------
# 1. NONAKTIFKAN USB AUTOSUSPEND & BLACKLIST usblp
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[1/6] Mematikan USB Autosuspend & Blacklist usblp...${NC}"
echo -1 > /sys/module/usbcore/parameters/autosuspend 2>/dev/null || true
for ctrl in /sys/bus/usb/devices/*/power/control; do
    echo "on" > "$ctrl" 2>/dev/null || true
done

cat <<'EOF' > /etc/modprobe.d/usb-no-autosuspend.conf
options usbcore autosuspend=-1
EOF

rmmod usblp 2>/dev/null || true
cat <<'EOF' > /etc/modprobe.d/blacklist-usblp.conf
blacklist usblp
EOF
echo -e "${GREEN}   [OK] Power management USB & usblp disesuaikan.${NC}"

# ------------------------------------------------------------------------------
# 2. BERSIHKAN ANTREAN & CACHE CUPS LAMA
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[2/6] Membersihkan antrean cetak & cache CUPS...${NC}"
cancel -a 2>/dev/null || true
for printer in $(lpstat -p 2>/dev/null | awk '{print $2}'); do
    lpadmin -x "$printer" 2>/dev/null || true
done

systemctl stop cups 2>/dev/null || true
sleep 1

rm -f /etc/cups/ppd/CX58D*
rm -rf /var/cache/cups/*
rm -rf /var/spool/cups/tmp/*
rm -rf /var/spool/cups/d*
rm -f /var/spool/cups/c*
rm -f /var/cache/cups/ppds.dat /var/cache/cups/job.cache 2>/dev/null || true

# ------------------------------------------------------------------------------
# 3. PASANG MODEL PPD WORLD-READABLE (644)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[3/6] Memasang PPD pos58 dengan ijin akses 644...${NC}"

PPD_SRC=""
for p in \
    "$PROJECT_DIR/posdrv_linux/ppd/pos58.ppd" \
    "$SCRIPT_DIR/posdrv_linux/ppd/pos58.ppd" \
    "/usr/share/cups/model/posdrv/pos58.ppd"; do
    if [ -f "$p" ]; then
        PPD_SRC="$p"
        break
    fi
done

if [ -z "$PPD_SRC" ]; then
    echo -e "${RED}[ERROR] File pos58.ppd tidak ditemukan!${NC}"
    exit 1
fi

mkdir -p /usr/share/cups/model/posdrv
if [ "$PPD_SRC" != "/usr/share/cups/model/posdrv/pos58.ppd" ]; then
    cp -f "$PPD_SRC" /usr/share/cups/model/posdrv/pos58.ppd
fi
chown -R root:root /usr/share/cups/model/posdrv
chmod 644 /usr/share/cups/model/posdrv/pos58.ppd

# ------------------------------------------------------------------------------
# 4. PASANG RASTERTOPOS WRAPPER (Solusi Kunci NULL PPD File Pointer)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[4/6] Memasang Filter Wrapper rastertopos...${NC}"

FILTER_SRC=""
for p in \
    "$PROJECT_DIR/posdrv_linux/filter/$ARCH/rastertopos" \
    "$PROJECT_DIR/posdrv_linux/filter/x86_64/rastertopos" \
    "$SCRIPT_DIR/posdrv_linux/filter/$ARCH/rastertopos" \
    "$SCRIPT_DIR/posdrv_linux/filter/x86_64/rastertopos" \
    "/usr/lib/cups/filter/rastertopos.real" \
    "/usr/lib/cups/filter/rastertopos"; do
    if [ -f "$p" ] && [ "$p" != "/usr/lib/cups/filter/rastertopos.real" ]; then
        FILTER_SRC="$p"
        break
    fi
done

if [ -z "$FILTER_SRC" ] && [ -f "/usr/lib/cups/filter/rastertopos" ]; then
    FILTER_SRC="/usr/lib/cups/filter/rastertopos"
fi

if [ -z "$FILTER_SRC" ]; then
    echo -e "${RED}[ERROR] Binary rastertopos asli tidak ditemukan!${NC}"
    exit 1
fi

# Salin binary asli ke rastertopos.real jika berbeda
if [ "$FILTER_SRC" != "/usr/lib/cups/filter/rastertopos.real" ]; then
    cp -f "$FILTER_SRC" /usr/lib/cups/filter/rastertopos.real
fi
chown root:root /usr/lib/cups/filter/rastertopos.real
chmod 755 /usr/lib/cups/filter/rastertopos.real

# Buat wrapper script yang menjamin PPD selalu terisi & terbaca
cat <<'EOF' > /usr/lib/cups/filter/rastertopos
#!/bin/bash
# Wrapper untuk rastertopos agar tidak terjadi NULL PPD File Pointer
if [ -z "$PPD" ] || [ ! -r "$PPD" ]; then
    if [ -r "/etc/cups/ppd/CX58D.ppd" ]; then
        export PPD="/etc/cups/ppd/CX58D.ppd"
    else
        export PPD="/usr/share/cups/model/posdrv/pos58.ppd"
    fi
fi
exec /usr/lib/cups/filter/rastertopos.real "$@"
EOF

chown root:root /usr/lib/cups/filter/rastertopos
chmod 755 /usr/lib/cups/filter/rastertopos

echo -e "${GREEN}   [OK] Wrapper rastertopos berhasil dipasang.${NC}"

# ------------------------------------------------------------------------------
# 5. START CUPS & DAFTARKAN PRINTER DENGAN PERMISSION FIX (644)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[5/6] Memulai CUPS & mendaftarkan printer CX58D...${NC}"
systemctl start cups
sleep 2

USB_URI=$(lpinfo -v 2>/dev/null | grep "direct usb://" | grep -iv "fax" | head -n1 | awk '{print $2}')
if [ -z "$USB_URI" ]; then
    USB_URI="usb://HaoYin/CX58D?serial=0.0"
    echo -e "${YELLOW}   [PERINGATAN] USB belum terdeteksi aktif saat ini. Menggunakan URI fallback: $USB_URI${NC}"
else
    echo -e "${GREEN}   [OK] USB Printer Terdeteksi: $USB_URI${NC}"
fi

lpadmin -p CX58D \
    -E \
    -v "$USB_URI" \
    -P /usr/share/cups/model/posdrv/pos58.ppd \
    -D "OKAY 58D Thermal Printer" \
    -L "POS Kasir" \
    -o PageSize=48mmx100mm \
    -o printer-error-policy=retry-current-job

cupsenable CX58D
cupsaccept CX58D
lpadmin -d CX58D

# PASTIKAN PPD DI /etc/cups/ppd/world-readable (chmod 644)
chmod 644 /etc/cups/ppd/CX58D.ppd 2>/dev/null || true

echo -e "${GREEN}   [OK] Printer CX58D terdaftar & PPD permission dieset ke 644.${NC}"

# ------------------------------------------------------------------------------
# 6. PEMBERSIHAN ASSET CACHE ODOO & TES CETAK PDF
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[6/6] Membersihkan cache Odoo asset & menguji cetak...${NC}"
psql -U setyo -d bigfrozenfood_db -c "DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR name LIKE '%.bundle%';" 2>/dev/null || true

echo ""
echo "========================================================================"
echo -e "  ${GREEN}[SUKSES] PERBAIKAN BULLETPROOF SELESAI!${NC}"
echo "========================================================================"
echo ""
echo -e "${YELLOW}Mengirim tes cetak halaman...${NC}"
echo -e "\n\n\n    ================================\n      TEST CETAK PRINTER OK!\n      Big Frozen Food POS\n      $(date +'%d/%m/%Y %H:%M:%S')\n    ================================\n\n\n\n\n" | lpr -P CX58D

echo ""
echo -e "${CYAN}PENTING: PENGATURAN DIALOG PRINT CHROME / ODOO POS:${NC}"
echo "------------------------------------------------------------------------"
echo "Saat Anda mengklik 'Print Receipt' di Odoo POS:"
echo " 1. Destination  : 'CX58D' (atau OKAY 58D Thermal Printer)"
echo " 2. Paper Size   : '48mm x 100mm' (atau 48mmx100mm / Roll 58mm)"
echo " 3. Margins      : 'None' (Tanpa Margin)"
echo " 4. Headers      : UNCHECK (Hapus centang Header & Footer)"
echo " 5. Scale        : 100%"
echo "========================================================================"
