# CLAUDE.md - Catálogo RELUVSA

## Inicio de Conversación

Cuando el usuario diga "lee el claude.md" o inicie una conversación pidiendo contexto del proyecto, ofrecer como **opción principal** la actualización del catálogo:

> **¿Buscas actualizar la información del catálogo?**
> Usa `/actualizar-catalogo` o coloca el archivo `borrador-catalogo.xlsx` en `data/` y dime que lo revise.

Además, mostrar un resumen breve de las otras capacidades disponibles (agentes expertos, debugging, etc.).

## Descripción del Proyecto

Sistema de catálogo de autopartes para RELUVSA con filtros en cascada estilo Amazon/MercadoLibre. Permite buscar productos por vehículo, marca, departamento, grupo de producto y características específicas (llantas, aceites, acumuladores). Incluye detección de productos intercambiables basada en SKUs compartidos.

## Arquitectura

```
catalogo-reluvsa/
├── backend/                 # API FastAPI + Python
│   ├── main.py             # Punto de entrada, CORS, routers
│   ├── database.py         # Conexión SQLite + schema completo
│   ├── models.py           # Modelos Pydantic
│   ├── routers/
│   │   ├── productos.py    # GET /api/productos, /buscar, /{sku}
│   │   ├── filtros.py      # Endpoints de filtros en cascada
│   │   ├── exportar.py     # Exportar Excel/PDF con imágenes
│   │   ├── auth.py         # Autenticación JWT (login, roles)
│   │   └── images.py       # Proxy de imágenes (HTTPS→HTTP)
│   ├── parsers/            # 82 parsers de marcas
│   │   ├── __init__.py     # Mapeo marca → parser
│   │   ├── base.py         # Clase base con patrones comunes
│   │   ├── extractores_caracteristicas.py  # Llantas, aceites, acumuladores
│   │   └── [marca].py      # Parser específico por marca
│   └── scripts/            # Scripts de utilidad
│       ├── importar_csv.py              # Importación inicial de productos
│       ├── extraer_compatibilidades.py  # Extrae compatibilidades vehiculares
│       ├── extraer_caracteristicas.py   # Extrae características (llantas, aceites, etc.)
│       ├── calcular_intercambiables.py  # Precalcula productos intercambiables
│       ├── importar_grupos.py           # Importa grupos de producto desde CSV
│       ├── reprocesar_completo.py       # Reprocesa nombres + compatibilidades
│       ├── reprocesar_compatibilidades.py
│       ├── reprocesar_nombres.py
│       ├── reprocesar_skus_alternos.py  # Re-extrae skus_alternos con regex mejorado
│       ├── procesar_productos_nuevos.py # Procesa productos recién importados
│       ├── actualizar_precios_excel.py  # Actualiza precios (IVA) + inventario desde Excel
│       ├── actualizar_top_vendidos.py   # Actualiza ranking de más vendidos (mensual)
│       └── validar_*.py                 # Scripts de validación
├── frontend/               # React SPA — VER frontend/ARQUITECTURA.md
│   ├── ARQUITECTURA.md     # 📘 Guía completa del frontend (leer antes de tocar)
│   ├── src/
│   │   ├── App.jsx         # Componente principal con modal de detalle inline
│   │   ├── lib/
│   │   │   ├── utils.js       # Utilidad cn() para clases condicionales
│   │   │   └── categorias.js  # Nombres amigables de departamentos
│   │   ├── components/
│   │   │   ├── FiltrosCascada.jsx    # Filtros condicionales (sidebar)
│   │   │   ├── BarraCategorias.jsx   # Barra de categorías estilo Amazon
│   │   │   ├── TopVendidos.jsx       # Vitrina "Los más vendidos"
│   │   │   ├── ProductImage.jsx      # Imagen con fallback + skeleton
│   │   │   ├── CartDrawer.jsx        # Drawer del carrito
│   │   │   ├── GestionUsuarios.jsx   # Modal admin: usuarios de proveedores
│   │   │   ├── Login.jsx / OrderResult.jsx  # Login y resultado de pago
│   │   │   └── DetalleProducto.jsx   # (No usado - modal está en App.jsx)
│   │   ├── context/        # AuthContext (useAuth) y CartContext (useCart)
│   │   ├── services/
│   │   │   └── api.js      # Servicios API con axios
│   │   └── styles.css      # Estilos CSS + Tailwind
│   └── package.json
├── data/
│   ├── catalogo.db         # Base de datos SQLite principal
│   └── grupos_producto.csv # Mapeo SKU → grupo de producto
└── .claude/
    └── commands/           # Agentes expertos
        ├── experto-catalogo.md
        ├── experto-autopartes.md
        ├── experto-debug-db.md
        └── experto-ecommerce.md
```

## Stack Tecnológico

- **Backend**: Python 3.x + FastAPI + SQLite + httpx (async HTTP client) + openpyxl + reportlab + Pillow
- **Frontend**: React 18 + Tailwind CSS + Lucide Icons
- **Base de datos**: SQLite (archivo local, se copia a Railway en deploy)
- **Parsers**: 82 marcas con extracción específica
- **Autenticación**: JWT (PyJWT)
- **Deploy**: Railway (backend) + GitHub auto-deploy

## Base de Datos

### Esquema Completo

```sql
-- Productos principales (22,178 registros)
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,          -- "Clave" del Excel (col 0), código interno
    sku_real TEXT,                     -- "SKU" comercial del Excel (col 2); ~19% poblado
    departamento TEXT,
    marca TEXT,
    descripcion_original TEXT,
    nombre_producto TEXT,              -- Nombre limpio extraído
    tipo_producto TEXT,
    skus_alternos TEXT,                -- JSON array de SKUs alternativos
    precio_publico REAL,
    precio_mayoreo REAL,
    imagen_url TEXT,
    inventario_total INTEGER DEFAULT 0,
    grupo_producto TEXT,               -- Grupo: AMORTIGUADORES, BALATAS, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compatibilidades vehiculares (29,168 registros)
CREATE TABLE compatibilidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    marca_vehiculo TEXT,
    modelo_vehiculo TEXT,
    año_inicio INTEGER,
    año_fin INTEGER,
    motor TEXT,                        -- Formato: X.XL, V6, V8, etc.
    cilindros TEXT,
    especificacion TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- Inventario por sucursal (19,763 registros)
CREATE TABLE inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    sucursal TEXT,
    cantidad INTEGER,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- Características específicas (2,866 registros) - Llantas, aceites, acumuladores
CREATE TABLE caracteristicas_producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    categoria TEXT,                    -- 'llanta', 'aceite', 'acumulador'
    clave TEXT,
    valor TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- Productos intercambiables (135,174 relaciones) - Precalculado
CREATE TABLE productos_intercambiables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    producto_intercambiable_id INTEGER NOT NULL,
    sku_comun TEXT,                    -- SKU que comparten
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_intercambiable_id) REFERENCES productos(id) ON DELETE CASCADE,
    UNIQUE(producto_id, producto_intercambiable_id)
);

-- Especificaciones manuales (editables por usuario)
CREATE TABLE especificaciones_manuales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,                -- 'garantia', 'material', 'posicion'
    valor TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    UNIQUE(producto_id, tipo)
);
```

### Índices

```sql
-- Productos
CREATE INDEX idx_productos_departamento ON productos(departamento);
CREATE INDEX idx_productos_marca ON productos(marca);
CREATE INDEX idx_productos_sku ON productos(sku);
CREATE INDEX idx_productos_grupo ON productos(grupo_producto);

-- Compatibilidades
CREATE INDEX idx_compat_producto ON compatibilidades(producto_id);
CREATE INDEX idx_compat_marca ON compatibilidades(marca_vehiculo);
CREATE INDEX idx_compat_modelo ON compatibilidades(modelo_vehiculo);

-- Características
CREATE INDEX idx_carac_producto ON caracteristicas_producto(producto_id);
CREATE INDEX idx_carac_categoria ON caracteristicas_producto(categoria);

-- Intercambiables
CREATE INDEX idx_intercambiables_producto ON productos_intercambiables(producto_id);
CREATE INDEX idx_intercambiables_inverso ON productos_intercambiables(producto_intercambiable_id);

-- Especificaciones manuales
CREATE INDEX idx_especs_manuales_producto ON especificaciones_manuales(producto_id);
```

## API Endpoints

### Productos

```
GET /api/productos
    ?departamento=SUSPENSION
    ?marca=MONROE&marca=KYB            # MULTI-selección: repetir el param (IN SQL)
    ?grupo_producto=AMORTIGUADORES     # Filtro por grupo
    ?marca_vehiculo=CHEVROLET
    ?modelo_vehiculo=SILVERADO
    ?año=2020
    ?motor=5.3L
    ?con_inventario=true
    ?q=busqueda
    ?page=1&limit=20

    # Filtros específicos llantas
    ?ancho_llanta=205
    ?relacion_llanta=55
    ?diametro_llanta=16
    ?tipo_llanta=RADIAL
    ?capas_llanta=4C

    # Filtros específicos aceites
    ?viscosidad=5W30
    ?tipo_aceite=SINTETICO
    ?presentacion=1L

    # Filtros específicos acumuladores
    ?grupo_bci=34
    ?capacidad_cca=550
    ?tamano_acumulador=...

    # Orden (Julio 2026): más nuevos primero (created_at DESC),
    # desempate por inventario_total DESC. Aplica también a /api/exportar/*
    # (el modo solo_top_vendidos ordena por ranking_ventas ASC).

GET /api/productos/buscar?q=termino&limit=20
GET /api/productos/{sku}
    # Retorna: producto + compatibilidades + características + intercambiables

PUT /api/productos/{sku}/especificaciones-manuales
    # Body: { garantia, material, posicion }
```

### Filtros (en cascada)

```
# Filtros generales
GET /api/filtros/departamentos
GET /api/filtros/marcas-producto?departamento=X
GET /api/filtros/tipos-producto?departamento=X&marca=Y
GET /api/filtros/grupos-producto?departamento=X&marca_producto=Y&...  # NUEVO

# Filtros vehiculares (cascada)
GET /api/filtros/marcas-vehiculo?departamento=X
GET /api/filtros/modelos-vehiculo?marca_vehiculo=X
GET /api/filtros/años?marca_vehiculo=X&modelo_vehiculo=Y
GET /api/filtros/motores?marca_vehiculo=X&modelo_vehiculo=Y&año=Z

# Filtros llantas (dept=LLANTAS)
GET /api/filtros/llantas/anchos
GET /api/filtros/llantas/relaciones?ancho=205
GET /api/filtros/llantas/diametros?ancho=205&relacion=55
GET /api/filtros/llantas/tipos
GET /api/filtros/llantas/capas

# Filtros aceites (dept=LUBRICACIÓN o QUIMICOS/ADITIVOS)
GET /api/filtros/aceites/viscosidades
GET /api/filtros/aceites/tipos
GET /api/filtros/aceites/presentaciones

# Filtros acumuladores (marcas: CHECKER, EXTREMA, CAMEL)
GET /api/filtros/acumuladores/grupos
GET /api/filtros/acumuladores/capacidades
GET /api/filtros/acumuladores/tamanos

# Stats
GET /api/stats

# Imágenes (proxy HTTPS)
GET /api/images/{sku}
    # Proxy para cargar imágenes HTTP vía HTTPS
    # Cache: 24 horas | Timeout: 10s

# Exportar (con imágenes embebidas)
GET /api/exportar/excel?[mismos filtros que /api/productos]
    # Genera Excel (.xlsx) con thumbnails 75x75, compatibilidades, intercambiables
    # Columna SKU = sku_real (comercial) con fallback a sku (Clave) si está vacío
    # Máx 1000 productos | Timeout imagen: 5s | Concurrencia: 25
    # ?solo_top_vendidos=true  -> exporta solo el ranking de más vendidos
    #                             (ranking_ventas IS NOT NULL, orden por ranking ASC)
GET /api/exportar/pdf?[mismos filtros que /api/productos]
    # Genera PDF landscape con thumbnails 50x50, filas alternadas
    # Compatibilidades/intercambiables: máx 5 + "... y X más"
    # ?solo_top_vendidos=true  -> igual que Excel (usado por la vitrina TopVendidos)
# Límite y concurrencia: constantes MAX_PRODUCTOS_EXPORT=1000, IMAGE_CONCURRENCY=25
# en backend/routers/exportar.py (subir concurrencia compensa el timeout de Railway).

# Autenticación
POST /api/auth/login
    # Body: { username, password }
    # Response: { access_token, token_type }
```

## Frontend - Estructura de Componentes

> 📘 **Para trabajar en el frontend, lee primero `frontend/ARQUITECTURA.md`** — guía
> completa de estructura, convenciones, colores de marca, API y patrones. Esta sección
> es solo un resumen.

Componentes principales (`frontend/src/`):
- `App.jsx` — componente principal (~930 líneas): estado de filtros, header, buscador,
  barra de categorías, grid, paginación y **modal de detalle inline**.
- `components/BarraCategorias.jsx` — barra horizontal estilo Amazon bajo el buscador.
- `components/TopVendidos.jsx` — vitrina "Los más vendidos" (carrusel + pestañas).
- `components/ProductImage.jsx` — imagen con fallback + skeleton (reutilizable).
- `components/FiltrosCascada.jsx` — sidebar de filtros en cascada.
- `components/CartDrawer.jsx` / `Login.jsx` / `OrderResult.jsx` — carrito, login, resultado de pago.
- `context/AuthContext.jsx` (`useAuth`) y `context/CartContext.jsx` (`useCart`, `puedeComprar`).
- `lib/categorias.js` — nombres amigables de departamentos (compartido barra/vitrina).
- `services/api.js` — **todas** las llamadas API.

### App.jsx (Componente Principal)
- Estado de filtros con 23 campos
- **Barra de categorías** (estilo Amazon) debajo del buscador
- **Vitrina "Más vendidos"** en la portada (cuando no hay filtros ni búsqueda: `vistaPortada`)
- **Botones Exportar Excel/PDF** en header de resultados (visibles cuando hay productos)
- Modal de detalle de producto **inline** (NO usa DetalleProducto.jsx)
- Secciones del modal:
  1. Header con imagen, SKU, marca, precio
  2. Descripción
  3. Precios (público/mayoreo)
  4. Inventario por sucursal
  5. Compatibilidades vehiculares
  6. **Productos Intercambiables** (click para navegar)
  7. Especificaciones Manuales (editables)

### FiltrosCascada.jsx (Sidebar)
- Filtros básicos: Departamento (single-select), **Marca del Producto (MULTI-select)**
  - Marca usa el componente `MultiSelectField` (checkboxes en panel desplegable, estilo
    Amazon). `filtros.marca` es un **array de strings** (no un string). Ver nota abajo.
- Sección "Compatibilidad Vehicular" (colapsable):
  - Marca del Vehículo → Modelo → Año → Motor → **Grupo de Producto**
- Secciones condicionales:
  - Medidas de Llanta (si dept=LLANTAS)
  - Especificaciones de Aceite (si dept=LUBRICACIÓN)
  - Especificaciones de Acumulador (si marca en CHECKER/EXTREMA/CAMEL)
- Checkbox "Solo con inventario"

### Lógica de Filtros Condicionales

```javascript
// Departamentos SIN compatibilidad vehicular
const DEPARTAMENTOS_SIN_COMPATIBILIDAD = ['LLANTAS', 'LUBRICACIÓN', 'QUIMICOS/ADITIVOS'];

// Marcas de acumuladores (filtros especiales)
const MARCAS_ACUMULADORES = ['CHECKER', 'EXTREMA', 'CAMEL'];

// Lógica de visualización
// OJO: filtros.marca es un ARRAY (multi-select). Se normaliza a marcasSel.
const marcasSel = Array.isArray(filtros.marca) ? filtros.marca : (filtros.marca ? [filtros.marca] : []);
const esLlantas = filtros.departamento === 'LLANTAS';
const esAceites = filtros.departamento === 'LUBRICACIÓN' || filtros.departamento === 'QUIMICOS/ADITIVOS';
const esAcumuladores = marcasSel.some((m) => MARCAS_ACUMULADORES.includes(m)); // alguna marca es de acumulador
const mostrarFiltrosVehiculo = !DEPARTAMENTOS_SIN_COMPATIBILIDAD.includes(filtros.departamento) && !esAcumuladores;
```

### ⚠️ Nota importante: Marca es MULTI-selección (array)
`filtros.marca` es un **array de strings**, NO un string. Consecuencias a recordar:
- Backend: `productos.py`, `exportar.py` y los 14 endpoints de `filtros.py` usan
  `p.marca IN (?,?,...)` (no `= ?`). El param es `Optional[List[str]] = Query(None)`.
  Retrocompatible: `?marca=X` (un valor) llega como `['X']`.
- Frontend: axios lleva un `paramsSerializer` (en `services/api.js`) que serializa arrays
  como `marca=X&marca=Y` (repeat), que es lo que FastAPI espera para `List[str]`.
- `[]` es truthy en JS: en TODO punto que itere `filtros` (`cargarProductos`,
  `buildExportParams`, `hayFiltrosActivos` en App.jsx; `tieneAlgunFiltro` en
  FiltrosCascada) hay que tratar el array vacío como "sin filtro" (`Array.isArray(v) ? v.length > 0 : ...`).
- Departamento sigue siendo **single-select** (string). Solo Marca es multi.

## Productos Intercambiables

### Concepto
Productos que comparten al menos un SKU (principal o alterno) son considerados intercambiables. Ejemplo: una bujía ACDELCO y una NGK con el mismo número de parte original.

### Algoritmo (calcular_intercambiables.py)
1. Construye índice invertido: `{sku_normalizado -> set(producto_ids)}`
2. Para cada SKU compartido por 2+ productos, crea relaciones bidireccionales
3. Almacena en tabla `productos_intercambiables`

### Estadísticas (Febrero 2026)
- **7,336 productos** tienen al menos 1 intercambiable
- **135,174 relaciones** bidireccionales
- **18.4 promedio** de intercambiables por producto
- **14,942 productos** con skus_alternos extraídos (67.4%)

### UI
En el modal de detalle, sección "Productos Intercambiables":
- Lista con marca (badge negro) + **SKU del producto** (no el nombre)
- Indicador de stock (verde/gris)
- Click navega al producto intercambiable

## Grupos de Producto

### Concepto
Categorización adicional independiente del departamento. Ejemplos: AMORTIGUADORES, BALATAS DELANTERAS Y TRASERAS, BOMBA ACEITE, EMPAQUES, etc.

### Datos
- **248 grupos únicos**
- **22,178 productos** con grupo asignado (100%)
- Fuente: `data/grupos_producto.csv`

### Cascading
El filtro de grupo aparece en la sección "Compatibilidad Vehicular" y se filtra según:
- Departamento seleccionado
- Marca del producto
- Filtros vehiculares (marca, modelo, año, motor)

## Top de Más Vendidos

### Concepto
Ranking mensual de los productos más vendidos (análisis 80-20 que exporta el cliente).
Alimenta la **vitrina "Los más vendidos"** en la portada del frontend (estilo Amazon/MercadoLibre).

### Datos
- Columna `productos.ranking_ventas INTEGER` (NULL = no está en el top). ALTER idempotente en `database.py`.
- Fuente: `data/top-mas-vendidos.xlsx` — 3 columnas: `Top` (rank), `SKU`, `Descripcion`.
- El SKU del archivo hace match **directo** con `productos.sku` (la Clave interna), NO con `sku_real`.
  ~97% de las filas (486/500) hacen match exacto; el resto son mano de obra / servicios /
  paquetes (prefijos `300...`, `1982...`) que no son productos físicos y se omiten.

### Actualización mensual (cuando el cliente manda el nuevo archivo)
```bash
# 1. Colocar el archivo nuevo en data/top-mas-vendidos.xlsx (mismo nombre, mismas 3 columnas)
# 2. Desde /backend:
cd backend
python3 scripts/actualizar_top_vendidos.py   # backup + limpia ranking + repuebla + reporte

# 3. Copiar BD y deploy (igual que actualizar_precios_excel.py):
cp data/catalogo.db ../data/catalogo.db
git add backend/data/catalogo.db data/catalogo.db
git commit -m "Update top más vendidos"
git push
```
El script `actualizar_top_vendidos.py` hace backup, limpia el ranking anterior (reset a NULL),
y repuebla por match de SKU exacto. Genera un reporte con los SKUs sin match.

### Endpoints
```
GET /api/productos/top-vendidos?departamento=&con_inventario=true&limit=20
    # Top ordenado por ranking_ventas ASC (1 = más vendido). Filtrable por categoría.
GET /api/productos/top-vendidos/categorias
    # Departamentos presentes en el top, con conteo (para las pestañas de la vitrina)
GET /api/filtros/departamentos-populares?limit=8
    # Top N departamentos por # de productos con inventario (para la barra de categorías)
```

### UI
- **Vitrina** (`components/TopVendidos.jsx`): carrusel horizontal, pestañas por categoría,
  badges de ranking (🥇🥈🥉 top 3, #N el resto). Solo en la portada (`vistaPortada`).
  - **Exportar Excel/PDF** desde el encabezado de la vitrina: exporta el ranking vía
    `?solo_top_vendidos=true`, respetando la pestaña de categoría activa (departamento)
    y TODO el ranking cargado (no solo los ~30 visibles del carrusel).
- **Barra de categorías** (`components/BarraCategorias.jsx`): "Más vendidos" + departamentos
  populares; al hacer clic filtra el catálogo por departamento.

## Scripts de Utilidad

```bash
# Desde /backend:

# Importar productos desde CSV inicial
python3 scripts/importar_csv.py

# Extraer compatibilidades vehiculares de descripciones
python3 scripts/extraer_compatibilidades.py

# Extraer características específicas (llantas, aceites, acumuladores)
python3 scripts/extraer_caracteristicas.py

# Calcular productos intercambiables (precálculo)
python3 scripts/calcular_intercambiables.py

# Importar grupos de producto desde CSV
python3 scripts/importar_grupos.py

# Reprocesar nombres + compatibilidades (completo)
python3 scripts/reprocesar_completo.py

# Reprocesar skus_alternos (re-extrae con regex mejorado)
python3 scripts/reprocesar_skus_alternos.py

# Actualizar precios (con IVA), inventario e insertar productos nuevos desde Excel
python3 scripts/actualizar_precios_excel.py

# Actualizar el ranking de más vendidos desde data/top-mas-vendidos.xlsx (mensual)
python3 scripts/actualizar_top_vendidos.py

# Validaciones
python3 scripts/validar_100_porciento.py
python3 scripts/validar_nombres.py
```

## Actualización de Datos desde Excel (MÉTODO PRINCIPAL)

### Contexto
Los datos se actualizan desde un archivo Excel (.xlsx) que RELUVSA exporta periódicamente. Los precios en el Excel ya vienen **CON IVA**. ⚠️ El formato ha cambiado con el tiempo — **siempre validar los headers contra las constantes `COL_*` del script** antes de ejecutar:
- Hasta Jul 2026 (corte 13 jul): 22 columnas.
- Desde Jul 2026 (corte 22 jul): **23 columnas** — trae una columna `Descripcion` extra en la posición 1 (duplicado exacto de la col 10) que recorre todo +1.
- Desde Jul 2026 la fuente de precios es **Precio Tres/Cinco C/IVA** (antes era Precio abierto 3/5).

### Formato del Excel (23 columnas, desde Jul 2026)

| Col | Columna | Uso |
|-----|---------|-----|
| 0 | Clave | SKU del producto |
| 1 | Descripcion | (ignorada — duplicado exacto de col 10) |
| 2 | Grupo -> Nombre | grupo_producto (para nuevos) |
| 3 | SKU | sku_real (número de parte comercial; vacío en ~81%) |
| 4 | Codigo de Barras | (ignorado) |
| 5 | Departamento -> Nombre | departamento (para nuevos) |
| 6 | Marcas Prodcuto -> Nombre | marca (para nuevos) |
| 7 | Ultima Venta | (ignorado) |
| 8 | Última Compra | fecha para filtro de nuevos (< 5 años) |
| 9 | Dias sin venta | (ignorado) |
| 10 | Descripcion | descripcion_original (para nuevos) |
| 11 | Precio Tres C/IVA | precio_publico (CON IVA) |
| 12 | Precio Cinco C/IVA | precio_mayoreo (CON IVA) |
| 13 | Precio abierto 3 C/IVA | (ignorado desde Jul 2026) |
| 14 | Precio abierto 5 C/IVA | (ignorado desde Jul 2026) |
| 15 | Variant Scr | imagen_url (para nuevos) |
| 16 | Carrera | inventario Suc. Carrera |
| 17 | Berriozabal | inventario Suc. Berriozabal |
| 18 | CEDIS | inventario CEDIS |
| 19 | 31 Juarez | inventario Suc. 31 Juarez |
| 20 | FULL | inventario FULL |
| 21 | E-commerce | inventario Suc. E-commerce |
| 22 | Total almacenes | inventario_total |

### Proceso de Actualización

#### 1. Colocar el Excel
Colocar el archivo en `data/limpieza-catalogo.xlsx` (sobrescribir el anterior).

#### 2. Ejecutar desde /backend
```bash
cd backend
python3 scripts/actualizar_precios_excel.py
```

#### 3. Copiar BD y hacer deploy
```bash
cp data/catalogo.db ../data/catalogo.db
cd ..
git add backend/data/catalogo.db data/catalogo.db
git commit -m "Update precios e inventario desde Excel"
git push
```

### Qué hace el script `actualizar_precios_excel.py`

#### Productos existentes (UPDATE)
- Actualiza `precio_publico` (col 12) y `precio_mayoreo` (col 13) con precios CON IVA
- Actualiza `inventario_total` (col 21) y tabla `inventario` por sucursal (cols 15-20)
- **Marca / Departamento / Grupo**: si cambian en el Excel respecto a la BD, se actualizan
  (correcciones de marca tipo "GENERICO → ESAEVER" o "RELUVSA → PMC").
- **SKU comercial (`sku_real`, col 2)**: si el Excel lo trae poblado, se escribe en `sku_real`.
  Nunca se borra un `sku_real` existente con un valor vacío del Excel.
  (Para poblar productos ya existentes de una sola vez: `python3 scripts/backfill_sku_real.py`.)
- Productos en BD que NO están en el Excel → inventario se pone en 0
- **Descripción cambiada (modo MERGE)**: si la columna Descripcion del Excel difiere de
  `descripcion_original` en BD, el script:
  - Actualiza `descripcion_original` con la nueva versión
  - Re-extrae nombre limpio, SKUs alternos, compatibilidades, características e intercambios
  - **Solo AGREGA lo nuevo** (no borra los datos existentes para preservar info validada)
  - Recalcula intercambios solo para los productos afectados

#### Productos nuevos (INSERT + procesamiento automático)
Productos del Excel que NO existen en BD se insertan si cumplen **ambas** condiciones:
1. **Inventario > 0** (col 21: Total Almacenes)
2. **Última compra < 5 años** (col 7: Última Compra)

Para los productos nuevos insertados, el script ejecuta **inline** (misma conexión BD):
- Extracción de nombre limpio (`nombre_producto`) usando el parser de la marca
- Extracción de compatibilidades vehiculares
- Extracción de SKUs alternos y tipo de producto
- Extracción de características específicas (llantas, aceites, acumuladores)
- Cálculo de productos intercambiables
- Los productos nuevos aparecen con badge "NUEVO" por 60 días

Productos nuevos que NO cumplen las condiciones se ignoran (sin inventario o compra muy vieja).

#### Otras operaciones
- Crea backup automático antes de actualizar
- Genera reporte detallado con estadísticas de actualización y productos nuevos

### Nota técnica importante
Todo el procesamiento de productos nuevos (nombres, compatibilidades, intercambiables, características) se hace **inline con el mismo cursor/conexión** sobre `backend/data/catalogo.db`. NO se usa `procesar_productos_nuevos.py` ni `get_db()` desde este script, ya que `get_db()` apunta a `data/catalogo.db` (raíz) y causaría que los cambios se escriban en la BD equivocada.

### Precios en el Frontend
- Los precios se muestran **CON IVA** (tal como vienen del Excel)
- Leyenda "Precios incluyen IVA" visible en modal de detalle
- Productos con precio $0 muestran "Consultar precio" en vez de $0.00

### Notas Importantes sobre SKUs
- Los SKUs se normalizan quitando ceros iniciales en numéricos para hacer match
- Ejemplo: `013030102` en Excel → `13030102` en BD
- El Excel puede traer productos nuevos que se insertarán si cumplen las condiciones

## Actualización Incremental desde CSV (método alternativo)

### Proceso
Para CSVs de inventario (formato diferente, 16 columnas), usar:

```bash
cd backend
python3 scripts/actualizar_inventario.py ../data/nuevo_inventario.csv
```

**NOTA**: Este método importa precios **SIN IVA** (del CSV). Si se usa, después ejecutar `actualizar_precios_excel.py` para corregir precios con IVA.

### Comportamiento

| Caso | Acción |
|------|--------|
| SKU existe en DB y CSV | UPDATE precios, inventario, grupo |
| SKU solo en CSV (nuevo) | INSERT con `created_at = NOW()` + procesamiento automático |
| SKU solo en DB (no en CSV) | `inventario_total = 0` |

- Los productos nuevos se procesan automáticamente (nombres, compatibilidades, intercambiables)
- Los productos nuevos aparecen con badge "NUEVO" por 60 días
- No se borran productos existentes, solo se pone inventario en 0

### Badge "Nuevo" en Frontend

- Productos con `created_at` en los últimos **60 días** muestran badge "NUEVO"
- Checkbox "Solo productos nuevos" filtra estos productos
- El badge es una etiqueta en la **esquina superior izquierda** con degradado rosa/coral
- Posición: `left-0 top-0 rounded-br-lg` (no tapa la marca del producto)

## Parsers de Marcas

### Estructura Base (backend/parsers/base.py)

```python
class ParserBase:
    PATRONES_MOTOR = [
        r'(\d+\.\d+)\s*L',           # 2.0L, 5.3L
        r'(\d+\.\d+)\s*LTS?',        # 2.0 LTS
        r'V(\d+)',                    # V6, V8
        r'L(\d+)',                    # L4, L6
    ]

    PATRONES_AÑOS = [
        r'(\d{4})\s*[-/]\s*(\d{4})', # 2015-2020
        r'(\d{4})\s*[-/]\s*(\d{2})', # 2015-20
        r'(\d{4})\+',                 # 2015+
    ]
```

### Detección de Modelo Más Cercano al Año

El método `_extraer_modelo_marca()` busca el modelo **más cercano al año** en la descripción, no el primero. Esto es crítico para descripciones con múltiples vehículos:

```
"EQUINOX 3.4L 05/09 MALIBU 3.5L 04/06 VENTURE 3.4L 97/05"
                                      ^^^^^^^ Detecta VENTURE (más cercano a 97/05)
```

Usa `rfind()` para encontrar la posición más a la derecha del modelo, garantizando que se asocie correctamente con su año.

### Limpieza de Nombres: medidas en pulgadas vs rangos de años (fix Julio 2026)

El pipeline `limpiar_nombre_producto()` (en `base.py`) recorta info vehicular del nombre,
incluyendo rangos de años tipo `07/20`. El regex de años lleva un **lookahead negativo
para comillas de pulgada**:

```python
# base.py (_strip_vehicle_info) — NO tocar el lookahead
match_year = re.search(r'\s+\d{2,4}[/-]\d{2,4}(?!\s*[\'"″])', nombre)
```

Sin ese lookahead, medidas dobles como `19/21''` (limpiaparabrisas) se confundían con
rangos de años y el nombre quedaba truncado a solo "LIMPIAPARABRISAS" (48 productos
RELUVSA, dept ACCESORIO, corregidos en Julio 2026). Las medidas sencillas (`16''`) nunca
tuvieron problema. Ojo: el dept **ACCESORIO** SÍ pasa por `_strip_vehicle_info` (no está
en la lista `es_sin_compat`), aunque la marca use `ParserSinCompatibilidad`.

### Limpieza de nombres de llantas: medida al final (fix Julio 2026)

`_limpiar_nombre_llanta()` (en `base.py`) coloca la **medida siempre al final** del
nombre y preserva el modelo aunque venga antes de la palabra LLANTA (caso TORNEL:
"REAL JK", "T2400"). Ejemplo: `195/65 R15 89V REAL JK TORNEL LLANTA` →
`REAL JK TORNEL LLANTA 195/65 R15`. Formatos de medida soportados:

| Formato | Ejemplo entrada | Medida extraída |
|---------|----------------|-----------------|
| Radial | `205/60 R13`, `225/55 ZR17`, `195/70 R15C` | igual, normalizada |
| LT | `31X10.5 R15` | `31X10.5 R15` |
| Camión radial | `11R 22.5` | `11R 22.5` |
| Métrica comercial | `195 R15C 106/104R 8PR` | `195 R15C 8PR` |
| Agrícola/industrial | `14.9 38`, `11L 15`, `19.5 L24` | `14.9-38`, `11L-15`, `19.5L-24` |
| Convencional camión | `750 16 8C`, `1000 20 14C` | `750-16 8C`, `1000-20 14C` |

Notas importantes:
- La ruta de llanta se activa por departamento LLANTAS **o por marca**: los parsers de
  marcas de llantas heredan de `ParserLlanta` (`ES_LLANTA = True`, en
  `sin_compatibilidad.py`). Esto cubre llantas mal clasificadas en otro dept
  (ej. 2 NEREUS en AFINACION).
- ⚠️ **HANKOOK NO hereda de ParserLlanta**: en este catálogo los productos HANKOOK son
  acumuladores (dept SISTEMA ELECTRICO), no llantas.
- La ruta de llantas NO pasa por el strip de SKUs iniciales (confundía medidas y modelos
  tipo `T2400` con códigos); recibe la descripción cruda.
- Se eliminan del nombre: índices de carga/velocidad (`91V`, `106/104R`, `109 S`),
  capas (`8C`, `16PR`), cámara (`S/C`, `C/C`) y tokens huérfanos (`TT`, `TL`, `LT`).
- En Julio 2026 se reprocesaron 380 nombres (NEREUS 101, TORNEL 258, MOBIL 21). Los
  MOBIL truncados a solo "MOBIL" eran residuo de un pipeline viejo que confundía la
  presentación (`5L`, `4.73L`) con cilindrada de motor. Otras marcas de llantas
  (HARVEST KING, POWER KING, etc., ~75 productos) NO se reprocesaron: sus nombres
  mejorarán solo si su descripción cambia en un Excel mensual (modo MERGE).

### Marcas con Parser Específico
82 parsers en `backend/parsers/` para marcas como: AC DELCO, GONHER, SYD, INJETECH, MONROE, NGK, BOSCH, etc.

## Comandos de Desarrollo

```bash
# Iniciar backend (desde /backend)
python3 -m uvicorn main:app --reload --port 8000

# Iniciar frontend (desde /frontend)
npm start

# Verificar base de datos
sqlite3 data/catalogo.db ".tables"
sqlite3 data/catalogo.db "SELECT COUNT(*) FROM productos"
sqlite3 data/catalogo.db "SELECT COUNT(*) FROM productos_intercambiables"
```

## Estadísticas del Catálogo (Febrero 2026)

| Métrica | Valor |
|---------|-------|
| Productos totales | 22,344 |
| Compatibilidades vehiculares | 29,554 |
| Características específicas | 2,874 |
| Productos con skus_alternos | ~15,100 |
| Relaciones intercambiables | ~136,152 |
| Grupos de producto únicos | ~248 |
| Productos con grupo | 22,344 (100%) |
| Registros de inventario | 19,976 |
| Productos con precio $0 | 217 |
| Precios | CON IVA incluido |

## Deploy (Railway)

### Flujo
1. Push a GitHub (`main` branch)
2. Railway detecta cambios automáticamente
3. Build + deploy (~2-3 minutos)

### Base de datos
- El archivo `data/catalogo.db` se incluye en el repo
- `database.py` copia la DB al directorio de Railway si no existe o es más pequeña
- Los cambios de schema se aplican con ALTER TABLE idempotente

## Sistema de Autenticación y Usuarios de Proveedores

### Modelo (Julio 2026)
- **Admin (semilla)**: UN usuario definido por env vars en Railway (`ADMIN_USERNAME`/`ADMIN_PASSWORD`).
  NO vive en la BD — garantiza acceso siempre. Es el único con herramientas de administración.
- **Proveedores**: usuarios en la tabla `usuarios` de **`pedidos.db`** (volumen persistente
  de Railway, `PEDIDOS_DB_PATH` — la misma BD de las órdenes de Stripe, ver `pedidos_db.py`).
  Los crea/administra el admin desde el portal (modal "Usuarios de proveedores" en el header).
  Rol `proveedor`: ve todo el catálogo y puede comprar; sin herramientas de admin.
- El rol `visitor` se **eliminó** (login obligatorio, no hay acceso público). Las env vars
  `VISITOR_USERNAME`/`VISITOR_PASSWORD` ya no se usan y pueden borrarse de Railway.
- Contraseñas de proveedores **hasheadas con bcrypt**. La asigna el admin al crear/resetear.
- Los tokens de proveedor se **revalidan contra la BD en cada request** (columna `activo`):
  desactivar un proveedor lo saca de inmediato, sin esperar a que expire su JWT (24h).
- ⚠️ Los usuarios NO viven en `catalogo.db`: la actualización mensual del catálogo
  sobrescribe esa BD y los borraría. `pedidos.db` nunca se sobrescribe en deploys.

### Endpoints
```
POST /api/auth/login
    Body: { "username", "password" }
    Response: { "token", "role", "username" }        # role: 'admin' | 'proveedor'

# Gestión de usuarios (solo admin):
GET  /api/auth/usuarios                # lista con conteo de pedidos por proveedor
POST /api/auth/usuarios                # { username, password, nombre_empresa, contacto? }
PUT  /api/auth/usuarios/{username}     # parcial: { password?, nombre_empresa?, contacto?, activo? }
                                       # activo=false = soft delete (conserva historial de pedidos)

# Órdenes:
GET /api/orders?username=&estado=&limit=   # (admin) resumen de todas las órdenes:
                                           # empresa del proveedor + num_renglones/num_piezas.
                                           # NO trae los items (un pedido puede tener cientos).
                                           # Incluye "resumen": {estado: {pedidos, monto}} del filtro.
GET /api/orders/{id}                       # detalle con items (admin ve cualquiera + contacto;
                                           # el proveedor solo las suyas, sin contacto)
GET /api/orders/mis-pedidos                # pedidos del usuario autenticado
```

### Portal de pedidos (admin)
`frontend/src/components/GestionPedidos.jsx` — modal con botón **"Pedidos"** (📋) en el header,
visible solo para admin. Lista los pedidos con proveedor, estado, fecha, # de productos y monto;
al hacer clic en uno se cargan sus renglones **bajo demanda** (`GET /api/orders/{id}`), con tabla
SKU/producto/cantidad/precio/importe y botón **Descargar lista (CSV)** para surtir el pedido.
Filtros por proveedor y estado; tarjetas de resumen (pagados con monto / pendientes).

⚠️ **`estado` es lo que importa**: la orden se crea al *iniciar* el checkout, así que
`pendiente` = armó el pedido pero Stripe **no** confirmó el pago (no surtir). Solo `pagado`
es venta real (`paid_at` poblado por el webhook). Valores: `pendiente|pagado|cancelado|fallido`.

### Referencia Stripe ↔ proveedor
- Cada orden en `pedidos.db` guarda el `username` del comprador (índice `idx_orders_username`).
- La Checkout Session lleva `client_reference_id=order_id` y `metadata={order_id, username, empresa}`.
- Cada proveedor tiene un **Stripe Customer** propio (`usuarios.stripe_customer_id`), creado
  perezosamente en su primer checkout — en el dashboard de Stripe todos los pagos de un
  proveedor quedan agrupados bajo su cliente. El admin paga sin Customer (no está en BD).
- UI: `frontend/src/components/GestionUsuarios.jsx` (modal, botón 👥 en header solo admin).

## Proxy de Imágenes

### Problema Resuelto
El frontend en HTTPS (Railway/Vercel) no puede cargar imágenes del servidor interno HTTP de RELUVSA debido a **Mixed Content blocking** del navegador.

### Solución
Endpoint proxy en el backend que:
1. Recibe petición HTTPS del frontend
2. Hace fetch HTTP interno al servidor de imágenes
3. Retorna la imagen con headers HTTPS

### Endpoint
```
GET /api/images/{sku}
```

### Implementación (`backend/routers/images.py`)
- Usa `httpx` para peticiones async
- Cache-Control: 24 horas (86400 segundos)
- Timeout: 10 segundos
- Maneja errores con 404/502

### Frontend
Componente `ProductImage` con:
- Estado de carga (skeleton)
- Fallback a icono si no hay imagen
- Helper: `getImageUrl(sku)` construye URL del proxy

### Disponibilidad de Imágenes
- ~19% de productos tienen imagen en el servidor RELUVSA
- ~81% no tienen imagen (limitación del servidor interno, no del código)

## Agentes Expertos Disponibles

### /experto-catalogo
Conoce toda la arquitectura: parsers, extractores, filtros, API.

### /experto-autopartes
Valida datos automotrices: motores, años, compatibilidades coherentes.

### /experto-debug-db
Diagnostica problemas de BD, logs de backend, errores de consola.

### /experto-ecommerce
Evalúa UX comparando con Amazon/MercadoLibre, sugiere mejoras.

## Notas Importantes

### Modal de Detalle
El modal de detalle de producto está construido **inline en App.jsx** (líneas ~328-523), NO usa el componente `DetalleProducto.jsx`. Cualquier cambio al modal debe hacerse en `App.jsx`.

### Departamentos sin compatibilidad vehicular
LLANTAS, LUBRICACIÓN, QUIMICOS/ADITIVOS no tienen compatibilidad vehicular. Usan filtros de características específicas.

### Filtros de acumuladores
Se activan por MARCA (CHECKER, EXTREMA, CAMEL), no por departamento.

## Próximos Pasos Sugeridos

1. ~~**Imágenes**: Implementar carga/display de imágenes de productos~~ ✅ Implementado (proxy HTTPS)
2. **Carrito**: Agregar funcionalidad de cotización/carrito
3. ~~**Exportación**: PDF/Excel de búsquedas~~ ✅ Implementado (Excel + PDF con imágenes embebidas)
4. ~~**Usuarios**: Sistema de login para empleados~~ ✅ Implementado (JWT básico)
5. **Analytics**: Tracking de búsquedas más comunes
6. **Búsqueda avanzada**: Autocompletado, sugerencias
7. **Mejora de imágenes**: Solicitar a RELUVSA actualizar imágenes faltantes (~81%)
8. **Tags de producto**: Categorización adicional por tags (pendiente recibir Excel del cliente)
