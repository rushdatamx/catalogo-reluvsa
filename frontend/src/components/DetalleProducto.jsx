import React, { useState, useEffect } from 'react';
import { getProducto } from '../services/api';

function DetalleProducto({ sku, onClose }) {
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!sku) return;

    setLoading(true);
    setError(null);

    getProducto(sku)
      .then(res => setProducto(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [sku]);

  const formatPrice = (price) => {
    if (!price) return '-';
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(price);
  };

  if (!sku) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        {loading && (
          <div className="loading" style={{ padding: '60px' }}>
            <div className="loading-spinner"></div>
            <p>Cargando detalles...</p>
          </div>
        )}

        {error && (
          <div className="modal-body">
            <p style={{ color: 'red' }}>Error: {error}</p>
          </div>
        )}

        {producto && !loading && (
          <>
            <div className="modal-header">
              <span className="product-sku" style={{ fontSize: '0.9rem' }}>{producto.sku}</span>
              <h2>{producto.nombre_producto || producto.descripcion_original?.substring(0, 100)}</h2>
              {producto.marca && (
                <span className="product-brand" style={{ marginTop: '8px', display: 'inline-block' }}>
                  {producto.marca}
                </span>
              )}
            </div>

            <div className="modal-body">
              {/* Precios e Inventario */}
              <div className="detail-section">
                <h3>💰 Precios e Inventario</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>Precio Público</label>
                    <span style={{ color: '#2f855a', fontWeight: 'bold', fontSize: '1.2rem' }}>
                      {formatPrice(producto.precio_publico)}
                    </span>
                  </div>
                  <div className="detail-item">
                    <label>Precio Mayoreo</label>
                    <span>{formatPrice(producto.precio_mayoreo)}</span>
                  </div>
                  <div className="detail-item">
                    <label>Inventario Total</label>
                    <span>{producto.inventario_total || 0} unidades</span>
                  </div>
                  <div className="detail-item">
                    <label>Departamento</label>
                    <span>{producto.departamento || '-'}</span>
                  </div>
                </div>
              </div>

              {/* Inventario por Sucursal */}
              {producto.inventario_sucursales && producto.inventario_sucursales.length > 0 && (
                <div className="detail-section">
                  <h3>🏪 Inventario por Sucursal</h3>
                  <div className="detail-grid">
                    {producto.inventario_sucursales.map((inv, idx) => (
                      <div key={idx} className="detail-item">
                        <label>{inv.sucursal}</label>
                        <span>{inv.cantidad} unidades</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SKUs Alternos */}
              {producto.skus_alternos && producto.skus_alternos.length > 0 && (
                <div className="detail-section">
                  <h3>🔄 Referencias Cruzadas</h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {producto.skus_alternos.map((sku, idx) => (
                      <span
                        key={idx}
                        style={{
                          background: '#edf2f7',
                          padding: '4px 10px',
                          borderRadius: '4px',
                          fontSize: '0.85rem',
                          fontFamily: 'monospace',
                        }}
                      >
                        {sku}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Compatibilidades */}
              {producto.compatibilidades && producto.compatibilidades.length > 0 && (
                <div className="detail-section">
                  <h3>🚗 Compatibilidades ({producto.compatibilidades.length})</h3>
                  <div className="compat-list">
                    {producto.compatibilidades.map((c, idx) => (
                      <div key={idx} className="compat-item">
                        <strong>
                          {c.marca_vehiculo || ''} {c.modelo_vehiculo || ''}
                        </strong>
                        {' '}
                        {c.año_inicio && c.año_fin && (
                          <span>({c.año_inicio} - {c.año_fin})</span>
                        )}
                        {c.motor && <span> • Motor: {c.motor}</span>}
                        {c.cilindros && <span> • {c.cilindros}</span>}
                        {c.especificacion && <span> • {c.especificacion}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Descripción Original */}
              <div className="detail-section">
                <h3>📝 Descripción Original</h3>
                <p style={{ fontSize: '0.9rem', color: '#4a5568', lineHeight: '1.6' }}>
                  {producto.descripcion_original}
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default DetalleProducto;
