#!/bin/bash

# Configuration paths
ODOO_PYTHON="/usr/bin/python3"
ODOO_BIN="/home/adi-purwanto/developer/odoo18/odoo-bin"
CONFIG_FILE="/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf"

echo "======================================================="
echo "        BIG FROZEN FOOD - ODOO 18 SERVER RUNNER        "
echo "======================================================="
echo "  Database    : big_frozen_food"
echo "  Config File : $CONFIG_FILE"
echo "  Web URL     : http://localhost:8069"
echo "======================================================="
echo ""

# Execute Odoo server
$ODOO_PYTHON $ODOO_BIN -c $CONFIG_FILE "$@"
