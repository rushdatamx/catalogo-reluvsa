import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const CartContext = createContext(null);

// Un producto se puede comprar solo si tiene precio > 0 e inventario > 0.
export const puedeComprar = (producto) =>
  (producto?.precio_publico || 0) > 0 && (producto?.inventario_total || 0) > 0;

// Clave de localStorage por usuario, para que el carrito no se mezcle entre sesiones.
const cartKey = (username) => `cart_${username || 'anon'}`;

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [items, setItems] = useState([]); // [{ sku, nombre, marca, precio, inventario, cantidad }]
  const [abierto, setAbierto] = useState(false);

  // Cargar carrito del usuario al montar / cambiar de usuario.
  useEffect(() => {
    if (!user) {
      setItems([]);
      return;
    }
    try {
      const saved = localStorage.getItem(cartKey(user.username));
      setItems(saved ? JSON.parse(saved) : []);
    } catch {
      setItems([]);
    }
  }, [user]);

  // Persistir cambios.
  useEffect(() => {
    if (user) {
      localStorage.setItem(cartKey(user.username), JSON.stringify(items));
    }
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

  const vaciar = useCallback(() => setItems([]), []);

  const totalItems = items.reduce((acc, i) => acc + i.cantidad, 0);
  const subtotal = items.reduce((acc, i) => acc + i.precio * i.cantidad, 0);

  return (
    <CartContext.Provider
      value={{
        items,
        abierto,
        setAbierto,
        agregar,
        actualizarCantidad,
        quitar,
        vaciar,
        totalItems,
        subtotal,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
