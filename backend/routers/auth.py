"""
Router de autenticación JWT para el catálogo RELUVSA.

Provee login simple con 2 usuarios (admin/visitante) desde variables de entorno.
"""
import os
import secrets
import hmac

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Configuración JWT - genera clave segura si no hay variable de entorno
_default_secret = secrets.token_urlsafe(64)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _default_secret)
if not os.getenv("JWT_SECRET_KEY"):
    print("ADVERTENCIA: JWT_SECRET_KEY no configurada. Usando clave temporal (tokens no sobrevivirán reinicios).")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# Usuarios desde variables de entorno
USERS = {
    os.getenv("ADMIN_USERNAME", "admin"): {
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    },
    os.getenv("VISITOR_USERNAME", "visitante"): {
        "password": os.getenv("VISITOR_PASSWORD", "visitante123"),
        "role": "visitor"
    }
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class UserInfo(BaseModel):
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """Endpoint de login que retorna JWT."""
    user = USERS.get(data.username)
    if not user or not hmac.compare_digest(user["password"], data.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Crear JWT
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": data.username,
        "role": user["role"],
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return LoginResponse(token=token, role=user["role"], username=data.username)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Dependency para validar JWT y obtener usuario actual."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return UserInfo(username=payload["sub"], role=payload["role"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Dependency que requiere rol admin."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return user
