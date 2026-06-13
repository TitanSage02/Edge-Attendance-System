import datetime
from datetime import timezone  

from fastapi import APIRouter, Depends, Body, HTTPException, Request, Response, status, BackgroundTasks

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

from app.models.user import RefreshToken, User         

from app.schemas import auth as auth_schema
from app.schemas import user as user_schema

from app.services.user_service import crud_user
from app.services.log_service import db_logger
from app.services.token_cleanup_service import cleanup_user_old_tokens

from app.services.email_service import send_welcome_email, send_password_reset_email
from app.core.security import create_access_token

from app.api.v1.deps import get_db, get_current_user

from app.utils.sanitization import ( 
    sanitize_string, 
    sanitize_email,
    validate_password_strength
)

from app.utils.hashing import (
    hash_password,
    verify_password,
    hash_token,
    create_refresh_token_raw,
    generate_password
)

router = APIRouter(tags=["auth"])

# ──────────────────────────────────────────────────────────────
# COOKIE_KW
# ──────────────────────────────────────────────────────────────
COOKIE_KW = {
    "httponly": True,
    "secure": True,
    "samesite": "lax",
    "path": "/api/v1/auth/",  # Permet l'envoi du cookie à tous les endpoints auth
}

# Fix the timezone usage
UTC = timezone.utc
now_utc = lambda: datetime.datetime.now(UTC)  # UTC 

def _remember_ttl_days(remember: bool) -> int:
    return settings.REFRESH_TTL_DAYS if remember else 1

def _set_refresh_cookie(response: Response, raw_token: str, ttl_days: int) -> None:
    response.set_cookie(
        "refresh",
        raw_token,
        max_age=ttl_days * 86_400,        # 24 h × jours
        **COOKIE_KW,
    )

# ──────────────────────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────────────────────
@router.post("/register", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: user_schema.UserCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    if current_user.role != "admin":
        await db_logger.error(
            f"🚫 Création non autorisée d’un compte sur la plateforme par {current_user.email} {current_user.firstName}",
            "auth.register",
            user_id=current_user.id
        )
        raise HTTPException(status_code=401, detail="Accès non autorisé")
    
    payload.email = sanitize_email(payload.email)
    
    if await crud_user.get_by_email(db, email=payload.email):
        await db_logger.warning(
            f"⚠️ L’email « {payload.email} » est déjà utilisé, impossible de créer le compte",
            "auth.register",
            user_id=current_user.id
        )
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    payload.firstName = sanitize_string(payload.firstName)
    payload.lastName = sanitize_string(payload.lastName)
    payload.role = sanitize_string(payload.role)
    
    user = await crud_user.create(db, 
                                  email=payload.email, 
                                  password=payload.password if payload.password else "",
                                  firstName=payload.firstName,
                                  lastName=payload.lastName,
                                  role=payload.role
                                  )
    
    await db_logger.info(
        f"👋 {user.firstName} {user.lastName} avec le statut {user.role} a été ajouté à la plateforme par {current_user.firstName} l'administrateur {current_user.lastName}[{current_user.email}]", 
        "auth.register",
        user_id=current_user.id,
    )

    if user:
        raw_password = generate_password(length=8)

        # Définition du mot de passe de l'interessé.
        user.hashed_password = hash_password(raw_password)

        try:
            await db.commit()
        except Exception as e:
            await db_logger.error(
                f"🚫 Échec de la mise à jour du mot de passe pour {current_user.firstName} {current_user.lastName} ⚠️", 
                "auth.password_update",
                user_id=current_user.id
            )
            raise HTTPException(status_code=500, detail="Erreur serveur lors de l'initialisation")        # Envoi du mail avec le nouveau mot de passe (à faire dans un worker mail après)
        background_tasks.add_task(
            send_welcome_email,
            to=user.email,
            username=user.firstName,
            password=raw_password,
        )

    return user


# ──────────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────────
@router.post("/login", response_model=auth_schema.LoginResponse)
async def login(
    request: Request,
    response: Response,
    payload: auth_schema.LoginRequest,  
    db: AsyncSession = Depends(get_db),
):
    payload.email = sanitize_email(payload.email)

    user: User | None = await crud_user.get_by_email(db, email=payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        await db_logger.warning(
            f"⚠️ Tentative de connexion échouée pour {payload.email} depuis {request.client.host}", 
            "auth.login"
        )
        raise HTTPException(status_code=401, detail="Accès incorrect")

    access_token = create_access_token(user.id)

    ttl_days = _remember_ttl_days(payload.remember_me)
    raw_refresh = create_refresh_token_raw()
    expires_at = now_utc() + datetime.timedelta(days=ttl_days)

    db.add(
        RefreshToken(
            token_hash=hash_token(raw_refresh),
            user_id=user.id,
            user_token_version=user.token_version,     # stocke la version courante
            expires_at=expires_at,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )
    await db.commit()
    _set_refresh_cookie(response, raw_refresh, ttl_days)
    
    user.last_login = now_utc()
    await db.commit()

    # Nettoyage automatique des anciens tokens de l'utilisateur (garde les 5 plus récents)
    try:
        await cleanup_user_old_tokens(db, user.id, keep_latest=5)
    except Exception:
        # Le nettoyage ne doit pas faire échouer la connexion
        pass

    await db_logger.info(
        f"{user.firstName} {user.lastName} s'est connecté.", 
        "auth.login",
        user_id=user.id,
    )

    user_json = {"id": user.id,                
                "firstName": user.firstName,
                "lastName": user.lastName,
                "email": user.email, 
                "role": user.role,
                "isActive": user.is_active,
                "lastLogin": user.last_login,
                }

    return auth_schema.LoginResponse(
        user=user_json,
        token=access_token,
        expires_at=expires_at.isoformat(),
        success=True,
    )


# ──────────────────────────────────────────────────────────────
# Refresh
# ──────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=auth_schema.Token)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    x_refresh: str | None = None,              # header anti‑CSRF
):
    # Vérification du header anti-CSRF
    if x_refresh != "true":
        await db_logger.warning(
            f"🚫 Tentative de refresh sans header X-Refresh depuis {request.client.host}",
            "auth.refresh"
        )
        raise HTTPException(status_code=400, detail="Missing or invalid X-Refresh header")

    # Vérification de la présence du cookie
    raw_refresh = request.cookies.get("refresh")
    if not raw_refresh:
        await db_logger.warning(
            f"🚫 Tentative de refresh sans cookie depuis {request.client.host}",
            "auth.refresh"
        )
        raise HTTPException(status_code=401, detail="Missing refresh token")

    token_hash = hash_token(raw_refresh)
    res = await db.execute(
                    select(RefreshToken).where(
                        RefreshToken.token_hash == token_hash,
                        RefreshToken.revoked_at.is_(None),
                    )
    )
    stored: RefreshToken | None = res.scalar_one_or_none()    
    
    if (
        not stored
        or stored.expires_at < now_utc()
        or stored.user_token_version != stored.user.token_version  #  version check réel
        ):

        await db_logger.warning(
            f"🚫 Tentative de refresh avec token invalide depuis {request.client.host}",
            "auth.refresh"
        )
        
        raise HTTPException(status_code=401, detail="Invalid refresh token")  # Rotation dans la même transaction
    
    new_raw = create_refresh_token_raw()
    
    # Calcul précis du TTL en conservant le temps restant
    remaining_time = stored.expires_at - now_utc()
    if remaining_time.total_seconds() <= 0:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    
    # Convertir en jours, avec un minimum de 1 jour
    ttl_days = max(1, int(remaining_time.total_seconds() // 86400))
    if remaining_time.total_seconds() % 86400 > 0:
        ttl_days += 1

    async with db.begin():
        stored.revoked_at = now_utc()
        db.add(
            RefreshToken(
                token_hash=hash_token(new_raw),
                user_id=stored.user_id,
                user_token_version=stored.user.token_version,
                expires_at=now_utc() + datetime.timedelta(days=ttl_days),
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )

    await db.commit()

    await db_logger.debug(
        f"🔄 Token rafraîchi avec succès pour l'utilisateur ID {stored.user_id} depuis {request.client.host} ✅", 
        "auth.refresh",
        user_id=stored.user_id,
        details={"ip": request.client.host, "user_agent": request.headers.get("user-agent")}
    )

    _set_refresh_cookie(response, new_raw, ttl_days)

    access_token = create_access_token(stored.user_id)
    return auth_schema.Token(access_token=access_token)

# ──────────────────────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────────────────────
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, 
    response: Response, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    raw_refresh = request.cookies.get("refresh")
    if raw_refresh:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == hash_token(raw_refresh),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now_utc())
        )
        await db.commit()

    await db_logger.info(
        f"👋 L'utilisateur  {current_user.firstName} {current_user.lastName} s'est déconnecté avec succès.", 
        "auth.logout",
        user_id=current_user.id,
    )

    response.delete_cookie("refresh", path="/api/v1/auth/")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# Reset‑password (génère un nouveau mot de passe et l'envoie)
# ──────────────────────────────────────────────────────────────
@router.post("/reset-password", response_model=auth_schema.ResetPasswordResponse)
async def reset_password(
    payload: auth_schema.ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_email(db, email=payload.email)

    if not user:
        await db_logger.warning(
            f"🔍 Tentative de réinitialisation pour un email non enregistré : {payload.email} ⚠️",
            "auth.reset_password"
        )
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if not user.is_active:
        await db_logger.warning(
            f"⏸️ Tentative de réinitialisation sur un compte inactif : {payload.email} ⚠️",
            "auth.reset_password",
            user_id=user.id
        )
        raise HTTPException(status_code=400, detail="Le compte utilisateur est inactif")

    # Génération d'un mot de passe temporaire robuste
    raw_password = generate_password(length=8)

    # Mise à jour du mot de passe dans la base
    user.hashed_password = hash_password(raw_password)
    
    # Incrémente token_version pour invalider les anciens tokens
    user.token_version = (user.token_version or 0) + 1
    
    email = user.email
    user_name = user.firstName + " " + user.lastName

    try:
        await db.commit()
    except Exception as e:
        await db_logger.error(
            f"❌ Échec de la mise à jour du mot de passe : {str(e)}",
            "auth.reset_password",
            user_id=user.id
        )
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la réinitialisation")
    
    # Envoi du mail avec le nouveau mot de passe
    background_tasks.add_task(
        send_password_reset_email,
        to=email,
        username=user_name,
        password=raw_password,
    )

    await db_logger.info(
        f"🔄 {email} a réinitialisé son mot de passe.",
        "auth.reset_password",
        user_id=user.id
    )

    return auth_schema.ResetPasswordResponse(
        message="Un nouveau mot de passe vient de vous être envoyé par e-mail.",
        success=True,
    )

# ──────────────────────────
# Change password
# ──────────────────────────
@router.post("/change-password", response_model=auth_schema.ChangePasswordResponse, status_code=status.HTTP_200_OK)
async def change_password(
    payload: auth_schema.ChangePasswordRequest,
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifie le mot de passe actuel
    if not verify_password(payload.old_password, current_user.hashed_password):
        await db_logger.warning(
            f"🔒 Tentative de changement de mot de passe avec ancien mot de passe incorrect pour {current_user.email} ⚠️",
            "auth.change_password",
            user_id=current_user.id
        )
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    # Valide la force du nouveau mot de passe
    try:
        validate_password_strength(payload.new_password)
    except ValueError as e:
        await db_logger.warning(
            f"🛡️ Tentative de changement avec mot de passe trop faible pour {current_user.email} : {str(e)}.",
            "auth.change_password",
            user_id=current_user.id
        )
        raise HTTPException(status_code=400, detail=str(e))

    # Met à jour la DB
    current_user.hashed_password = hash_password(payload.new_password)

    # Incrémente token_version pour invalider les anciens refresh tokens
    current_user.token_version = (current_user.token_version or 0) + 1
    await db.commit()

    await db_logger.info(
        f"🔐 {current_user.firstName} {current_user.lastName} a modifié son mot de passe.",
        "auth.change_password",
        user_id=current_user.id
    )

    return auth_schema.ChangePasswordResponse(
        message="Mot de passe modifié avec succès",
        success=True
    )

@router.get("/profile", response_model=user_schema.UserRead, status_code=status.HTTP_200_OK)
async def get_profile(
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user : User = await crud_user.get_by_id(db, current_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_data = {
        "email": user.email,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login
    }
    
    return user_data

@router.patch("/profile", response_model=user_schema.UserRead, status_code=status.HTTP_200_OK)
async def update_profile(
    payload: user_schema.UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # On applique uniquement les champs fournis
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour fourni")
    
    try:
        user = await crud_user.update(db, user_id=current_user.id, **update_data)
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de la mise à jour du profil pour {current_user.email}: {str(e)}",
            "auth.update_profile",
            user_id=current_user.id,
        )
        raise HTTPException(status_code=500, detail="Impossible de mettre à jour le profil")
    
    await db_logger.info(
        f"👤 {current_user.firstName} {current_user.lastName} a mis à jour son profil.",
        "auth.update_profile",
        user_id=user.id
    )
    return user