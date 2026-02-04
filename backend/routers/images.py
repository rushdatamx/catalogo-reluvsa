"""
Router proxy para imágenes de productos.

Resuelve el problema de Mixed Content (HTTPS frontend → HTTP servidor de imágenes)
actuando como intermediario HTTPS.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

router = APIRouter(prefix="/api/images", tags=["images"])

# URL base del servidor de imágenes interno
IMAGE_SERVER_BASE = "http://reluvsa.zapto.org/cgi-vel/omner2/fotos"


@router.get("/{sku}")
async def get_product_image(sku: str):
    """
    Proxy para obtener imagen de producto.

    El frontend solicita: GET /api/images/125010075
    El backend obtiene: http://reluvsa.zapto.org/.../125010075.jpg
    Y retorna la imagen al frontend via HTTPS.
    """
    # Limpiar SKU (quitar espacios, caracteres especiales)
    sku_clean = sku.strip()

    # Construir URL del servidor interno
    url = f"{IMAGE_SERVER_BASE}/{sku_clean}.jpg"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error obteniendo imagen: {response.status_code}"
            )

        # Verificar que sea una imagen
        content_type = response.headers.get("content-type", "image/jpeg")
        if not content_type.startswith("image/"):
            content_type = "image/jpeg"

        return Response(
            content=response.content,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache 24 horas
                "X-Image-Source": "proxy"
            }
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout obteniendo imagen")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error de conexión: {str(e)}")
