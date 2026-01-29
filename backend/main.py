"""
API FastAPI para el catálogo de RELUVSA
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import filtros, productos
from database import DATABASE_PATH
from utils.busqueda_inteligente import cargar_vocabulario_vehiculos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación - carga vocabulario al iniciar."""
    # Startup: cargar vocabulario de vehículos para búsqueda inteligente
    cargar_vocabulario_vehiculos(DATABASE_PATH)
    yield
    # Shutdown: nada que hacer

app = FastAPI(
    title="Catálogo RELUVSA API",
    description="API para el catálogo de refacciones de RELUVSA con filtros en cascada",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS dinámico para desarrollo y producción
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://catalogo-reluvsa.vercel.app,https://catalogo-reluvsa-git-main-rushdatas-projects.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(filtros.router)
app.include_router(productos.router)


@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "message": "API del Catálogo RELUVSA",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/stats")
def get_stats():
    """Obtiene estadísticas generales del catálogo"""
    from database import get_db

    with get_db() as conn:
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) as total FROM productos")
        stats['total_productos'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_total > 0")
        stats['productos_con_inventario'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM compatibilidades")
        stats['total_compatibilidades'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(DISTINCT producto_id) as total FROM compatibilidades")
        stats['productos_con_compatibilidades'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(DISTINCT marca_vehiculo) as total FROM compatibilidades WHERE marca_vehiculo IS NOT NULL")
        stats['marcas_vehiculo'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(DISTINCT modelo_vehiculo) as total FROM compatibilidades WHERE modelo_vehiculo IS NOT NULL")
        stats['modelos_vehiculo'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(DISTINCT departamento) as total FROM productos WHERE departamento IS NOT NULL")
        stats['departamentos'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(DISTINCT marca) as total FROM productos WHERE marca IS NOT NULL")
        stats['marcas_producto'] = cursor.fetchone()['total']

        return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
