import axios from 'axios';

// Usar variable de entorno para producción o localhost para desarrollo
export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  // Serializa arrays como key=v1&key=v2 (repeat), que es lo que FastAPI
  // espera para parámetros de tipo List[str] (multi-selección de marcas).
  paramsSerializer: {
    serialize: (params) => {
      const parts = [];
      Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null) return;
        if (Array.isArray(value)) {
          value.forEach((v) => {
            if (v !== undefined && v !== null && v !== '') {
              parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`);
            }
          });
        } else {
          parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
        }
      });
      return parts.join('&');
    },
  },
});

// Interceptor para agregar token JWT a todas las peticiones
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar 401 (token expirado o inválido)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

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
  departamentosPopulares: (params) => api.get('/filtros/departamentos-populares', { params }),

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
export const getTopVendidos = (params) => api.get('/productos/top-vendidos', { params });
export const getTopVendidosCategorias = (params) => api.get('/productos/top-vendidos/categorias', { params });
export const getProducto = (sku, config = {}) => api.get(`/productos/${encodeURIComponent(sku)}`, config);
export const buscarProductos = (q, limit = 20) => api.get('/productos/buscar', { params: { q, limit } });

// Especificaciones manuales
export const actualizarEspecificacionesManuales = (sku, datos) =>
  api.put(`/productos/${encodeURIComponent(sku)}/especificaciones-manuales`, datos);

// Exportar
export const exportarExcel = (params) => api.get('/exportar/excel', {
  params, responseType: 'blob', timeout: 60000
});
export const exportarPDF = (params) => api.get('/exportar/pdf', {
  params, responseType: 'blob', timeout: 60000
});

// Stats
export const getStats = () => api.get('/stats');

// Pagos / Checkout
// items: [{ sku, cantidad }]
export const crearCheckout = (items, sucursal_pickup) =>
  api.post('/checkout', { items, tipo_entrega: 'pickup', sucursal_pickup });
// Pedido sin pago en línea: queda 'pendiente' y RELUVSA lo cotiza/cobra por fuera.
export const crearPedido = (items, sucursal_pickup) =>
  api.post('/pedido', { items, tipo_entrega: 'pickup', sucursal_pickup });
export const getMisPedidos = () => api.get('/orders/mis-pedidos');
export const getOrden = (orderId) => api.get(`/orders/${orderId}`);

// Gestión de usuarios de proveedores (solo admin)
export const getUsuarios = () => api.get('/auth/usuarios');
export const crearUsuario = (datos) => api.post('/auth/usuarios', datos);
export const actualizarUsuario = (username, datos) =>
  api.put(`/auth/usuarios/${encodeURIComponent(username)}`, datos);

// Todas las órdenes (solo admin) — params: { username, estado, limit }
export const getOrdenes = (params) => api.get('/orders', { params });

export default api;
