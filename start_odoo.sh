#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ODOO_PYTHON="/usr/bin/python3"
if [ -f "/home/setyo/developer/odoo18/odoo-bin" ]; then
    ODOO_BIN="/home/setyo/developer/odoo18/odoo-bin"
elif [ -f "/home/adi-purwanto/developer/odoo18/odoo-bin" ]; then
    ODOO_BIN="/home/adi-purwanto/developer/odoo18/odoo-bin"
else
    ODOO_BIN="odoo-bin"
fi
CONFIG_FILE="$SCRIPT_DIR/big_frozen_food.conf"

echo "======================================================="
echo "        BIG FROZEN FOOD - ODOO 18 SERVER RUNNER        "
echo "======================================================="
echo "  Database    : odoo-big-frozen"
echo "  Config File : $CONFIG_FILE"
echo "  Web URL     : http://localhost:8069"
echo "======================================================="
echo ""

# Execute Odoo server
$ODOO_PYTHON $ODOO_BIN -c $CONFIG_FILE "$@"

