# Fibra Manager

**Fibra Manager** es una aplicación web para operar y documentar una red de fibra óptica: cajas NAP, empalmes, clientes, mediciones de potencia, inventarios, asistencia de personal y un repositorio de archivos. Está pensada para uso en **escritorio y celular**, con interfaz adaptable y tema claro/oscuro.

**Producción:** [fibra-app-ashen.vercel.app](https://fibra-app-ashen.vercel.app)  
**Repositorio:** [github.com/ton-cast5/Fibra_app](https://github.com/ton-cast5/Fibra_app)

---

## ¿Qué hace la app?

Centraliza en un solo lugar la información que antes suele estar repartida entre hojas de cálculo, mapas y carpetas locales.

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | Resumen de la red: cajas, clientes, alertas de saturación y accesos rápidos. |
| **Mapa geográfico** | Visualización interactiva de cajas de **distribución** y **empalmes** con filtros por tipo y estado. |
| **Cajas NAP / Empalmes** | Alta, edición y detalle de cada caja: ubicación GPS, modelo, hilo, puertos, descripción y clientes asociados. |
| **Clientes** | Registro por caja, puerto asignado, estado activo/inactivo y vínculo con la NAP correspondiente. |
| **Potencias** | Mediciones de potencia en NAP y modem, cálculo de pérdida, estado de señal y propagación a clientes de la misma caja. |
| **Modelos de cajas** | Catálogo de modelos (distribución o empalme) con imagen de referencia. |
| **Inventarios** | Exportación de inventario completo, clientes, NAP y asistencias en **PDF** y **Excel** corporativo. |
| **Asistencias laborales** | Control de entradas/salidas del personal por día. |
| **Repositorio** | Archivos en la nube (Supabase Storage): subida, búsqueda, etiquetas y descarga. |

---

## Stack tecnológico

- **Backend:** Python 3 + [Flask](https://flask.palletsprojects.com/)
- **Base de datos:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Archivos:** Supabase Storage
- **Frontend:** HTML + [Tailwind CSS](https://tailwindcss.com/) (CDN)
- **Mapas:** [Folium](https://python-visualization.github.io/folium/) / Leaflet
- **Reportes:** pandas + openpyxl (Excel), jsPDF (PDF en navegador)
- **Despliegue:** [Vercel](https://vercel.com/) (serverless Python)

---

## Estructura del proyecto

```
fibra_app/
├── app.py                 # Rutas, modelos SQLAlchemy y lógica principal
├── report_exports.py      # Plantillas Excel corporativas
├── supabase_schema.sql    # Esquema de tablas para Supabase
├── requirements.txt       # Dependencias Python
├── vercel.json            # Configuración de despliegue
├── .vercelignore          # Archivos excluidos del deploy
├── templates/             # Vistas HTML (Jinja2)
└── static/                # CSS, iconos PWA, imágenes
```

---

## Desarrollo local

### Requisitos

- Python 3.11+
- Proyecto en Supabase con PostgreSQL y Storage configurados

### Pasos

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# Edita .env con tus credenciales de Supabase
venv\Scripts\python.exe app.py
```

Abre **http://127.0.0.1:5000**

### Base de datos

Si es la primera vez, ejecuta `supabase_schema.sql` en el **SQL Editor** de Supabase para crear tablas e índices.

### Variables de entorno (`.env`)

| Variable | Descripción |
|----------|-------------|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_ANON_KEY` | Clave pública / anon |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role (subidas al repositorio) |
| `SUPABASE_STORAGE_BUCKET` | Nombre del bucket (ej. `documentos`) |
| `DB_PASSWORD` | Contraseña de PostgreSQL |
| `DB_USE_POOLER` | `true` (recomendado) |
| `DB_POOLER_HOST` | Host del pooler Supabase |
| `DB_POOLER_PORT` | `6543` |
| `SECRET_KEY` | Clave secreta Flask (aleatoria y larga) |

También puedes usar `DATABASE_URL` con la URI completa del pooler en lugar de `DB_PASSWORD`.

---

## Despliegue en Vercel

El proyecto está preparado para desplegarse con `vercel.json` y `app.py` usando el runtime `@vercel/python`.

### 1. Conectar el repositorio

1. Entra en [vercel.com](https://vercel.com) → **Add New Project**
2. Importa **ton-cast5/Fibra_app**
3. Framework: **Other**
4. Root Directory: `.` (raíz del repo)

### 2. Variables de entorno

En **Settings → Environment Variables** (entorno Production), configura las mismas variables del `.env.example`.  
Vercel inyecta `VERCEL=1` automáticamente vía `vercel.json`.

### 3. Deploy

Cada push a la rama `main` genera un nuevo despliegue automático.

### Notas de producción

- Usa el **pooler** de Supabase (puerto **6543**), no la conexión directa IPv6.
- El endpoint `/health` sirve para comprobar que la app arrancó correctamente.
- Si el build supera el límite de tamaño por dependencias pesadas (folium, pandas), alternativas: [Render](https://render.com) o Railway.

---

## Rutas principales

| Ruta | Uso |
|------|-----|
| `/dashboard` | Panel principal |
| `/mapa_nats` | Mapa de cajas |
| `/` o `/cajas` | Listado de NAP / empalmes |
| `/ver_nat/<id>` | Detalle de una caja |
| `/clientes` | Listado de clientes |
| `/potencias` | Mediciones de potencia |
| `/inventarios` | Exportaciones PDF / Excel |
| `/gestion/asistencias` | Control de asistencia |
| `/repositorio` | Gestor de archivos |
| `/nap_models` | Catálogo de modelos |

---

## Licencia y autor

Proyecto privado de gestión de infraestructura de fibra óptica.  
Desarrollado por **ton-cast5**.
