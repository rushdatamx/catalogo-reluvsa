import React from 'react';

function ListaProductos({ productos, loading, onProductoClick }) {
  const formatPrice = (price) => {
    if (!price) return '-';
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(price);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Cargando productos...</p>
      </div>
    );
  }

  if (!productos || productos.length === 0) {
    return (
      <div className="loading">
        <p>No se encontraron productos con los filtros seleccionados.</p>
      </div>
    );
  }

  return (
    <div className="products-grid">
      {productos.map((producto) => (
        <div
          key={producto.id}
          className="product-card"
          onClick={() => onProductoClick(producto.sku)}
        >
          <div className="product-card-header">
            <span className="product-sku">{producto.sku}</span>
            {producto.marca && (
              <span className="product-brand">{producto.marca}</span>
            )}
          </div>

          <div className="product-name">
            {producto.nombre_producto || producto.descripcion_original?.substring(0, 80) || 'Sin nombre'}
          </div>

          {producto.descripcion_original && (
            <div className="product-description">
              {producto.descripcion_original}
            </div>
          )}

          <div className="product-footer">
            <span className="product-price">
              {formatPrice(producto.precio_publico)}
            </span>
            <span className={`product-stock ${producto.inventario_total > 0 ? 'in-stock' : 'out-of-stock'}`}>
              {producto.inventario_total > 0
                ? `${producto.inventario_total} en stock`
                : 'Sin stock'}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default ListaProductos;
