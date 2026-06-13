"""
-------------------------------------------------------------
Service d'envoi d'e‑mails (SMTP)
-------------------------------------------------------------
"""

from __future__ import annotations

import os
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from types import TracebackType
from typing import Iterable, Optional, Type
import aiosmtplib

from app.services.log_service import db_logger
from app.services.email_template_manager import email_template_manager

# ---------------------------------------------------------------------------
# Configuration 
# ---------------------------------------------------------------------------
from app.core.config import settings

SMTP_HOST: str = settings.SMTP_HOST
SMTP_PORT: int = 2525 # Port ouvert sur DigitalOcean
SMTP_USER: str = settings.SMTP_USER
SMTP_PASSWORD: str = settings.SMTP_PASSWORD
SMTP_FROM: str = settings.SMTP_FROM
SMTP_FROM_NAME: str = settings.SMTP_FROM_NAME
USE_TLS: bool = settings.SMTP_STARTTLS

# ---------------------------------------------------------------------------
# Context manager pour la connexion SMTP (async)
# ---------------------------------------------------------------------------
class SMTPConnection:
    """Async context manager gérant la connexion SMTP."""
    def __init__(self):
        self._client: Optional[aiosmtplib.SMTP] = None

    async def __aenter__(self) -> aiosmtplib.SMTP:
        self._client = aiosmtplib.SMTP(
            hostname=SMTP_HOST, 
            port=SMTP_PORT, 
            start_tls=USE_TLS
            )
        await self._client.connect()
        await self._client.login(SMTP_USER, SMTP_PASSWORD)
        return self._client

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if self._client:
            try:
                await self._client.quit()
            except Exception: 
                db_logger.critical("Error while quitting SMTP connection")

# ---------------------------------------------------------------------------
# Fonction générique d'envoi avec templates professionnels
# ---------------------------------------------------------------------------
async def send_professional_email(
    *,
    template_name: str,
    recipients: Iterable[str],
    **template_vars
) -> None:
    """
    Envoie un email en utilisant un template professionnel.
    
    Args:
        template_name: Nom du template à utiliser
        recipients: Liste des destinataires
        **template_vars: Variables à injecter dans le template
    """
    if not recipients:
        raise ValueError("recipients must not be empty")

    # Générer le sujet et le contenu HTML
    subject = email_template_manager.get_subject(template_name, **template_vars)
    html_body = email_template_manager.render_email(template_name, **template_vars)
    
    # Générer une version texte simple depuis le HTML
    plain_body = _html_to_plain_text(html_body)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Ajouter les versions texte et HTML
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    async with SMTPConnection() as client:
        await client.send_message(msg)

    await db_logger.debug(
        f"📧 Email envoyé avec succès à : {recipients}.",
        source="email_service",
        details={
            "template": template_name,
            "subject": subject[:100] + "..." if len(subject) > 100 else subject
        }
    )

def _html_to_plain_text(html_content: str) -> str:
    """Convertit du HTML en texte brut pour la version plain text."""
    import re
    
    # Supprimer les balises HTML
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Remplacer les entités HTML communes
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    
    # Nettoyer les espaces multiples et les sauts de ligne
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


# ---------------------------------------------------------------------------
# Template : nouveau mot de passe
# ---------------------------------------------------------------------------
NEW_PWD_HTML = Path(__file__).with_suffix(".new_pwd.html")
if NEW_PWD_HTML.exists():
    _HTML_TEMPLATE = NEW_PWD_HTML.read_text("utf-8")
else:
    _HTML_TEMPLATE = (
        """
        <p>Bonjour, {username}</p>
        <p>Voici vos nouveaux identifiants de connexion pour accéder à votre compte : </p>
        <ul>
            <li><strong>Email :</strong> {email}</li>
            <li><strong>Mot de passe :</strong> {password}</li>
        </ul>
        <p>Merci de changer ce mot de passe dès votre prochaine connexion.</p>
        <p>— L'équipe Edge Attendance System</p>
        """
    )


# ---------------------------------------------------------------------------
# Templates d'emails modernisés et fonctions d'envoi professionnelles
# ---------------------------------------------------------------------------

async def send_new_password(*, to: str, username: str, password: str) -> None:
    """Envoie un e‑mail contenant le nouveau mot de passe généré avec un template professionnel."""
    await send_professional_email(
        template_name="new_password",
        recipients=[to],
        username=username,
        email=to,
        password=password
    )

async def send_welcome_email(*, to: str, username: str, password: str) -> None:
    """Envoie un email de bienvenue pour un nouveau compte."""
    await send_professional_email(
        template_name="welcome",
        recipients=[to],
        username=username,
        email=to,
        password=password
    )

async def send_account_deletion_notification(*, to: str, username: str, deleted_by: str) -> None:
    """Envoie un e-mail de notification de suppression de compte avec un template professionnel."""
    await send_professional_email(
        template_name="account_deletion",
        recipients=[to],
        username=username,
        email=to,
        deleted_by=deleted_by,
        deletion_date=datetime.now().strftime("%d/%m/%Y à %H:%M")
    )

async def send_password_reset_email(*, to: str, username: str, password: str) -> None:
    """Envoie un email de réinitialisation de mot de passe."""
    await send_professional_email(
        template_name="password_reset",
        recipients=[to],
        username=username,
        email=to,
        password=password
    )

async def send_account_locked_notification(*, to: str, username: str, locked_until: str, reason: str = "Tentatives de connexion multiples") -> None:
    """Envoie un email de notification de verrouillage de compte."""
    await send_professional_email(
        template_name="account_locked",
        recipients=[to],
        username=username,
        email=to,
        locked_until=locked_until,
        reason=reason
    )
