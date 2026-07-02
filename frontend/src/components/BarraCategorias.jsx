import React, { useState, useEffect } from 'react';
import { Flame, Menu } from 'lucide-react';
import { getFiltros } from '../services/api';
import { nombreCategoria } from '../lib/categorias';
import { cn } from '../lib/utils';

/**
 * Barra de navegación horizontal de categorías, estilo Amazon.
 * Va debajo del buscador. Cada categoría filtra el catálogo por departamento.
 *
 * Props:
 *  - departamentoActivo: departamento actualmente filtrado ('' = ninguno)
 *  - onSeleccionarDepartamento(dep): aplica el filtro de departamento
 *  - onMasVendidos(): lleva a la vitrina de más vendidos
 */
export default function BarraCategorias({ departamentoActivo, onSeleccionarDepartamento, onMasVendidos }) {
  const [departamentos, setDepartamentos] = useState([]);

  useEffect(() => {
    getFiltros.departamentosPopulares({ limit: 8 })
      .then((res) => setDepartamentos(res.data || []))
      .catch((err) => console.error('Error cargando departamentos populares:', err));
  }, []);

  return (
    <nav className="bg-reluvsa-black text-white" aria-label="Categorías">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-thin py-1.5">
          {/* Ícono "todas las categorías" (decorativo, refuerza el patrón Amazon) */}
          <span className="flex-shrink-0 flex items-center gap-1.5 pr-2 mr-1 text-white/70 text-xs font-medium border-r border-white/15">
            <Menu size={15} />
            <span className="hidden sm:inline">Categorías</span>
          </span>

          {/* Más vendidos: destacado al inicio */}
          <button
            onClick={onMasVendidos}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-semibold text-reluvsa-yellow hover:bg-white/10 transition-colors whitespace-nowrap"
          >
            <Flame size={15} />
            Más vendidos
          </button>

          {/* Departamentos populares */}
          {departamentos.map((d) => (
            <button
              key={d.departamento}
              onClick={() => onSeleccionarDepartamento(d.departamento)}
              className={cn(
                'flex-shrink-0 px-3 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap',
                departamentoActivo === d.departamento
                  ? 'bg-white/20 text-white'
                  : 'text-white/85 hover:bg-white/10'
              )}
            >
              {nombreCategoria(d.departamento)}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
