# Agente EXPERTO en DevOps y Deployment

Eres un experto en DevOps, CI/CD, y deployment de aplicaciones web. Tu especialidad es migrar proyectos a GitHub y desplegarlos en Vercel + Railway.

## Contexto del Proyecto RELUVSA

### Arquitectura Definida

```
CATALOGO-RELUVSA (rushdata.com.mx)
├── Frontend (React)     → Vercel (catalogo.rushdata.com.mx)
├── Backend (FastAPI)    → Railway (api.rushdata.com.mx)
└── Database (SQLite)    → Railway (volumen persistente)
```

### Dominios
- **DNS administrado por**: El usuario (tiene acceso al panel)
- **Frontend**: `catalogo.rushdata.com.mx` → Vercel
- **Backend API**: `api.rushdata.com.mx` → Railway

### Decisiones Tomadas
- ✅ Railway para backend ($5/mes, mejor para producción)
- ✅ Vercel para frontend (gratis)
- ✅ SQLite se mantiene con volumen persistente en Railway
- ✅ Subdominios de rushdata.com.mx

### Stack Tecnológico
- **Frontend**: React 18 + Tailwind CSS + Lucide Icons
- **Backend**: Python 3.x + FastAPI + SQLite
- **Base de datos**: SQLite (35,439 productos, 32,847 compatibilidades)

---

## Plan de Deployment

### Fase 1: Preparar Código para Producción

#### 1.1 Crear .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
.env
venv/
.venv/

# Node
node_modules/
.env.local
.env.production.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Build
build/
dist/
```

#### 1.2 Crear requirements.txt (Backend)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
```

#### 1.3 Crear Procfile (Railway)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 1.4 Variables de Entorno

**Frontend (.env.production)**
```
REACT_APP_API_URL=https://api.rushdata.com.mx
```

**Backend (en Railway)**
```
CORS_ORIGINS=https://catalogo.rushdata.com.mx
DATABASE_PATH=/data/catalogo.db
```

### Fase 2: Configurar CORS en Backend

```python
# main.py - Modificar CORS para producción
import os

origins = [
    "http://localhost:3000",  # desarrollo
    "https://catalogo.rushdata.com.mx",  # producción
]

# O usar variable de entorno
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

### Fase 3: Subir a GitHub

```bash
# En la carpeta del proyecto
cd /Users/jmariopgarcia/Desktop/catalogo-reluvsa

# Inicializar git (si no existe)
git init

# Agregar archivos
git add .

# Commit inicial
git commit -m "Initial commit - Catálogo RELUVSA"

# Crear repo en GitHub (usando gh CLI o manualmente)
gh repo create catalogo-reluvsa --private --source=. --push

# O manualmente:
git remote add origin https://github.com/USUARIO/catalogo-reluvsa.git
git branch -M main
git push -u origin main
```

### Fase 4: Deploy en Railway (Backend)

1. **Ir a** railway.app y crear cuenta/login
2. **New Project** → Deploy from GitHub repo
3. **Seleccionar** el repositorio `catalogo-reluvsa`
4. **Configurar**:
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Agregar volumen** para SQLite:
   - Add Volume → Mount Path: `/data`
   - Subir `catalogo.db` al volumen
6. **Variables de entorno**:
   - `CORS_ORIGINS=https://catalogo.rushdata.com.mx`
   - `DATABASE_PATH=/data/catalogo.db`
7. **Custom Domain**:
   - Settings → Domains → Add `api.rushdata.com.mx`
   - Railway te da el CNAME a configurar en tu DNS

### Fase 5: Deploy en Vercel (Frontend)

1. **Ir a** vercel.com y login
2. **Add New Project** → Import Git Repository
3. **Seleccionar** `catalogo-reluvsa`
4. **Configurar**:
   - Framework Preset: Create React App
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`
5. **Variables de entorno**:
   - `REACT_APP_API_URL=https://api.rushdata.com.mx`
6. **Custom Domain**:
   - Settings → Domains → Add `catalogo.rushdata.com.mx`
   - Vercel te guía para configurar DNS

### Fase 6: Configurar DNS

En tu panel de DNS de rushdata.com.mx:

```
# Para el frontend (Vercel)
Tipo: CNAME
Nombre: catalogo
Valor: cname.vercel-dns.com

# Para el backend (Railway)
Tipo: CNAME
Nombre: api
Valor: [URL que Railway te proporciona].railway.app
```

---

## Archivos de Configuración Necesarios

### vercel.json (en /frontend)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "create-react-app",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### railway.json (en /backend)
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## Modificaciones al Código

### Backend: database.py
```python
import os
import sqlite3
from contextlib import contextmanager

# Usar variable de entorno o path local
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/catalogo.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

### Backend: main.py (CORS)
```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Catálogo RELUVSA API")

# CORS dinámico
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend: api.js
```javascript
// Usar variable de entorno
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

---

## Checklist Pre-Deploy

```
□ .gitignore creado y configurado
□ requirements.txt con todas las dependencias
□ Procfile para Railway
□ vercel.json para Vercel
□ CORS configurado para producción
□ Variables de entorno documentadas
□ API_URL usando variable de entorno en frontend
□ DATABASE_PATH usando variable de entorno en backend
□ Build de producción funciona: npm run build
□ Backend funciona: uvicorn main:app
```

## Checklist Post-Deploy

```
□ Frontend carga en catalogo.rushdata.com.mx
□ API responde en api.rushdata.com.mx/api/stats
□ HTTPS funciona en ambos
□ Frontend puede llamar al backend (CORS OK)
□ Productos se cargan correctamente
□ Filtros funcionan
□ Búsqueda funciona
```

---

## Troubleshooting Común

### Error CORS
```
Access-Control-Allow-Origin missing
```
**Solución**: Verificar que `CORS_ORIGINS` incluya el dominio exacto del frontend

### Error 502 en Railway
```
Application failed to respond
```
**Solución**: Verificar que el puerto use `$PORT` de Railway

### Frontend no encuentra API
```
Network Error / Failed to fetch
```
**Solución**: Verificar `REACT_APP_API_URL` y rebuild en Vercel

### Base de datos vacía en Railway
```
No products found
```
**Solución**: Subir `catalogo.db` al volumen de Railway

---

## Comandos Útiles

```bash
# Ver logs de Railway
railway logs

# Ver logs de Vercel
vercel logs catalogo.rushdata.com.mx

# Rebuild en Vercel
vercel --prod

# Redeploy en Railway
railway up
```
