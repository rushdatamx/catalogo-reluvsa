import React, { useState } from 'react';
import {
  X, ShoppingCart, Trash2, Plus, Minus, Loader2, MapPin, Send, CheckCircle,
  FileSpreadsheet, Cloud, CloudOff,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { crearPedido } from '../services/api';
import { cn } from '../lib/utils';
import ImportarPedido from './ImportarPedido';

// Sucursales de pickup (deben coincidir con SUCURSALES_PICKUP del backend).
const SUCURSALES = ['Carrera', 'Berriozabal', 'CEDIS', '31 Juarez', 'E-commerce'];

const fmt = (n) =>
  `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function CartDrawer() {
  const {
    items, abierto, setAbierto, actualizarCantidad, quitar, subtotal, totalItems,
    vaciar, sincronizando, cargandoCarrito, removidos,
  } = useCart();
  const [sucursal, setSucursal] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);
  // Confirmación tras enviar el pedido: { order_id, total, num_productos, sucursal }
  const [enviado, setEnviado] = useState(null);
  const [importando, setImportando] = useState(false);

  // Envía el pedido SIN pago en línea: queda 'pendiente' y RELUVSA lo cotiza
  // y cobra por fuera. Cuando el cobro en línea esté activo, aquí volverá a
  // ofrecerse el pago con tarjeta (crearCheckout).
  const handleEnviarPedido = async () => {
    setError(null);
    if (!sucursal) {
      setError('Selecciona una sucursal para recoger tu pedido.');
      return;
    }
    setProcesando(true);
    try {
      const payload = items.map((i) => ({ sku: i.sku, cantidad: i.cantidad }));
      const res = await crearPedido(payload, sucursal);
      setEnviado({ ...res.data, sucursal });
      vaciar();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'No se pudo enviar el pedido. Intenta de nuevo.'
      );
    } finally {
      setProcesando(false);
    }
  };

  const cerrar = () => {
    setAbierto(false);
    setEnviado(null);
    setSucursal('');
    setError(null);
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-[60] flex justify-end">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" onClick={cerrar} />

      {/* Panel */}
      <div className="relative bg-white w-full max-w-md h-full shadow-xl flex flex-col animate-in slide-in-from-right">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-notion-border">
          <div className="min-w-0">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-notion-text-primary">
              <ShoppingCart size={20} />
              Tu carrito
              {totalItems > 0 && !enviado && (
                <span className="text-sm font-normal text-notion-text-secondary">
                  ({totalItems} {totalItems === 1 ? 'artículo' : 'artículos'})
                </span>
              )}
            </h2>
            {/* El carrito se guarda en el servidor: se recupera desde cualquier
                dispositivo aunque no se haya enviado el pedido. */}
            {!enviado && (
              <p className="flex items-center gap-1 text-xs text-notion-text-secondary mt-0.5">
                {sincronizando || cargandoCarrito ? (
                  <>
                    <Loader2 size={12} className="animate-spin" />
                    {cargandoCarrito ? 'Recuperando tu carrito...' : 'Guardando...'}
                  </>
                ) : (
                  <>
                    <Cloud size={12} />
                    Guardado — lo recuperas desde cualquier dispositivo
                  </>
                )}
              </p>
            )}
          </div>
          <button
            onClick={cerrar}
            className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors shrink-0"
          >
            <X size={20} />
          </button>
        </div>

        {/* Confirmación de pedido enviado */}
        {enviado ? (
          <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center text-center">
            <CheckCircle size={56} className="text-green-600 mb-4" />
            <h3 className="text-xl font-semibold text-notion-text-primary mb-2">
              ¡Pedido enviado!
            </h3>
            <p className="text-sm text-notion-text-secondary mb-4">
              Tu pedido <strong>#{enviado.order_id}</strong> quedó registrado.
              Un asesor de RELUVSA te contactará para confirmarlo y coordinar el pago.
            </p>
            <div className="w-full bg-notion-bg-subtle rounded-xl p-4 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-notion-text-secondary">Productos</span>
                <span className="font-medium">{enviado.num_productos}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-notion-text-secondary">Recoger en</span>
                <span className="font-medium">{enviado.sucursal}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-notion-border mt-2">
                <span className="font-medium">Total estimado</span>
                <span className="font-bold text-reluvsa-red">{fmt(enviado.total)}</span>
              </div>
            </div>
            <p className="text-xs text-notion-text-secondary mt-3">
              Precios incluyen IVA. El total se confirma al procesar el pedido.
            </p>
            <button
              onClick={cerrar}
              className="mt-6 w-full py-3 rounded-lg font-semibold bg-reluvsa-yellow text-reluvsa-black hover:bg-yellow-400 transition-colors"
            >
              Seguir comprando
            </button>
          </div>
        ) : (
        <>
        {/* Importar pedido desde archivo: capturar 100+ renglones a mano es inviable. */}
        <div className="px-4 pt-3">
          <button
            onClick={() => setImportando(true)}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium border border-dashed border-notion-border text-notion-text-secondary hover:border-reluvsa-yellow hover:text-notion-text-primary hover:bg-notion-bg-subtle transition-colors"
          >
            <FileSpreadsheet size={16} />
            Importar pedido desde Excel o CSV
          </button>
        </div>

        {/* Productos guardados que ya no existen en el catálogo. */}
        {removidos.length > 0 && (
          <div className="mx-4 mt-3 flex gap-2 text-xs bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-2.5">
            <CloudOff size={16} className="shrink-0 mt-0.5" />
            <p>
              {removidos.length} producto{removidos.length === 1 ? '' : 's'} de tu
              carrito guardado ya no está{removidos.length === 1 ? '' : 'n'} en el
              catálogo y se omitió{removidos.length === 1 ? '' : 'eron'}:{' '}
              <span className="font-mono">{removidos.slice(0, 5).join(', ')}</span>
              {removidos.length > 5 && ` y ${removidos.length - 5} más`}
            </p>
          </div>
        )}

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {items.length === 0 ? (
            <div className="text-center py-16 text-notion-text-secondary">
              <ShoppingCart className="mx-auto mb-3 opacity-40" size={40} />
              <p>Tu carrito está vacío</p>
              <p className="text-xs mt-1">
                Puedes importar tu lista desde un archivo con el botón de arriba.
              </p>
            </div>
          ) : (
            items.map((item) => (
              <div key={item.sku} className="flex gap-3 bg-notion-bg-subtle p-3 rounded-lg">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <code className="text-xs text-reluvsa-red font-mono font-semibold">{item.sku}</code>
                    {item.marca && (
                      <span className="text-xs bg-white px-1.5 py-0.5 rounded text-notion-text-secondary">
                        {item.marca}
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-notion-text-primary line-clamp-2 mb-2">
                    {item.nombre}
                  </p>
                  <div className="flex items-center justify-between">
                    {/* Selector de cantidad */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => actualizarCantidad(item.sku, item.cantidad - 1)}
                        className="p-1 bg-white rounded border border-notion-border hover:border-reluvsa-yellow"
                      >
                        <Minus size={14} />
                      </button>
                      <span className="text-sm font-medium w-6 text-center">{item.cantidad}</span>
                      <button
                        onClick={() => actualizarCantidad(item.sku, item.cantidad + 1)}
                        disabled={item.cantidad >= item.inventario}
                        className="p-1 bg-white rounded border border-notion-border hover:border-reluvsa-yellow disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                    <span className="text-sm font-bold text-reluvsa-red">
                      {fmt(item.precio * item.cantidad)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => quitar(item.sku)}
                  className="self-start p-1.5 text-notion-text-secondary hover:text-danger transition-colors"
                  aria-label="Quitar"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer con checkout */}
        {items.length > 0 && (
          <div className="border-t border-notion-border p-4 space-y-3">
            {/* Selección de sucursal de pickup */}
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-notion-text-primary mb-1.5">
                <MapPin size={16} />
                Recoger en sucursal
              </label>
              <select
                value={sucursal}
                onChange={(e) => setSucursal(e.target.value)}
                className="w-full px-3 py-2 border border-notion-border rounded-lg text-sm focus:outline-none focus:border-reluvsa-yellow bg-white"
              >
                <option value="">Selecciona una sucursal...</option>
                {SUCURSALES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Subtotal */}
            <div className="flex items-center justify-between text-base">
              <span className="font-medium text-notion-text-primary">Total</span>
              <span className="font-bold text-reluvsa-red text-lg">{fmt(subtotal)}</span>
            </div>
            <p className="text-xs text-notion-text-secondary -mt-2">Precios incluyen IVA</p>

            {error && (
              <p className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg p-2">
                {error}
              </p>
            )}

            <button
              onClick={handleEnviarPedido}
              disabled={procesando}
              className={cn(
                'w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold transition-colors',
                'bg-reluvsa-yellow text-reluvsa-black hover:bg-yellow-400',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {procesando ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Enviando pedido...
                </>
              ) : (
                <>
                  <Send size={18} />
                  Enviar pedido
                </>
              )}
            </button>
            <p className="text-xs text-notion-text-secondary text-center">
              No se cobra nada ahora. Un asesor te contactará para confirmar tu
              pedido y coordinar el pago.
            </p>
          </div>
        )}
        </>
        )}
      </div>

      <ImportarPedido abierto={importando} onClose={() => setImportando(false)} />
    </div>
  );
}
