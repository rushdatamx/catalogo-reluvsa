import React, { useState } from 'react';
import { X, ShoppingCart, Trash2, Plus, Minus, Loader2, MapPin } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { crearCheckout } from '../services/api';
import { cn } from '../lib/utils';

// Sucursales de pickup (deben coincidir con SUCURSALES_PICKUP del backend).
const SUCURSALES = ['Carrera', 'Berriozabal', 'CEDIS', '31 Juarez', 'E-commerce'];

const fmt = (n) =>
  `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function CartDrawer() {
  const { items, abierto, setAbierto, actualizarCantidad, quitar, subtotal, totalItems } = useCart();
  const [sucursal, setSucursal] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);

  const handlePagar = async () => {
    setError(null);
    if (!sucursal) {
      setError('Selecciona una sucursal para recoger tu pedido.');
      return;
    }
    setProcesando(true);
    try {
      const payload = items.map((i) => ({ sku: i.sku, cantidad: i.cantidad }));
      const res = await crearCheckout(payload, sucursal);
      // Redirigir a la página de pago hosted de Stripe.
      window.location.href = res.data.checkout_url;
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      setError(
        status === 503
          ? 'Los pagos aún no están configurados. Contacta al administrador.'
          : detail || 'No se pudo iniciar el pago. Intenta de nuevo.'
      );
      setProcesando(false);
    }
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-[60] flex justify-end">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" onClick={() => setAbierto(false)} />

      {/* Panel */}
      <div className="relative bg-white w-full max-w-md h-full shadow-xl flex flex-col animate-in slide-in-from-right">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-notion-border">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-notion-text-primary">
            <ShoppingCart size={20} />
            Tu carrito
            {totalItems > 0 && (
              <span className="text-sm font-normal text-notion-text-secondary">
                ({totalItems} {totalItems === 1 ? 'artículo' : 'artículos'})
              </span>
            )}
          </h2>
          <button
            onClick={() => setAbierto(false)}
            className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {items.length === 0 ? (
            <div className="text-center py-16 text-notion-text-secondary">
              <ShoppingCart className="mx-auto mb-3 opacity-40" size={40} />
              <p>Tu carrito está vacío</p>
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

            {error && <p className="text-sm text-danger">{error}</p>}

            <button
              onClick={handlePagar}
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
                  Redirigiendo a pago...
                </>
              ) : (
                'Proceder al pago'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
