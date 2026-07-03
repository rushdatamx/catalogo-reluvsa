# Arquitectura del Frontend — Catálogo RELUVSA

> Guía de referencia para trabajar en el frontend. Léela antes de hacer cambios.
> Última actualización: julio 2026.

## Stack

- **React 18** (Create React App / `react-scripts`) — SPA sin router externo.
- **Tailwind CSS** con colores custom (ver `tailwind.config.js`).
- **Lucide Icons** para iconografía.
- **Axios** para llamadas API (`src/services/api.js`).
- Autenticación **JWT** (login obligatorio, no hay tienda pública).

Comandos:
```bash
cd frontend
npm start            # dev server en :3000 (asume backend en :8000)
CI=true npm run build # build de producción (valida que compile)
```

Backend local para desarrollo:
```bash
cd backend
python3 -m uvicorn main:app --reload --port 8000
# Login de dev: admin / admin123  (o visitante / visitante123)
```

## Estructura de archivos

```
frontend/src/
├── App.jsx                      # ⭐ Componente principal (~930 líneas). Contiene:
│                                #    - Estado global de filtros (23 campos)
│                                #    - Header + buscador + barra de categorías
│                                #    - Grid de productos + paginación
│                                #    - Modal de detalle de producto (INLINE, no es componente aparte)
│                                #    - Lógica de "vista portada" (vitrina más vendidos)
│                                #    - Wrappers de Auth/Cart providers y rutas /success /cancel
├── index.js                     # Punto de entrada React
├── components/
│   ├── BarraCategorias.jsx      # Barra horizontal estilo Amazon bajo el buscador
│   ├── TopVendidos.jsx          # Vitrina "Los más vendidos" (carrusel + pestañas categoría)
│   ├── ProductImage.jsx         # Imagen de producto con fallback + skeleton (reutilizable)
│   ├── FiltrosCascada.jsx       # Sidebar de filtros en cascada (~670 líneas)
│   ├── CartDrawer.jsx           # Drawer lateral del carrito de compra
│   ├── Login.jsx                # Pantalla de login
│   └── OrderResult.jsx          # Pantalla resultado de pago (/success, /cancel)
├── context/
│   ├── AuthContext.jsx          # useAuth(): user, logout, isAdmin, loading
│   └── CartContext.jsx          # useCart() + helper puedeComprar()
├── lib/
│   ├── categorias.js            # Nombres amigables de departamentos (compartido)
│   └── utils.js                 # cn() — merge de clases condicionales
├── services/
│   └── api.js                   # ⭐ TODAS las llamadas API viven aquí
├── styles.css                   # Estilos globales + Tailwind
└── index.css
```

## Convenciones y decisiones importantes

### 1. El modal de detalle está INLINE en App.jsx
El modal de detalle de producto está construido dentro de `App.jsx` (busca `productoSeleccionado`),
**NO** usa un componente separado. Cualquier cambio al modal se hace ahí. Existe un
`DetalleProducto.jsx` viejo que **no se usa** — ignóralo.

### 2. No hay router — la navegación es por estado
La app decide qué mostrar con estado local y `window.location.pathname` (solo para /success y /cancel).
No agregar react-router sin discutirlo: rompería el patrón actual y el flujo de Stripe.

### 3. Todas las llamadas API en `services/api.js`
Nunca hagas `axios.get` directo en un componente. Agrega la función a `api.js` y expórtala.
El interceptor ya maneja el token JWT y el 401 (logout automático). Patrón:
```js
export const getAlgo = (params) => api.get('/ruta', { params });
```

### 4. Colores de marca (Tailwind)
Usa siempre las clases custom, no hex sueltos:
- `reluvsa-yellow` (#FFED00) — color primario / CTAs
- `reluvsa-black` (#1a1a1a) — texto fuerte, barra de categorías
- `reluvsa-red` (#E31E24) — precios, badges de acento
- `notion-bg-subtle`, `notion-border`, `notion-text-primary/secondary` — grises de UI
- `success` / `danger` / `warning` — estados

### 5. Imágenes de producto
Usa el componente `ProductImage` (maneja fallback y skeleton). Las imágenes van por un
proxy HTTPS del backend: `getImageUrl(sku)` → `/api/images/{sku}`. Solo ~19% de productos
tienen imagen; el resto cae al placeholder automáticamente. Tamaños: `sm|md|lg|xl`.

### 6. Carrito y disponibilidad
- `useCart()` da: `agregar(producto, cantidad)`, `setAbierto`, `totalItems`, `items`, etc.
- `puedeComprar(producto)` → `true` solo si hay inventario Y precio > 0. Úsalo SIEMPRE
  antes de mostrar el botón "Agregar al carrito"; si no, muestra "AGOTADO" / "Consultar precio".
- Decisiones de negocio fijas: login-only, pickup en sucursal, $0 o sin stock = AGOTADO,
  precio mostrado = `precio_publico` (ya incluye IVA).

### 7. "Vista portada" vs "resultados"
En `App.jsx`, `vistaPortada` es `true` cuando NO hay filtros ni búsqueda activos.
- En portada: se muestra la vitrina `<TopVendidos>` arriba del grid.
- Al filtrar/buscar: la vitrina desaparece y el grid muestra los resultados filtrados.
Si agregas secciones de descubrimiento (destacados, novedades, etc.), engánchalas al
patrón `vistaPortada` para que solo aparezcan en la portada.

## Features de descubrimiento (portada estilo Amazon/MercadoLibre)

### Barra de categorías (`BarraCategorias.jsx`)
Barra horizontal oscura, sticky, dentro del `<header>` debajo del buscador.
- Botón "🔥 Más vendidos" → scroll a la vitrina (o vuelve a portada si estabas filtrando).
- Departamentos populares → al hacer clic filtran el catálogo por departamento (toggle).
- Datos: `GET /api/filtros/departamentos-populares?limit=8` (top departamentos por # de
  productos con inventario — automático, cero mantenimiento).
- Handlers en App.jsx: `handleSeleccionarDepartamento`, `handleIrMasVendidos`.

### Vitrina "Los más vendidos" (`TopVendidos.jsx`)
Carrusel horizontal + pestañas por categoría. Badges de ranking (🥇🥈🥉 top 3, #N resto).
- Datos: `GET /api/productos/top-vendidos?departamento=&limit=` y
  `GET /api/productos/top-vendidos/categorias`.
- El ranking vive en la columna `productos.ranking_ventas` (BD), poblada mensualmente
  desde `data/top-mas-vendidos.xlsx` con `backend/scripts/actualizar_top_vendidos.py`.
- Ver detalle del flujo mensual en el CLAUDE.md raíz, sección "Top de Más Vendidos".

### Nombres de categorías (`lib/categorias.js`)
Mapa `DEPARTAMENTO_BD → nombre amigable` compartido entre la barra y la vitrina.
Si el catálogo trae un departamento nuevo sin entrada, cae a un fallback capitalizado.
Agrega ahí los nombres bonitos que quieras que se vean en la UI.

## Endpoints del backend que consume el frontend

| Función en api.js | Endpoint | Uso |
|---|---|---|
| `getProductos(params)` | `GET /api/productos` | Grid principal (filtros + paginación) |
| `getProducto(sku)` | `GET /api/productos/{sku}` | Modal de detalle |
| `getTopVendidos(params)` | `GET /api/productos/top-vendidos` | Vitrina más vendidos |
| `getTopVendidosCategorias()` | `GET /api/productos/top-vendidos/categorias` | Pestañas de la vitrina |
| `getFiltros.departamentosPopulares()` | `GET /api/filtros/departamentos-populares` | Barra de categorías |
| `getFiltros.*` | `GET /api/filtros/*` | Sidebar de filtros en cascada |
| `getStats()` | `GET /api/stats` | Badges de stats en el header |
| `crearCheckout(items, sucursal)` | `POST /api/checkout` | Stripe Checkout |
| `exportarExcel/PDF(params)` | `GET /api/exportar/*` | Botones exportar |

## Cómo validar cambios antes de subir

1. `cd frontend && CI=true npm run build` — debe decir **"Compiled successfully"** sin errores.
2. Con backend en :8000 y `npm start`, probar el flujo en el navegador (login admin/admin123).
3. Revisar consola del navegador sin errores.

## Deploy

- **Frontend** → Vercel (auto-deploy al hacer `git push` a `main`). Proyecto: catalogo-reluvsa.vercel.app
- **Backend + BD** → Railway (auto-deploy al push). Proyecto Railway: `catalogo-reluvsa`.
- Si un cambio toca datos de la BD (ej. ranking), hay que copiar la BD:
  `cp backend/data/catalogo.db data/catalogo.db` y commitear ambas.
- Vercel suele desplegar más rápido que Railway; si el frontend nuevo aún no ve datos
  nuevos, espera a que Railway termine de reiniciar.

## Ideas pendientes de frontend (backlog sugerido)

- Sección "Novedades" en portada (ya existe badge NUEVO y filtro solo_nuevos; falta la vitrina).
- Autocompletado / sugerencias en el buscador.
- Chips de filtros aplicados removibles (estilo MercadoLibre).
- Galería de imágenes + tabs en el modal de detalle.
- Mejora mobile: drawer de filtros, bottom navigation.
- Rango de precios con slider.
