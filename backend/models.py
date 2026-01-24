"""
Modelos Pydantic para la API
"""
from typing import List, Optional
from pydantic import BaseModel


class InventarioSucursal(BaseModel):
    sucursal: str
    cantidad: float


class Compatibilidad(BaseModel):
    marca_vehiculo: Optional[str] = None
    modelo_vehiculo: Optional[str] = None
    año_inicio: Optional[int] = None
    año_fin: Optional[int] = None
    motor: Optional[str] = None
    cilindros: Optional[str] = None
    especificacion: Optional[str] = None


class ProductoBase(BaseModel):
    sku: str
    departamento: Optional[str] = None
    marca: Optional[str] = None
    descripcion_original: Optional[str] = None
    nombre_producto: Optional[str] = None
    tipo_producto: Optional[str] = None
    precio_publico: Optional[float] = None
    precio_mayoreo: Optional[float] = None
    imagen_url: Optional[str] = None
    inventario_total: Optional[float] = None


class ProductoDetalle(ProductoBase):
    id: int
    skus_alternos: List[str] = []
    compatibilidades: List[Compatibilidad] = []
    inventario_sucursales: List[InventarioSucursal] = []


class ProductoLista(ProductoBase):
    id: int


class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[ProductoLista]


class FiltroOpciones(BaseModel):
    valores: List[str]
    total: int
