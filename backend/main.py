"""
API FastAPI para el catálogo de RELUVSA
"""
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import filtros, productos, auth, images, exportar, pagos
from database import DATABASE_PATH
from utils.busqueda_inteligente import cargar_vocabulario_vehiculos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación - carga vocabulario al iniciar."""
    # Startup: cargar vocabulario en thread pool para no bloquear event loop
    await asyncio.to_thread(cargar_vocabulario_vehiculos, DATABASE_PATH)
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
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Registrar routers
app.include_router(auth.router)
app.include_router(filtros.router)
app.include_router(productos.router)
app.include_router(images.router)
app.include_router(exportar.router)
app.include_router(pagos.router)


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

        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM productos) as total_productos,
                (SELECT COUNT(*) FROM productos WHERE inventario_total > 0) as productos_con_inventario,
                (SELECT COUNT(*) FROM compatibilidades) as total_compatibilidades,
                (SELECT COUNT(DISTINCT producto_id) FROM compatibilidades) as productos_con_compatibilidades,
                (SELECT COUNT(DISTINCT marca_vehiculo) FROM compatibilidades WHERE marca_vehiculo IS NOT NULL) as marcas_vehiculo,
                (SELECT COUNT(DISTINCT modelo_vehiculo) FROM compatibilidades WHERE modelo_vehiculo IS NOT NULL) as modelos_vehiculo,
                (SELECT COUNT(DISTINCT departamento) FROM productos WHERE departamento IS NOT NULL) as departamentos,
                (SELECT COUNT(DISTINCT marca) FROM productos WHERE marca IS NOT NULL) as marcas_producto,
                (SELECT MAX(created_at) FROM productos) as ultima_actualizacion
        """)
        row = cursor.fetchone()

        return {
            'total_productos': row['total_productos'],
            'productos_con_inventario': row['productos_con_inventario'],
            'total_compatibilidades': row['total_compatibilidades'],
            'productos_con_compatibilidades': row['productos_con_compatibilidades'],
            'marcas_vehiculo': row['marcas_vehiculo'],
            'modelos_vehiculo': row['modelos_vehiculo'],
            'departamentos': row['departamentos'],
            'marcas_producto': row['marcas_producto'],
            'ultima_actualizacion': row['ultima_actualizacion'],
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
