import React, { useState, useEffect, useCallback } from 'react';
import { Search, Package, Car, Link2, Filter, X, ChevronDown, CheckCircle, XCircle, AlertCircle, Tag, Calendar, Gauge, Truck, Settings, Save } from 'lucide-react';
import { getProductos, getStats, getProducto, actualizarEspecificacionesManuales } from './services/api';
import { cn } from './lib/utils';

// Componentes de Filtros
import FiltrosCascada from './components/FiltrosCascada';

function App() {
  const [filtros, setFiltros] = useState({
    departamento: '',
    marca: '',
    grupo_producto: '',
    marca_vehiculo: '',
    modelo_vehiculo: '',
    año: '',
    motor: '',
    con_inventario: false,
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

  // Estados para especificaciones manuales
  const [especsManuales, setEspecsManuales] = useState({
    garantia: '',
    material: '',
    posicion: ''
  });
  const [guardandoEspecs, setGuardandoEspecs] = useState(false);
  const [especsGuardadas, setEspecsGuardadas] = useState(false);

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

  // Cargar detalle de producto
  useEffect(() => {
    if (productoSeleccionado) {
      setLoadingDetalle(true);
      setEspecsGuardadas(false);
      getProducto(productoSeleccionado)
        .then(res => {
          setDetalleProducto(res.data);
          // Cargar especificaciones manuales existentes
          if (res.data.especificaciones_manuales) {
            setEspecsManuales({
              garantia: res.data.especificaciones_manuales.garantia || '',
              material: res.data.especificaciones_manuales.material || '',
              posicion: res.data.especificaciones_manuales.posicion || ''
            });
          } else {
            setEspecsManuales({ garantia: '', material: '', posicion: '' });
          }
        })
        .catch(console.error)
        .finally(() => setLoadingDetalle(false));
    } else {
      setDetalleProducto(null);
      setEspecsManuales({ garantia: '', material: '', posicion: '' });
    }
  }, [productoSeleccionado]);

  // Guardar especificaciones manuales
  const handleGuardarEspecs = async () => {
    setGuardandoEspecs(true);
    setEspecsGuardadas(false);
    try {
      await actualizarEspecificacionesManuales(productoSeleccionado, especsManuales);
      setEspecsGuardadas(true);
      setTimeout(() => setEspecsGuardadas(false), 3000);
    } catch (err) {
      console.error('Error guardando especificaciones:', err);
      alert('Error al guardar las especificaciones');
    } finally {
      setGuardandoEspecs(false);
    }
  };

  const handleFiltrosChange = (nuevosFiltros) => {
    setFiltros(nuevosFiltros);
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
              </div>
            )}
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
              <h2 className="text-lg font-semibold text-notion-text-primary">
                Productos
              </h2>
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
                    className="bg-white rounded-xl p-4 border border-notion-border hover:border-reluvsa-yellow hover:shadow-lg cursor-pointer transition-all group"
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                      <code className="text-xs text-reluvsa-red font-mono font-semibold">
                        {producto.sku}
                      </code>
                      <span className="text-xs bg-notion-bg-subtle px-2 py-0.5 rounded font-medium text-notion-text-secondary">
                        {producto.marca}
                      </span>
                    </div>

                    {/* Nombre */}
                    <h3 className="font-medium text-notion-text-primary mb-1 line-clamp-2 group-hover:text-reluvsa-black">
                      {producto.nombre_producto || producto.tipo_producto || 'Producto'}
                    </h3>

                    {/* Descripción */}
                    <p className="text-sm text-notion-text-secondary mb-4 line-clamp-2">
                      {producto.descripcion_original}
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-3 border-t border-notion-border">
                      <span className="text-lg font-bold text-reluvsa-red">
                        ${producto.precio_publico?.toLocaleString('es-MX', { minimumFractionDigits: 2 }) || '0.00'}
                      </span>

                      {producto.inventario_total > 0 ? (
                        <span className="flex items-center gap-1 text-xs font-medium text-success bg-success/10 px-2 py-1 rounded-full">
                          <CheckCircle size={12} />
                          {producto.inventario_total} en stock
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs font-medium text-danger bg-danger/10 px-2 py-1 rounded-full">
                          <XCircle size={12} />
                          Sin stock
                        </span>
                      )}
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
                      <p className="text-2xl font-bold text-reluvsa-red">
                        ${detalleProducto.precio_publico?.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div className="bg-notion-bg-subtle p-4 rounded-lg">
                      <p className="text-sm text-notion-text-secondary mb-1">Precio Mayoreo</p>
                      <p className="text-2xl font-bold text-notion-text-primary">
                        ${detalleProducto.precio_mayoreo?.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                  </div>

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
                              <span className="text-sm text-notion-text-primary truncate">
                                {item.nombre_producto || item.sku}
                              </span>
                            </div>
                            <span className={cn(
                              "text-xs font-medium whitespace-nowrap ml-3",
                              item.inventario_total > 0 ? "text-success" : "text-notion-text-secondary"
                            )}>
                              {item.inventario_total > 0 ? `${item.inventario_total} en stock` : 'Sin stock'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Especificaciones Manuales */}
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
                    <button
                      onClick={handleGuardarEspecs}
                      disabled={guardandoEspecs}
                      className={cn(
                        "mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
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
                  </div>
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
    </div>
  );
}

export default App;
