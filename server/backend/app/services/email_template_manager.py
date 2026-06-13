"""
-------------------------------------------------------------
Gestionnaire de templates d'emails professionnels
-------------------------------------------------------------
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import re
from string import Template

class EmailTemplateManager:
    """Gestionnaire pour les templates d'emails professionnels."""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "email_templates"
        self.base_template_path = self.templates_dir / "base_template.html"
        self._base_template = None
        
    def _load_base_template(self) -> str:
        """Charge le template de base."""
        if self._base_template is None:
            if self.base_template_path.exists():
                self._base_template = self.base_template_path.read_text("utf-8")
            else:
                # Template de base minimal en cas d'absence du fichier
                self._base_template = """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Edge Attendance System</h2>
                        $content
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 14px;">
                            Cordialement,<br>
                            <strong>L'équipe Edge Attendance System</strong>
                        </p>
                        <p style="color: #999; font-size: 12px;">
                            © $year Edge Attendance System. Tous droits réservés.
                        </p>
                    </div>
                </body>
                </html>
                """
        return self._base_template
    
    def _load_content_template(self, template_name: str) -> str:
        """Charge un template de contenu spécifique."""
        template_path = self.templates_dir / f"{template_name}.html"
        if template_path.exists():
            return template_path.read_text("utf-8")
        return ""
    
    def render_email(self, template_name: str, **kwargs) -> str:
        """
        Génère un email complet en combinant le template de base et le contenu.
        
        Args:
            template_name: Nom du template de contenu (sans extension)
            **kwargs: Variables à injecter dans le template
        
        Returns:
            HTML de l'email complet
        """
        # Charger le template de contenu
        content_template = self._load_content_template(template_name)
        
        content = content_template.format(**kwargs)
        
        # Charger le template de base
        base_template_str = self._load_base_template()
        
        # Utiliser string.Template pour éviter les conflits avec les CSS curly braces
        base_template = Template(base_template_str)
        
        # Variables globales pour le template de base
        global_vars = {
            'content': content,
            'year': datetime.now().year,
            'version': '1.0',  # Version du système
        }
        
        # Générer l'email final en utilisant safe_substitute pour ignorer les variables manquantes
        return base_template.safe_substitute(**global_vars)
    
    def get_subject(self, template_name: str, **kwargs) -> str:
        """
        Retourne un sujet professionnel selon le type de template.
        
        Args:
            template_name: Nom du template
            **kwargs: Variables pour personnaliser le sujet
          Returns:
            Sujet de l'email
        """
        subjects = {
            'new_password': 'Edge Attendance System - Mise à jour de vos identifiants de connexion',
            'welcome': 'Edge Attendance System - Bienvenue dans le système de gestion de présence',
            'account_deletion': 'Edge Attendance System - Notification de suppression de compte',
            'password_reset': 'Edge Attendance System - Réinitialisation de votre mot de passe',
            'account_locked': 'Edge Attendance System - Verrouillage temporaire de votre compte',
        }
        
        base_subject = subjects.get(template_name, 'Edge Attendance System - Notification système')
        
        # Personnalisation du sujet selon le template
        if template_name == 'welcome' and 'username' in kwargs:
            return f"Edge Attendance System - Bienvenue {kwargs['username']}"
        elif template_name == 'account_deletion' and 'username' in kwargs:
            return f"Edge Attendance System - Suppression du compte de {kwargs['username']}"
        
        return base_subject

# Instance globale du gestionnaire de templates
email_template_manager = EmailTemplateManager()
