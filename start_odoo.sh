#!/bin/bash

# Configuration paths
ODOO_PYTHON="/home/setyo/developer/odoo18/venv/bin/python"
ODOO_BIN="/home/setyo/developer/odoo18/odoo-bin"
CONFIG_FILE="/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf"

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
