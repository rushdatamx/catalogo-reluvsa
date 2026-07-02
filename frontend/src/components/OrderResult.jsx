import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, Package, MapPin, ArrowLeft } from 'lucide-react';
import { getOrden } from '../services/api';
import { useCart } from '../context/CartContext';

const fmt = (n) =>
  `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// Página de resultado tras volver de Stripe Checkout.
// tipo: 'success' | 'cancel'
export default function OrderResult({ tipo }) {
  const { vaciar } = useCart();
  const [orden, setOrden] = useState(null);
  const [loading, setLoading] = useState(true);

  const params = new URLSearchParams(window.location.search);
  const orderId = params.get('order');

  useEffect(() => {
    if (tipo === 'success') {
      // El pago fue exitoso: vaciar carrito local.
      vaciar();
    }
    if (orderId) {
      getOrden(orderId)
        .then((res) => setOrden(res.data))
        .catch(() => setOrden(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []); // eslint-disable-line

  const volver = () => {
    window.location.href = '/';
  };

  const esExito = tipo === 'success';

  return (
    <div className="min-h-screen bg-notion-bg-subtle flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm max-w-lg w-full p-8">
        <div className="text-center">
          {esExito ? (
            <CheckCircle className="mx-auto text-success mb-4" size={64} />
          ) : (
            <XCircle className="mx-auto text-danger mb-4" size={64} />
          )}
          <h1 className="text-2xl font-bold text-notion-text-primary mb-2">
            {esExito ? '¡Pago recibido!' : 'Pago cancelado'}
          </h1>
          <p className="text-notion-text-secondary mb-6">
            {esExito
              ? 'Tu pedido está en proceso. Te avisaremos cuando esté listo para recoger.'
              : 'No se realizó ningún cargo. Tu carrito sigue disponible.'}
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="animate-spin text-reluvsa-yellow" size={28} />
          </div>
        ) : orden ? (
          <div className="bg-notion-bg-subtle rounded-xl p-5 mb-6 text-left">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-notion-text-secondary">Pedido</span>
              <span className="font-mono font-semibold">#{orden.id}</span>
            </div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-notion-text-secondary">Estado</span>
              <EstadoBadge estado={orden.estado} />
            </div>
            {orden.sucursal_pickup && (
              <div className="flex items-center justify-between mb-3">
                <span className="flex items-center gap-1 text-sm text-notion-text-secondary">
                  <MapPin size={14} /> Recoger en
                </span>
                <span className="font-medium text-sm">{orden.sucursal_pickup}</span>
              </div>
            )}

            {orden.items?.length > 0 && (
              <div className="border-t border-notion-border pt-3 mt-3 space-y-2">
                {orden.items.map((it) => (
                  <div key={it.sku} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 min-w-0">
                      <Package size={14} className="text-notion-text-secondary flex-shrink-0" />
                      <span className="truncate">
                        {it.cantidad}× {it.nombre}
                      </span>
                    </span>
                    <span className="font-medium whitespace-nowrap ml-2">
                      {fmt(it.precio_unitario * it.cantidad)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t border-notion-border pt-3 mt-3 flex items-center justify-between">
              <span className="font-semibold">Total</span>
              <span className="font-bold text-reluvsa-red text-lg">{fmt(orden.total)}</span>
            </div>
          </div>
        ) : null}

        <button
          onClick={volver}
          className="w-full flex items-center justify-center gap-2 py-3 bg-reluvsa-yellow text-reluvsa-black font-semibold rounded-lg hover:bg-yellow-400 transition-colors"
        >
          <ArrowLeft size={18} />
          Volver al catálogo
        </button>
      </div>
    </div>
  );
}

function EstadoBadge({ estado }) {
  const map = {
    pagado: { label: 'Pagado', cls: 'bg-green-100 text-green-700' },
    pendiente: { label: 'Pendiente de pago', cls: 'bg-amber-100 text-amber-700' },
    cancelado: { label: 'Cancelado', cls: 'bg-gray-100 text-gray-600' },
    fallido: { label: 'Fallido', cls: 'bg-red-100 text-red-700' },
  };
  const info = map[estado] || map.pendiente;
  return <span className={`text-xs font-semibold px-2 py-1 rounded ${info.cls}`}>{info.label}</span>;
}
