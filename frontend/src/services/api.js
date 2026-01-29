import axios from 'axios';

// Usar variable de entorno para producción o localhost para desarrollo
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Filtros básicos
export const getFiltros = {
  departamentos: () => api.get('/filtros/departamentos'),
  marcasProducto: (params) => api.get('/filtros/marcas-producto', { params }),
  marcasVehiculo: (params) => api.get('/filtros/marcas-vehiculo', { params }),
  modelosVehiculo: (params) => api.get('/filtros/modelos-vehiculo', { params }),
  años: (params) => api.get('/filtros/años', { params }),
  motores: (params) => api.get('/filtros/motores', { params }),
  tiposProducto: (params) => api.get('/filtros/tipos-producto', { params }),
  gruposProducto: (params) => api.get('/filtros/grupos-producto', { params }),

  // Filtros para LLANTAS
  anchosLlanta: (params) => api.get('/filtros/llantas/anchos', { params }),
  relacionesLlanta: (params) => api.get('/filtros/llantas/relaciones', { params }),
  diametrosLlanta: (params) => api.get('/filtros/llantas/diametros', { params }),
  tiposLlanta: (params) => api.get('/filtros/llantas/tipos', { params }),
  capasLlanta: (params) => api.get('/filtros/llantas/capas', { params }),

  // Filtros para ACEITES
  viscosidades: (params) => api.get('/filtros/aceites/viscosidades', { params }),
  tiposAceite: (params) => api.get('/filtros/aceites/tipos', { params }),
  presentaciones: (params) => api.get('/filtros/aceites/presentaciones', { params }),

  // Filtros para ACUMULADORES
  gruposBci: (params) => api.get('/filtros/acumuladores/grupos', { params }),
  capacidadesCca: (params) => api.get('/filtros/acumuladores/capacidades', { params }),
  tamanosAcumulador: (params) => api.get('/filtros/acumuladores/tamanos', { params }),
};

// Productos
export const getProductos = (params) => api.get('/productos', { params });
export const getProducto = (sku) => api.get(`/productos/${encodeURIComponent(sku)}`);
export const buscarProductos = (q, limit = 20) => api.get('/productos/buscar', { params: { q, limit } });

// Especificaciones manuales
export const actualizarEspecificacionesManuales = (sku, datos) =>
  api.put(`/productos/${encodeURIComponent(sku)}/especificaciones-manuales`, datos);

// Stats
export const getStats = () => api.get('/stats');

export default api;
