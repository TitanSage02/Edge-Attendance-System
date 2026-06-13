#!/bin/bash
# Script pour exécuter les tests automatisés

# Activer l'environnement virtuel si nécessaire
# source venv/bin/activate

echo "======================================================"
echo "     Exécution des tests unitaires et d'intégration"
echo "======================================================"
echo ""

# Vérifier les dépendances nécessaires pour les tests
echo "Vérification des dépendances pour les tests..."
python -m pip install -q pytest pytest-asyncio pytest-mock pytest-cov coverage
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances. Essai avec sudo..."
    sudo python -m pip install pytest pytest-asyncio pytest-mock pytest-cov coverage
    if [ $? -ne 0 ]; then
        echo "❌ Impossible d'installer les dépendances requises."
        exit 1
    fi
fi
echo "✅ Dépendances installées/vérifiées"
echo ""

# Créer le répertoire des rapports s'il n'existe pas
mkdir -p reports

# Nettoyer les anciens rapports
rm -f reports/*.xml
rm -f reports/coverage.xml
rm -rf reports/html

# Exécuter les tests avec pytest et générer des rapports
echo ">> Exécution des tests..."

# Vérifier si un test spécifique est demandé
if [ -n "$1" ]; then
    TEST_PATH="tests/$1"
    echo "Exécution des tests spécifiques: $TEST_PATH"
else
    TEST_PATH="tests/"
fi

python -m pytest $TEST_PATH -v \
    --junitxml=reports/test-results.xml \
    --cov=. \
    --cov-report=xml:reports/coverage.xml \
    --cov-report=html:reports/html \
    --cov-report=term

EXIT_CODE=$?

echo ""
echo "======================================================"
echo "                  Résumé des tests"
echo "======================================================"
echo ""
echo "Rapports générés dans le dossier 'reports/'."
echo "Code de sortie: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tous les tests ont réussi!"
else
    echo "❌ Certains tests ont échoué. Vérifiez les rapports pour plus de détails."
fi

echo ""
echo "Pour voir la couverture détaillée: ouvrez reports/html/index.html"
echo ""

exit $EXIT_CODE
