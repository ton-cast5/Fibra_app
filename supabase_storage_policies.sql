-- ============================================================
-- Políticas RLS para Supabase Storage — bucket "documentos"
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- Alternativa a usar SUPABASE_SERVICE_ROLE_KEY en el servidor Flask
-- ============================================================

-- Asegúrate de que el bucket exista (Storage → New bucket → documentos)
-- Si el bucket es solo para la app en servidor, preferible: service_role en .env
-- y NO exponer políticas públicas de escritura.

-- Opción A: lectura pública + escritura solo autenticada (anon con JWT de usuario)
-- Opción B (desarrollo): permitir INSERT/SELECT/DELETE al rol anon en este bucket
-- El script siguiente es la opción B simplificada para que funcione la clave publishable.

-- Eliminar políticas previas con el mismo nombre (re-ejecutable)
DROP POLICY IF EXISTS "documentos_select_public" ON storage.objects;
DROP POLICY IF EXISTS "documentos_insert_public" ON storage.objects;
DROP POLICY IF EXISTS "documentos_update_public" ON storage.objects;
DROP POLICY IF EXISTS "documentos_delete_public" ON storage.objects;

CREATE POLICY "documentos_select_public"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'documentos');

CREATE POLICY "documentos_insert_public"
ON storage.objects FOR INSERT
TO public
WITH CHECK (bucket_id = 'documentos');

CREATE POLICY "documentos_update_public"
ON storage.objects FOR UPDATE
TO public
USING (bucket_id = 'documentos')
WITH CHECK (bucket_id = 'documentos');

CREATE POLICY "documentos_delete_public"
ON storage.objects FOR DELETE
TO public
USING (bucket_id = 'documentos');
