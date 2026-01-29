# CLAUDE.md - Catálogo RELUVSA

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
│   │   └── filtros.py      # Endpoints de filtros en cascada
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
│       └── validar_*.py                 # Scripts de validación
├── frontend/               # React SPA
│   ├── src/
│   │   ├── App.jsx         # Componente principal con modal de detalle
│   │   ├── lib/utils.js    # Utilidad cn() para clases condicionales
│   │   ├── components/
│   │   │   ├── FiltrosCascada.jsx    # Filtros condicionales (sidebar)
│   │   │   ├── ListaProductos.jsx    # Grid de productos
│   │   │   └── DetalleProducto.jsx   # (No usado - modal está en App.jsx)
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

- **Backend**: Python 3.x + FastAPI + SQLite
- **Frontend**: React 18 + Tailwind CSS + Lucide Icons
- **Base de datos**: SQLite (archivo local, se copia a Railway en deploy)
- **Parsers**: 82 marcas con extracción específica
- **Deploy**: Railway (backend) + GitHub auto-deploy

## Base de Datos

### Esquema Completo

```sql
-- Productos principales (35,439 registros)
CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
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

-- Compatibilidades vehiculares (59,121 registros)
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

-- Inventario por sucursal (19,528 registros)
CREATE TABLE inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    sucursal TEXT,
    cantidad INTEGER,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- Características específicas (4,299 registros) - Llantas, aceites, acumuladores
CREATE TABLE caracteristicas_producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    categoria TEXT,                    -- 'llanta', 'aceite', 'acumulador'
    clave TEXT,
    valor TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- Productos intercambiables (37,458 relaciones) - Precalculado
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
    ?marca=MONROE
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
```

## Frontend - Estructura de Componentes

### App.jsx (Componente Principal)
- Estado de filtros con 19 campos
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
- Filtros básicos: Departamento, Marca del Producto
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
const esLlantas = filtros.departamento === 'LLANTAS';
const esAceites = filtros.departamento === 'LUBRICACIÓN' || filtros.departamento === 'QUIMICOS/ADITIVOS';
const esAcumuladores = MARCAS_ACUMULADORES.includes(filtros.marca);
const mostrarFiltrosVehiculo = !DEPARTAMENTOS_SIN_COMPATIBILIDAD.includes(filtros.departamento) && !esAcumuladores;
```

## Productos Intercambiables

### Concepto
Productos que comparten al menos un SKU (principal o alterno) son considerados intercambiables. Ejemplo: una bujía ACDELCO y una NGK con el mismo número de parte original.

### Algoritmo (calcular_intercambiables.py)
1. Construye índice invertido: `{sku_normalizado -> set(producto_ids)}`
2. Para cada SKU compartido por 2+ productos, crea relaciones bidireccionales
3. Almacena en tabla `productos_intercambiables`

### Estadísticas
- **10,032 productos** tienen al menos 1 intercambiable
- **37,458 relaciones** bidireccionales
- **3.7 promedio** de intercambiables por producto

### UI
En el modal de detalle, sección "Productos Intercambiables":
- Lista con marca (badge negro) + nombre del producto
- Indicador de stock (verde/gris)
- Click navega al producto intercambiable

## Grupos de Producto

### Concepto
Categorización adicional independiente del departamento. Ejemplos: AMORTIGUADORES, BALATAS DELANTERAS Y TRASERAS, BOMBA ACEITE, EMPAQUES, etc.

### Datos
- **254 grupos únicos**
- **35,249 productos** con grupo asignado (99.5%)
- **190 productos** sin grupo
- Fuente: `data/grupos_producto.csv`

### Cascading
El filtro de grupo aparece en la sección "Compatibilidad Vehicular" y se filtra según:
- Departamento seleccionado
- Marca del producto
- Filtros vehiculares (marca, modelo, año, motor)

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

# Validaciones
python3 scripts/validar_100_porciento.py
python3 scripts/validar_nombres.py
```

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

## Estadísticas del Catálogo (Enero 2026)

| Métrica | Valor |
|---------|-------|
| Productos totales | 35,439 |
| Compatibilidades vehiculares | 59,121 |
| Características específicas | 4,299 |
| Relaciones intercambiables | 37,458 |
| Productos con intercambiables | 10,032 (28.3%) |
| Grupos de producto únicos | 254 |
| Productos con grupo | 35,249 (99.5%) |
| Registros de inventario | 19,528 |

## Deploy (Railway)

### Flujo
1. Push a GitHub (`main` branch)
2. Railway detecta cambios automáticamente
3. Build + deploy (~2-3 minutos)

### Base de datos
- El archivo `data/catalogo.db` se incluye en el repo
- `database.py` copia la DB al directorio de Railway si no existe o es más pequeña
- Los cambios de schema se aplican con ALTER TABLE idempotente

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

1. **Imágenes**: Implementar carga/display de imágenes de productos
2. **Carrito**: Agregar funcionalidad de cotización/carrito
3. **Exportación**: PDF/Excel de búsquedas
4. **Usuarios**: Sistema de login para empleados
5. **Analytics**: Tracking de búsquedas más comunes
6. **Búsqueda avanzada**: Autocompletado, sugerencias
