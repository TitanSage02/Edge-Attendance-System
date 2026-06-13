#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test spécifique pour le capteur VL53L0X
Ce script permet de tester en profondeur le capteur de distance
"""

import os
import sys
import time
import asyncio
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Ajouter le répertoire parent au path pour importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
from config import config
from sensors.sensor import VL065XController

# Configuration du logger
logger = setup_logger("vl53l0x_test", logging.INFO)

class VL53L0XTester:
    """
    Classe de test pour le capteur VL53L0X
    Permet de valider le fonctionnement et calibrer le seuil de détection
    """
    
    def __init__(self, threshold=None):
        """
        Initialisation du testeur
        
        Args:
            threshold: Seuil de détection en mm (défaut: valeur de config)
        """
        self.threshold = threshold or config.DISTANCE_THRESHOLD_MM
        self.sensor = None
        self.distances = []
        self.timestamps = []
        self.detections = []
        
    async def initialize(self):
        """Initialisation du capteur"""
        try:
            logger.info(f"Initialisation du capteur VL53L0X (seuil: {self.threshold}mm)...")
            self.sensor = VL065XController(threshold=self.threshold)
            logger.info("✅ Capteur initialisé avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation du capteur: {e}")
            return False
    
    async def test_reading(self, duration=5, interval=0.1):
        """
        Test de lecture simple du capteur
        
        Args:
            duration: Durée du test en secondes
            interval: Intervalle entre les lectures en secondes
        """
        logger.info(f"Test de lecture pendant {duration} secondes...")
        
        end_time = time.time() + duration
        count = 0
        error_count = 0
        
        while time.time() < end_time:
            distance = self.sensor.read_distance()
            
            if distance is not None:
                logger.info(f"Distance: {distance:.2f}mm")
                count += 1
            else:
                logger.warning("Erreur de lecture")
                error_count += 1
                
            await asyncio.sleep(interval)
        
        success_rate = (count / (count + error_count)) * 100 if (count + error_count) > 0 else 0
        logger.info(f"Test terminé: {count} lectures réussies, {error_count} erreurs")
        logger.info(f"Taux de réussite: {success_rate:.1f}%")
        
        return success_rate >= 90  # Considéré réussi si au moins 90% des lectures sont bonnes
    
    async def collect_data(self, duration=30, interval=0.1):
        """
        Collecte des données pour analyse et calibration
        
        Args:
            duration: Durée de la collecte en secondes
            interval: Intervalle entre les mesures en secondes
        """
        logger.info(f"Collecte de données pendant {duration} secondes...")
        logger.info("Approchez et éloignez votre main du capteur pendant ce test.")
        
        # Réinitialiser les données
        self.distances = []
        self.timestamps = []
        self.detections = []
        
        start_time = time.time()
        end_time = start_time + duration
        
        try:
            while time.time() < end_time:
                # Lecture de la distance
                distance = self.sensor.read_distance()
                
                if distance is not None:
                    # Enregistrer les données
                    timestamp = time.time() - start_time
                    detection = distance < self.threshold
                    
                    self.distances.append(distance)
                    self.timestamps.append(timestamp)
                    self.detections.append(detection)
                    
                    status = "DÉTECTÉ" if detection else "NON DÉTECTÉ"
                    logger.info(f"{timestamp:.1f}s: {distance:.1f}mm - {status}")
                
                # Attendre avant la prochaine mesure
                await asyncio.sleep(interval)
            
            logger.info(f"Collecte terminée: {len(self.distances)} mesures")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de données: {e}")
            return False
    
    def analyze_data(self):
        """
        Analyse les données collectées et suggère un seuil optimal
        
        Returns:
            float: Suggestion de seuil en mm
        """
        if not self.distances:
            logger.warning("Aucune donnée à analyser")
            return None
            
        # Statistiques de base
        min_dist = min(self.distances)
        max_dist = max(self.distances)
        avg_dist = sum(self.distances) / len(self.distances)
        
        logger.info("=== ANALYSE DES DONNÉES ===")
        logger.info(f"Nombre de mesures: {len(self.distances)}")
        logger.info(f"Distance minimale: {min_dist:.1f}mm")
        logger.info(f"Distance maximale: {max_dist:.1f}mm")
        logger.info(f"Distance moyenne: {avg_dist:.1f}mm")
        
        # Calcul d'un seuil suggéré basé sur les données
        sorted_distances = sorted(self.distances)
        
        # Si l'écart entre min et max est significatif, on peut trouver un seuil naturel
        if max_dist - min_dist > 100:  # Écart d'au moins 10cm
            # Trouver le plus grand écart dans les données triées
            max_gap = 0
            gap_index = 0
            
            for i in range(1, len(sorted_distances)):
                gap = sorted_distances[i] - sorted_distances[i-1]
                if gap > max_gap:
                    max_gap = gap
                    gap_index = i
            
            suggested_threshold = (sorted_distances[gap_index-1] + sorted_distances[gap_index]) / 2
            
            logger.info(f"Plus grand écart détecté: {max_gap:.1f}mm")
            logger.info(f"Seuil suggéré: {suggested_threshold:.1f}mm")
            
            return suggested_threshold
        else:
            logger.info("Écart insuffisant pour déterminer un seuil naturel")
            return None
    
    def generate_graph(self, save_path="sensor_data"):
        """
        Génère un graphique des données collectées
        
        Args:
            save_path: Chemin où enregistrer le graphique
        """
        if not self.distances:
            logger.warning("Aucune donnée à visualiser")
            return False
            
        try:
            # Créer le dossier si nécessaire
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                
            # Générer le nom de fichier avec horodatage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_path, f"vl53l0x_test_{timestamp}.png")
            
            # Créer le graphique
            plt.figure(figsize=(12, 8))
            
            # Tracer les distances
            plt.subplot(2, 1, 1)
            plt.plot(self.timestamps, self.distances, 'b-', label='Distance (mm)')
            plt.axhline(y=self.threshold, color='r', linestyle='--', label=f'Seuil ({self.threshold}mm)')
            plt.fill_between(self.timestamps, 0, self.threshold, color='red', alpha=0.1)
            plt.ylabel('Distance (mm)')
            plt.title('Test du capteur VL53L0X')
            plt.legend()
            plt.grid(True)
            
            # Tracer les détections
            plt.subplot(2, 1, 2)
            plt.plot(self.timestamps, self.detections, 'g-', label='Détection')
            plt.ylabel('Détection')
            plt.xlabel('Temps (s)')
            plt.yticks([0, 1], ['Non', 'Oui'])
            plt.legend()
            plt.grid(True)
            
            # Enregistrer le graphique
            plt.tight_layout()
            plt.savefig(filename)
            logger.info(f"Graphique enregistré: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique: {e}")
            return False
    
    async def calibrate(self, duration=30, interval=0.1):
        """
        Processus complet de calibration du capteur
        
        Args:
            duration: Durée du test en secondes
            interval: Intervalle entre les mesures en secondes
        """
        logger.info("=== CALIBRATION DU CAPTEUR VL53L0X ===")
        
        # Collecter des données
        success = await self.collect_data(duration=duration, interval=interval)
        if not success:
            return None
            
        # Analyser les données
        suggested_threshold = self.analyze_data()
        
        # Générer un graphique
        self.generate_graph()
        
        return suggested_threshold

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Test et calibration du capteur VL53L0X')
    parser.add_argument('--read', action='store_true', help='Test simple de lecture')
    parser.add_argument('--collect', action='store_true', help='Collecte de données')
    parser.add_argument('--calibrate', action='store_true', help='Calibration complète')
    parser.add_argument('--duration', type=int, default=30, help='Durée du test en secondes')
    parser.add_argument('--threshold', type=float, help='Seuil de détection en mm')
    
    args = parser.parse_args()
    
    # Créer l'instance de test
    tester = VL53L0XTester(threshold=args.threshold)
    
    # Initialiser le capteur
    if not await tester.initialize():
        logger.error("Impossible d'initialiser le capteur VL53L0X")
        return
    
    # Exécuter le test demandé
    if args.read or (not args.collect and not args.calibrate):
        await tester.test_reading(duration=args.duration)
    
    if args.collect:
        await tester.collect_data(duration=args.duration)
        tester.analyze_data()
        tester.generate_graph()
    
    if args.calibrate:
        suggested_threshold = await tester.calibrate(duration=args.duration)
        
        if suggested_threshold:
            logger.info("\n=== RÉSULTATS DE CALIBRATION ===")
            logger.info(f"Seuil actuel: {tester.threshold}mm")
            logger.info(f"Seuil suggéré: {suggested_threshold:.1f}mm")
            
            # Suggérer la mise à jour du fichier .env
            logger.info("\nPour mettre à jour le seuil, ajoutez cette ligne à votre fichier .env:")
            logger.info(f"DISTANCE_THRESHOLD_MM={suggested_threshold:.1f}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrompu par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur lors de l'exécution du test: {e}")
        sys.exit(1)
