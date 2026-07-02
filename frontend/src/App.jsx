import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Package, Car, Link2, Filter, X, ChevronDown, CheckCircle, XCircle, AlertCircle, Tag, Calendar, Gauge, Truck, Settings, Save, LogOut, User, ImageOff, FileSpreadsheet, FileText, Download, Loader2, ShoppingCart, Plus } from 'lucide-react';
import { getProductos, getStats, getProducto, actualizarEspecificacionesManuales, exportarExcel, exportarPDF, API_BASE } from './services/api';
import { cn } from './lib/utils';

// URL base para imágenes via proxy
const getImageUrl = (sku) => `${API_BASE}/images/${encodeURIComponent(sku)}`;

// Componente de imagen de producto con fallback
function ProductImage({ sku, alt, className, size = 'md' }) {
  const [error, setError] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-48 h-48'
  };

  if (error) {
    return (
      <div className={cn(
        "flex items-center justify-center bg-notion-bg-subtle rounded-lg",
        sizeClasses[size],
        className
      )}>
        <ImageOff className="text-notion-text-secondary" size={size === 'lg' ? 48 : size === 'md' ? 32 : 20} />
      </div>
    );
  }

  return (
    <div className={cn("relative", sizeClasses[size], className)}>
      {loading && (
        <div className={cn(
          "absolute inset-0 flex items-center justify-center bg-notion-bg-subtle rounded-lg animate-pulse",
          sizeClasses[size]
        )}>
          <Package className="text-notion-text-secondary" size={size === 'lg' ? 48 : size === 'md' ? 32 : 20} />
        </div>
      )}
      <img
        src={getImageUrl(sku)}
        alt={alt}
        className={cn(
          "object-contain rounded-lg",
          sizeClasses[size],
          loading && "opacity-0"
        )}
        onLoad={() => setLoading(false)}
        onError={() => {
          setLoading(false);
          setError(true);
        }}
      />
    </div>
  );
}

// Componentes de Filtros
import FiltrosCascada from './components/FiltrosCascada';

// Autenticación
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';

// Carrito / Compra
import { CartProvider, useCart, puedeComprar } from './context/CartContext';
import CartDrawer from './components/CartDrawer';
import OrderResult from './components/OrderResult';

function AppContent() {
  const { user, logout, isAdmin } = useAuth();
  const { agregar, setAbierto, totalItems } = useCart();
  const [filtros, setFiltros] = useState({
    departamento: '',
    marca: '',
    grupo_producto: '',
    marca_vehiculo: '',
    modelo_vehiculo: '',
    año: '',
    motor: '',
    con_inventario: false,
    solo_nuevos: false,
    ancho_llanta: '',
    relacion_llanta: '',
    diametro_llanta: '',
    tipo_llanta: '',
    capas_llanta: '',
    viscosidad: '',
    tipo_aceite: '',
    presentacion: '',
    grupo_bci: '',
    capacidad_cca: '',
    tamano_acumulador: '',
  });

  const [busqueda, setBusqueda] = useState('');
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [paginacion, setPaginacion] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 1,
  });

  const [productoSeleccionado, setProductoSeleccionado] = useState(null);
  const [detalleProducto, setDetalleProducto] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [stats, setStats] = useState(null);
  const [exportando, setExportando] = useState(null); // null | 'excel' | 'pdf'

  // Estados para especificaciones manuales
  const [especsManuales, setEspecsManuales] = useState({
    garantia: '',
    material: '',
    posicion: ''
  });
  const [guardandoEspecs, setGuardandoEspecs] = useState(false);
  const [especsGuardadas, setEspecsGuardadas] = useState(false);
  const [errorEspecs, setErrorEspecs] = useState(null);

  // Ref para AbortController del detalle de producto
  const detalleAbortRef = useRef(null);

  // Cerrar modal con ESC
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && productoSeleccionado) {
        setProductoSeleccionado(null);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [productoSeleccionado]);

  // Cargar estadísticas
  useEffect(() => {
    getStats()
      .then(res => setStats(res.data))
      .catch(console.error);
  }, []);

  // Cargar productos
  const cargarProductos = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: paginacion.page,
        limit: paginacion.limit,
      };

      Object.entries(filtros).forEach(([key, value]) => {
        if (value && value !== false) params[key] = value;
      });
      if (busqueda.length >= 2) params.q = busqueda;

      const res = await getProductos(params);
      setProductos(res.data.items);
      setPaginacion(prev => ({
        ...prev,
        total: res.data.total,
        pages: res.data.pages,
      }));
    } catch (err) {
      console.error('Error cargando productos:', err);
      setProductos([]);
    } finally {
      setLoading(false);
    }
  }, [filtros, busqueda, paginacion.page, paginacion.limit]);

  useEffect(() => {
    cargarProductos();
  }, [cargarProductos]);

  useEffect(() => {
    setPaginacion(prev => ({ ...prev, page: 1 }));
  }, [filtros, busqueda]);

  // Cargar detalle de producto (con AbortController para evitar race conditions)
  useEffect(() => {
    if (productoSeleccionado) {
      // Cancelar petición anterior si existe
      if (detalleAbortRef.current) {
        detalleAbortRef.current.abort();
      }
      const controller = new AbortController();
      detalleAbortRef.current = controller;

      setLoadingDetalle(true);
      setEspecsGuardadas(false);
      getProducto(productoSeleccionado, { signal: controller.signal })
        .then(res => {
          if (!controller.signal.aborted) {
            setDetalleProducto(res.data);
            if (res.data.especificaciones_manuales) {
              setEspecsManuales({
                garantia: res.data.especificaciones_manuales.garantia || '',
                material: res.data.especificaciones_manuales.material || '',
                posicion: res.data.especificaciones_manuales.posicion || ''
              });
            } else {
              setEspecsManuales({ garantia: '', material: '', posicion: '' });
            }
          }
        })
        .catch(err => {
          if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
            console.error('Error cargando detalle:', err);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setLoadingDetalle(false);
          }
        });
    } else {
      setDetalleProducto(null);
      setEspecsManuales({ garantia: '', material: '', posicion: '' });
    }
    return () => {
      if (detalleAbortRef.current) {
        detalleAbortRef.current.abort();
      }
    };
  }, [productoSeleccionado]);

  // Guardar especificaciones manuales
  const handleGuardarEspecs = async () => {
    setGuardandoEspecs(true);
    setEspecsGuardadas(false);
    setErrorEspecs(null);
    try {
      await actualizarEspecificacionesManuales(productoSeleccionado, especsManuales);
      setEspecsGuardadas(true);
      setTimeout(() => setEspecsGuardadas(false), 3000);
    } catch (err) {
      console.error('Error guardando especificaciones:', err);
      setErrorEspecs('Error al guardar las especificaciones');
      setTimeout(() => setErrorEspecs(null), 5000);
    } finally {
      setGuardandoEspecs(false);
    }
  };

  const handleFiltrosChange = (nuevosFiltros) => {
    setFiltros(nuevosFiltros);
  };

  // Export helpers
  const buildExportParams = () => {
    const params = {};
    Object.entries(filtros).forEach(([key, value]) => {
      if (value && value !== false) params[key] = value;
    });
    if (busqueda.length >= 2) params.q = busqueda;
    return params;
  };

  const handleExportExcel = async () => {
    setExportando('excel');
    try {
      const res = await exportarExcel(buildExportParams());
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'catalogo_reluvsa.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const msg = err.response?.status === 400
        ? 'Demasiados productos. Aplique más filtros para exportar.'
        : err.response?.status === 404
          ? 'No se encontraron productos con los filtros aplicados.'
          : 'Error al exportar. Intente de nuevo.';
      alert(msg);
    } finally {
      setExportando(null);
    }
  };

  const handleExportPDF = async () => {
    setExportando('pdf');
    try {
      const res = await exportarPDF(buildExportParams());
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'catalogo_reluvsa.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const msg = err.response?.status === 400
        ? 'Demasiados productos. Aplique más filtros para exportar.'
        : err.response?.status === 404
          ? 'No se encontraron productos con los filtros aplicados.'
          : 'Error al exportar. Intente de nuevo.';
      alert(msg);
    } finally {
      setExportando(null);
    }
  };

  return (
    <div className="min-h-screen bg-notion-bg-subtle">
      {/* Header */}
      <header className="bg-reluvsa-yellow sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          {/* Logo y Stats */}
          <div className="flex items-center justify-between mb-4">
            <img
              src="/reluvsa-logo.png"
              alt="RELUVSA Autopartes"
              className="h-12 object-contain"
            />

            <div className="flex items-center gap-4">
              {stats && (
                <div className="hidden md:flex items-center gap-4 text-reluvsa-black">
                  <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-sm font-medium">
                    <Package size={16} />
                    <span>{stats.total_productos?.toLocaleString()} productos</span>
                  </div>
                  <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-sm font-medium">
                    <Car size={16} />
                    <span>{stats.marcas_vehiculo} marcas</span>
                  </div>
                  <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-sm font-medium">
                    <Link2 size={16} />
                    <span>{stats.total_compatibilidades?.toLocaleString()} compat.</span>
                  </div>
                  {stats.ultima_actualizacion && (
                    <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-sm font-medium">
                      <Calendar size={16} />
                      <span>Act. {new Date(stats.ultima_actualizacion).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                    </div>
                  )}
                </div>
              )}
              {/* Carrito */}
              <button
                onClick={() => setAbierto(true)}
                className="relative flex items-center gap-1 bg-black/10 hover:bg-black/20 px-3 py-1.5 rounded-full text-sm font-medium transition-colors"
                aria-label="Abrir carrito"
              >
                <ShoppingCart size={16} />
                {totalItems > 0 && (
                  <span className="absolute -top-1 -right-1 bg-reluvsa-red text-white text-[10px] font-bold min-w-[18px] h-[18px] flex items-center justify-center rounded-full px-1">
                    {totalItems}
                  </span>
                )}
              </button>
              {/* Usuario y Logout */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-sm font-medium">
                  <User size={16} />
                  <span>{user?.username}</span>
                  {isAdmin() && (
                    <span className="bg-reluvsa-red text-white text-xs px-1.5 py-0.5 rounded">Admin</span>
                  )}
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-1 bg-black/10 hover:bg-black/20 px-3 py-1.5 rounded-full text-sm font-medium transition-colors"
                >
                  <LogOut size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Buscador */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-notion-text-secondary" size={20} />
            <input
              type="text"
              className="w-full pl-12 pr-4 py-3 bg-white border-2 border-reluvsa-black rounded-xl text-base placeholder:text-notion-text-secondary focus:outline-none focus:ring-2 focus:ring-reluvsa-black/20 transition-all"
              placeholder="Buscar por SKU, nombre, vehículo, marca, motor..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Contenido Principal */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar de Filtros */}
          <aside className="lg:w-72 flex-shrink-0">
            <FiltrosCascada
              filtros={filtros}
              onFiltrosChange={handleFiltrosChange}
            />
          </aside>

          {/* Productos */}
          <section className="flex-1">
            {/* Header de resultados */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-notion-text-primary">
                  Productos
                </h2>
                {productos.length > 0 && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleExportExcel}
                      disabled={exportando !== null}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {exportando === 'excel' ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <FileSpreadsheet size={14} />
                      )}
                      Excel
                    </button>
                    <button
                      onClick={handleExportPDF}
                      disabled={exportando !== null}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {exportando === 'pdf' ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <FileText size={14} />
                      )}
                      PDF
                    </button>
                  </div>
                )}
              </div>
              <span className="text-sm text-notion-text-secondary">
                {paginacion.total.toLocaleString()} resultados
                {paginacion.pages > 1 && ` · Página ${paginacion.page} de ${paginacion.pages}`}
              </span>
            </div>

            {/* Grid de productos */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
                    <div className="h-4 bg-notion-bg-subtle rounded w-1/3 mb-3"></div>
                    <div className="h-5 bg-notion-bg-subtle rounded w-full mb-2"></div>
                    <div className="h-4 bg-notion-bg-subtle rounded w-2/3 mb-4"></div>
                    <div className="flex justify-between">
                      <div className="h-6 bg-notion-bg-subtle rounded w-20"></div>
                      <div className="h-6 bg-notion-bg-subtle rounded w-16"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : productos.length === 0 ? (
              <div className="bg-white rounded-xl p-12 text-center">
                <Package className="mx-auto mb-4 text-notion-text-secondary" size={48} />
                <p className="text-notion-text-secondary">No se encontraron productos</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {productos.map((producto) => (
                  <article
                    key={producto.id}
                    onClick={() => setProductoSeleccionado(producto.sku)}
                    className="bg-white rounded-xl p-4 border border-notion-border hover:border-reluvsa-yellow hover:shadow-lg cursor-pointer transition-all group relative overflow-hidden"
                  >
                    {/* Badge NUEVO - Esquina superior izquierda */}
                    {producto.es_nuevo && (
                      <div className="absolute left-0 top-0 bg-gradient-to-r from-pink-500 via-rose-500 to-orange-400 text-white text-[10px] font-bold px-2 py-0.5 rounded-br-lg shadow-sm z-10">
                        NUEVO
                      </div>
                    )}

                    {/* Layout con imagen */}
                    <div className="flex gap-3">
                      {/* Imagen del producto */}
                      <ProductImage
                        sku={producto.sku}
                        alt={producto.nombre_producto || producto.sku}
                        size="md"
                        className="flex-shrink-0"
                      />

                      {/* Contenido */}
                      <div className="flex-1 min-w-0">
                        {/* Header - SKU y Marca juntos */}
                        <div className="flex items-center gap-2 mb-1">
                          <code className="text-xs text-reluvsa-red font-mono font-semibold">
                            {producto.sku}
                          </code>
                          <span className="text-xs bg-notion-bg-subtle px-2 py-0.5 rounded font-medium text-notion-text-secondary">
                            {producto.marca}
                          </span>
                        </div>

                        {/* Nombre */}
                        <h3 className="font-medium text-notion-text-primary mb-1 line-clamp-2 group-hover:text-reluvsa-black text-sm">
                          {producto.nombre_producto || producto.tipo_producto || 'Producto'}
                        </h3>

                        {/* Precio inline con inventario */}
                        <div className="flex items-center gap-2">
                          {producto.precio_publico > 0 ? (
                            <span className="text-base font-bold text-reluvsa-red">
                              ${producto.precio_publico.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                            </span>
                          ) : (
                            <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                              Consultar precio
                            </span>
                          )}
                          {producto.inventario_total > 0 ? (
                            <span className="flex items-center gap-1 text-xs font-medium text-success">
                              <CheckCircle size={10} />
                              {producto.inventario_total}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-xs font-medium text-danger">
                              <XCircle size={10} />
                            </span>
                          )}
                        </div>

                        {/* Botón comprar / AGOTADO */}
                        <div className="mt-2">
                          {puedeComprar(producto) ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                agregar(producto, 1);
                                setAbierto(true);
                              }}
                              className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-reluvsa-yellow text-reluvsa-black text-xs font-semibold rounded-lg hover:bg-yellow-400 transition-colors"
                            >
                              <Plus size={14} />
                              Agregar al carrito
                            </button>
                          ) : (
                            <div className="w-full text-center py-1.5 bg-notion-bg-subtle text-notion-text-secondary text-xs font-semibold rounded-lg">
                              AGOTADO
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}

            {/* Paginación */}
            {paginacion.pages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-8">
                <button
                  onClick={() => setPaginacion(p => ({ ...p, page: p.page - 1 }))}
                  disabled={paginacion.page <= 1}
                  className="px-4 py-2 bg-white border border-notion-border rounded-lg font-medium text-sm hover:border-reluvsa-yellow disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Anterior
                </button>
                <span className="text-sm text-notion-text-secondary">
                  Página {paginacion.page} de {paginacion.pages}
                </span>
                <button
                  onClick={() => setPaginacion(p => ({ ...p, page: p.page + 1 }))}
                  disabled={paginacion.page >= paginacion.pages}
                  className="px-4 py-2 bg-white border border-notion-border rounded-lg font-medium text-sm hover:border-reluvsa-yellow disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Siguiente
                </button>
              </div>
            )}
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-notion-bg-subtle border-t border-notion-border mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-3 text-rushdata-gray">
            <img
              src="/rushdata-icono-gris.png"
              alt="Rushdata"
              className="h-6 w-6 object-contain opacity-60"
            />
            <span className="text-sm">
              Desarrollado por Rushdata · © {new Date().getFullYear()}
            </span>
          </div>
        </div>
      </footer>

      {/* Modal de Detalle */}
      {productoSeleccionado && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setProductoSeleccionado(null)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Detalle de producto"
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            {loadingDetalle ? (
              <div className="p-8 text-center">
                <div className="w-8 h-8 border-2 border-reluvsa-yellow border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="mt-4 text-notion-text-secondary">Cargando...</p>
              </div>
            ) : detalleProducto ? (
              <>
                {/* Header del Modal */}
                <div className="sticky top-0 bg-white border-b border-notion-border p-6 flex items-start justify-between">
                  <div className="flex gap-4">
                    {/* Imagen grande del producto */}
                    <ProductImage
                      sku={detalleProducto.sku}
                      alt={detalleProducto.nombre_producto || detalleProducto.sku}
                      size="lg"
                      className="flex-shrink-0"
                    />
                    <div>
                      <code className="text-sm text-reluvsa-red font-mono font-semibold">
                        {detalleProducto.sku}
                      </code>
                      <h2 className="text-xl font-semibold text-notion-text-primary mt-1">
                        {detalleProducto.nombre_producto || detalleProducto.tipo_producto}
                      </h2>
                      <span className="inline-block mt-2 text-sm bg-notion-bg-subtle px-3 py-1 rounded-full font-medium">
                        {detalleProducto.marca}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setProductoSeleccionado(null)}
                    className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors"
                  >
                    <X size={20} />
                  </button>
                </div>

                {/* Cuerpo del Modal */}
                <div className="p-6 space-y-6">
                  {/* Descripción */}
                  <div>
                    <h3 className="flex items-center gap-2 font-semibold text-notion-text-primary mb-3">
                      <Tag size={18} />
                      Descripción
                    </h3>
                    <p className="text-notion-text-secondary bg-notion-bg-subtle p-4 rounded-lg">
                      {detalleProducto.descripcion_original}
                    </p>
                  </div>

                  {/* Precios e Inventario */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-notion-bg-subtle p-4 rounded-lg">
                      <p className="text-sm text-notion-text-secondary mb-1">Precio Público</p>
                      {detalleProducto.precio_publico > 0 ? (
                        <p className="text-2xl font-bold text-reluvsa-red">
                          ${detalleProducto.precio_publico.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                        </p>
                      ) : (
                        <p className="text-lg font-medium text-amber-600">Consultar precio</p>
                      )}
                    </div>
                    <div className="bg-notion-bg-subtle p-4 rounded-lg">
                      <p className="text-sm text-notion-text-secondary mb-1">Precio Mayoreo</p>
                      {detalleProducto.precio_mayoreo > 0 ? (
                        <p className="text-2xl font-bold text-notion-text-primary">
                          ${detalleProducto.precio_mayoreo.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                        </p>
                      ) : (
                        <p className="text-lg font-medium text-amber-600">Consultar precio</p>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-notion-text-secondary mt-1">Precios incluyen IVA</p>

                  {/* Botón comprar / AGOTADO */}
                  {puedeComprar(detalleProducto) ? (
                    <button
                      onClick={() => {
                        agregar(detalleProducto, 1);
                        setProductoSeleccionado(null);
                        setAbierto(true);
                      }}
                      className="w-full flex items-center justify-center gap-2 py-3 bg-reluvsa-yellow text-reluvsa-black font-semibold rounded-lg hover:bg-yellow-400 transition-colors"
                    >
                      <ShoppingCart size={18} />
                      Agregar al carrito
                    </button>
                  ) : (
                    <div className="w-full text-center py-3 bg-notion-bg-subtle text-notion-text-secondary font-semibold rounded-lg">
                      {detalleProducto.precio_publico > 0 ? 'AGOTADO' : 'Consultar precio'}
                    </div>
                  )}

                  {/* Inventario */}
                  {detalleProducto.inventario_sucursales?.length > 0 && (
                    <div>
                      <h3 className="flex items-center gap-2 font-semibold text-notion-text-primary mb-3">
                        <Package size={18} />
                        Inventario por Sucursal
                      </h3>
                      <div className="grid grid-cols-2 gap-2">
                        {detalleProducto.inventario_sucursales.map((inv, i) => (
                          <div key={i} className="flex items-center justify-between bg-notion-bg-subtle p-3 rounded-lg">
                            <span className="text-sm font-medium">{inv.sucursal}</span>
                            <span className={cn(
                              "text-sm font-bold",
                              inv.cantidad > 0 ? "text-success" : "text-danger"
                            )}>
                              {inv.cantidad}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Compatibilidades */}
                  {detalleProducto.compatibilidades?.length > 0 && (
                    <div>
                      <h3 className="flex items-center gap-2 font-semibold text-notion-text-primary mb-3">
                        <Car size={18} />
                        Compatibilidades ({detalleProducto.compatibilidades.length})
                      </h3>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {detalleProducto.compatibilidades.map((compat, i) => (
                          <div key={i} className="bg-notion-bg-subtle p-3 rounded-lg text-sm">
                            <span className="font-semibold text-reluvsa-black">
                              {compat.marca_vehiculo} {compat.modelo_vehiculo}
                            </span>
                            <span className="text-notion-text-secondary ml-2">
                              {compat.año_inicio && compat.año_fin
                                ? `${compat.año_inicio}-${compat.año_fin}`
                                : 'Todos los años'}
                              {compat.motor && ` · ${compat.motor}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Productos Intercambiables */}
                  {detalleProducto.intercambiables?.length > 0 && (
                    <div>
                      <h3 className="flex items-center gap-2 font-semibold text-notion-text-primary mb-3">
                        <Link2 size={18} />
                        Productos Intercambiables ({detalleProducto.intercambiables.length})
                      </h3>
                      <div className="space-y-2">
                        {detalleProducto.intercambiables.map((item, i) => (
                          <div
                            key={i}
                            onClick={() => setProductoSeleccionado(item.sku)}
                            className="flex items-center justify-between bg-notion-bg-subtle p-3 rounded-lg cursor-pointer hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-all"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="bg-reluvsa-black text-white text-xs font-semibold px-2 py-0.5 rounded whitespace-nowrap">
                                {item.marca}
                              </span>
                              <code className="text-sm text-reluvsa-red font-mono font-semibold">
                                {item.sku}
                              </code>
                            </div>
                            <div className="flex items-center gap-3 ml-3 whitespace-nowrap">
                              {item.precio_publico > 0 ? (
                                <span className="text-sm font-bold text-reluvsa-red">
                                  ${item.precio_publico.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                                </span>
                              ) : (
                                <span className="text-xs font-medium text-amber-600">
                                  Consultar
                                </span>
                              )}
                              <span className={cn(
                                "text-xs font-medium",
                                item.inventario_total > 0 ? "text-success" : "text-notion-text-secondary"
                              )}>
                                {item.inventario_total > 0 ? `${item.inventario_total} en stock` : 'Sin stock'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Especificaciones Manuales - Solo visible para admin */}
                  {isAdmin() && (
                    <div>
                      <h3 className="flex items-center gap-2 font-semibold text-notion-text-primary mb-3">
                        <Settings size={18} />
                        Especificaciones Manuales
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Campo Garantía */}
                        <div className="bg-notion-bg-subtle p-3 rounded-lg">
                          <label className="text-xs text-notion-text-secondary mb-1 block">Garantía</label>
                          <input
                            type="text"
                            value={especsManuales.garantia}
                            onChange={(e) => setEspecsManuales({...especsManuales, garantia: e.target.value})}
                            placeholder="Ej: 1 año"
                            className="w-full px-2 py-1.5 border border-notion-border rounded text-sm focus:outline-none focus:border-reluvsa-yellow"
                          />
                        </div>
                        {/* Campo Material */}
                        <div className="bg-notion-bg-subtle p-3 rounded-lg">
                          <label className="text-xs text-notion-text-secondary mb-1 block">Material</label>
                          <input
                            type="text"
                            value={especsManuales.material}
                            onChange={(e) => setEspecsManuales({...especsManuales, material: e.target.value})}
                            placeholder="Ej: Acero inoxidable"
                            className="w-full px-2 py-1.5 border border-notion-border rounded text-sm focus:outline-none focus:border-reluvsa-yellow"
                          />
                        </div>
                        {/* Campo Posición */}
                        <div className="bg-notion-bg-subtle p-3 rounded-lg">
                          <label className="text-xs text-notion-text-secondary mb-1 block">Posición</label>
                          <input
                            type="text"
                            value={especsManuales.posicion}
                            onChange={(e) => setEspecsManuales({...especsManuales, posicion: e.target.value})}
                            placeholder="Ej: Delantera izquierda"
                            className="w-full px-2 py-1.5 border border-notion-border rounded text-sm focus:outline-none focus:border-reluvsa-yellow"
                          />
                        </div>
                      </div>
                      {/* Botón Guardar */}
                      <div className="flex items-center gap-3 mt-3">
                        <button
                          onClick={handleGuardarEspecs}
                          disabled={guardandoEspecs}
                          className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                            especsGuardadas
                              ? "bg-success text-white"
                              : "bg-reluvsa-yellow text-reluvsa-black hover:bg-yellow-400",
                            "disabled:opacity-50 disabled:cursor-not-allowed"
                          )}
                        >
                          {guardandoEspecs ? (
                            <>
                              <div className="w-4 h-4 border-2 border-reluvsa-black border-t-transparent rounded-full animate-spin"></div>
                              Guardando...
                            </>
                          ) : especsGuardadas ? (
                            <>
                              <CheckCircle size={16} />
                              Guardado
                            </>
                          ) : (
                            <>
                              <Save size={16} />
                              Guardar Especificaciones
                            </>
                          )}
                        </button>
                        {errorEspecs && (
                          <span className="text-sm text-danger flex items-center gap-1">
                            <AlertCircle size={14} />
                            {errorEspecs}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="p-8 text-center text-notion-text-secondary">
                Error al cargar el producto
              </div>
            )}
          </div>
        </div>
      )}

      {/* Drawer del Carrito */}
      <CartDrawer />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <AppWithAuth />
      </CartProvider>
    </AuthProvider>
  );
}

function AppWithAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-500">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  // Rutas de resultado de pago (behind login, sin router externo).
  const path = window.location.pathname;
  if (path === '/success' || path === '/cancel') {
    return <OrderResult tipo={path === '/success' ? 'success' : 'cancel'} />;
  }

  return <AppContent />;
}

export default App;
