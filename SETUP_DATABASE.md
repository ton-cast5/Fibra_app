# Base de datos Supabase

## 1. Crear tablas

Supabase → **SQL Editor** → ejecuta todo `supabase_schema.sql`.

## 2. `.env` (proyecto ckzkznyaajmqwrjdlcld)

```env
SUPABASE_URL=https://ckzkznyaajmqwrjdlcld.supabase.co
SUPABASE_ANON_KEY=sb_publishable_...
# Obligatorio para el Repositorio (subir/descargar archivos sin error RLS):
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # Settings → API → service_role (secret)
SUPABASE_STORAGE_BUCKET=documentos
DB_PASSWORD=tu_contraseña
DB_USE_POOLER=true
DB_POOLER_HOST=aws-1-us-west-2.pooler.supabase.com
DB_POOLER_PORT=6543
```

**Repositorio / Storage:** la clave `publishable` (anon) no puede subir archivos si RLS está activo. Usa `SUPABASE_SERVICE_ROLE_KEY` solo en el servidor (nunca en el navegador).

Si no quieres usar service role, ejecuta también `supabase_storage_policies.sql` en el SQL Editor (menos restrictivo).

En Windows no uses `db.xxx.supabase.co` (error DNS/IPv6). El host del pooler sale en Supabase → **Connect**.

## 3. Comandos

```powershell
venv\Scripts\python.exe scripts\test_connection.py
venv\Scripts\python.exe scripts\init_database.py
venv\Scripts\python.exe app.py
```
