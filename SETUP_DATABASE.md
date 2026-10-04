# Configuración

La app corre en Vercel y usa la base PostgreSQL del proyecto Supabase `ckzkznyaajmqwrjdlcld`.
Los cambios de esquema se aplican como migraciones en Supabase (no hay `db.create_all()`).

## Variables de entorno

En Vercel: Project → Settings → Environment Variables. En local: copia `.env.example` a `.env`.

| Variable | Para qué |
| --- | --- |
| `DATABASE_URL` | URI del pooler: Supabase → Connect → Transaction pooler. Alternativa: `DB_PASSWORD` |
| `SECRET_KEY` | Firma las sesiones de login. Si falta, se deriva de la URL de la base. Genera una con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SUPABASE_URL` | `https://ckzkznyaajmqwrjdlcld.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Solo servidor. Necesaria para subir y descargar archivos del Repositorio |

Si cambias `SECRET_KEY`, todas las sesiones abiertas se cierran.

## Seguridad de la base

- Todas las tablas tienen RLS activo y los roles `anon` y `authenticated` no tienen permisos:
  la API pública de Supabase no puede leer ni escribir nada. Solo el servidor Flask entra, con el usuario `postgres`.
- Los buckets de Storage `documentos` y `Cajas` son privados.
- Nunca pongas la clave `service_role` ni la contraseña de la base en el navegador ni en el repositorio.

## Usuarios

Todas las páginas piden login. Los usuarios se administran desde el menú de usuario → **Usuarios y contraseña**.
Tras 5 intentos fallidos, el usuario queda bloqueado 15 minutos.

## Probar la conexión local

```powershell
python scripts\test_connection.py
python app.py
```
