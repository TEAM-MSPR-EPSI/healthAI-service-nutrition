from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
from typing import Optional

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Vérifie le JWT depuis le cookie auth_jwt (défini par l'API Express)
    ou depuis le header Authorization: Bearer <token> (pour les tests Bruno).
    Retourne { "id": int, "role": str }.
    """
    token = request.cookies.get("auth_jwt")

    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dépendance réservée aux admins."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return current_user