import React, { useState, useEffect, useCallback } from 'react';
import {
  ClipboardList, X, Loader2, RefreshCw, ChevronDown, ChevronRight,
  CheckCircle, Clock, XCircle, AlertTriangle, Store, FileSpreadsheet, Search,
  ShoppingCart,
} from 'lucide-react';
import { getOrdenes, getOrden, getUsuarios, getCarritos } from '../services/api';
import { cn } from '../lib/utils';

/**
 * Portal de pedidos para el admin (solo admin). Dos pestañas:
 *
 *  - PEDIDOS: órdenes ya enviadas. Al expandir una se cargan sus renglones
 *    (la lista NO los trae para no arrastrar cientos de items por pedido).
 *    'pendiente' = el proveedor lo envió y falta atenderlo; 'pagado' = Stripe
 *    confirmó el cobro.
 *
 *  - CARRITOS ACTIVOS: carritos armados que TODAVÍA NO se envían. Es la red de
 *    seguridad: antes vivían solo en el navegador del proveedor y si se perdían
 *    no quedaba rastro. Ahora RELUVSA los ve y puede levantarlos por teléfono.
 */

const ESTADOS = {
  pagado: {
    label: 'Pagado',
    icono: CheckCircle,
    clase: 'bg-green-100 text-green-700 border-green-300',
    ayuda: 'Stripe confirmó el pago. Es una venta real.',
  },
  pendiente: {
    label: 'Por atender',
    icono: Clock,
    clase: 'bg-amber-100 text-amber-700 border-amber-300',
    ayuda: 'El proveedor envió el pedido. Falta confirmarlo y cobrarlo.',
  },
  cancelado: {
    label: 'Cancelado',
    icono: XCircle,
    clase: 'bg-gray-200 text-gray-600 border-gray-300',
    ayuda: 'El pedido se canceló antes de pagarse.',
  },
  fallido: {
    label: 'Pago fallido',
    icono: AlertTriangle,
    clase: 'bg-red-100 text-red-700 border-red-300',
    ayuda: 'El intento de pago falló.',
  },
};

const money = (n) =>
  (n ?? 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });

// Las fechas se guardan en SQLite como UTC ("YYYY-MM-DD HH:MM:SS", sin zona).
const fechaLegible = (s) => {
  if (!s) return '—';
  const iso = s.includes('T') ? s : s.replace(' ', 'T') + 'Z';
  const d = new Date(iso);
  if (isNaN(d)) return s;
  return d.toLocaleString('es-MX', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
};

/** Descarga filas como CSV. BOM para que Excel respete los acentos. */
const descargarFilasCSV = (filas, nombreArchivo) => {
  const escapar = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = '﻿' + filas.map((f) => f.map(escapar).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = nombreArchivo;
  a.click();
  URL.revokeObjectURL(url);
};

function EstadoBadge({ estado }) {
  const cfg = ESTADOS[estado] || {
    label: estado || 'Desconocido',
    icono: AlertTriangle,
    clase: 'bg-gray-100 text-gray-600 border-gray-300',
    ayuda: '',
  };
  const Icono = cfg.icono;
  return (
    <span
      title={cfg.ayuda}
      className={cn(
        'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium border',
        cfg.clase
      )}
    >
      <Icono size={12} />
      {cfg.label}
    </span>
  );
}

export default function GestionPedidos({ abierto, onClose }) {
  const [tab, setTab] = useState('pedidos'); // 'pedidos' | 'carritos'
  const [pedidos, setPedidos] = useState([]);
  const [resumen, setResumen] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Carritos activos (armados pero sin enviar)
  const [carritos, setCarritos] = useState([]);
  const [loadingCarritos, setLoadingCarritos] = useState(false);
  const [carritoAbierto, setCarritoAbierto] = useState(null);

  // Filtros
  const [filtroUsuario, setFiltroUsuario] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [usuarios, setUsuarios] = useState([]);

  // Detalle expandido: { [orderId]: { loading, items, error } }
  const [detalles, setDetalles] = useState({});
  const [expandido, setExpandido] = useState(null);

  const cargarPedidos = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { limit: 200 };
      if (filtroUsuario) params.username = filtroUsuario;
      if (filtroEstado) params.estado = filtroEstado;
      const res = await getOrdenes(params);
      setPedidos(res.data.pedidos || []);
      setResumen(res.data.resumen || {});
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando los pedidos');
    } finally {
      setLoading(false);
    }
  }, [filtroUsuario, filtroEstado]);

  const cargarCarritos = useCallback(async () => {
    setLoadingCarritos(true);
    try {
      const res = await getCarritos();
      setCarritos(res.data.carritos || []);
    } catch {
      setCarritos([]);
    } finally {
      setLoadingCarritos(false);
    }
  }, []);

  useEffect(() => {
    if (abierto) cargarPedidos();
  }, [abierto, cargarPedidos]);

  // Los carritos se cargan al abrir (no solo al entrar a la pestaña) para poder
  // mostrar el contador en el tab desde el principio.
  useEffect(() => {
    if (abierto) cargarCarritos();
  }, [abierto, cargarCarritos]);

  // Lista de proveedores para el selector (una sola vez al abrir).
  useEffect(() => {
    if (!abierto) return;
    getUsuarios()
      .then((res) => setUsuarios(res.data || []))
      .catch(() => setUsuarios([]));
  }, [abierto]);

  // Cerrar con ESC
  useEffect(() => {
    if (!abierto) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [abierto, onClose]);

  const toggleDetalle = async (pedido) => {
    const id = pedido.id;
    if (expandido === id) { setExpandido(null); return; }
    setExpandido(id);
    if (detalles[id]?.items) return; // ya cargado

    setDetalles((d) => ({ ...d, [id]: { loading: true } }));
    try {
      const res = await getOrden(id);
      setDetalles((d) => ({ ...d, [id]: { loading: false, ...res.data } }));
    } catch (err) {
      setDetalles((d) => ({
        ...d,
        [id]: { loading: false, error: err.response?.data?.detail || 'Error cargando el detalle' },
      }));
    }
  };

  // Descarga el detalle como CSV (se abre en Excel) para surtir el pedido.
  const descargarCSV = (pedido, items) => {
    descargarFilasCSV(
      [
        ['SKU', 'Producto', 'Cantidad', 'Precio unitario', 'Importe'],
        ...items.map((i) => [
          i.sku,
          i.nombre || '',
          i.cantidad,
          i.precio_unitario,
          i.importe ?? i.cantidad * i.precio_unitario,
        ]),
      ],
      `pedido-${pedido.id}-${pedido.username}.csv`
    );
  };

  // Un carrito sin enviar también se puede bajar: sirve para cotizarlo por
  // teléfono sin esperar a que el proveedor le dé "Enviar pedido".
  const descargarCarritoCSV = (c) => {
    descargarFilasCSV(
      [
        ['SKU', 'Producto', 'Marca', 'Cantidad', 'Precio unitario', 'Importe'],
        ...c.items.map((i) => [
          i.sku,
          i.nombre || '',
          i.marca || '',
          i.cantidad,
          i.precio,
          i.precio * i.cantidad,
        ]),
      ],
      `carrito-${c.username}.csv`
    );
  };

  if (!abierto) return null;

  const totalPagado = resumen.pagado?.monto || 0;
  const numPagados = resumen.pagado?.pedidos || 0;
  const numPendientes = resumen.pendiente?.pedidos || 0;
  const montoPendiente = resumen.pendiente?.monto || 0;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Pedidos"
        className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-notion-border p-6 z-10">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <ClipboardList size={22} />
              <div>
                <h2 className="text-xl font-semibold text-notion-text-primary">Pedidos</h2>
                <p className="text-sm text-notion-text-secondary">
                  Todos los pedidos de proveedores. Haz clic en uno para ver qué pidió.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { cargarPedidos(); cargarCarritos(); }}
                disabled={loading || loadingCarritos}
                className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors disabled:opacity-50"
                title="Actualizar"
              >
                <RefreshCw size={18} className={cn((loading || loadingCarritos) && 'animate-spin')} />
              </button>
              <button onClick={onClose} className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Pestañas */}
          <div className="flex gap-1 mt-4 border-b border-notion-border -mb-px">
            {[
              { id: 'pedidos', label: 'Pedidos enviados', n: pedidos.length },
              { id: 'carritos', label: 'Carritos sin enviar', n: carritos.length },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  tab === t.id
                    ? 'border-reluvsa-yellow text-notion-text-primary'
                    : 'border-transparent text-notion-text-secondary hover:text-notion-text-primary'
                )}
              >
                {t.label}
                {t.n > 0 && (
                  <span className="ml-1.5 text-xs bg-notion-bg-subtle px-1.5 py-0.5 rounded-full">
                    {t.n}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Resumen */}
          {tab === 'pedidos' && (
          <div className="flex flex-wrap gap-3 mt-4">
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <div className="text-xs text-green-700 font-medium">Pagados</div>
              <div className="text-lg font-semibold text-green-800">
                {numPagados} · {money(totalPagado)}
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              <div className="text-xs text-amber-700 font-medium">Por atender</div>
              <div className="text-lg font-semibold text-amber-800">
                {numPendientes} · {money(montoPendiente)}
              </div>
            </div>
          </div>
          )}

          {/* Filtros */}
          {tab === 'pedidos' && (
          <div className="flex flex-wrap gap-2 mt-4">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-notion-text-secondary" />
              <select
                value={filtroUsuario}
                onChange={(e) => setFiltroUsuario(e.target.value)}
                className="pl-8 pr-3 py-2 border border-notion-border rounded-lg text-sm focus:outline-none focus:border-reluvsa-yellow bg-white"
              >
                <option value="">Todos los proveedores</option>
                {usuarios.map((u) => (
                  <option key={u.username} value={u.username}>
                    {u.nombre_empresa || u.username} ({u.username})
                  </option>
                ))}
              </select>
            </div>
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="px-3 py-2 border border-notion-border rounded-lg text-sm focus:outline-none focus:border-reluvsa-yellow bg-white"
            >
              <option value="">Todos los estados</option>
              <option value="pendiente">Por atender</option>
              <option value="pagado">Pagado</option>
              <option value="cancelado">Cancelado</option>
              <option value="fallido">Pago fallido</option>
            </select>
          </div>
          )}
        </div>

        {tab === 'carritos' ? (
          <CarritosActivos
            carritos={carritos}
            loading={loadingCarritos}
            abiertoId={carritoAbierto}
            onToggle={(u) => setCarritoAbierto((prev) => (prev === u ? null : u))}
            onDescargar={descargarCarritoCSV}
          />
        ) : (
        <div className="p-6 space-y-3">
          {error && (
            <div className="p-3 bg-red-50 border border-red-300 rounded-lg text-red-600 text-sm font-medium">
              {error}
            </div>
          )}

          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-reluvsa-yellow border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="mt-4 text-notion-text-secondary text-sm">Cargando pedidos...</p>
            </div>
          ) : pedidos.length === 0 ? (
            <div className="p-8 text-center text-notion-text-secondary text-sm">
              {filtroUsuario || filtroEstado
                ? 'No hay pedidos con esos filtros.'
                : 'Todavía no hay ningún pedido. Cuando un proveedor complete un checkout, aparecerá aquí.'}
            </div>
          ) : (
            pedidos.map((p) => {
              const abiertoDet = expandido === p.id;
              const det = detalles[p.id];
              return (
                <div key={p.id} className="border border-notion-border rounded-xl overflow-hidden">
                  {/* Fila resumen (clic para expandir) */}
                  <button
                    onClick={() => toggleDetalle(p)}
                    className="w-full text-left p-4 hover:bg-notion-bg-subtle transition-colors"
                    aria-expanded={abiertoDet}
                  >
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div className="flex items-start gap-2 min-w-0">
                        {abiertoDet
                          ? <ChevronDown size={18} className="mt-0.5 flex-shrink-0" />
                          : <ChevronRight size={18} className="mt-0.5 flex-shrink-0" />}
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-notion-text-primary">
                              {p.nombre_empresa || p.username}
                            </span>
                            <code className="text-xs bg-notion-bg-subtle px-2 py-0.5 rounded font-mono">
                              {p.username}
                            </code>
                            <EstadoBadge estado={p.estado} />
                          </div>
                          <div className="text-xs text-notion-text-secondary mt-1 flex items-center gap-3 flex-wrap">
                            <span>Pedido #{p.id}</span>
                            <span>{fechaLegible(p.created_at)}</span>
                            <span className="font-medium text-notion-text-primary">
                              {p.num_renglones} producto{p.num_renglones === 1 ? '' : 's'}
                              {p.num_piezas !== p.num_renglones && ` · ${p.num_piezas} pzas`}
                            </span>
                            {p.sucursal_pickup && (
                              <span className="flex items-center gap-1">
                                <Store size={12} />
                                {p.sucursal_pickup}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className="text-lg font-semibold text-notion-text-primary">
                          {money(p.total)}
                        </div>
                        <div className="text-xs text-notion-text-secondary">IVA incluido</div>
                      </div>
                    </div>
                  </button>

                  {/* Detalle */}
                  {abiertoDet && (
                    <div className="border-t border-notion-border bg-notion-bg-subtle p-4">
                      {det?.loading ? (
                        <div className="flex items-center gap-2 text-sm text-notion-text-secondary py-4">
                          <Loader2 size={16} className="animate-spin" />
                          Cargando los productos del pedido...
                        </div>
                      ) : det?.error ? (
                        <div className="text-sm text-red-600">{det.error}</div>
                      ) : det?.items ? (
                        <>
                          <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
                            <div className="text-sm text-notion-text-secondary">
                              {det.contacto && <span className="mr-3">Contacto: {det.contacto}</span>}
                              {p.paid_at && <span>Pagado: {fechaLegible(p.paid_at)}</span>}
                            </div>
                            <button
                              onClick={() => descargarCSV(p, det.items)}
                              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-notion-border bg-white hover:bg-notion-bg-subtle font-medium transition-colors"
                            >
                              <FileSpreadsheet size={14} />
                              Descargar lista (CSV)
                            </button>
                          </div>

                          <div className="overflow-x-auto bg-white rounded-lg border border-notion-border">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b border-notion-border text-left text-xs text-notion-text-secondary">
                                  <th className="p-2 font-medium">SKU</th>
                                  <th className="p-2 font-medium">Producto</th>
                                  <th className="p-2 font-medium text-right">Cant.</th>
                                  <th className="p-2 font-medium text-right">P. unit.</th>
                                  <th className="p-2 font-medium text-right">Importe</th>
                                </tr>
                              </thead>
                              <tbody>
                                {det.items.map((i, idx) => (
                                  <tr key={idx} className="border-b border-notion-border last:border-0">
                                    <td className="p-2 font-mono text-xs">{i.sku}</td>
                                    <td className="p-2">{i.nombre || '—'}</td>
                                    <td className="p-2 text-right font-medium">{i.cantidad}</td>
                                    <td className="p-2 text-right">{money(i.precio_unitario)}</td>
                                    <td className="p-2 text-right font-medium">
                                      {money(i.importe ?? i.cantidad * i.precio_unitario)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                              <tfoot>
                                <tr className="bg-notion-bg-subtle font-semibold">
                                  <td className="p-2" colSpan={2}>
                                    Total ({det.items.length} producto{det.items.length === 1 ? '' : 's'})
                                  </td>
                                  <td className="p-2 text-right">
                                    {det.items.reduce((s, i) => s + i.cantidad, 0)}
                                  </td>
                                  <td className="p-2"></td>
                                  <td className="p-2 text-right">{money(p.total)}</td>
                                </tr>
                              </tfoot>
                            </table>
                          </div>

                          {p.stripe_session_id && (
                            <div className="text-[11px] text-notion-text-secondary mt-2 font-mono break-all">
                              Stripe: {p.stripe_session_id}
                            </div>
                          )}
                        </>
                      ) : null}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
        )}
      </div>
    </div>
  );
}

/**
 * Pestaña de carritos ACTIVOS: armados por el proveedor pero todavía no
 * enviados como pedido.
 *
 * Antes esto era invisible — el carrito vivía solo en el navegador del cliente
 * y si lo perdía no había forma de recuperarlo. Ahora RELUVSA lo ve en cuanto
 * el proveedor agrega el primer producto y puede levantarlo por teléfono.
 */
function CarritosActivos({ carritos, loading, abiertoId, onToggle, onDescargar }) {
  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="w-8 h-8 border-2 border-reluvsa-yellow border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="mt-4 text-notion-text-secondary text-sm">Cargando carritos...</p>
      </div>
    );
  }

  if (carritos.length === 0) {
    return (
      <div className="p-8 text-center text-notion-text-secondary text-sm">
        <ShoppingCart size={32} className="mx-auto mb-3 opacity-30" />
        <p>Ningún proveedor tiene un carrito armado en este momento.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-3">
      <div className="flex gap-2 text-sm bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-900">
        <AlertTriangle size={18} className="shrink-0 mt-0.5" />
        <p>
          Estos carritos <strong>todavía no son pedidos</strong>: el proveedor los
          está armando y aún no le da a "Enviar pedido". Si ves uno grande que
          lleva días parado, vale la pena hablarle.
        </p>
      </div>

      {carritos.map((c) => {
        const abierto = abiertoId === c.username;
        return (
          <div key={c.username} className="border border-notion-border rounded-xl overflow-hidden">
            <button
              onClick={() => onToggle(c.username)}
              className="w-full text-left p-4 hover:bg-notion-bg-subtle transition-colors"
              aria-expanded={abierto}
            >
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-start gap-2 min-w-0">
                  {abierto
                    ? <ChevronDown size={18} className="mt-0.5 flex-shrink-0" />
                    : <ChevronRight size={18} className="mt-0.5 flex-shrink-0" />}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-notion-text-primary">
                        {c.nombre_empresa || c.username}
                      </span>
                      <code className="text-xs bg-notion-bg-subtle px-2 py-0.5 rounded font-mono">
                        {c.username}
                      </code>
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium border bg-blue-100 text-blue-700 border-blue-300">
                        <ShoppingCart size={12} />
                        Sin enviar
                      </span>
                    </div>
                    <div className="text-xs text-notion-text-secondary mt-1 flex items-center gap-3 flex-wrap">
                      <span>Última actividad: {fechaLegible(c.updated_at)}</span>
                      <span className="font-medium text-notion-text-primary">
                        {c.num_renglones} producto{c.num_renglones === 1 ? '' : 's'}
                        {c.num_piezas !== c.num_renglones && ` · ${c.num_piezas} pzas`}
                      </span>
                      {c.contacto && <span>Contacto: {c.contacto}</span>}
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-lg font-semibold text-notion-text-primary">
                    {money(c.total_estimado)}
                  </div>
                  <div className="text-xs text-notion-text-secondary">estimado, IVA incl.</div>
                </div>
              </div>
            </button>

            {abierto && (
              <div className="border-t border-notion-border bg-notion-bg-subtle p-4">
                <div className="flex justify-end mb-3">
                  <button
                    onClick={() => onDescargar(c)}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-notion-border bg-white hover:bg-notion-bg-subtle font-medium transition-colors"
                  >
                    <FileSpreadsheet size={14} />
                    Descargar lista (CSV)
                  </button>
                </div>
                <div className="overflow-x-auto bg-white rounded-lg border border-notion-border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-notion-border text-left text-xs text-notion-text-secondary">
                        <th className="p-2 font-medium">SKU</th>
                        <th className="p-2 font-medium">Producto</th>
                        <th className="p-2 font-medium text-right">Cant.</th>
                        <th className="p-2 font-medium text-right">P. unit.</th>
                        <th className="p-2 font-medium text-right">Importe</th>
                      </tr>
                    </thead>
                    <tbody>
                      {c.items.map((i, idx) => (
                        <tr key={idx} className="border-b border-notion-border last:border-0">
                          <td className="p-2 font-mono text-xs">{i.sku}</td>
                          <td className="p-2">{i.nombre || '—'}</td>
                          <td className="p-2 text-right font-medium">{i.cantidad}</td>
                          <td className="p-2 text-right">{money(i.precio)}</td>
                          <td className="p-2 text-right font-medium">
                            {money(i.precio * i.cantidad)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-notion-bg-subtle font-semibold">
                        <td className="p-2" colSpan={2}>
                          Total ({c.num_renglones} producto{c.num_renglones === 1 ? '' : 's'})
                        </td>
                        <td className="p-2 text-right">{c.num_piezas}</td>
                        <td className="p-2"></td>
                        <td className="p-2 text-right">{money(c.total_estimado)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
