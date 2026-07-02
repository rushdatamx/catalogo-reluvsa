import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Trophy, ChevronLeft, ChevronRight, Plus, CheckCircle, Flame } from 'lucide-react';
import { getTopVendidos, getTopVendidosCategorias } from '../services/api';
import ProductImage from './ProductImage';
import { useCart, puedeComprar } from '../context/CartContext';
import { cn } from '../lib/utils';
import { nombreCategoria } from '../lib/categorias';

// Badge de ranking: medalla para top 3, número para el resto.
function BadgeRanking({ rank }) {
  const medalla =
    rank === 1 ? { bg: 'bg-yellow-400', text: 'text-yellow-900', label: '🥇' } :
    rank === 2 ? { bg: 'bg-gray-300', text: 'text-gray-800', label: '🥈' } :
    rank === 3 ? { bg: 'bg-amber-600', text: 'text-white', label: '🥉' } :
    null;

  if (medalla) {
    return (
      <div className={cn('absolute top-2 left-2 z-10 flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold shadow', medalla.bg, medalla.text)}>
        <span>{medalla.label}</span>
        <span>#{rank}</span>
      </div>
    );
  }
  return (
    <div className="absolute top-2 left-2 z-10 flex items-center justify-center min-w-[26px] h-6 px-1.5 rounded-full bg-reluvsa-black text-white text-xs font-bold shadow">
      #{rank}
    </div>
  );
}

// Card individual del carrusel de más vendidos.
function CardVendido({ producto, onClick, onAgregar }) {
  const disponible = puedeComprar(producto);
  return (
    <article
      onClick={() => onClick(producto.sku)}
      className="flex-shrink-0 w-44 sm:w-48 bg-white rounded-xl border border-notion-border hover:border-reluvsa-yellow hover:shadow-lg cursor-pointer transition-all group relative overflow-hidden snap-start"
    >
      <BadgeRanking rank={producto.ranking_ventas} />
      {producto.es_nuevo && (
        <div className="absolute top-2 right-2 z-10 bg-gradient-to-r from-pink-500 to-orange-400 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow">
          NUEVO
        </div>
      )}

      <div className="p-3 pt-9 flex flex-col items-center">
        <ProductImage
          sku={producto.sku}
          alt={producto.nombre_producto || producto.sku}
          size="md"
          className="mb-2"
        />
      </div>

      <div className="px-3 pb-3">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-[10px] bg-notion-bg-subtle px-1.5 py-0.5 rounded font-medium text-notion-text-secondary truncate">
            {producto.marca}
          </span>
        </div>
        <h3 className="text-xs font-medium text-notion-text-primary line-clamp-2 h-8 mb-1.5 group-hover:text-reluvsa-black">
          {producto.nombre_producto || producto.tipo_producto || 'Producto'}
        </h3>

        {producto.precio_publico > 0 ? (
          <p className="text-base font-bold text-reluvsa-red leading-tight">
            ${producto.precio_publico.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
          </p>
        ) : (
          <p className="text-xs font-medium text-amber-600">Consultar precio</p>
        )}

        {producto.inventario_total > 0 ? (
          <span className="flex items-center gap-1 text-[11px] font-medium text-success mt-0.5">
            <CheckCircle size={10} /> Disponible
          </span>
        ) : (
          <span className="text-[11px] font-medium text-notion-text-secondary mt-0.5 block">
            Sin stock
          </span>
        )}

        <div className="mt-2">
          {disponible ? (
            <button
              onClick={(e) => { e.stopPropagation(); onAgregar(producto); }}
              className="w-full flex items-center justify-center gap-1 py-1.5 bg-reluvsa-yellow text-reluvsa-black text-xs font-semibold rounded-lg hover:bg-yellow-400 transition-colors"
            >
              <Plus size={13} /> Agregar
            </button>
          ) : (
            <div className="w-full text-center py-1.5 bg-notion-bg-subtle text-notion-text-secondary text-xs font-semibold rounded-lg">
              AGOTADO
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

export default function TopVendidos({ onProductoClick }) {
  const { agregar, setAbierto } = useCart();
  const [categorias, setCategorias] = useState([]);
  const [categoriaActiva, setCategoriaActiva] = useState(''); // '' = todas
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef(null);

  // Cargar categorías del top una sola vez
  useEffect(() => {
    getTopVendidosCategorias()
      .then((res) => setCategorias(res.data || []))
      .catch((err) => console.error('Error cargando categorías top:', err));
  }, []);

  // Cargar productos del top según categoría activa
  useEffect(() => {
    setLoading(true);
    const params = { limit: 30 };
    if (categoriaActiva) params.departamento = categoriaActiva;
    getTopVendidos(params)
      .then((res) => setProductos(res.data || []))
      .catch((err) => {
        console.error('Error cargando top vendidos:', err);
        setProductos([]);
      })
      .finally(() => setLoading(false));
  }, [categoriaActiva]);

  const handleAgregar = useCallback((producto) => {
    agregar(producto, 1);
    setAbierto(true);
  }, [agregar, setAbierto]);

  const scroll = (dir) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir * 400, behavior: 'smooth' });
    }
  };

  // Si no hay datos de ranking cargados, no renderizar la sección
  if (!loading && productos.length === 0 && !categoriaActiva) {
    return null;
  }

  return (
    <section className="bg-white rounded-2xl border border-notion-border p-4 sm:p-5 mb-6 shadow-sm">
      {/* Encabezado */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-9 h-9 rounded-full bg-reluvsa-yellow">
            <Trophy size={18} className="text-reluvsa-black" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-notion-text-primary leading-tight flex items-center gap-1.5">
              Los más vendidos
              <Flame size={16} className="text-orange-500" />
            </h2>
            <p className="text-xs text-notion-text-secondary">Los favoritos de nuestros clientes</p>
          </div>
        </div>
        {/* Flechas de navegación (desktop) */}
        <div className="hidden sm:flex items-center gap-1">
          <button
            onClick={() => scroll(-1)}
            className="p-2 rounded-full border border-notion-border hover:bg-notion-bg-subtle transition-colors"
            aria-label="Anterior"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            onClick={() => scroll(1)}
            className="p-2 rounded-full border border-notion-border hover:bg-notion-bg-subtle transition-colors"
            aria-label="Siguiente"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Pestañas de categoría */}
      {categorias.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2 mb-3 scrollbar-thin">
          <button
            onClick={() => setCategoriaActiva('')}
            className={cn(
              'flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap',
              categoriaActiva === ''
                ? 'bg-reluvsa-black text-white'
                : 'bg-notion-bg-subtle text-notion-text-secondary hover:bg-notion-border'
            )}
          >
            Todos
          </button>
          {categorias.map((cat) => (
            <button
              key={cat.departamento}
              onClick={() => setCategoriaActiva(cat.departamento)}
              className={cn(
                'flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap',
                categoriaActiva === cat.departamento
                  ? 'bg-reluvsa-black text-white'
                  : 'bg-notion-bg-subtle text-notion-text-secondary hover:bg-notion-border'
              )}
            >
              {nombreCategoria(cat.departamento)}
              <span className="ml-1 opacity-60">{cat.total}</span>
            </button>
          ))}
        </div>
      )}

      {/* Carrusel de productos */}
      {loading ? (
        <div className="flex gap-3 overflow-hidden">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex-shrink-0 w-44 sm:w-48 h-72 bg-notion-bg-subtle rounded-xl animate-pulse" />
          ))}
        </div>
      ) : productos.length === 0 ? (
        <div className="py-8 text-center text-sm text-notion-text-secondary">
          No hay más vendidos disponibles en esta categoría por ahora.
        </div>
      ) : (
        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin"
        >
          {productos.map((producto) => (
            <CardVendido
              key={producto.id}
              producto={producto}
              onClick={onProductoClick}
              onAgregar={handleAgregar}
            />
          ))}
        </div>
      )}
    </section>
  );
}
