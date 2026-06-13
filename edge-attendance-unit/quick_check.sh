#!/bin/bash

# Script de vérification rapide pour le système Edge Attendance System

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== VÉRIFICATION RAPIDE SYSTÈME EDGE ATTENDANCE SYSTEM ===${NC}"
echo ""

# Vérifier le service systemd
if systemctl is-active --quiet crec-presence-complete; then
    echo -e "${GREEN}✓${NC} Service systemd actif"
else
    echo -e "${RED}✗${NC} Service systemd inactif"
    echo "  Commande : sudo systemctl start crec-presence-complete"
fi

# Vérifier les processus
if pgrep -f "startup.py\|main.py" > /dev/null; then
    echo -e "${GREEN}✓${NC} Service principal en cours"
else
    echo -e "${YELLOW}⚠${NC} Service principal non détecté"
fi

if pgrep -f "config_web/app.py" > /dev/null; then
    echo -e "${GREEN}✓${NC} Interface web en cours"
else
    echo -e "${YELLOW}⚠${NC} Interface web non détectée"
fi

# Vérifier les ports
if netstat -tlnp 2>/dev/null | grep -q ":80"; then
    echo -e "${GREEN}✓${NC} Port 80 ouvert (interface web)"
else
    echo -e "${YELLOW}⚠${NC} Port 80 fermé"
fi

# Vérifier les logs
if [ -f "/tmp/crec-presence.log" ]; then
    echo -e "${GREEN}✓${NC} Log principal présent"
else
    echo -e "${YELLOW}⚠${NC} Log principal absent"
fi

if [ -f "/tmp/crec-config-web.log" ]; then
    echo -e "${GREEN}✓${NC} Log interface web présent"
else
    echo -e "${YELLOW}⚠${NC} Log interface web absent"
fi

echo ""
echo "Interface web : http://localhost:80"
echo "Logs : tail -f /tmp/crec-*.log"
echo ""
echo "Pour un diagnostic complet : ./test_system.sh"
echo "Pour redémarrer : ./auto_start.sh"
