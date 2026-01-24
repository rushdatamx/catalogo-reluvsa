# CLAUDE.md - Catálogo RELUVSA

## Descripción del Proyecto

Sistema de catálogo de autopartes para RELUVSA con filtros en cascada estilo Amazon/MercadoLibre. Permite buscar productos por vehículo, marca, departamento y características específicas (llantas, aceites, acumuladores).

## Arquitectura

```
catalogo-reluvsa/
├── backend/                 # API FastAPI + Python
│   ├── main.py             # Punto de entrada, CORS, routers
│   ├── database.py         # Conexión SQLite con context manager
│   ├── models.py           # Modelos Pydantic
│   ├── routers/
│   │   ├── productos.py    # GET /api/productos, /buscar, /{sku}
│   │   └── filtros.py      # Endpoints de filtros en cascada
│   └── parsers/            # 82 parsers de marcas
│       ├── __init__.py     # Mapeo marca → parser
│       ├── base.py         # Clase base con patrones comunes
│       ├── extractores_caracteristicas.py  # Llantas, aceites, acumuladores
│       └── [marca].py      # Parser específico por marca
├── frontend/               # React SPA
│   ├── src/
│   │   ├── App.jsx         # Componente principal
│   │   ├── components/
│   │   │   ├── FiltrosCascada.jsx    # Filtros condicionales
│   │   │   ├── ListaProductos.jsx    # Grid de productos
│   │   │   └── DetalleProducto.jsx   # Modal de detalle
│   │   └── styles.css      # Estilos CSS
│   └── package.json
├── data/
│   └── catalogo.db         # Base de datos SQLite
└── .claude/
    └── commands/           # Agentes expertos
        ├── experto-catalogo.md
        ├── experto-autopartes.md
        ├── experto-debug-db.md
        └── experto-ecommerce.md
```

## Stack Tecnológico

- **Backend**: Python 3.x + FastAPI + SQLite
- **Frontend**: React 18 + CSS puro
- **Base de datos**: SQLite (archivo local)
- **Parsers**: 82 marcas con extracción específica

## Base de Datos

### Esquema

```sql
-- Productos principales (19,303 registros)
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE,
    departamento TEXT,
    marca TEXT,
    descripcion_original TEXT,
    nombre_producto TEXT,
    tipo_producto TEXT,
    skus_alternos TEXT,           -- JSON array
    precio_publico REAL,
    precio_mayoreo REAL,
    imagen_url TEXT,
    inventario_total INTEGER
);

-- Compatibilidades vehiculares (32,847 registros)
CREATE TABLE compatibilidades (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER,
    marca_vehiculo TEXT,
    modelo_vehiculo TEXT,
    año_inicio INTEGER,
    año_fin INTEGER,
    motor TEXT,                   -- Formato: X.XL, V6, V8, etc.
    cilindros TEXT,
    especificacion TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Inventario por sucursal
CREATE TABLE inventario (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER,
    sucursal TEXT,
    cantidad INTEGER,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Características específicas (4,299 registros)
CREATE TABLE caracteristicas_producto (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER,
    categoria TEXT,               -- 'llanta', 'aceite', 'acumulador'
    clave TEXT,
    valor TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
```

### Índices Importantes

```sql
CREATE INDEX idx_productos_departamento ON productos(departamento);
CREATE INDEX idx_productos_marca ON productos(marca);
CREATE INDEX idx_compat_producto ON compatibilidades(producto_id);
CREATE INDEX idx_compat_marca ON compatibilidades(marca_vehiculo);
CREATE INDEX idx_compat_modelo ON compatibilidades(modelo_vehiculo);
CREATE INDEX idx_carac_producto ON caracteristicas_producto(producto_id);
CREATE INDEX idx_carac_categoria ON caracteristicas_producto(categoria);
```

## API Endpoints

### Productos

```
GET /api/productos
    ?departamento=SUSPENSION
    ?marca=MONROE
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

    # Filtros específicos aceites
    ?viscosidad=5W30
    ?tipo_aceite=SINTETICO

    # Filtros específicos acumuladores
    ?grupo_bci=34
    ?capacidad_cca=550

GET /api/productos/buscar?q=termino&limit=20
GET /api/productos/{sku}
```

### Filtros (en cascada)

```
GET /api/filtros/departamentos
GET /api/filtros/marcas-producto?departamento=X
GET /api/filtros/tipos-producto?departamento=X&marca=Y
GET /api/filtros/marcas-vehiculo?departamento=X
GET /api/filtros/modelos-vehiculo?marca_vehiculo=X
GET /api/filtros/años?marca_vehiculo=X&modelo_vehiculo=Y
GET /api/filtros/motores?marca_vehiculo=X&modelo_vehiculo=Y&año=Z

# Filtros llantas
GET /api/filtros/llantas/anchos
GET /api/filtros/llantas/relaciones?ancho=205
GET /api/filtros/llantas/diametros?ancho=205&relacion=55
GET /api/filtros/llantas/tipos
GET /api/filtros/llantas/capas

# Filtros aceites
GET /api/filtros/aceites/viscosidades
GET /api/filtros/aceites/tipos
GET /api/filtros/aceites/presentaciones

# Filtros acumuladores
GET /api/filtros/acumuladores/grupos
GET /api/filtros/acumuladores/capacidades
GET /api/filtros/acumuladores/tamanos
```

## Lógica de Filtros Condicionales

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

## Parsers de Marcas

### Estructura Base

```python
# backend/parsers/base.py
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

### Marcas con Parser Específico (82)

```python
# backend/parsers/__init__.py
PARSERS = {
    'AC DELCO': ParserAcDelco,
    'GONHER': ParserGonher,
    'SYD': ParserSyd,
    'INJETECH': ParserInjetech,
    # ... 78 más
}
```

## Búsqueda Flexible

La búsqueda está optimizada para encontrar productos por CUALQUIER campo:

```python
# Campos donde busca (10 total)
WHERE p.descripcion_original LIKE ?
   OR p.sku LIKE ?
   OR p.nombre_producto LIKE ?
   OR p.skus_alternos LIKE ?
   OR p.marca LIKE ?
   OR p.departamento LIKE ?
   OR p.tipo_producto LIKE ?
   OR p.id IN (
       SELECT producto_id FROM compatibilidades
       WHERE marca_vehiculo LIKE ?
          OR modelo_vehiculo LIKE ?
          OR motor LIKE ?
   )
```

## Validación de Datos

### Motores Válidos

```python
# Patrones válidos
PATRON_MOTOR = r'^(\d+\.\d+L|V\d+|L\d+|I\d+)$'

# Cilindradas americanas válidas
CILINDRADAS_VALIDAS = {
    '289', '302', '305', '327', '350', '351', '360', '390',
    '400', '427', '428', '429', '440', '454', '455', '460', '472', '500'
}
```

### Años Válidos

```python
# Rango válido: 1950 - 2025
# año_fin >= año_inicio
# Diferencia máxima: 50 años
```

## Comandos de Desarrollo

```bash
# Iniciar backend
cd backend
python3 -m uvicorn main:app --reload --port 8000

# Iniciar frontend
cd frontend
npm start

# Ejecutar parsers (reimportar datos)
cd backend
python3 importar_csv.py

# Verificar base de datos
sqlite3 data/catalogo.db ".tables"
sqlite3 data/catalogo.db "SELECT COUNT(*) FROM productos"
```

## Estadísticas del Catálogo

- **Productos totales**: 19,303
- **Compatibilidades**: 32,847 (54.5% de productos con compatibilidad)
- **Características específicas**: 4,299
- **Marcas de productos**: 236
- **Marcas de vehículos**: ~50
- **Motores válidos**: 83 valores únicos

## Agentes Expertos Disponibles

### /experto-catalogo
Conoce toda la arquitectura: parsers, extractores, filtros, API.

### /experto-autopartes
Valida datos automotrices: motores, años, compatibilidades coherentes.

### /experto-debug-db
Diagnostica problemas de BD, logs de backend, errores de consola.

### /experto-ecommerce
Evalúa UX comparando con Amazon/MercadoLibre, sugiere mejoras.

## Problemas Conocidos y Soluciones

### Motor con valores inválidos
**Problema**: Parsers extraían valores como "011", "016", "0L"
**Solución**: Validación con regex + limpieza de datos (5,716 registros corregidos)

### Productos sin compatibilidad
**Esperado**: Llantas, aceites, químicos no tienen compatibilidad vehicular
**Solución**: Filtros condicionales que muestran características específicas

## Próximos Pasos Sugeridos

1. **Diseño visual**: Mejorar UI/UX del catálogo
2. **Imágenes**: Implementar carga de imágenes de productos
3. **Carrito**: Agregar funcionalidad de cotización/carrito
4. **Exportación**: PDF/Excel de búsquedas
5. **Usuarios**: Sistema de login para empleados
6. **Analytics**: Tracking de búsquedas más comunes
