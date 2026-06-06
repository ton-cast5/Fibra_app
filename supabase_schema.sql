-- ============================================================
-- FIBRA MANAGER - Esquema de base de datos (Supabase PostgreSQL)
-- Ejecutar en: Supabase Dashboard → SQL Editor → New query → Run
-- ============================================================

-- Catálogo de modelos de cajas (NAP distribución / empalme)
CREATE TABLE IF NOT EXISTS nap_model (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    tipo_caja VARCHAR(20) NOT NULL DEFAULT 'distribucion',
    capacidad_max INTEGER,
    imagen_url VARCHAR(500),
    CONSTRAINT chk_tipo_caja CHECK (tipo_caja IN ('distribucion', 'empalme'))
);

CREATE INDEX IF NOT EXISTS idx_nap_model_nombre ON nap_model(nombre);
CREATE INDEX IF NOT EXISTS idx_nap_model_tipo ON nap_model(tipo_caja);

-- Cajas instaladas en la red (NAT / NAP / empalme)
CREATE TABLE IF NOT EXISTS nat (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    descripcion TEXT,
    puertos_total INTEGER NOT NULL DEFAULT 8,
    hilo_conexion VARCHAR(50),
    nap_model_id INTEGER REFERENCES nap_model(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_nat_nombre ON nat(nombre);
CREATE INDEX IF NOT EXISTS idx_nat_model ON nat(nap_model_id);

-- Clientes conectados a cajas de distribución
CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    direccion TEXT NOT NULL,
    plan VARCHAR(100),
    contacto VARCHAR(150),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    nat_id INTEGER NOT NULL REFERENCES nat(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cliente_nombre ON cliente(nombre);
CREATE INDEX IF NOT EXISTS idx_cliente_activo ON cliente(activo);
CREATE INDEX IF NOT EXISTS idx_cliente_nat ON cliente(nat_id);

-- Mediciones de potencia óptica
CREATE TABLE IF NOT EXISTS potencias (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    nap_id INTEGER REFERENCES nat(id) ON DELETE SET NULL,
    potencia_entrada DOUBLE PRECISION NOT NULL,
    potencia_salida DOUBLE PRECISION NOT NULL,
    perdida DOUBLE PRECISION,
    estado VARCHAR(20) DEFAULT 'normal',
    observaciones TEXT,
    tecnico VARCHAR(100),
    equipo_medicion VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_potencias_cliente ON potencias(cliente_id);
CREATE INDEX IF NOT EXISTS idx_potencias_nap ON potencias(nap_id);

-- Repositorio de archivos (metadatos; binarios en Supabase Storage bucket "documentos")
-- url_storage = URL pública: .../storage/v1/object/public/documentos/{ruta}
-- RLS Storage: ver supabase_storage_policies.sql o SUPABASE_SERVICE_ROLE_KEY en .env
CREATE TABLE IF NOT EXISTS archivos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    extension VARCHAR(50) NOT NULL,
    tamano INTEGER NOT NULL,
    fecha_subida TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    categoria VARCHAR(100) DEFAULT 'otros',
    etiquetas TEXT,
    descripcion TEXT,
    contenido TEXT,
    url_storage VARCHAR(500),
    fecha_actualizacion TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_archivos_nombre ON archivos(nombre);
CREATE INDEX IF NOT EXISTS idx_archivos_categoria ON archivos(categoria);

-- Asistencia laboral (entrada / salida de personal)
-- Si existía la tabla antigua "asistencia" de visitas técnicas, elimínala manualmente:
-- DROP TABLE IF EXISTS asistencia;

CREATE TABLE IF NOT EXISTS trabajador (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    apellido_paterno VARCHAR(80),
    apellido_materno VARCHAR(80),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    nfc_uid VARCHAR(64) UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_trabajador_activo ON trabajador(activo);

CREATE TABLE IF NOT EXISTS registro_asistencia (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    tipo VARCHAR(10) NOT NULL,
    fecha_hora TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT chk_registro_tipo CHECK (tipo IN ('entrada', 'salida'))
);

CREATE INDEX IF NOT EXISTS idx_registro_trabajador ON registro_asistencia(trabajador_id);
CREATE INDEX IF NOT EXISTS idx_registro_fecha ON registro_asistencia(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_registro_tipo ON registro_asistencia(tipo);

INSERT INTO trabajador (nombre_completo, apellido_paterno, apellido_materno)
SELECT v.nombre, NULL, NULL
FROM (VALUES
    ('Julio Morales'),
    ('Angel David Vicente Carrillo'),
    ('Marcos'),
    ('Tony'),
    ('Juan')
) AS v(nombre)
WHERE NOT EXISTS (SELECT 1 FROM trabajador LIMIT 1);

-- Datos de ejemplo opcionales (descomenta si quieres probar la app)
/*
INSERT INTO nap_model (nombre, tipo_caja, capacidad_max) VALUES
  ('NAP 8 puertos', 'distribucion', 8),
  ('Caja empalme estándar', 'empalme', NULL);
*/
