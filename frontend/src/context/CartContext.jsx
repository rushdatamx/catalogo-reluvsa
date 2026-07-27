import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import { getCarrito, guardarCarrito, vaciarCarritoServidor } from '../services/api';

const CartContext = createContext(null);

// Un producto se puede comprar solo si tiene precio > 0 e inventario > 0.
export const puedeComprar = (producto) =>
  (producto?.precio_publico || 0) > 0 && (producto?.inventario_total || 0) > 0;

// Clave de localStorage por usuario. Sigue existiendo como caché para pintar el
// carrito al instante (sin esperar la red) y como respaldo si el backend falla,
// pero la FUENTE DE VERDAD es el servidor.
const cartKey = (username) => `cart_${username || 'anon'}`;

// Espera antes de guardar en el servidor. Evita una petición por cada clic en
// +/- de cantidad; agrupa la ráfaga en un solo PUT.
const DEBOUNCE_MS = 800;

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [items, setItems] = useState([]); // [{ sku, nombre, marca, precio, inventario, cantidad }]
  const [abierto, setAbierto] = useState(false);
  // Estado de sincronización con el servidor, para dar feedback en la UI.
  const [sincronizando, setSincronizando] = useState(false);
  const [cargandoCarrito, setCargandoCarrito] = useState(false);
  // Productos que estaban guardados pero ya no existen en el catálogo.
  const [removidos, setRemovidos] = useState([]);

  // Evita que el primer render (o la carga inicial desde el servidor) dispare
  // un PUT que sobrescriba el carrito bueno con un array vacío.
  const listoParaGuardar = useRef(false);
  const timerRef = useRef(null);

  // --- Carga inicial: servidor primero, localStorage como respaldo ----------
  useEffect(() => {
    let cancelado = false;
    listoParaGuardar.current = false;

    if (!user) {
      setItems([]);
      setRemovidos([]);
      return;
    }

    // 1) Pintar de inmediato lo que haya en caché local (sin esperar la red).
    let local = [];
    try {
      const saved = localStorage.getItem(cartKey(user.username));
      local = saved ? JSON.parse(saved) : [];
    } catch {
      local = [];
    }
    setItems(local);

    // 2) Traer el carrito del servidor, que es la fuente de verdad.
    setCargandoCarrito(true);
    getCarrito()
      .then(({ data }) => {
        if (cancelado) return;
        const delServidor = data.items || [];
        // Si el servidor tiene algo, manda: viene con precios/inventario frescos.
        // Si está vacío pero hay carrito local (ej. armado antes de esta feature,
        // o guardado mientras el backend estaba caído), se conserva el local y se
        // sube en el siguiente guardado.
        if (delServidor.length > 0) {
          setItems(delServidor);
          setRemovidos(data.removidos || []);
        }
      })
      .catch(() => {
        // Sin red o backend caído: seguimos con el carrito local.
      })
      .finally(() => {
        if (cancelado) return;
        setCargandoCarrito(false);
        // A partir de aquí sí se puede guardar en el servidor.
        listoParaGuardar.current = true;
      });

    return () => {
      cancelado = true;
    };
  }, [user]);

  // --- Persistencia: localStorage inmediato + servidor con debounce ---------
  useEffect(() => {
    if (!user) return;

    // Caché local siempre (instantáneo, sobrevive un refresh sin red).
    localStorage.setItem(cartKey(user.username), JSON.stringify(items));

    if (!listoParaGuardar.current) return;

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setSincronizando(true);
      guardarCarrito(items.map((i) => ({ sku: i.sku, cantidad: i.cantidad })))
        .catch(() => {
          // El carrito local queda intacto; se reintenta en el próximo cambio.
        })
        .finally(() => setSincronizando(false));
    }, DEBOUNCE_MS);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [items, user]);

  const agregar = useCallback((producto, cantidad = 1) => {
    if (!puedeComprar(producto)) return false;
    setItems((prev) => {
      const existente = prev.find((i) => i.sku === producto.sku);
      const inventario = producto.inventario_total || 0;
      if (existente) {
        // No exceder el inventario disponible.
        const nuevaCantidad = Math.min(existente.cantidad + cantidad, inventario);
        return prev.map((i) =>
          i.sku === producto.sku ? { ...i, cantidad: nuevaCantidad } : i
        );
      }
      return [
        ...prev,
        {
          sku: producto.sku,
          nombre: producto.nombre_producto || producto.tipo_producto || producto.sku,
          marca: producto.marca,
          precio: producto.precio_publico,
          inventario,
          cantidad: Math.min(cantidad, inventario),
        },
      ];
    });
    return true;
  }, []);

  // Agrega varios renglones de golpe (importación desde Excel/CSV).
  // Los SKUs que ya estaban en el carrito se SUSTITUYEN por la cantidad del
  // archivo: al importar una lista, esa lista es la intención del usuario.
  const agregarVarios = useCallback((nuevos) => {
    setItems((prev) => {
      const porSku = new Map(prev.map((i) => [i.sku, i]));
      nuevos.forEach((n) => {
        porSku.set(n.sku, {
          sku: n.sku,
          nombre: n.nombre || n.sku,
          marca: n.marca,
          precio: n.precio,
          inventario: n.inventario,
          cantidad: Math.min(n.cantidad, n.inventario || n.cantidad),
        });
      });
      return Array.from(porSku.values());
    });
  }, []);

  const actualizarCantidad = useCallback((sku, cantidad) => {
    setItems((prev) =>
      prev
        .map((i) =>
          i.sku === sku
            ? { ...i, cantidad: Math.max(1, Math.min(cantidad, i.inventario)) }
            : i
        )
        .filter((i) => i.cantidad > 0)
    );
  }, []);

  const quitar = useCallback((sku) => {
    setItems((prev) => prev.filter((i) => i.sku !== sku));
  }, []);

  // Vacía el carrito local Y el del servidor. Se llama al enviar el pedido:
  // el carrito ya se convirtió en orden, no debe quedar colgando como "activo".
  const vaciar = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setItems([]);
    setRemovidos([]);
    vaciarCarritoServidor().catch(() => {});
  }, []);

  const totalItems = items.reduce((acc, i) => acc + i.cantidad, 0);
  const subtotal = items.reduce((acc, i) => acc + i.precio * i.cantidad, 0);

  return (
    <CartContext.Provider
      value={{
        items,
        abierto,
        setAbierto,
        agregar,
        agregarVarios,
        actualizarCantidad,
        quitar,
        vaciar,
        totalItems,
        subtotal,
        sincronizando,
        cargandoCarrito,
        removidos,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
