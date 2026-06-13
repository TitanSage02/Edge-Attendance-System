#!/bin/bash
# Ce script aide à configurer les permissions du script de démarrage

# Obtenir le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Rendre tous les scripts dans le répertoire exécutable
for script in "$SCRIPT_DIR"/*.sh; do
    if [[ -f "$script" ]]; then
        chmod +x "$script"
    fi
done

echo "Les permissions du script start.sh ont été configurées correctement!"
echo "Vous pouvez maintenant lancer le script de test avec:"
echo "  ./run_tests.sh"
echo "Vous pouvez maintenant lancer le système avec:"
echo "  ./start.sh"
echo 
echo "Options disponibles:"
echo "  ./start.sh --diagnostic    # Pour exécuter les diagnostics"
echo "  ./start.sh --skip-update   # Pour forcer la mise à jour du système (utile pour le premier déploiement)"
echo "  ./start.sh --force-reinstall  # Pour recréer l'environnement virtuel"
