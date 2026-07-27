import React, { useState, useRef } from 'react';
import {
  X, Upload, FileSpreadsheet, Loader2, CheckCircle, AlertTriangle, Info,
} from 'lucide-react';
import { importarCarrito } from '../services/api';
import { useCart } from '../context/CartContext';
import { cn } from '../lib/utils';

const fmt = (n) =>
  `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * Modal para armar el carrito desde un Excel/CSV de (SKU, cantidad).
 *
 * Existe porque capturar un pedido de 100+ renglones producto por producto en la
 * UI es inviable, y las refaccionarias ya tienen su lista en archivo.
 *
 * Flujo: subir -> el backend valida contra el catálogo -> se muestra qué entró y
 * qué no -> el usuario confirma y recién ahí se toca el carrito.
 */
export default function ImportarPedido({ abierto, onClose }) {
  const { agregarVarios, setAbierto: abrirCarrito } = useCart();
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [arrastrando, setArrastrando] = useState(false);
  const inputRef = useRef(null);

  const reset = () => {
    setArchivo(null);
    setResultado(null);
    setError(null);
    setCargando(false);
    setArrastrando(false);
  };

  const cerrar = () => {
    reset();
    onClose();
  };

  const procesar = async (file) => {
    if (!file) return;
    setArchivo(file);
    setError(null);
    setResultado(null);
    setCargando(true);
    try {
      const { data } = await importarCarrito(file);
      setResultado(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'No se pudo leer el archivo. Verifica que sea .xlsx o .csv con columnas de SKU y cantidad.'
      );
    } finally {
      setCargando(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setArrastrando(false);
    procesar(e.dataTransfer.files?.[0]);
  };

  const confirmar = () => {
    if (!resultado?.items?.length) return;
    agregarVarios(resultado.items);
    cerrar();
    abrirCarrito(true); // llevarlo directo al carrito ya cargado
  };

  if (!abierto) return null;

  const totalEstimado =
    resultado?.items?.reduce((acc, i) => acc + (i.precio || 0) * i.cantidad, 0) || 0;
  const hayProblemas =
    resultado &&
    (resultado.no_encontrados.length > 0 ||
      resultado.sin_stock.length > 0 ||
      resultado.ajustados.length > 0);

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={cerrar} />

      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-notion-border">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-notion-text-primary">
            <FileSpreadsheet size={20} />
            Importar pedido desde archivo
          </h2>
          <button
            onClick={cerrar}
            className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Instrucciones */}
          {!resultado && (
            <div className="flex gap-2 text-sm text-notion-text-secondary bg-blue-50 border border-blue-200 rounded-lg p-3">
              <Info size={18} className="shrink-0 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-notion-text-primary mb-1">
                  Formato del archivo
                </p>
                <p>
                  Excel (.xlsx) o CSV con una columna de <strong>SKU</strong> (o
                  Clave/Código) y otra de <strong>Cantidad</strong>. Si no hay
                  encabezados, se toma la primera columna como SKU y la segunda
                  como cantidad. Si no se indica cantidad, se asume 1.
                </p>
              </div>
            </div>
          )}

          {/* Zona de carga */}
          {!resultado && (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setArrastrando(true);
              }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className={cn(
                'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
                arrastrando
                  ? 'border-reluvsa-yellow bg-yellow-50'
                  : 'border-notion-border hover:border-reluvsa-yellow hover:bg-notion-bg-subtle'
              )}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".xlsx,.xlsm,.csv,.txt"
                className="hidden"
                onChange={(e) => procesar(e.target.files?.[0])}
              />
              {cargando ? (
                <div className="flex flex-col items-center gap-2 text-notion-text-secondary">
                  <Loader2 size={32} className="animate-spin" />
                  <p className="text-sm">Leyendo {archivo?.name}...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-notion-text-secondary">
                  <Upload size={32} className="opacity-50" />
                  <p className="text-sm font-medium text-notion-text-primary">
                    Arrastra tu archivo aquí o haz clic para elegirlo
                  </p>
                  <p className="text-xs">.xlsx o .csv — hasta 5 MB</p>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="flex gap-2 text-sm text-danger bg-red-50 border border-red-200 rounded-lg p-3">
              <AlertTriangle size={18} className="shrink-0 mt-0.5" />
              <p>{error}</p>
            </div>
          )}

          {/* Resultado */}
          {resultado && (
            <>
              <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg p-3">
                <CheckCircle size={22} className="text-green-600 shrink-0" />
                <div className="text-sm">
                  <p className="font-semibold text-notion-text-primary">
                    {resultado.encontrados} producto
                    {resultado.encontrados === 1 ? '' : 's'} listo
                    {resultado.encontrados === 1 ? '' : 's'} para agregar
                  </p>
                  <p className="text-notion-text-secondary">
                    Total estimado: <strong>{fmt(totalEstimado)}</strong> (IVA incluido)
                  </p>
                </div>
              </div>

              {/* Avisos: qué NO entró y por qué */}
              {hayProblemas && (
                <div className="space-y-2 text-sm">
                  {resultado.no_encontrados.length > 0 && (
                    <Aviso
                      titulo={`${resultado.no_encontrados.length} SKU(s) no existen en el catálogo`}
                      lista={resultado.no_encontrados}
                    />
                  )}
                  {resultado.sin_stock.length > 0 && (
                    <Aviso
                      titulo={`${resultado.sin_stock.length} SKU(s) agotados o sin precio en línea`}
                      lista={resultado.sin_stock}
                    />
                  )}
                  {resultado.ajustados.length > 0 && (
                    <Aviso
                      titulo={`${resultado.ajustados.length} cantidad(es) ajustada(s) al inventario disponible`}
                      lista={resultado.ajustados}
                      tono="info"
                    />
                  )}
                </div>
              )}

              {/* Tabla de lo que sí entró */}
              {resultado.items.length > 0 && (
                <div className="border border-notion-border rounded-lg overflow-hidden">
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-notion-bg-subtle sticky top-0">
                        <tr className="text-left text-xs text-notion-text-secondary">
                          <th className="px-3 py-2 font-medium">SKU</th>
                          <th className="px-3 py-2 font-medium">Producto</th>
                          <th className="px-3 py-2 font-medium text-right">Cant.</th>
                          <th className="px-3 py-2 font-medium text-right">Importe</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resultado.items.map((i) => (
                          <tr key={i.sku} className="border-t border-notion-border">
                            <td className="px-3 py-2">
                              <code className="text-xs text-reluvsa-red font-mono">{i.sku}</code>
                            </td>
                            <td className="px-3 py-2 text-notion-text-primary">
                              <span className="line-clamp-1">{i.nombre}</span>
                            </td>
                            <td className="px-3 py-2 text-right font-medium">{i.cantidad}</td>
                            <td className="px-3 py-2 text-right font-medium">
                              {fmt((i.precio || 0) * i.cantidad)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {resultado && (
          <div className="border-t border-notion-border p-4 flex gap-3">
            <button
              onClick={reset}
              className="flex-1 py-2.5 rounded-lg font-medium border border-notion-border hover:bg-notion-bg-subtle transition-colors"
            >
              Elegir otro archivo
            </button>
            <button
              onClick={confirmar}
              disabled={!resultado.items.length}
              className={cn(
                'flex-1 py-2.5 rounded-lg font-semibold transition-colors',
                'bg-reluvsa-yellow text-reluvsa-black hover:bg-yellow-400',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              Agregar {resultado.encontrados} al carrito
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/** Aviso colapsable con la lista de SKUs problemáticos. */
function Aviso({ titulo, lista, tono = 'warn' }) {
  const [abierto, setAbierto] = useState(false);
  const estilos =
    tono === 'info'
      ? 'bg-blue-50 border-blue-200 text-blue-900'
      : 'bg-amber-50 border-amber-200 text-amber-900';

  return (
    <div className={cn('border rounded-lg p-3', estilos)}>
      <button
        onClick={() => setAbierto((v) => !v)}
        className="flex items-center gap-2 w-full text-left font-medium"
      >
        <AlertTriangle size={16} className="shrink-0" />
        <span className="flex-1">{titulo}</span>
        <span className="text-xs underline">{abierto ? 'ocultar' : 'ver'}</span>
      </button>
      {abierto && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {lista.map((s) => (
            <code key={s} className="text-xs bg-white/70 px-1.5 py-0.5 rounded font-mono">
              {s}
            </code>
          ))}
        </div>
      )}
    </div>
  );
}
