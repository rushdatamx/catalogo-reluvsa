"""
Parser genérico para marcas que no tienen un parser específico
Intenta extraer información usando patrones comunes
"""
from .base import BaseParser


class GenericParser(BaseParser):
    """Parser genérico que usa los métodos base"""

    def parse(self, descripcion: str):
        """Usa el método parse de la clase base"""
        return super().parse(descripcion)
