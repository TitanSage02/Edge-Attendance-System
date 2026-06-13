#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de diagnostic pour le module Edge Attendance System
Ce script permet de tester tous les composants du système
"""

import os
import sys
import argparse
import asyncio
import logging
from utils.logger import setup_logger

# Configuration du logger
logger = setup_logger("diagnostic", logging.INFO)

async def run_test(test_name, extra_args=None):
    """
    Exécute un script de test spécifique
    
    Args:
        test_name: Nom du script de test
        extra_args: Arguments supplémentaires pour le script
    """
    # Construire le chemin vers le script de test
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              f"tests/test_{test_name}.py")
    
    if not os.path.exists(script_path):
        logger.error(f"❌ Script de test non trouvé: {script_path}")
        return False
    
    # Construire la commande
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    
    cmd_str = " ".join(cmd)
    logger.info(f"Exécution du test: {cmd_str}")
    
    try:
        # Exécuter le script
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Récupérer la sortie
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"✅ Test {test_name} terminé avec succès")
            return True
        else:
            logger.error(f"❌ Échec du test {test_name} (code: {process.returncode})")
            logger.error(stderr.decode())
            return False
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du test {test_name}: {e}")
        return False

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Diagnostic du module Edge Attendance System')
    parser.add_argument('--all', action='store_true', help='Exécuter tous les tests')
    parser.add_argument('--hardware', action='store_true', help='Tests des composants matériels')
    parser.add_argument('--presence', action='store_true', help='Test du système de présence')
    parser.add_argument('--vl53l0x', action='store_true', help='Test et calibration du capteur VL53L0X')
    parser.add_argument('--calibrate', action='store_true', help='Mode calibration pour le capteur VL53L0X')
    parser.add_argument('--duration', type=int, default=30, help='Durée des tests en secondes')
    
    args = parser.parse_args()
    
    logger.info("=== DIAGNOSTIC DU MODULE EDGE ATTENDANCE SYSTEM ===")
    
    tests_results = {}
    
    # Exécuter les tests demandés
    if args.all or (not args.hardware and not args.presence and not args.vl53l0x):
        # Exécuter tous les tests
        logger.info("Exécution de tous les tests...")
        
        # Test matériel
        hardware_result = await run_test("hardware", ["--all"])
        tests_results["hardware"] = hardware_result
        
        # Test du système de présence
        presence_result = await run_test("presence_unit", ["--all"])
        tests_results["presence"] = presence_result
        
        # Test de base du capteur VL53L0X
        vl53l0x_result = await run_test("vl53l0x", ["--read", "--duration", str(args.duration)])
        tests_results["vl53l0x"] = vl53l0x_result
    else:
        # Tests spécifiques
        if args.hardware:
            hardware_result = await run_test("hardware", ["--all"])
            tests_results["hardware"] = hardware_result
        
        if args.presence:
            presence_result = await run_test("presence_unit", ["--all"])
            tests_results["presence"] = presence_result
            
        if args.vl53l0x:
            if args.calibrate:
                vl53l0x_result = await run_test("vl53l0x", ["--calibrate", "--duration", str(args.duration)])
            else:
                vl53l0x_result = await run_test("vl53l0x", ["--read", "--duration", str(args.duration)])
                
            tests_results["vl53l0x"] = vl53l0x_result
    
    # Afficher un résumé des résultats
    logger.info("\n=== RÉSUMÉ DES TESTS ===")
    for test_name, result in tests_results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        logger.info(f"{test_name}: {status}")
    
    # Déterminer le résultat global
    all_passed = all(tests_results.values())
    if all_passed:
        logger.info("\n✅ TOUS LES TESTS ONT RÉUSSI")
        return 0
    else:
        logger.warning("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Diagnostic interrompu par l'utilisateur")
        sys.exit(130)  # Code de sortie standard pour Ctrl+C
    except Exception as e:
        logger.critical(f"Erreur lors de l'exécution du diagnostic: {e}")
        sys.exit(1)
