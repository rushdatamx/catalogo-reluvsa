import React, { useState, useEffect, useCallback } from 'react';
import {
  ClipboardList, X, Loader2, RefreshCw, ChevronDown, ChevronRight,
  CheckCircle, Clock, XCircle, AlertTriangle, Store, FileSpreadsheet, Search,
} from 'lucide-react';
import { getOrdenes, getOrden, getUsuarios } from '../services/api';
import { cn } from '../lib/utils';

/**
 * Portal de pedidos para el admin (solo admin).
 * Lista todas las órdenes con su proveedor, estado y monto; al expandir un
 * pedido se cargan sus renglones (la lista NO los trae para no arrastrar
 * cientos de items por pedido).
 *
 * Ojo con el estado: la orden se crea al iniciar el checkout, así que
 * 'pendiente' significa que armó el carrito pero Stripe no confirmó el pago.
 * Solo 'pagado' es una venta real.
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
  const [pedidos, setPedidos] = useState([]);
  const [resumen, setResumen] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  useEffect(() => {
    if (abierto) cargarPedidos();
  }, [abierto, cargarPedidos]);

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
    const filas = [
      ['SKU', 'Producto', 'Cantidad', 'Precio unitario', 'Importe'],
      ...items.map((i) => [
        i.sku,
        i.nombre || '',
        i.cantidad,
        i.precio_unitario,
        (i.importe ?? i.cantidad * i.precio_unitario),
      ]),
    ];
    const escapar = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    // BOM para que Excel respete los acentos.
    const csv = '﻿' + filas.map((f) => f.map(escapar).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `pedido-${pedido.id}-${pedido.username}.csv`;
    a.click();
    URL.revokeObjectURL(url);
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
                onClick={cargarPedidos}
                disabled={loading}
                className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors disabled:opacity-50"
                title="Actualizar"
              >
                <RefreshCw size={18} className={cn(loading && 'animate-spin')} />
              </button>
              <button onClick={onClose} className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Resumen */}
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

          {/* Filtros */}
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
        </div>

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
      </div>
    </div>
  );
}
