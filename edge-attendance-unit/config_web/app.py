#!/usr/bin/env python3
"""
Interface web de configuration pour le module Edge Attendance System
"""

import os
import sys
import secrets
import subprocess
import socket
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import logging
import requests

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

app = Flask(__name__)
# Session signing key. Set FLASK_SECRET_KEY in the environment for a stable key
# across restarts; falls back to a random per-process key in development.
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Configuration du logger
logger = setup_logger(
    name="config_web",
    level=logging.INFO,
    console_level=logging.INFO
)

# Chemin vers le fichier .env
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

def kill_process_on_port(port):
    """
    Tue le processus qui occupe le port spécifié
    
    Args:
        port (int): Port à libérer
    
    Returns:
        bool: True si le port a été libéré, False sinon
    """
    try:
        # Trouver le processus qui utilise le port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            logger.info(f"Processus trouvés sur le port {port}: {pids}")
            
            # Tuer chaque processus
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    logger.info(f"Processus {pid} tué avec succès")
                except subprocess.CalledProcessError:
                    logger.warning(f"Impossible de tuer le processus {pid}")
            
            # Attendre un peu pour que le port se libère
            import time
            time.sleep(2)
            
            # Vérifier que le port est maintenant libre
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('0.0.0.0', port))
                    logger.info(f"Port {port} libéré avec succès")
                    return True
            except OSError:
                logger.error(f"Port {port} toujours occupé après avoir tué les processus")
                return False
        else:
            logger.info(f"Aucun processus trouvé sur le port {port}")
            return True
            
    except FileNotFoundError:
        # lsof n'est pas disponible, essayer avec netstat
        logger.warning("lsof non disponible, tentative avec netstat")
        try:
            result = subprocess.run(['netstat', '-tlnp'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f':{port} ' in line and 'LISTEN' in line:
                        # Extraire le PID de la ligne netstat
                        parts = line.split()
                        if len(parts) >= 7:
                            pid_program = parts[6]
                            if '/' in pid_program:
                                pid = pid_program.split('/')[0]
                                try:
                                    subprocess.run(['kill', '-9', pid], check=True)
                                    logger.info(f"Processus {pid} tué avec netstat")
                                    import time
                                    time.sleep(2)
                                    return True
                                except subprocess.CalledProcessError:
                                    logger.warning(f"Impossible de tuer le processus {pid}")
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur avec netstat: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Erreur lors de la libération du port {port}: {e}")
        return False

def ensure_port_available(port):
    """
    S'assure que le port spécifié est disponible
    
    Args:
        port (int): Port à vérifier/libérer
    
    Returns:
        bool: True si le port est disponible, False sinon
    """
    try:
        # Tester si le port est libre
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            logger.info(f"Port {port} disponible")
            return True
    except OSError:
        logger.warning(f"Port {port} occupé, tentative de libération...")
        return kill_process_on_port(port)

class ConfigManager:
    """Gestionnaire de configuration pour le fichier .env"""
    
    def __init__(self, env_file_path):
        self.env_file = env_file_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier .env"""
        if not os.path.exists(self.env_file):
            logger.warning(f"Fichier .env non trouvé: {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Nettoyer les guillemets
                        value = value.strip().strip('"').strip("'")
                        self.config[key] = value
            logger.info(f"Configuration chargée: {len(self.config)} paramètres")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier .env"""
        try:
            # Lire le fichier existant pour préserver les commentaires
            lines = []
            if os.path.exists(self.env_file):
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
            
            # Créer le nouveau contenu
            new_lines = []
            updated_keys = set()
            
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                    key = line_stripped.split('=', 1)[0]
                    if key in self.config:
                        # Mettre à jour la valeur
                        new_lines.append(f"{key}={self.config[key]}\n")
                        updated_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Ajouter les nouvelles clés
            for key, value in self.config.items():
                if key not in updated_keys:
                    new_lines.append(f"{key}={value}\n")
            
            # Écrire le fichier
            with open(self.env_file, 'w') as f:
                f.writelines(new_lines)
            
            logger.info("Configuration sauvegardée avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Définit une valeur de configuration"""
        self.config[key] = str(value)
    
    def get_all(self):
        """Retourne toute la configuration"""
        return self.config.copy()

# Instance du gestionnaire de configuration
config_manager = ConfigManager(ENV_FILE)

@app.route('/')
def index():
    """Page d'accueil avec le dashboard"""
    config = config_manager.get_all()
    
    # Informations système
    system_info = {
        'hostname': subprocess.getoutput('hostname'),
        'uptime': subprocess.getoutput('uptime -p'),
        'ip': subprocess.getoutput("hostname -I | awk '{print $1}'"),
        'git_branch': subprocess.getoutput('git branch --show-current'),
        'git_commit': subprocess.getoutput('git rev-parse --short HEAD')
    }
    
    return render_template('index.html', config=config, system_info=system_info)

@app.route('/config')
def config_page():
    """Page de configuration"""
    config = config_manager.get_all()
    return render_template('config.html', config=config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """API pour mettre à jour la configuration avec support mode local/prod"""
    try:
        data = request.get_json()
        logger.info(f"Réception données config: {data}")
        
        # Validation des données
        required_fields = ['BASE_URL', 'API_KEY', 'MODULE_ID', 'connection_mode']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Champ requis manquant: {field}'}), 400
        
        # Validation des types et valeurs
        try:
            if 'DISTANCE_THRESHOLD_MM' in data:
                float(data['DISTANCE_THRESHOLD_MM'])
            if 'SIMILARITY_THRESHOLD' in data:
                val = float(data['SIMILARITY_THRESHOLD'])
                if not 0.1 <= val <= 1.0:
                    raise ValueError("SIMILARITY_THRESHOLD doit être entre 0.1 et 1.0")
            if 'PRESENCE_COOLDOWN' in data:
                int(data['PRESENCE_COOLDOWN'])
            if 'MAX_FAILURES' in data:
                int(data['MAX_FAILURES'])
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Valeur invalide: {e}'}), 400
        
        # Mettre à jour la configuration selon le mode
        connection_mode = data.get('connection_mode', 'local')
        
        # Configuration commune
        common_fields = [
            'BASE_URL', 'API_KEY', 'MODULE_ID', 'MQTT_USERNAME', 'MQTT_PASSWORD',
            'DISTANCE_THRESHOLD_MM', 'SIMILARITY_THRESHOLD', 'PRESENCE_COOLDOWN', 'MAX_FAILURES'
        ]
        
        for field in common_fields:
            if field in data:
                config_manager.set(field, data[field])
        
        # Configuration spécifique au mode
        config_manager.set('MQTT_CONNECTION_MODE', connection_mode)
        
        if connection_mode == 'local':
            # Mode local: MQTT natif
            config_manager.set('MQTT_BROKER', data.get('MQTT_BROKER', ''))
            config_manager.set('MQTT_PORT', data.get('MQTT_PORT', '1883'))
            config_manager.set('MQTT_TLS_PORT', data.get('MQTT_TLS_PORT', '8883'))
            config_manager.set('USE_TLS', str(data.get('USE_TLS', False)))
            config_manager.set('MQTT_USE_WEBSOCKETS', 'False')
            config_manager.set('MQTT_WSS_PORT', '443')  # Valeur par défaut
            
        elif connection_mode == 'prod':
            # Mode production: WebSocket sécurisé
            config_manager.set('MQTT_BROKER', data.get('MQTT_BROKER', ''))
            config_manager.set('MQTT_WSS_PORT', data.get('MQTT_WSS_PORT', '443'))
            config_manager.set('USE_TLS', 'True')
            config_manager.set('MQTT_USE_WEBSOCKETS', 'True')
            config_manager.set('MQTT_PORT', '1883')  # Valeur par défaut
            config_manager.set('MQTT_TLS_PORT', '8883')  # Valeur par défaut
        
        # Sauvegarder
        if config_manager.save_config():
            logger.info(f"Configuration sauvegardée en mode {connection_mode}")
            return jsonify({
                'success': True, 
                'message': f'Configuration mise à jour en mode {connection_mode}',
                'mode': connection_mode
            })
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la sauvegarde'}), 500
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_backend_connection():
    """API pour tester la connexion au backend"""
    try:
        data = request.get_json()
        base_url = data.get('BASE_URL', '')
        
        if not base_url:
            return jsonify({'success': False, 'message': 'URL requise'}), 400
        
        # Tester la connexion au backend
        test_url = f"{base_url.rstrip('/')}/health"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True, 
                'message': 'Connexion backend réussie',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Backend inaccessible (HTTP {response.status_code})',
                'status_code': response.status_code
            })
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Timeout de connexion (>10s)'}), 408
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'message': 'Impossible de se connecter au serveur'}), 503
    except Exception as e:
        logger.error(f"Erreur test connexion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-mqtt', methods=['POST'])
def test_mqtt_connection():
    """API pour tester la connexion MQTT"""
    try:
        data = request.get_json()
        logger.info(f"Test MQTT avec config: {data}")
        
        # Import paho.mqtt.client for testing
        import paho.mqtt.client as mqtt
        import ssl
        import threading
        import time
        
        mode = data.get('mode', 'local')
        broker = data.get('MQTT_BROKER', '')
        username = data.get('MQTT_USERNAME', '')
        password = data.get('MQTT_PASSWORD', '')
        
        if not broker:
            return jsonify({'success': False, 'message': 'Broker MQTT requis'}), 400
        
        # Configuration selon le mode
        test_result = {'success': False, 'message': 'Test non effectué'}
        
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                test_result['success'] = True
                test_result['message'] = f'Connexion MQTT réussie (mode {mode})'
                test_result['details'] = {
                    'broker': broker,
                    'mode': mode,
                    'rc': rc
                }
            else:
                test_result['success'] = False
                test_result['message'] = f'Échec connexion MQTT: code {rc}'
                test_result['details'] = {'rc': rc}
            
            # Déconnexion immédiate après test
            client.disconnect()
        
        def on_disconnect(client, userdata, rc, properties=None):
            test_result['disconnected'] = True
        
        # Créer le client selon le mode
        if mode == 'prod':
            # Mode production: WebSocket sécurisé
            client = mqtt.Client(transport="websockets")
            port = int(data.get('MQTT_WSS_PORT', 443))
            use_tls = True
        else:
            # Mode local: MQTT natif
            client = mqtt.Client()
            port = int(data.get('MQTT_PORT', 1883))
            use_tls = data.get('USE_TLS', False)
            
            # Utiliser port TLS si activé en local
            if use_tls:
                port = int(data.get('MQTT_TLS_PORT', 8883))
        
        # Configuration authentification
        if username and password:
            client.username_pw_set(username, password)
        
        # Configuration TLS
        if use_tls:
            if mode == 'prod':
                # Production: TLS avec certificats système
                client.tls_set()
            else:
                # Local: TLS simple
                context = ssl.create_default_context()
                client.tls_set_context(context)
        
        # Callbacks
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        # Test de connexion avec timeout
        try:
            logger.info(f"Tentative connexion MQTT: {broker}:{port} (TLS: {use_tls})")
            client.connect(broker, port, 10)
            
            # Boucle avec timeout
            start_time = time.time()
            client.loop_start()
            
            # Attendre jusqu'à 15 secondes pour la connexion
            while time.time() - start_time < 15:
                if 'disconnected' in test_result:
                    break
                time.sleep(0.1)
            
            client.loop_stop()
            
            if not test_result['success']:
                if 'message' not in test_result or test_result['message'] == 'Test non effectué':
                    test_result['message'] = 'Timeout de connexion MQTT'
            
            return jsonify(test_result)
            
        except Exception as e:
            logger.error(f"Erreur test MQTT: {e}")
            return jsonify({
                'success': False, 
                'message': f'Erreur connexion MQTT: {str(e)}',
                'details': {'exception': str(e)}
            })
            
    except Exception as e:
        logger.error(f"Erreur test MQTT global: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/git-pull', methods=['POST'])
def git_pull():
    """API pour effectuer un git pull et redémarrer le service"""
    try:
        # Changer vers le répertoire du projet
        project_dir = os.path.dirname(os.path.dirname(__file__))
        os.chdir(project_dir)
        
        # Ajouter le répertoire comme sûr pour Git
        safe_dir_result = subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', project_dir], 
                                       capture_output=True, text=True)
        if safe_dir_result.returncode != 0:
            logger.warning(f"Impossible d'ajouter le répertoire comme sûr: {safe_dir_result.stderr}")
        
        # Configuration SSH pour Git - créer le répertoire .ssh si nécessaire
        ssh_dir = os.path.expanduser('~/.ssh')
        os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
        
        # Créer known_hosts si inexistant
        known_hosts_file = os.path.join(ssh_dir, 'known_hosts')
        if not os.path.exists(known_hosts_file):
            open(known_hosts_file, 'a').close()
            os.chmod(known_hosts_file, 0o600)
        
        # Ajouter GitHub à known_hosts si pas déjà présent
        with open(known_hosts_file, 'r') as f:
            content = f.read()
        
        if 'github.com' not in content:
            github_keys_result = subprocess.run(['ssh-keyscan', '-H', 'github.com'], 
                                              capture_output=True, text=True)
            if github_keys_result.returncode == 0:
                with open(known_hosts_file, 'a') as f:
                    f.write(github_keys_result.stdout)
                logger.info("Clés d'hôte GitHub ajoutées")
        
        # Exécuter git pull
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
        
        if result.returncode == 0:
            output_message = result.stdout
            
            # Vérifier s'il y a eu des changements
            if "Already up to date" not in result.stdout:
                logger.info("Modifications détectées après git pull, redémarrage du service...")
                
                # Arrêter le service principal s'il est en cours d'exécution
                try:
                    # Arrêter le service systemd
                    stop_result = subprocess.run(['sudo', 'systemctl', 'stop', 'crec-presence'], 
                                               capture_output=True, text=True, timeout=30)
                    if stop_result.returncode == 0:
                        output_message += "\n✓ Service principal arrêté"
                    else:
                        output_message += f"\n⚠ Erreur lors de l'arrêt: {stop_result.stderr}"
                    
                except subprocess.TimeoutExpired:
                    logger.warning("Timeout lors de l'arrêt du service")
                    output_message += "\n⚠ Timeout lors de l'arrêt du service"
                
                # Redémarrer le service après un délai
                try:
                    import time
                    time.sleep(2)  # Attendre un peu avant de redémarrer
                    
                    # Redémarrer le service systemd
                    restart_result = subprocess.run(['sudo', 'systemctl', 'start', 'crec-presence'], 
                                                  capture_output=True, text=True, timeout=30)
                    if restart_result.returncode == 0:
                        output_message += "\n✓ Service systemd redémarré"
                        logger.info("Service redémarré via systemd")
                    else:
                        output_message += f"\n⚠ Erreur lors du redémarrage: {restart_result.stderr}"
                
                except subprocess.TimeoutExpired:
                    logger.error("Timeout lors du redémarrage du service")
                    output_message += "\n⚠ Timeout lors du redémarrage"
                except Exception as restart_error:
                    logger.error(f"Erreur lors du redémarrage: {restart_error}")
                    output_message += f"\n⚠ Erreur de redémarrage: {str(restart_error)}"
            
            return jsonify({
                'success': True, 
                'message': 'Mise à jour effectuée avec succès',
                'output': output_message,
                'restart_performed': "Already up to date" not in result.stdout
            })
        else:
            # Gestion des erreurs de git pull
            error_message = result.stderr
            
            if "would be overwritten by merge" in error_message:
                logger.warning("Conflit détecté, annulation des modifications locales...")
                
                # S'assurer que le répertoire est sûr pour Git et configurer SSH
                subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', project_dir], 
                             capture_output=True, text=True)
                
                # Configuration SSH pour known_hosts
                ssh_dir = os.path.expanduser('~/.ssh')
                os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
                
                known_hosts_file = os.path.join(ssh_dir, 'known_hosts')
                if not os.path.exists(known_hosts_file):
                    open(known_hosts_file, 'a').close()
                    os.chmod(known_hosts_file, 0o600)
                
                # Ajouter GitHub à known_hosts si nécessaire
                with open(known_hosts_file, 'r') as f:
                    content = f.read()
                
                if 'github.com' not in content:
                    github_keys_result = subprocess.run(['ssh-keyscan', '-H', 'github.com'], 
                                                      capture_output=True, text=True)
                    if github_keys_result.returncode == 0:
                        with open(known_hosts_file, 'a') as f:
                            f.write(github_keys_result.stdout)
                
                # Annuler toutes les modifications locales
                checkout_result = subprocess.run(['git', 'checkout', '--', '.'], 
                                               capture_output=True, text=True)
                
                if checkout_result.returncode == 0:
                    # Retry git pull après checkout
                    retry_result = subprocess.run(['git', 'pull'], 
                                                capture_output=True, text=True)
                    
                    if retry_result.returncode == 0:
                        output_message = "⚠ Modifications locales annulées (priorité aux versions commitées)\n"
                        output_message += retry_result.stdout
                        
                        # Vérifier s'il y a eu des changements et redémarrer si nécessaire
                        if "Already up to date" not in retry_result.stdout:
                            logger.info("Modifications détectées après git pull, redémarrage du service...")
                            
                            # Arrêter et redémarrer le service
                            try:
                                # Arrêter le service systemd
                                stop_result = subprocess.run(['sudo', 'systemctl', 'stop', 'crec-presence'], 
                                                           capture_output=True, text=True, timeout=30)
                                
                                import time
                                time.sleep(2)  # Attendre un peu
                                
                                # Redémarrer le service systemd
                                start_result = subprocess.run(['sudo', 'systemctl', 'start', 'crec-presence'], 
                                                            capture_output=True, text=True, timeout=30)
                                if start_result.returncode == 0:
                                    output_message += "\n✓ Service redémarré avec nouvelles versions"
                                else:
                                    output_message += f"\n⚠ Erreur lors du redémarrage: {start_result.stderr}"
                                
                            except subprocess.TimeoutExpired:
                                logger.error("Timeout lors du redémarrage")
                                output_message += "\n⚠ Timeout lors du redémarrage"
                            except Exception as restart_error:
                                logger.error(f"Erreur lors du redémarrage: {restart_error}")
                                output_message += f"\n⚠ Erreur de redémarrage: {str(restart_error)}"
                        
                        return jsonify({
                            'success': True,
                            'message': 'Mise à jour réussie après résolution de conflit',
                            'output': output_message,
                            'restart_performed': "Already up to date" not in retry_result.stdout
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'Erreur lors du git pull après résolution de conflit',
                            'error': retry_result.stderr
                        }), 500
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Impossible d\'annuler les modifications locales',
                        'error': checkout_result.stderr
                    }), 500
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Erreur lors de la mise à jour',
                    'error': error_message
                }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/system-info')
def system_info():
    """API pour récupérer les informations système"""
    try:
        info = {
            'hostname': subprocess.getoutput('hostname'),
            'uptime': subprocess.getoutput('uptime -p'),
            'ip': subprocess.getoutput("hostname -I | awk '{print $1}'"),
            'git_branch': subprocess.getoutput('git branch --show-current'),
            'git_commit': subprocess.getoutput('git rev-parse --short HEAD'),
            'git_status': subprocess.getoutput('git status --porcelain'),
            'disk_usage': subprocess.getoutput('df -h / | tail -1'),
            'memory_usage': subprocess.getoutput('free -h | grep Mem'),
            'temperature': subprocess.getoutput('vcgencmd measure_temp 2>/dev/null || echo "N/A"')
        }
        return jsonify(info)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations système: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """API pour tester la connexion aux services"""
    try:
        data = request.get_json()
        base_url = data.get('BASE_URL', config_manager.get('BASE_URL'))
        
        if not base_url:
            return jsonify({'success': False, 'message': 'URL du serveur non définie'})
        
        # Test de ping vers le serveur
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            
            if response.status_code == 200:
                return jsonify({'success': True, 'message': 'Connexion OK'})
            else:
                return jsonify({'success': False, 'message': f'Erreur HTTP: {response.status_code}'})
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'Impossible de se connecter au serveur'})
        except requests.exceptions.Timeout:
            return jsonify({'success': False, 'message': 'Timeout de connexion'})
        except requests.exceptions.RequestException as e:
            return jsonify({'success': False, 'message': f'Erreur de requête: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur inattendue: {str(e)}'})

@app.route('/api/restart-service', methods=['POST'])
def restart_service():
    """API pour redémarrer le service du module"""
    try:
        # Redémarrer directement le service systemd
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'crec-presence'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Service crec-presence redémarré avec succès")
            return jsonify({
                'success': True, 
                'message': 'Service systemd redémarré avec succès'
            })
        else:
            logger.error(f"Erreur lors du redémarrage du service: {result.stderr}")
            return jsonify({
                'success': False, 
                'message': 'Erreur lors du redémarrage du service',
                'error': result.stderr.strip() if result.stderr else 'Erreur inconnue'
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout lors du redémarrage du service")
        return jsonify({
            'success': False, 
            'message': 'Timeout lors du redémarrage du service (>30s)'
        }), 500
    except Exception as e:
        logger.error(f"Erreur lors du redémarrage du service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/start-service', methods=['POST'])
def start_service():
    """API pour démarrer le service du module"""
    try:
        # Vérifier d'abord si le service est déjà actif
        status_result = subprocess.run(['systemctl', 'is-active', 'crec-presence'], 
                                     capture_output=True, text=True)
        
        if status_result.returncode == 0 and status_result.stdout.strip() == 'active':
            return jsonify({
                'success': False, 
                'message': 'Le service est déjà en cours d\'exécution'
            }), 400
        
        # Démarrer le service systemd
        result = subprocess.run(['sudo', 'systemctl', 'start', 'crec-presence'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Service crec-presence démarré avec succès")
            return jsonify({
                'success': True, 
                'message': 'Service systemd démarré avec succès'
            })
        else:
            logger.error(f"Erreur lors du démarrage du service: {result.stderr}")
            return jsonify({
                'success': False, 
                'message': 'Erreur lors du démarrage du service',
                'error': result.stderr.strip() if result.stderr else 'Erreur inconnue'
            }), 500
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout lors du démarrage du service")
        return jsonify({
            'success': False, 
            'message': 'Timeout lors du démarrage du service (>30s)'
        }), 500
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop-service', methods=['POST'])
def stop_service():
    """API pour arrêter le service du module"""
    try:
        # Arrêter le service systemd
        result = subprocess.run(['sudo', 'systemctl', 'stop', 'crec-presence'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Service crec-presence arrêté avec succès")
            return jsonify({
                'success': True, 
                'message': 'Service systemd arrêté avec succès'
            })
        else:
            logger.error(f"Erreur lors de l'arrêt du service: {result.stderr}")
            return jsonify({
                'success': False, 
                'message': 'Erreur lors de l\'arrêt du service',
                'error': result.stderr.strip() if result.stderr else 'Erreur inconnue'
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout lors de l'arrêt du service")
        return jsonify({
            'success': False, 
            'message': 'Timeout lors de l\'arrêt du service (>30s)'
        }), 500
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/service-status')
def service_status():
    """API pour vérifier le statut du service"""
    try:
        # Vérifier le statut du service systemd
        status_result = subprocess.run(['systemctl', 'is-active', 'crec-presence'], 
                                     capture_output=True, text=True)
        
        # Obtenir des informations détaillées sur le service
        detailed_result = subprocess.run(['systemctl', 'status', 'crec-presence', '--no-pager', '--lines=0'], 
                                       capture_output=True, text=True)
        
        # Vérifier si le service est activé pour le démarrage automatique
        enabled_result = subprocess.run(['systemctl', 'is-enabled', 'crec-presence'], 
                                      capture_output=True, text=True)
        
        # Obtenir le PID principal si le service est actif
        main_pid = None
        if status_result.returncode == 0 and status_result.stdout.strip() == 'active':
            pid_result = subprocess.run(['systemctl', 'show', '-p', 'MainPID', 'crec-presence'], 
                                      capture_output=True, text=True)
            if pid_result.returncode == 0:
                pid_line = pid_result.stdout.strip()
                if '=' in pid_line:
                    main_pid = pid_line.split('=')[1]
                    if main_pid == '0':
                        main_pid = None
        
        # Déterminer le statut
        if status_result.returncode == 0:
            status = status_result.stdout.strip()
            is_active = status == 'active'
        else:
            # Le service pourrait ne pas exister ou être dans un état d'erreur
            status = 'inactive'
            is_active = False
        
        # Analyser les informations détaillées pour obtenir plus de contexte
        service_info = {
            'service_type': 'systemd',
            'status': status,
            'active': is_active,
            'enabled': enabled_result.stdout.strip() == 'enabled' if enabled_result.returncode == 0 else False,
            'main_pid': main_pid
        }
        
        # Ajouter des informations supplémentaires si disponibles
        if detailed_result.returncode == 0:
            lines = detailed_result.stdout.split('\n')
            for line in lines:
                if 'Active:' in line:
                    service_info['detailed_status'] = line.strip()
                    break
        
        # Si le service n'existe pas, indiquer qu'il n'est pas installé
        if 'not-found' in status or 'could not be found' in detailed_result.stderr.lower():
            service_info.update({
                'status': 'not-found',
                'active': False,
                'enabled': False,
                'error': 'Service crec-presence non trouvé. Utilisez le script d\'installation.'
            })
        
        return jsonify(service_info)
                
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        return jsonify({
            'service_type': 'systemd',
            'status': 'error',
            'active': False,
            'enabled': False,
            'error': str(e)
        }), 500

@app.route('/api/service-logs')
def service_logs():
    """API pour récupérer les logs du service"""
    try:
        lines = request.args.get('lines', '50')  # Par défaut 50 lignes
        
        # Obtenir les logs du service
        result = subprocess.run(['journalctl', '-u', 'crec-presence', '-n', lines, '--no-pager'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'logs': result.stdout,
                'lines_requested': lines
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la récupération des logs',
                'error': result.stderr.strip() if result.stderr else 'Erreur inconnue'
            }), 500
                
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Port fixe à utiliser
    TARGET_PORT = 80
    
    logger.info(f"Tentative d'utilisation du port {TARGET_PORT}")
    
    # S'assurer que le port est disponible
    if not ensure_port_available(TARGET_PORT):
        logger.error(f"Impossible de libérer le port {TARGET_PORT}")
        sys.exit(1)
    
    logger.info(f"Démarrage de l'interface web sur le port {TARGET_PORT}")
    
    # Affichage des URLs d'accès avec détection de l'IP locale
    try:
        # Obtenir l'IP du réseau local
        local_ip = subprocess.getoutput("hostname -I | awk '{print $1}'").strip()
        if not local_ip:
            local_ip = "IP_NON_DETECTEE"
    except:
        local_ip = "IP_NON_DETECTEE"
    
    if TARGET_PORT == 80:
        print(f"Interface web accessible sur :")
        print(f"  • http://localhost")
        if local_ip != "IP_NON_DETECTEE":
            print(f"  • http://{local_ip}")
        print(f"  • http://0.0.0.0 (toutes interfaces)")
    else:
        print(f"Interface web accessible sur :")
        print(f"  • http://localhost:{TARGET_PORT}")
        if local_ip != "IP_NON_DETECTEE":
            print(f"  • http://{local_ip}:{TARGET_PORT}")
        print(f"  • http://0.0.0.0:{TARGET_PORT} (toutes interfaces)")
    
    try:
        app.run(host='0.0.0.0', port=TARGET_PORT, debug=False)
    except PermissionError:
        logger.error(f"Permission refusée pour le port {TARGET_PORT}")
        print(f"Erreur: Permission refusée pour le port {TARGET_PORT}")
        if TARGET_PORT < 1024:
            print("Le service doit être exécuté avec les privilèges root pour utiliser ce port")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {TARGET_PORT} déjà utilisé par un autre processus")
            print(f"Erreur: Port {TARGET_PORT} déjà utilisé")
            print("Arrêtez l'autre service ou changez de port")
        else:
            logger.error(f"Erreur réseau: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Arrêt de l'interface web")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface web: {e}")
        sys.exit(1)
