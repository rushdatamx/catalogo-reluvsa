# Catálogo RELUVSA - Sistema de Filtros en Cascada

Sistema de catálogo para refaccionaria con filtros tipo Amazon/MercadoLibre.

## Estructura del Proyecto

```
catalogo-reluvsa/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── database.py          # Conexión SQLite
│   ├── models.py            # Modelos Pydantic
│   ├── parsers/             # Parsers por marca
│   ├── routers/             # Endpoints API
│   └── scripts/             # Scripts de importación
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── services/        # Conexión a API
│   │   └── App.jsx          # Aplicación principal
│   └── package.json
└── data/
    ├── catalogo-reluvsa-oficial.csv
    └── catalogo.db
```

## Requisitos

- Python 3.10+
- Node.js 16+
- npm o yarn

## Instalación

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Uso

### 1. Iniciar el Backend (API)

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- http://localhost:8000 (raíz)
- http://localhost:8000/docs (documentación Swagger)

### 2. Iniciar el Frontend

```bash
cd frontend
npm start
```

El frontend estará disponible en http://localhost:3000

## API Endpoints

### Filtros (cascada)
- `GET /api/filtros/departamentos` - Lista departamentos
- `GET /api/filtros/marcas-producto` - Marcas de producto
- `GET /api/filtros/marcas-vehiculo` - Marcas de vehículo
- `GET /api/filtros/modelos-vehiculo?marca_vehiculo=X` - Modelos
- `GET /api/filtros/años?marca_vehiculo=X&modelo_vehiculo=Y` - Años
- `GET /api/filtros/motores?marca_vehiculo=X` - Motores

### Productos
- `GET /api/productos` - Lista con filtros y paginación
- `GET /api/productos/{sku}` - Detalle de producto
- `GET /api/productos/buscar?q=texto` - Búsqueda rápida

### Parámetros de filtrado
- `departamento` - Filtrar por departamento
- `marca` - Marca del producto (ACDELCO, GONHER, etc.)
- `marca_vehiculo` - Marca del vehículo (CHEVROLET, FORD, etc.)
- `modelo_vehiculo` - Modelo del vehículo
- `año` - Año del vehículo
- `motor` - Tipo de motor
- `con_inventario` - Solo productos con stock
- `q` - Búsqueda por texto
- `page` - Página (default: 1)
- `limit` - Productos por página (default: 20)

## Estadísticas del Catálogo

- **35,439** productos
- **20,682** productos con compatibilidades (58.4%)
- **35,089** compatibilidades extraídas
- **15** marcas de vehículo principales
- **22** departamentos

### Top Marcas de Vehículo
1. CHEVROLET - 14,178 compatibilidades
2. FORD - 5,601
3. NISSAN - 4,769
4. DODGE - 3,267
5. VOLKSWAGEN - 2,128

### Top Modelos
1. AVEO - 1,462
2. MALIBU - 944
3. CHEVY - 938
4. SILVERADO - 787
5. SENTRA - 774

## Re-importar datos

Si necesitas re-importar el CSV:

```bash
cd backend/scripts

# Importar CSV a base de datos
python importar_csv.py

# Extraer compatibilidades
python extraer_compatibilidades.py
```

## Notas

- Los productos de **TORNEL** y **NEREUS** son llantas y no tienen compatibilidades de vehículo
- Los productos de **RELUVSA** son aceites/líquidos propios sin compatibilidades
- El parser extrae automáticamente: marca vehículo, modelo, años, motor, cilindros y especificaciones
