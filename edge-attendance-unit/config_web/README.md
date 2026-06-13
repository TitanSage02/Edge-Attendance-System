# Interface Web de Configuration — Edge Attendance Unit

Cette interface web permet de configurer facilement le module Edge Attendance System depuis un navigateur web.

## Fonctionnalités

- **Dashboard** : Vue d'ensemble du système avec informations temps réel
- **Configuration** : Modification des paramètres du module (.env)
- **Git Pull** : Mise à jour automatique du code depuis le repository
- **Test de connexion** : Vérification de la connectivité avec le serveur
- **Gestion du service** : Redémarrage du service du module
- **Interface moderne** : Design responsive avec Bootstrap 5

## Installation

### Installation automatique (recommandée)

```bash
cd /home/unit/CREC-Presence-Unit/config_web
sudo chmod +x install.sh
sudo ./install.sh
```

### Installation manuelle

```bash
# Installer les dépendances
pip3 install -r requirements.txt

# Créer le fichier .env
cp ../.env.example ../.env

# Lancer l'interface web
python3 app.py
```

## Utilisation

### Accès à l'interface

Une fois installé, l'interface web est accessible sur :
- **Local** : http://localhost:5000
- **Réseau** : http://IP_DU_PI:5000

### Configuration du module

1. Accéder à l'onglet **Configuration**
2. Modifier les paramètres souhaités :
   - **URL du serveur** : Adresse du serveur backend Edge Attendance System
   - **Clé API** : Clé d'authentification
   - **Seuil de distance** : Distance de détection en mm
   - **ID du module** : Identifiant unique du module
   - **Paramètres MQTT** : Configuration du broker MQTT

3. Cliquer sur **Sauvegarder Configuration**

### Actions disponibles

- **Mettre à jour** : Effectue un `git pull` pour récupérer les dernières modifications
- **Tester Connexion** : Vérifie la connectivité avec le serveur backend
- **Redémarrer Service** : Redémarre le service du module de présence
- **Actualiser** : Met à jour les informations système

## Gestion du service

```bash
# Vérifier le statut
sudo systemctl status crec-config-web

# Arrêter le service
sudo systemctl stop crec-config-web

# Démarrer le service
sudo systemctl start crec-config-web

# Redémarrer le service
sudo systemctl restart crec-config-web

# Voir les logs
sudo journalctl -u crec-config-web -f
```

## Sécurité

- L'interface web est conçue pour être utilisée sur un réseau local sécurisé
- Les mots de passe sont masqués par défaut dans l'interface
- Aucune authentification n'est requise (à configurer selon vos besoins)

## Développement

### Structure des fichiers

```
config_web/
├── app.py                    # Application Flask principale
├── requirements.txt          # Dépendances Python
├── install.sh               # Script d'installation
├── crec-config-web.service  # Service systemd
├── templates/
│   ├── base.html            # Template de base
│   ├── index.html           # Dashboard
│   └── config.html          # Page de configuration
└── README.md               # Cette documentation
```

### Personnalisation

L'interface peut être personnalisée en modifiant :
- **CSS** : Styles dans `templates/base.html`
- **JavaScript** : Fonctions dans les templates
- **Configuration** : Paramètres dans `app.py`

## Dépannage

### L'interface ne se lance pas

1. Vérifier les logs : `sudo journalctl -u crec-config-web -f`
2. Vérifier les dépendances : `pip3 list | grep -E "(flask|requests|python-dotenv)"`
3. Vérifier les permissions : `ls -la /home/unit/CREC-Presence-Unit/`

### Erreur lors de la sauvegarde

1. Vérifier que le fichier .env existe et est accessible en écriture
2. Vérifier les permissions : `ls -la /home/unit/CREC-Presence-Unit/.env`
3. Vérifier les logs de l'application

### Git pull ne fonctionne pas

1. Vérifier que git est installé : `git --version`
2. Vérifier les permissions dans le répertoire : `ls -la /home/unit/CREC-Presence-Unit/`
3. Tester manuellement : `cd /home/unit/CREC-Presence-Unit && git pull`

## Support

Pour toute question ou problème, consulter les logs de l'application :

```bash
sudo journalctl -u crec-config-web -f
```
