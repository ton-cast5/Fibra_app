# Fibra Manager

Aplicación Flask para gestión de red de fibra óptica (clientes, NAP, potencias, inventario, asistencias y repositorio).

Base de datos: **Supabase PostgreSQL** + Storage.

## Desarrollo local

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# Edita .env con tus credenciales Supabase
venv\Scripts\python.exe app.py
```

Abre http://127.0.0.1:5000

## Despliegue en Vercel

Repositorio: [github.com/ton-cast5/Fibra_app](https://github.com/ton-cast5/Fibra_app)

### 1. Subir código a GitHub

El proyecto usa `vercel.json` + `app.py` con `@vercel/python` (instala `requirements.txt`).

### 2. Conectar Vercel

1. Entra en [vercel.com](https://vercel.com) → **Add New Project**
2. Importa el repo **ton-cast5/Fibra_app**
3. Framework: **Other** (detectará Python)
4. Root Directory: `.` (raíz)

### 3. Variables de entorno (obligatorias)

En Vercel → **Settings → Environment Variables**, agrega las mismas que en `.env.example`:

| Variable | Descripción |
|----------|-------------|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_ANON_KEY` | Clave publishable/anon |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role (repositorio/storage) |
| `SUPABASE_STORAGE_BUCKET` | `documentos` |
| `DB_PASSWORD` | Contraseña PostgreSQL Supabase |
| `DB_USE_POOLER` | `true` |
| `DB_POOLER_HOST` | Host del pooler (Connect en Supabase) |
| `DB_POOLER_PORT` | `6543` |
| `SECRET_KEY` | Clave secreta Flask (aleatoria) |
| `FLASK_ENV` | `production` |

Vercel define automáticamente `VERCEL=1` vía `vercel.json`.

### 4. Deploy

Pulsa **Deploy**. Cada push a `main` redeploya automáticamente.

### Notas

- Usa el **pooler** de Supabase (puerto 6543), no la conexión directa.
- Ejecuta `supabase_schema.sql` en Supabase si aún no creaste las tablas.
- Si el build falla por tamaño (folium/pandas), considera [Render](https://render.com) o Railway como alternativa para Flask.
