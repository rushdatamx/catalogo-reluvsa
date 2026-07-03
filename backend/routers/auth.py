"""
Router de autenticación JWT para el catálogo RELUVSA.

Modelo de usuarios (julio 2026):
  - Admin: UN usuario semilla definido por env vars (ADMIN_USERNAME/ADMIN_PASSWORD).
    NO vive en la BD — garantiza acceso aunque la BD de usuarios esté vacía.
  - Proveedores: usuarios en la tabla `usuarios` de pedidos.db (volumen persistente
    de Railway, ver pedidos_db.py). Los crea/administra el admin desde el portal.
    Contraseñas hasheadas con bcrypt. Rol 'proveedor': puede ver todo el catálogo
    y comprar; no ve herramientas de admin.
  - El rol 'visitor' se eliminó: no hay acceso público, login obligatorio.

Los tokens de proveedor se revalidan contra la BD en cada request (activo=1),
así desactivar un proveedor lo saca de inmediato sin esperar a que expire su JWT.
"""
import os
import re
import secrets
import hmac
from typing import Optional, List

import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from pedidos_db import get_pedidos_db, init_pedidos_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Configuración JWT - genera clave segura si no hay variable de entorno
_default_secret = secrets.token_urlsafe(64)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _default_secret)
if not os.getenv("JWT_SECRET_KEY"):
    print("ADVERTENCIA: JWT_SECRET_KEY no configurada. Usando clave temporal (tokens no sobrevivirán reinicios).")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# Admin semilla desde variables de entorno (no vive en la BD).
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Garantizar que la tabla usuarios exista (idempotente).
init_pedidos_db()


# --- Modelos ------------------------------------------------------------------
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


class CrearUsuarioRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    nombre_empresa: str = Field(min_length=1, max_length=200)
    contacto: Optional[str] = Field(default=None, max_length=300)


class ActualizarUsuarioRequest(BaseModel):
    """Actualización parcial: solo se aplican los campos enviados."""
    password: Optional[str] = Field(default=None, min_length=6, max_length=100)
    nombre_empresa: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contacto: Optional[str] = Field(default=None, max_length=300)
    activo: Optional[bool] = None


class UsuarioOut(BaseModel):
    username: str
    nombre_empresa: Optional[str]
    contacto: Optional[str]
    role: str
    activo: bool
    created_at: Optional[str]
    last_login: Optional[str]
    total_pedidos: int = 0


# --- Helpers -------------------------------------------------------------------
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _crear_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --- Endpoints -------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """Login: primero el admin semilla (env vars), luego proveedores en BD."""
    username = data.username.strip()

    # 1) Admin semilla desde env vars.
    if hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(data.password, ADMIN_PASSWORD):
        return LoginResponse(token=_crear_token(username, "admin"), role="admin", username=username)

    # 2) Proveedores en BD (solo activos).
    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, password_hash, role, activo FROM usuarios WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()
        if user and user["activo"] and _verificar_password(data.password, user["password_hash"]):
            cursor.execute(
                "UPDATE usuarios SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
                (username,),
            )
            return LoginResponse(
                token=_crear_token(user["username"], user["role"]),
                role=user["role"],
                username=user["username"],
            )

    raise HTTPException(status_code=401, detail="Credenciales inválidas")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Dependency para validar JWT y obtener usuario actual.

    Los usuarios de BD (proveedores) se revalidan contra la tabla en cada request:
    si fueron desactivados, su token deja de servir de inmediato."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = UserInfo(username=payload["sub"], role=payload["role"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if user.role != "admin":
        with get_pedidos_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT activo FROM usuarios WHERE username = ?", (user.username,))
            row = cursor.fetchone()
        if row is None or not row["activo"]:
            raise HTTPException(status_code=401, detail="Usuario desactivado o inexistente")

    return user


def require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Dependency que requiere rol admin."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return user


# --- Gestión de usuarios (solo admin) -----------------------------------------
@router.get("/usuarios", response_model=List[UsuarioOut])
def listar_usuarios(admin: UserInfo = Depends(require_admin)):
    """Lista los usuarios de proveedores con su conteo de pedidos."""
    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT u.username, u.nombre_empresa, u.contacto, u.role, u.activo,
                      u.created_at, u.last_login,
                      COUNT(o.id) AS total_pedidos
               FROM usuarios u
               LEFT JOIN orders o ON o.username = u.username
               GROUP BY u.id
               ORDER BY u.created_at DESC"""
        )
        return [
            UsuarioOut(
                username=row["username"],
                nombre_empresa=row["nombre_empresa"],
                contacto=row["contacto"],
                role=row["role"],
                activo=bool(row["activo"]),
                created_at=row["created_at"],
                last_login=row["last_login"],
                total_pedidos=row["total_pedidos"],
            )
            for row in cursor.fetchall()
        ]


@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear_usuario(data: CrearUsuarioRequest, admin: UserInfo = Depends(require_admin)):
    """Crea un usuario de proveedor. La contraseña la asigna el admin."""
    username = data.username.strip()
    if not USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="El usuario solo puede tener letras, números, punto, guion y guion bajo",
        )
    if username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="Ese nombre de usuario está reservado")

    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail=f"El usuario '{username}' ya existe")

        cursor.execute(
            """INSERT INTO usuarios (username, password_hash, nombre_empresa, contacto, role, activo)
               VALUES (?, ?, ?, ?, 'proveedor', 1)""",
            (username, _hash_password(data.password), data.nombre_empresa.strip(),
             (data.contacto or "").strip() or None),
        )
        cursor.execute(
            "SELECT username, nombre_empresa, contacto, role, activo, created_at, last_login FROM usuarios WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()

    return UsuarioOut(
        username=row["username"],
        nombre_empresa=row["nombre_empresa"],
        contacto=row["contacto"],
        role=row["role"],
        activo=bool(row["activo"]),
        created_at=row["created_at"],
        last_login=row["last_login"],
        total_pedidos=0,
    )


@router.put("/usuarios/{username}", response_model=UsuarioOut)
def actualizar_usuario(username: str, data: ActualizarUsuarioRequest,
                       admin: UserInfo = Depends(require_admin)):
    """Actualización parcial: resetear contraseña, editar empresa/contacto,
    activar/desactivar (soft delete — el historial de pedidos se conserva)."""
    campos = []
    valores = []
    if data.password is not None:
        campos.append("password_hash = ?")
        valores.append(_hash_password(data.password))
    if data.nombre_empresa is not None:
        campos.append("nombre_empresa = ?")
        valores.append(data.nombre_empresa.strip())
    if data.contacto is not None:
        campos.append("contacto = ?")
        valores.append(data.contacto.strip() or None)
    if data.activo is not None:
        campos.append("activo = ?")
        valores.append(1 if data.activo else 0)

    if not campos:
        raise HTTPException(status_code=400, detail="No se envió ningún campo para actualizar")

    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE username = ?", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")

        cursor.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE username = ?",
                       (*valores, username))
        cursor.execute(
            """SELECT u.username, u.nombre_empresa, u.contacto, u.role, u.activo,
                      u.created_at, u.last_login, COUNT(o.id) AS total_pedidos
               FROM usuarios u LEFT JOIN orders o ON o.username = u.username
               WHERE u.username = ? GROUP BY u.id""",
            (username,),
        )
        row = cursor.fetchone()

    return UsuarioOut(
        username=row["username"],
        nombre_empresa=row["nombre_empresa"],
        contacto=row["contacto"],
        role=row["role"],
        activo=bool(row["activo"]),
        created_at=row["created_at"],
        last_login=row["last_login"],
        total_pedidos=row["total_pedidos"],
    )
