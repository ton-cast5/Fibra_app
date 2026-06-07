# app.py (versión actualizada con repositorio de archivos)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sys
import folium
from werkzeug.utils import secure_filename 
from sqlalchemy import func 
from datetime import datetime, timedelta
import uuid
import math
from folium.plugins import Fullscreen
from flask import jsonify
import pandas as pd
from io import BytesIO
from sqlalchemy import Text, cast, text
from sqlalchemy.pool import NullPool
import json
import mimetypes
import requests
from urllib.parse import quote, unquote
from flask_cors import CORS
from report_exports import exportar_dataframe_corporativo, crear_workbook_corporativo_multihoja

# ----------------------------------------------------------------------
# CONFIGURACIÓN SUPABASE - URL DEL POOLER (IPv4 compatible)
# ----------------------------------------------------------------------

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)  # Habilitar CORS

# =========================================================================
# CONFIGURACIÓN SUPABASE (desde .env)
# =========================================================================
from dotenv import load_dotenv
from urllib.parse import quote_plus

if os.getenv('VERCEL') != '1':
    load_dotenv(override=True)
else:
    load_dotenv(override=False)


def _supabase_project_ref():
    base = os.getenv('SUPABASE_URL', '')
    if 'supabase.co' in base:
        return base.replace('https://', '').replace('http://', '').split('.')[0]
    return 'ckzkznyaajmqwrjdlcld'


def _normalize_pg_url(url):
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


def _resolve_database_url():
    """URL de PostgreSQL. Por defecto usa pooler Supabase (IPv4, compatible con Windows)."""
    placeholders = ('[YOUR-PASSWORD]', 'TU_PASSWORD', '[TU_PASSWORD]')
    project_ref = _supabase_project_ref()

    database_url = (os.getenv('DATABASE_URL') or '').strip()
    if database_url and not any(p in database_url for p in placeholders):
        return _normalize_pg_url(database_url)

    pooler_url = (os.getenv('DATABASE_POOLER_URL') or '').strip()
    if pooler_url and not any(p in pooler_url for p in placeholders):
        return _normalize_pg_url(pooler_url)

    password = os.getenv('DB_PASSWORD', '').strip()
    if not password:
        raise ValueError(
            'Define DATABASE_URL o DB_PASSWORD en las variables de entorno '
            '(Supabase > Settings > Database).'
        )

    use_pooler = os.getenv('DB_USE_POOLER', 'true').lower() in ('1', 'true', 'yes')
    db_name = os.getenv('DB_NAME', 'postgres')

    if use_pooler:
        pooler_host = os.getenv(
            'DB_POOLER_HOST',
            'aws-1-us-west-2.pooler.supabase.com',
        )
        pooler_port = os.getenv('DB_POOLER_PORT', '6543')
        pooler_user = os.getenv('DB_POOLER_USER', f'postgres.{project_ref}')
        return (
            f'postgresql://{pooler_user}:{quote_plus(password)}'
            f'@{pooler_host}:{pooler_port}/{db_name}'
        )

    host = os.getenv('DB_HOST', f'db.{project_ref}.supabase.co')
    port = os.getenv('DB_PORT', '5432')
    user = os.getenv('DB_USER', 'postgres')
    return f'postgresql://{user}:{quote_plus(password)}@{host}:{port}/{db_name}'


_db_config_error = None
try:
    DATABASE_URL = _resolve_database_url()
except ValueError as exc:
    DATABASE_URL = None
    _db_config_error = str(exc)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fibra-manager-dev-key')
app.config['DEBUG'] = os.getenv('FLASK_ENV', 'development') != 'production'
app.config['PROPAGATE_EXCEPTIONS'] = True

_connect_args = {
    'connect_timeout': 10,
    'sslmode': 'require',
    'application_name': 'fibra_manager',
}

# Vercel/serverless: sin pool persistente (NullPool)
if os.getenv('VERCEL') == '1':
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'poolclass': NullPool,
        'connect_args': _connect_args,
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': _connect_args,
    }

# Configuración para el repositorio de archivos (Supabase Storage)
SUPABASE_URL_STORAGE = os.getenv("SUPABASE_URL", "https://ckzkznyaajmqwrjdlcld.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Subidas desde Flask: usar service role (bypass RLS). La clave anon/public falla con RLS activo.
SUPABASE_STORAGE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SECRET_KEY")
)
_allow_anon_storage = os.getenv("SUPABASE_STORAGE_ALLOW_ANON", "").lower() in ("1", "true", "yes")
if _allow_anon_storage and not SUPABASE_STORAGE_KEY:
    SUPABASE_STORAGE_KEY = SUPABASE_ANON_KEY
SUPABASE_KEY = SUPABASE_STORAGE_KEY or SUPABASE_ANON_KEY
SUPABASE_STORAGE_URL = f"{SUPABASE_URL_STORAGE}/storage/v1"
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "documentos")

# Configuración de la carpeta de imágenes
if os.getenv('VERCEL') == '1':
    UPLOAD_FOLDER = os.path.join('/tmp', 'nap_images')
else:
    UPLOAD_FOLDER = os.path.join(basedir, 'static/nap_images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB límite

# Inicializar extensiones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

print("=" * 60)
print("FIBRA MANAGER - Supabase PostgreSQL")
print(f"Proyecto: {SUPABASE_URL_STORAGE}")
if SUPABASE_STORAGE_KEY:
    _storage_key_label = "service_role (OK para subir)"
elif SUPABASE_ANON_KEY:
    _storage_key_label = "solo anon/public (RLS puede bloquear subidas)"
else:
    _storage_key_label = "sin clave"
print("Repositorio Storage:", _storage_key_label)
print(f"Bucket Storage: {STORAGE_BUCKET}")
print("=" * 60)

# ----------------------------------------------------------------------
# MODELOS DE BASE DE DATOS - OPTIMIZADOS PARA POSTGRESQL
# ----------------------------------------------------------------------

# Modelo para el repositorio de archivos
class Archivo(db.Model):
    __tablename__ = 'archivos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    nombre_original = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(50), nullable=False, index=True)
    tamano = db.Column(db.Integer, nullable=False)  # Tamaño en bytes
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    categoria = db.Column(db.String(100), default='otros', index=True)
    etiquetas = db.Column(db.Text)  # Almacenar como JSON string
    descripcion = db.Column(db.Text)
    contenido = db.Column(db.Text, nullable=True)  # Para archivos de texto
    url_storage = db.Column(db.String(500))  # URL de Supabase Storage
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.utcnow)

# Modelo 1: Catálogo de Modelos de NAPs (ACTUALIZADO PARA SOPORTAR DISTRIBUCIÓN Y EMPALME)
class NapModel(db.Model):
    __tablename__ = 'nap_model'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    tipo_caja = db.Column(db.String(20), nullable=False, default='distribucion')  # 'distribucion' o 'empalme'
    capacidad_max = db.Column(db.Integer, nullable=True)  # Nullable para empalme
    imagen_url = db.Column(db.String(500), nullable=True)  # Aumentado para URLs largas
    
    # Relaciones
    nats = db.relationship('Nat', backref='modelo', lazy='dynamic', 
                          cascade='all, delete-orphan')

    def __repr__(self):
        tipo = "Distribución" if self.tipo_caja == "distribucion" else "Empalme"
        return f'<Modelo {self.nombre} ({tipo})>'

# Modelo Nat (cajas NAP / empalme instaladas)
class Nat(db.Model):
    __tablename__ = 'nat'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    puertos_total = db.Column(db.Integer, nullable=False, default=8)
    hilo_conexion = db.Column(db.String(50), nullable=True)
    nap_model_id = db.Column(db.Integer, 
                            db.ForeignKey('nap_model.id', ondelete='SET NULL'), 
                            nullable=True)

    @property
    def tipo_caja(self):
        if self.modelo:
            return self.modelo.tipo_caja
        return 'distribucion'

    @property
    def ubicacion(self):
        if self.latitud is not None and self.longitud is not None:
            return f"{self.latitud},{self.longitud}"
        return None

    @property
    def puertos_usados(self):
        return self.clientes.filter_by(activo=True).count()

    @property
    def porcentaje_uso(self):
            if self.puertos_total == 0:
                return 0

            usados = Cliente.query.filter_by(
                activo=True,
                nat_id=self.id
            ).count()

            return round((usados / self.puertos_total) * 100)

    def __repr__(self):
        return f'<NAT {self.nombre}>'

# Modelo Cliente
class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False, index=True)
    direccion = db.Column(db.Text, nullable=False)
    plan = db.Column(db.String(100), nullable=True)
    contacto = db.Column(db.String(150), nullable=True)
    activo = db.Column(db.Boolean, default=True, index=True)
    nat_id = db.Column(db.Integer, 
                      db.ForeignKey('nat.id', ondelete='CASCADE'), 
                      nullable=False, index=True)
    
    # Relación
    nat = db.relationship('Nat', backref=db.backref('clientes', lazy='dynamic', 
                                                   cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

class Potencia(db.Model):
    __tablename__ = 'potencias'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)  # CORREGIDO
    nap_id = db.Column(db.Integer, db.ForeignKey('nat.id'))  # CORREGIDO
    
    # Valores de potencia (en dBm)
    potencia_entrada = db.Column(db.Float, nullable=False)  # Potencia recibida del cliente
    potencia_salida = db.Column(db.Float, nullable=False)   # Potencia enviada por OLT
    perdida = db.Column(db.Float)  # Calculado automáticamente: salida - entrada
    
    # Estado calculado automáticamente
    estado = db.Column(db.String(20), default='normal')  # excelente, normal, bajo, critico
    
    # Información adicional
    observaciones = db.Column(db.Text)
    tecnico = db.Column(db.String(100))  # Nombre del técnico que midió
    equipo_medicion = db.Column(db.String(50))  # Modelo del equipo usado
    
    # Relaciones CORREGIDAS
    cliente = db.relationship('Cliente', backref=db.backref('potencias', lazy=True))
    nap = db.relationship('Nat', backref=db.backref('potencias', lazy=True))
    
    def calcular_perdida(self):
        """Calcula la pérdida automáticamente"""
        if self.potencia_salida and self.potencia_entrada:
            self.perdida = round(abs(self.potencia_salida - self.potencia_entrada), 2)
            return self.perdida
        return None
    
    def determinar_estado(self):
        """Determina el estado basado en la pérdida"""
        if not self.perdida:
            self.calcular_perdida()

        perdida_abs = abs(self.perdida)

        if perdida_abs <= 1.0:
            self.estado = 'excelente'
        elif perdida_abs <= 2.5:
            self.estado = 'normal'
        elif perdida_abs <= 4.0:
            self.estado = 'bajo'
        else:
            self.estado = 'critico'
        return self.estado

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S') if self.fecha else '',
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre if self.cliente else '',
            'nap_id': self.nap_id,
            'nap_nombre': self.nap.nombre if self.nap else '',
            'potencia_entrada': self.potencia_entrada,
            'potencia_salida': self.potencia_salida,
            'perdida': self.perdida,
            'estado': self.estado,
            'observaciones': self.observaciones,
            'tecnico': self.tecnico,
            'equipo_medicion': self.equipo_medicion
        }


TRABAJADORES_INICIALES = [
    'Julio Morales',
    'Angel David Vicente Carrillo',
    'Marcos',
    'Tony',
    'Juan',
]


class Trabajador(db.Model):
    __tablename__ = 'trabajador'

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    apellido_paterno = db.Column(db.String(80), nullable=True)
    apellido_materno = db.Column(db.String(80), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    nfc_uid = db.Column(db.String(64), nullable=True, unique=True)

    registros = db.relationship(
        'RegistroAsistencia',
        backref='trabajador',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<Trabajador {self.nombre_completo}>'


class RegistroAsistencia(db.Model):
    __tablename__ = 'registro_asistencia'

    TIPOS = {'entrada': 'Entrada', 'salida': 'Salida'}

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(
        db.Integer,
        db.ForeignKey('trabajador.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    tipo = db.Column(db.String(10), nullable=False, index=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    @property
    def tipo_label(self):
        return self.TIPOS.get(self.tipo, self.tipo)

    def __repr__(self):
        return f'<RegistroAsistencia {self.trabajador_id} {self.tipo}>'


# ----------------------------------------------------------------------
# FUNCIONES DE UTILIDAD PARA EL REPOSITORIO
# ----------------------------------------------------------------------

def allowed_repo_file(filename):
    """Permite extensiones para el repositorio."""
    allowed_extensions = {
        'txt', 'csv', 'json', 'xml', 'config', 'conf', 'ini', 'py', 'js', 'html', 'css', 'md',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'kml', 'kmz',
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _storage_rls_help_message():
    return (
        'Storage bloqueado por RLS. En .env agrega SUPABASE_SERVICE_ROLE_KEY '
        f'(Supabase → Settings → API → service_role, solo servidor) '
        f'o ejecuta supabase_storage_policies.sql en el SQL Editor. '
        f'Bucket: {STORAGE_BUCKET}.'
    )


def _storage_auth_headers(content_type=None, upsert=True):
    """Cabeceras requeridas por Supabase Storage REST (apikey + Authorization)."""
    if not SUPABASE_STORAGE_KEY:
        return None
    headers = {
        'Authorization': f'Bearer {SUPABASE_STORAGE_KEY}',
        'apikey': SUPABASE_STORAGE_KEY,
    }
    if content_type:
        headers['Content-Type'] = content_type
    if upsert:
        headers['x-upsert'] = 'true'
    return headers


def build_storage_public_url(object_path, bucket=None):
    """URL pública para descargar desde un bucket público."""
    bucket = bucket or STORAGE_BUCKET
    safe_path = quote(object_path, safe='/')
    return f"{SUPABASE_URL_STORAGE}/storage/v1/object/public/{bucket}/{safe_path}"


def _storage_path_from_url(url_storage):
    """Extrae la ruta del objeto dentro del bucket desde la URL guardada."""
    if not url_storage:
        return None
    for marker in (
        f'/object/public/{STORAGE_BUCKET}/',
        f'/object/authenticated/{STORAGE_BUCKET}/',
        f'/object/{STORAGE_BUCKET}/',
    ):
        if marker in url_storage:
            return unquote(url_storage.split(marker, 1)[1].split('?')[0])
    parts = url_storage.rstrip('/').split('/')
    if len(parts) >= 2 and parts[-2] == STORAGE_BUCKET:
        return parts[-1]
    return None


def upload_to_supabase_storage(file_bytes, object_path, content_type=None):
    """
    Sube bytes al bucket configurado. Devuelve (url_publica, error).
    """
    headers = _storage_auth_headers(content_type=content_type or 'application/octet-stream')
    if not headers:
        return None, _storage_rls_help_message()

    safe_path = quote(object_path, safe='/')
    upload_url = f"{SUPABASE_STORAGE_URL}/object/{STORAGE_BUCKET}/{safe_path}"
    try:
        response = requests.post(
            upload_url,
            headers=headers,
            data=file_bytes,
            timeout=120,
        )
    except requests.RequestException as exc:
        return None, str(exc)

    if response.status_code in (200, 201):
        public_url = build_storage_public_url(object_path)
        print(f"Archivo subido a Supabase Storage ({STORAGE_BUCKET}): {public_url}")
        return public_url, None

    err_body = response.text or ''
    if response.status_code in (400, 401, 403) and 'row-level security' in err_body.lower():
        return None, _storage_rls_help_message()
    return None, f"Storage HTTP {response.status_code}: {err_body}"


def fetch_from_supabase_storage(url_storage, object_path=None):
    """Descarga el archivo desde Storage (público o autenticado)."""
    if url_storage:
        try:
            resp = requests.get(url_storage, stream=True, timeout=60)
            if resp.status_code == 200:
                return resp
        except requests.RequestException:
            pass

    path = object_path or _storage_path_from_url(url_storage)
    if not path or not SUPABASE_STORAGE_KEY:
        return None

    headers = _storage_auth_headers(upsert=False)
    download_url = (
        f"{SUPABASE_STORAGE_URL}/object/authenticated/"
        f"{STORAGE_BUCKET}/{quote(path, safe='/')}"
    )
    try:
        return requests.get(download_url, headers=headers, stream=True, timeout=60)
    except requests.RequestException:
        return None


def delete_from_supabase_storage(url_storage=None, object_path=None):
    """Elimina un objeto del bucket."""
    path = object_path or _storage_path_from_url(url_storage)
    if not path:
        return False
    headers = _storage_auth_headers(upsert=False)
    if not headers:
        return False
    delete_url = (
        f"{SUPABASE_STORAGE_URL}/object/{STORAGE_BUCKET}/{quote(path, safe='/')}"
    )
    try:
        response = requests.delete(delete_url, headers=headers, timeout=30)
        return response.status_code in (200, 204)
    except requests.RequestException as exc:
        print(f"Error eliminando de storage: {exc}")
        return False

def get_etiquetas_from_string(etiquetas_str):
    """Convierte string de etiquetas a lista."""
    try:
        if isinstance(etiquetas_str, str):
            if etiquetas_str.startswith('[') and etiquetas_str.endswith(']'):
                return json.loads(etiquetas_str)
            else:
                return [tag.strip() for tag in etiquetas_str.split(',') if tag.strip()]
        return []
    except:
        return []

# ----------------------------------------------------------------------
# FUNCIONES DE UTILIDAD
# ----------------------------------------------------------------------

def allowed_image_file(filename):
    """Permite solo ciertas extensiones de imagen."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def generar_filename(original_filename):
    """Genera un nombre de archivo seguro y único."""
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def generar_mapa_mejorado():
    """Mapa limpio: solo cajas NAP (distribución) y empalmes."""
    nats = Nat.query.filter(Nat.latitud.isnot(None), Nat.longitud.isnot(None)).all()

    lat_center, lon_center = 19.4326, -99.1332
    zoom_start = 6
    if nats:
        lats = [n.latitud for n in nats]
        lons = [n.longitud for n in nats]
        lat_center = sum(lats) / len(lats)
        lon_center = sum(lons) / len(lons)
        zoom_start = 14 if len(nats) == 1 else 13

    mapa = folium.Map(
        location=[lat_center, lon_center],
        zoom_start=zoom_start,
        tiles='CartoDB positron',
        control_scale=True,
        zoom_control=True
    )
    Fullscreen(position='topleft').add_to(mapa)
    folium.TileLayer('CartoDB positron', name='Claro', show=True).add_to(mapa)
    folium.TileLayer('OpenStreetMap', name='Calles', show=False).add_to(mapa)

    fg_distribucion = folium.FeatureGroup(name='Distribución', show=True)
    fg_empalme = folium.FeatureGroup(name='Empalmes', show=True)
    mapa.add_child(fg_distribucion)
    mapa.add_child(fg_empalme)

    for nat in nats:
        tipo = nat.tipo_caja
        es_empalme = tipo == 'empalme'
        uso = nat.porcentaje_uso if not es_empalme and nat.puertos_total else 0

        if es_empalme:
            estado = 'empalme'
            estado_texto = 'Empalme'
            color_bg = 'linear-gradient(135deg, #6366f1, #4f46e5)'
            emoji = '🔗'
        elif uso >= 100:
            estado = 'saturado'
            estado_texto = 'Saturada'
            color_bg = 'linear-gradient(135deg, #ef4444, #dc2626)'
            emoji = '📡'
        elif uso >= 80:
            estado = 'critico'
            estado_texto = 'Crítica'
            color_bg = 'linear-gradient(135deg, #f59e0b, #d97706)'
            emoji = '📡'
        else:
            estado = 'normal'
            estado_texto = 'Normal'
            color_bg = 'linear-gradient(135deg, #10b981, #059669)'
            emoji = '📡'

        tipo_label = 'Empalme' if es_empalme else 'Distribución'
        puertos_info = (
            f'<p><strong>Puertos:</strong> {nat.puertos_usados}/{nat.puertos_total} ({uso:.0f}%)</p>'
            if not es_empalme and nat.puertos_total
            else ''
        )
        nav_payload = json.dumps({
            'type': 'fibra-nap-nav',
            'id': nat.id,
            'nombre': nat.nombre,
            'lat': nat.latitud,
            'lng': nat.longitud,
        })
        popup_html = f'''
        <div style="min-width: 240px; font-family: system-ui, sans-serif;">
            <div style="background: {color_bg}; color: white; padding: 12px; border-radius: 8px 8px 0 0;">
                <h4 style="margin: 0; font-size: 14px;">{emoji} {nat.nombre}</h4>
                <span style="font-size: 11px; opacity: 0.9;">{tipo_label} · {estado_texto}</span>
            </div>
            <div style="padding: 12px;">
                {puertos_info}
                <p style="margin: 8px 0 0;"><strong>Modelo:</strong> {nat.modelo.nombre if nat.modelo else "—"}</p>
                <button type="button"
                   onclick='window.parent.postMessage({nav_payload}, "*")'
                   style="display: block; width: 100%; margin-top: 10px; background: #0ea5e9; color: white; padding: 8px;
                   border: none; cursor: pointer; text-align: center; border-radius: 6px; font-size: 13px; font-weight: 600;">
                   🧭 Cómo llegar
                </button>
                <a href="{url_for('ver_nat', nat_id=nat.id)}" target="_blank"
                   style="display: block; margin-top: 8px; background: #4f46e5; color: white; padding: 8px;
                   text-align: center; text-decoration: none; border-radius: 6px; font-size: 13px;">
                   Ver detalle
                </a>
            </div>
        </div>
        '''

        icono_html = f'''
        <div class="marker-caja marker-tipo-{tipo} marker-estado-{estado}"
             data-tipo-caja="{tipo}" data-estado="{estado}" data-nombre="{nat.nombre}">
            <div style="background:{color_bg};color:white;border:2px solid white;border-radius:50%;
                width:34px;height:34px;display:flex;align-items:center;justify-content:center;
                font-size:15px;box-shadow:0 2px 8px rgba(0,0,0,0.25);">{emoji}</div>
        </div>
        '''
        icono = folium.DivIcon(html=icono_html, icon_size=(34, 34), icon_anchor=(17, 17))
        grupo = fg_empalme if es_empalme else fg_distribucion
        tooltip = nat.nombre if es_empalme else f'{nat.nombre} ({uso:.0f}%)'

        folium.Marker(
            [nat.latitud, nat.longitud],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip,
            icon=icono
        ).add_to(grupo)

    folium.LayerControl(collapsed=True, position='topright').add_to(mapa)
    mapa.get_root().width = '100%'
    mapa.get_root().height = '100%'
    mapa.get_root().html.add_child(folium.Element(
        '<script>setTimeout(function(){ window.dispatchEvent(new Event("mapaListo")); }, 600);</script>'
    ))
    return mapa._repr_html_()

# ============================================
# RUTAS PARA EL REPOSITORIO DE ARCHIVOS
# ============================================

@app.route('/repositorio')
def repositorio():
    """Página principal del gestor de archivos"""
    return render_template('repositorio.html')

@app.route('/api/archivos', methods=['GET'])
def obtener_archivos():
    """Obtener todos los archivos"""
    try:
        archivos = Archivo.query.order_by(Archivo.fecha_subida.desc()).all()
        
        result = []
        for archivo in archivos:
            archivo_data = {
                'id': archivo.id,
                'nombre': archivo.nombre,
                'nombre_original': archivo.nombre_original,
                'extension': archivo.extension,
                'tamano': archivo.tamano,
                'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
                'categoria': archivo.categoria,
                'etiquetas': get_etiquetas_from_string(archivo.etiquetas),
                'descripcion': archivo.descripcion,
                'contenido': archivo.contenido,
                'url_storage': archivo.url_storage
            }
            result.append(archivo_data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error obteniendo archivos: {e}")
        return jsonify({'error': 'Error al obtener archivos'}), 500

@app.route('/api/archivos/<int:archivo_id>', methods=['GET'])
def obtener_archivo(archivo_id):
    """Obtener un archivo específico"""
    try:
        archivo = Archivo.query.get_or_404(archivo_id)
        
        archivo_data = {
            'id': archivo.id,
            'nombre': archivo.nombre,
            'nombre_original': archivo.nombre_original,
            'extension': archivo.extension,
            'tamano': archivo.tamano,
            'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
            'categoria': archivo.categoria,
            'etiquetas': get_etiquetas_from_string(archivo.etiquetas),
            'descripcion': archivo.descripcion,
            'contenido': archivo.contenido,
            'url_storage': archivo.url_storage
        }
        
        return jsonify(archivo_data)
        
    except Exception as e:
        print(f"Error obteniendo archivo: {e}")
        return jsonify({'error': 'Error al obtener archivo'}), 500

@app.route('/api/archivos/buscar', methods=['POST'])
def buscar_archivos():
    """Buscar archivos por contenido"""
    try:
        data = request.get_json()
        termino = data.get('termino', '').lower()
        
        if not termino:
            return jsonify({'error': 'Término de búsqueda requerido'}), 400
        
        # Buscar en todos los campos usando SQLAlchemy
        archivos = Archivo.query.filter(
            db.or_(
                Archivo.nombre.ilike(f'%{termino}%'),
                Archivo.descripcion.ilike(f'%{termino}%'),
                Archivo.contenido.ilike(f'%{termino}%'),
                cast(Archivo.etiquetas, Text).ilike(f'%{termino}%')
            )
        ).order_by(Archivo.fecha_subida.desc()).all()
        
        result = []
        for archivo in archivos:
            archivo_data = {
                'id': archivo.id,
                'nombre': archivo.nombre,
                'nombre_original': archivo.nombre_original,
                'extension': archivo.extension,
                'tamano': archivo.tamano,
                'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
                'categoria': archivo.categoria,
                'etiquetas': get_etiquetas_from_string(archivo.etiquetas),
                'descripcion': archivo.descripcion,
                'contenido': archivo.contenido,
                'url_storage': archivo.url_storage
            }
            result.append(archivo_data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error buscando archivos: {e}")
        return jsonify({'error': 'Error en la búsqueda'}), 500

@app.route('/api/archivos', methods=['POST'])
def subir_archivo():
    """Subir un nuevo archivo"""
    try:
        # Verificar que haya un archivo
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se recibió ningún archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400
        
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        categoria = request.form.get('categoria', 'otros').strip()
        etiquetas_str = request.form.get('etiquetas', '[]')
        extension_provided = request.form.get('extension', '').strip()
        
        # Procesar etiquetas
        etiquetas = get_etiquetas_from_string(etiquetas_str)
        
        # Si no se proporciona nombre, usar el nombre original
        if not nombre:
            nombre = secure_filename(file.filename)
        
        # Obtener extensión del archivo
        nombre_original = secure_filename(file.filename)
        extension = extension_provided or nombre_original.split('.')[-1].lower() if '.' in nombre_original else 'txt'
        
        file_bytes = file.read()
        tamano = len(file_bytes)

        if not allowed_repo_file(nombre_original):
            return jsonify({
                'success': False,
                'error': f'Extensión no permitida: {extension}',
            }), 400

        # Nombre único en el bucket 'documentos'
        archivo_id = str(uuid.uuid4())
        nombre_almacenamiento = f"{archivo_id}_{nombre_original}"
        content_type = mimetypes.guess_type(nombre_original)[0] or 'application/octet-stream'

        url_storage, storage_error = upload_to_supabase_storage(
            file_bytes, nombre_almacenamiento, content_type
        )
        if storage_error:
            print(f"Error subiendo a Supabase Storage: {storage_error}")
            return jsonify({
                'success': False,
                'error': f'No se pudo guardar en Storage ({STORAGE_BUCKET}): {storage_error}',
            }), 502

        # Guardar en base de datos
        nuevo_archivo = Archivo(
            nombre=nombre,
            nombre_original=nombre_original,
            extension=extension,
            tamano=tamano,
            fecha_subida=datetime.now(),
            categoria=categoria,
            etiquetas=json.dumps(etiquetas),
            descripcion=descripcion,
            url_storage=url_storage
        )
        
        db.session.add(nuevo_archivo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'archivo': {
                'id': nuevo_archivo.id,
                'nombre': nombre,
                'nombre_original': nombre_original,
                'extension': extension,
                'tamano': tamano,
                'categoria': categoria,
                'etiquetas': etiquetas,
                'descripcion': descripcion,
                'url_storage': url_storage,
            }
        })
        
    except Exception as e:
        print(f"Error subiendo archivo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/archivos/<int:archivo_id>', methods=['PUT'])
def actualizar_archivo(archivo_id):
    """Actualizar información de un archivo"""
    try:
        data = request.get_json()
        archivo = Archivo.query.get_or_404(archivo_id)
        
        # Solo permitir actualizar ciertos campos
        if 'nombre' in data:
            archivo.nombre = data['nombre']
        if 'descripcion' in data:
            archivo.descripcion = data['descripcion']
        if 'categoria' in data:
            archivo.categoria = data['categoria']
        if 'etiquetas' in data:
            archivo.etiquetas = json.dumps(data['etiquetas'])
        
        archivo.fecha_actualizacion = datetime.now()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Archivo actualizado'})
        
    except Exception as e:
        print(f"Error actualizando archivo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/archivos/<int:archivo_id>', methods=['DELETE'])
def eliminar_archivo(archivo_id):
    """Eliminar un archivo"""
    try:
        archivo = Archivo.query.get_or_404(archivo_id)
        
        if archivo.url_storage:
            if not delete_from_supabase_storage(url_storage=archivo.url_storage):
                print(f"No se pudo eliminar el objeto en Storage: {archivo.url_storage}")
        
        # Eliminar de la base de datos
        db.session.delete(archivo)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Archivo eliminado'})
        
    except Exception as e:
        print(f"Error eliminando archivo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/archivos/<int:archivo_id>/descargar')
def descargar_archivo(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)

    if not archivo.url_storage:
        return jsonify({'error': 'Archivo sin URL en Storage. Vuelve a subirlo.'}), 404

    response = fetch_from_supabase_storage(archivo.url_storage)
    if not response or response.status_code != 200:
        return jsonify({
            'error': 'No se pudo descargar desde Storage. Verifica que el bucket sea público o la clave de servicio.',
        }), 502

    mimetype = mimetypes.guess_type(archivo.nombre_original)[0] or 'application/octet-stream'
    return send_file(
        BytesIO(response.content),
        as_attachment=True,
        download_name=archivo.nombre_original,
        mimetype=mimetype,
    )

@app.route('/api/archivos/exportar/csv', methods=['GET'])
def exportar_csv():
    """Exportar listado de archivos como CSV"""
    try:
        archivos = Archivo.query.order_by(Archivo.fecha_subida.desc()).all()
        
        # Crear CSV
        csv_lines = ['ID,Nombre,Nombre Original,Extensión,Tamaño,Fecha,Categoría,Etiquetas,Descripción']
        
        for archivo in archivos:
            etiquetas = get_etiquetas_from_string(archivo.etiquetas)
            etiquetas_str = ';'.join(etiquetas) if isinstance(etiquetas, list) else str(etiquetas)
            
            # Escapar comas y comillas
            nombre = str(archivo.nombre).replace('"', '""')
            descripcion = str(archivo.descripcion).replace('"', '""') if archivo.descripcion else ''
            
            fecha_str = archivo.fecha_subida.strftime('%Y-%m-%d %H:%M') if archivo.fecha_subida else ''
            
            line = f'{archivo.id},"{nombre}","{archivo.nombre_original}","{archivo.extension}",{archivo.tamano},{fecha_str},"{archivo.categoria}","{etiquetas_str}","{descripcion}"'
            csv_lines.append(line)
        
        csv_content = '\n'.join(csv_lines)
        
        # Crear respuesta
        output = BytesIO(csv_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name='archivos_repositorio.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"Error exportando CSV: {e}")
        return jsonify({'error': 'Error al exportar CSV'}), 500

# ============================================
# RUTAS EXISTENTES DE TU APLICACIÓN (se mantienen igual)
# ============================================

# (Aquí va el resto de tu código existente, incluyendo todas las rutas que ya tenías)

# Rutas para las APIs de datos
@app.route('/api/clientes')
def api_clientes():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    lista = [{
        'id': c.id,
        'nombre': c.nombre,
        'direccion': c.direccion,
        'plan': c.plan,
        'contacto': c.contacto,
        'activo': c.activo,
        'nat_id': c.nat_id,
        'nap_nombre': c.nat.nombre if c.nat else None,
    } for c in clientes]
    if request.args.get('format') == 'wrapped':
        return jsonify(success=True, clientes=lista, total=len(lista))
    return jsonify(lista)

@app.route('/api/naps')
def api_naps():
    """API para obtener todas las cajas NAP con datos completos"""
    try:
        naps = Nat.query.all()
        result = []
        for nap in naps:
            # Contar clientes activos en este NAP
            clientes_count = Cliente.query.filter_by(nat_id=nap.id, activo=True).count()
            # Calcular porcentaje de uso
            porcentaje_uso = 0
            if nap.puertos_total > 0:
                porcentaje_uso = round((clientes_count / nap.puertos_total) * 100, 1)
            
            result.append({
                'id': nap.id,
                'nombre': nap.nombre,
                'puertos_total': nap.puertos_total,
                'puertos_ocupados': clientes_count,  # Añadir este campo
                'porcentaje_uso': porcentaje_uso,     # Añadir este campo
                'hilo_conexion': nap.hilo_conexion,
                'latitud': nap.latitud,
                'longitud': nap.longitud,
                'nap_model_nombre': nap.modelo.nombre if nap.modelo else None,
                'tipo_caja': nap.tipo_caja,
                'tipo_caja_display': 'Distribución' if nap.tipo_caja == 'distribucion' else 'Empalme',
                'clientes_count': clientes_count
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error en API naps: {e}")
        return jsonify([])

@app.route('/api/modelos-nap')
def api_modelos_nap():
    modelos = NapModel.query.all()
    return jsonify([{
        'id': m.id,
        'nombre': m.nombre,
        'tipo_caja': m.tipo_caja,
        'tipo_caja_display': 'Distribución' if m.tipo_caja == 'distribucion' else 'Empalme',
        'capacidad_max': m.capacidad_max,
        'imagen_url': m.imagen_url
    } for m in modelos])

def _excel_subtitulo_inventario():
    return (
        f'Inventario consolidado | {datetime.now().strftime("%d/%m/%Y %H:%M")} | '
        'Uso interno y confidencial'
    )


def _dataframes_asistencias_export(dias=30):
    """DataFrames corporativos para exportación de asistencia laboral."""
    dias = max(1, min(int(dias), 365))
    seed_trabajadores()
    ref_inicio = _inicio_del_dia(datetime.now() - timedelta(days=dias))
    ref_fin = _fin_del_dia(_inicio_del_dia())

    registros = (
        RegistroAsistencia.query.filter(
            RegistroAsistencia.fecha_hora >= ref_inicio,
            RegistroAsistencia.fecha_hora <= ref_fin,
        )
        .order_by(RegistroAsistencia.fecha_hora.desc())
        .all()
    )
    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre_completo).all()
    hoy_inicio = _inicio_del_dia()
    hoy_fin = _fin_del_dia(hoy_inicio)
    registros_hoy = [r for r in registros if hoy_inicio <= r.fecha_hora <= hoy_fin]
    dentro_hoy = sum(
        1 for t in trabajadores if estado_trabajador_hoy(t.id, hoy_inicio)['en_jornada']
    )

    periodo_txt = (
        f'{ref_inicio.strftime("%d/%m/%Y")} — {datetime.now().strftime("%d/%m/%Y")} '
        f'({dias} dias)'
    )
    subtitulo = f'Periodo: {periodo_txt} | Generado {datetime.now().strftime("%d/%m/%Y %H:%M")}'

    df_resumen = pd.DataFrame([
        {'Indicador': 'Trabajadores activos', 'Valor': len(trabajadores)},
        {'Indicador': 'Registros en el periodo', 'Valor': len(registros)},
        {'Indicador': 'Entradas en el periodo', 'Valor': sum(1 for r in registros if r.tipo == 'entrada')},
        {'Indicador': 'Salidas en el periodo', 'Valor': sum(1 for r in registros if r.tipo == 'salida')},
        {'Indicador': 'Personal dentro hoy', 'Valor': dentro_hoy},
        {'Indicador': 'Entradas registradas hoy', 'Valor': sum(1 for r in registros_hoy if r.tipo == 'entrada')},
        {'Indicador': 'Periodo del reporte', 'Valor': periodo_txt},
    ])

    filas_registros = [
        {
            'ID': r.id,
            'Trabajador': r.trabajador.nombre_completo,
            'Tipo': r.tipo_label,
            'Fecha': r.fecha_hora.strftime('%d/%m/%Y'),
            'Hora': r.fecha_hora.strftime('%H:%M:%S'),
        }
        for r in registros
    ]
    if filas_registros:
        df_registros = pd.DataFrame(filas_registros)
    else:
        df_registros = pd.DataFrame(columns=['ID', 'Trabajador', 'Tipo', 'Fecha', 'Hora'])

    return [
        {'sheet_name': 'Resumen', 'df': df_resumen, 'titulo': 'Resumen de Asistencia Laboral', 'subtitulo': subtitulo},
        {'sheet_name': 'Registros', 'df': df_registros, 'titulo': 'Registro Detallado de Asistencia', 'subtitulo': subtitulo},
    ]


# Ruta para descargar todo en Excel
@app.route('/descargar-excel-todo')
def descargar_excel_todo():
    subtitulo = _excel_subtitulo_inventario()
    naps = Nat.query.join(NapModel).all()
    df_naps = pd.DataFrame([{
        'ID': n.id,
        'Nombre': n.nombre,
        'Puertos Totales': n.puertos_total,
        'Hilo Conexión': n.hilo_conexion,
        'Modelo': n.modelo.nombre if n.modelo else '',
        'Tipo Caja': ('Distribución' if n.modelo.tipo_caja == 'distribucion' else 'Empalme') if n.modelo else 'No especificado',
        'Latitud': n.latitud,
        'Longitud': n.longitud,
    } for n in naps])

    clientes = Cliente.query.all()
    df_clientes = pd.DataFrame([{
        'ID': c.id,
        'Nombre': c.nombre,
        'Dirección': c.direccion,
        'Plan': c.plan,
        'Contacto': c.contacto,
        'Activo': 'Sí' if c.activo else 'No',
        'NAP ID': c.nat_id,
    } for c in clientes])

    modelos = NapModel.query.all()
    df_modelos = pd.DataFrame([{
        'ID': m.id,
        'Nombre': m.nombre,
        'Tipo Caja': 'Distribución' if m.tipo_caja == 'distribucion' else 'Empalme',
        'Capacidad Máx': m.capacidad_max if m.tipo_caja == 'distribucion' else 'N/A',
        'Imagen URL': m.imagen_url,
    } for m in modelos])

    hojas = [
        {'sheet_name': 'Clientes', 'df': df_clientes, 'titulo': 'Cartera de Clientes', 'subtitulo': subtitulo},
        {'sheet_name': 'Cajas NAP', 'df': df_naps, 'titulo': 'Cajas NAP y Empalmes', 'subtitulo': subtitulo},
        {'sheet_name': 'Modelos NAP', 'df': df_modelos, 'titulo': 'Catalogo de Modelos NAP', 'subtitulo': subtitulo},
    ]
    hojas.extend(_dataframes_asistencias_export(30))

    output = crear_workbook_corporativo_multihoja(hojas, subtitulo)
    fecha = datetime.now().strftime('%Y-%m-%d')

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'inventario-completo-{fecha}.xlsx',
    )

@app.route('/')
def home():
    return redirect(url_for('dashboard'))


@app.route('/cajas')
def index():
    nats = Nat.query.order_by(Nat.nombre).all()
    return render_template('index.html', nats=nats)

@app.route('/dashboard')
def dashboard():
    """Dashboard principal - ÚNICO dashboard"""
    
    try:
        clientes_activos = Cliente.query.filter_by(activo=True).count()
        
        capacidad_total_resultado = db.session.query(func.sum(Nat.puertos_total)).scalar()
        capacidad_total = capacidad_total_resultado if capacidad_total_resultado is not None else 0
        capacidad_libre = max(capacidad_total - clientes_activos, 0)
        porcentaje_ocupacion = round((clientes_activos / capacidad_total) * 100) if capacidad_total > 0 else 0
        total_nats = Nat.query.count()
        total_clientes = Cliente.query.count()
        total_empalmes = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'empalme').count()
        total_distribucion = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'distribucion').count()

        reporte_tipos = []
        for tipo_key, tipo_label, color in [
            ('distribucion', 'Distribución (NAP)', '#10b981'),
            ('empalme', 'Empalmes', '#6366f1'),
        ]:
            nats_tipo = Nat.query.join(NapModel).filter(NapModel.tipo_caja == tipo_key).all()
            puertos_usados = sum(n.puertos_usados for n in nats_tipo if n.puertos_total)
            total_puertos = sum(n.puertos_total for n in nats_tipo)
            porcentaje = round((puertos_usados / total_puertos) * 100) if total_puertos else 0
            reporte_tipos.append({
                'nombre': tipo_label,
                'cantidad': len(nats_tipo),
                'puertos_usados': puertos_usados,
                'total_puertos': total_puertos,
                'porcentaje': porcentaje,
                'color': color,
            })

        # NATs saturadas y críticas
        nats_saturadas = [] 
        nats_criticas = []
        
        todas_nats = Nat.query.all()
        for nat in todas_nats:
            if not nat.puertos_total or nat.puertos_total <= 0:
                continue

            clientes_en_nat = db.session.query(func.count(Cliente.id)).filter(
                Cliente.nat_id == nat.id,
                Cliente.activo == True
            ).scalar() or 0

            uso_porcentaje = round((clientes_en_nat / nat.puertos_total) * 100)

            if uso_porcentaje >= 100:
                nats_saturadas.append(nat)
            elif uso_porcentaje >= 80:
                nats_criticas.append(nat)

        return render_template('dashboard.html', 
            clientes_activos=clientes_activos,
            capacidad_total=capacidad_total,
            capacidad_libre=capacidad_libre,
            porcentaje_ocupacion=porcentaje_ocupacion,
            total_nats=total_nats,
            total_clientes=total_clientes,
            total_empalmes=total_empalmes,
            total_distribucion=total_distribucion,
            reporte_tipos=reporte_tipos,
            nats_saturadas=nats_saturadas,
            nats_criticas=nats_criticas
        )
        
    except Exception as e:
        print(f"ERROR en dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback simple si hay error
        return f"""
        <html>
        <head><title>Error Dashboard</title></head>
        <body>
            <h1>Error cargando dashboard</h1>
            <p>{str(e)}</p>
            <a href="/dashboard">Volver al dashboard</a>
        </body>
        </html>
        """, 500

@app.route('/mapa_nats')
def mapa_nats():
    """Mapa geográfico de cajas NAP y empalmes."""
    total_nats = Nat.query.filter(Nat.latitud.isnot(None), Nat.longitud.isnot(None)).count()
    total_empalmes = Nat.query.join(NapModel).filter(
        NapModel.tipo_caja == 'empalme',
        Nat.latitud.isnot(None)
    ).count()
    total_distribucion = total_nats - total_empalmes

    capacidad_total = db.session.query(func.sum(Nat.puertos_total)).scalar() or 1
    capacidad_usada = db.session.query(func.count(Cliente.id)).filter_by(activo=True).scalar() or 0
    capacidad_ocupada = round((capacidad_usada / capacidad_total) * 100) if capacidad_total > 0 else 0

    nats_criticas = [n for n in Nat.query.all() if n.puertos_total and n.porcentaje_uso >= 80]
    mapa_html = generar_mapa_mejorado()

    return render_template('mapa_nats.html',
                         total_nats=total_nats,
                         total_empalmes=total_empalmes,
                         total_distribucion=total_distribucion,
                         capacidad_ocupada=capacidad_ocupada,
                         nats_criticas_count=len(nats_criticas),
                         mapa_html=mapa_html)

# ----------------------------------------------------------------------
# (Aquí van todas las demás rutas existentes de tu aplicación...)
# ----------------------------------------------------------------------

# RUTAS DE GESTIÓN DE NAPs
@app.route('/ver_nat/<int:nat_id>')
def ver_nat(nat_id):
    nat = Nat.query.get_or_404(nat_id)
    clientes = Cliente.query.filter_by(nat_id=nat_id).order_by(Cliente.activo.desc(), Cliente.nombre).all()
    imagen_nap = nat.modelo.imagen_url if nat.modelo and nat.modelo.imagen_url else url_for('static', filename='placeholder.jpg')
    return render_template('detalle_nat.html', nat=nat, clientes=clientes, imagen_nap=imagen_nap)

@app.route('/agregar_nat', methods=['GET', 'POST'])
def agregar_nat():
    modelos = NapModel.query.all()

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
        hilo_conexion = request.form.get('hilo_conexion')
        nap_model_id = request.form.get('nap_model_id')
        descripcion = request.form.get('descripcion')

        try:
            lat = float(latitud) if latitud else None
            lon = float(longitud) if longitud else None
        except (ValueError, TypeError):
            flash('Error: Las coordenadas deben ser números válidos.', 'danger')
            return render_template('agregar_nat.html', modelos=modelos)

        modelo_seleccionado = NapModel.query.get(nap_model_id)
        if modelo_seleccionado and modelo_seleccionado.tipo_caja == 'distribucion':
            puertos_total = modelo_seleccionado.capacidad_max or 8
        else:
            puertos_total = 0

        if not nombre or not nap_model_id:
            flash('Error: Nombre y modelo de caja son obligatorios.', 'danger')
            return render_template('agregar_nat.html', modelos=modelos)

        if Nat.query.filter_by(nombre=nombre).first():
            flash(f'Error: Ya existe una caja con el nombre "{nombre}".', 'danger')
            return render_template('agregar_nat.html', modelos=modelos)

        try:
            nueva_nat = Nat(
                nombre=nombre,
                latitud=lat,
                longitud=lon,
                descripcion=descripcion,
                puertos_total=puertos_total,
                hilo_conexion=hilo_conexion,
                nap_model_id=nap_model_id,
            )
            db.session.add(nueva_nat)
            db.session.commit()
            flash(f'Caja "{nombre}" registrada con éxito.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la caja: {e}', 'danger')

    return render_template('agregar_nat.html', modelos=modelos)

@app.route('/editar_nat/<int:nat_id>', methods=['GET', 'POST'])
def editar_nat(nat_id):
    nat = Nat.query.get_or_404(nat_id)
    modelos = NapModel.query.all()

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
        hilo_conexion = request.form.get('hilo_conexion')
        nap_model_id = request.form.get('nap_model_id')
        descripcion = request.form.get('descripcion')

        try:
            lat = float(latitud) if latitud else None
            lon = float(longitud) if longitud else None
        except (ValueError, TypeError):
            flash('Error: Las coordenadas deben ser números válidos.', 'danger')
            return render_template('agregar_nat.html', nat=nat, modelos=modelos)

        modelo_seleccionado = NapModel.query.get(nap_model_id)
        if modelo_seleccionado and modelo_seleccionado.tipo_caja == 'distribucion':
            nueva_capacidad = modelo_seleccionado.capacidad_max or nat.puertos_total
        else:
            nueva_capacidad = 0

        if Nat.query.filter_by(nombre=nombre).filter(Nat.id != nat_id).first():
            flash(f'Error: Ya existe otra caja con el nombre "{nombre}".', 'danger')
            return render_template('agregar_nat.html', nat=nat, modelos=modelos)

        if modelo_seleccionado and modelo_seleccionado.tipo_caja == 'distribucion':
            if nueva_capacidad < nat.puertos_usados:
                flash(f'La capacidad ({nueva_capacidad}) no puede ser menor a los puertos usados ({nat.puertos_usados}).', 'danger')
                return render_template('agregar_nat.html', nat=nat, modelos=modelos)

        try:
            nat.nombre = nombre
            nat.latitud = lat
            nat.longitud = lon
            nat.descripcion = descripcion
            nat.puertos_total = nueva_capacidad
            nat.hilo_conexion = hilo_conexion
            nat.nap_model_id = nap_model_id
            db.session.commit()
            flash(f'Caja "{nombre}" actualizada con éxito.', 'success')
            return redirect(url_for('ver_nat', nat_id=nat.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la caja: {e}', 'danger')

    return render_template('agregar_nat.html', nat=nat, modelos=modelos)

@app.route('/eliminar_nat/<int:nat_id>', methods=['POST'])
def eliminar_nat(nat_id):
    nat = Nat.query.get_or_404(nat_id)
    nombre = nat.nombre
    
    try:
        db.session.delete(nat)
        db.session.commit()
        flash(f'NAT "{nombre}" eliminada con éxito y sus clientes asociados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la NAT: {e}', 'danger')
        
    return redirect(url_for('index'))

# ----------------------------------------------------------------------
# RUTAS DE GESTIÓN DE INFRAESTRUCTURA
# ----------------------------------------------------------------------

## A. Gestión de Modelos de NAPs (ACTUALIZADA PARA SOPORTAR DISTRIBUCIÓN Y EMPALME)
@app.route('/nap_models')
def listar_nap_models():
    modelos = NapModel.query.order_by(NapModel.nombre).all()
    return render_template('listar_nap_models.html', modelos=modelos)

@app.route('/agregar_nap_model', methods=['GET', 'POST'])
def agregar_nap_model():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo_caja = request.form.get('tipo_caja')
        capacidad_max = request.form.get('capacidad_max')
        imagen = request.files.get('imagen_nap')

        if not nombre or not tipo_caja:
            flash('Nombre y Tipo de Caja son obligatorios.', 'danger')
            return render_template('agregar_nap_model.html')
            
        if tipo_caja not in ['distribucion', 'empalme']:
            flash('Tipo de caja no válido.', 'danger')
            return render_template('agregar_nap_model.html')
            
        # Validar capacidad para distribución
        if tipo_caja == 'distribucion':
            if not capacidad_max:
                flash('Para cajas de distribución, la capacidad es obligatoria.', 'danger')
                return render_template('agregar_nap_model.html')
            try:
                capacidad_max = int(capacidad_max)
                if capacidad_max <= 0:
                    flash('Capacidad debe ser un número positivo.', 'danger')
                    return render_template('agregar_nap_model.html')
            except ValueError:
                flash('Capacidad debe ser un número entero.', 'danger')
                return render_template('agregar_nap_model.html')
        else:
            # Para empalme, capacidad_max es None
            capacidad_max = None
            
        imagen_url = None
        if imagen and imagen.filename:
            if allowed_image_file(imagen.filename):
                filename = generar_filename(imagen.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(save_path)
                imagen_url = url_for('static', filename=f'nap_images/{filename}')
            else:
                flash('Formato de imagen no permitido. Use PNG, JPG, JPEG o GIF.', 'danger')
                return render_template('agregar_nap_model.html')

        try:
            nuevo_modelo = NapModel(
                nombre=nombre, 
                tipo_caja=tipo_caja,
                capacidad_max=capacidad_max,
                imagen_url=imagen_url
            )
            db.session.add(nuevo_modelo)
            db.session.commit()
            
            tipo_texto = "de distribución (NAP/FAT)" if tipo_caja == "distribucion" else "de empalme"
            flash(f'Modelo "{nombre}" ({tipo_texto}) registrado con éxito.', 'success')
            return redirect(url_for('listar_nap_models'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el modelo: {e}', 'danger')

    return render_template('agregar_nap_model.html')

@app.route('/editar_nap_model/<int:model_id>', methods=['GET', 'POST'])
def editar_nap_model(model_id):
    modelo = NapModel.query.get_or_404(model_id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo_caja = request.form.get('tipo_caja')
        capacidad_max = request.form.get('capacidad_max')
        imagen = request.files.get('imagen_nap')
        eliminar_imagen = request.form.get('eliminar_imagen') == 'on'

        if not nombre or not tipo_caja:
            flash('Nombre y Tipo de Caja son obligatorios.', 'danger')
            return render_template('agregar_nap_model.html', modelo=modelo)
            
        if tipo_caja not in ['distribucion', 'empalme']:
            flash('Tipo de caja no válido.', 'danger')
            return render_template('agregar_nap_model.html', modelo=modelo)
            
        # Validar capacidad para distribución
        if tipo_caja == 'distribucion':
            if not capacidad_max:
                flash('Para cajas de distribución, la capacidad es obligatoria.', 'danger')
                return render_template('agregar_nap_model.html', modelo=modelo)
            try:
                capacidad_max = int(capacidad_max)
                if capacidad_max <= 0:
                    flash('Capacidad debe ser un número positivo.', 'danger')
                    return render_template('agregar_nap_model.html', modelo=modelo)
            except ValueError:
                flash('Capacidad debe ser un número entero.', 'danger')
                return render_template('agregar_nap_model.html', modelo=modelo)
        else:
            # Para empalme, capacidad_max es None
            capacidad_max = None
            
        if NapModel.query.filter_by(nombre=nombre).filter(NapModel.id != model_id).first():
            flash(f'Error: Ya existe otro modelo con el nombre "{nombre}".', 'danger')
            return render_template('agregar_nap_model.html', modelo=modelo)
            
        # Verificar que no se cambie de distribución a empalme si hay NAPs con clientes
        if modelo.tipo_caja == 'distribucion' and tipo_caja == 'empalme':
            # Contar clientes en NAPs que usan este modelo
            total_clientes = 0
            for nap in modelo.nats:
                total_clientes += nap.clientes.count()
            
            if total_clientes > 0:
                flash(f'Error: No se puede cambiar a tipo "Empalme" porque hay {total_clientes} cliente(s) usando este modelo.', 'danger')
                return render_template('agregar_nap_model.html', modelo=modelo)
            
        if eliminar_imagen and modelo.imagen_url:
            try:
                filename = os.path.basename(modelo.imagen_url)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                modelo.imagen_url = None
            except Exception as e:
                flash(f'Error al eliminar la imagen antigua: {e}', 'warning')
        
        if imagen and imagen.filename:
            if allowed_image_file(imagen.filename):
                try:
                    if modelo.imagen_url:
                        filename_old = os.path.basename(modelo.imagen_url)
                        file_path_old = os.path.join(app.config['UPLOAD_FOLDER'], filename_old)
                        if os.path.exists(file_path_old):
                            os.remove(file_path_old)

                    filename = generar_filename(imagen.filename)
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    imagen.save(save_path)
                    modelo.imagen_url = url_for('static', filename=f'nap_images/{filename}')
                except Exception as e:
                     flash(f'Error al procesar la nueva imagen: {e}', 'warning')
            else:
                flash('Formato de imagen no permitido. Use PNG, JPG, JPEG o GIF.', 'danger')

        try:
            modelo.nombre = nombre
            modelo.tipo_caja = tipo_caja
            modelo.capacidad_max = capacidad_max
            db.session.commit()
            
            tipo_texto = "de distribución (NAP/FAT)" if tipo_caja == "distribucion" else "de empalme"
            flash(f'Modelo "{nombre}" ({tipo_texto}) actualizado con éxito.', 'success')
            return redirect(url_for('listar_nap_models'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el modelo: {e}', 'danger')

    return render_template('agregar_nap_model.html', modelo=modelo)

@app.route('/eliminar_nap_model/<int:model_id>', methods=['POST'])
def eliminar_nap_model(model_id):
    modelo = NapModel.query.get_or_404(model_id)
    
    if modelo.nats.count() > 0:
        flash(f'Error: No se puede eliminar el modelo "{modelo.nombre}" porque está siendo usado por {modelo.nats.count()} NATs.', 'danger')
        return redirect(url_for('listar_nap_models'))
        
    try:
        if modelo.imagen_url:
            try:
                filename = os.path.basename(modelo.imagen_url)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass 
                
        db.session.delete(modelo)
        db.session.commit()
        flash(f'Modelo "{modelo.nombre}" eliminado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el modelo: {e}', 'danger')
        
    return redirect(url_for('listar_nap_models'))

# ----------------------------------------------------------------------
# RUTAS DE GESTIÓN DE CLIENTES
# ----------------------------------------------------------------------

@app.route('/clientes')
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('listar_clientes.html', clientes=clientes)
    
@app.route('/cliente/<int:cliente_id>')
def ver_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return redirect(url_for('ver_nat', nat_id=cliente.nat_id))

@app.route('/agregar_cliente/<int:nat_id>', methods=['GET', 'POST'])
@app.route('/agregar_cliente', methods=['GET', 'POST'])
def agregar_cliente(nat_id=None):
    # Solo mostrar NAPs de distribución (no empalme)
    nats = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'distribucion').order_by(Nat.nombre).all()
    nat_destino = Nat.query.get(nat_id) if nat_id else None
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        plan = request.form.get('plan')
        contacto = request.form.get('contacto')
        nat_seleccionada_id = request.form.get('nat_id')
        activo = request.form.get('activo') == 'on'
        
        if not nombre or not direccion or not nat_seleccionada_id:
            flash('Nombre, Dirección y NAT son obligatorios.', 'danger')
            return render_template('agregar_cliente.html', nats=nats, nat_destino=nat_destino)

        nat_obj = Nat.query.get(nat_seleccionada_id)
        if nat_obj and nat_obj.puertos_usados >= nat_obj.puertos_total and activo:
             flash('Error: La NAT seleccionada está llena (100% de uso).', 'danger')
             return render_template('agregar_cliente.html', nats=nats, nat_destino=nat_destino)
        
        try:
            nuevo_cliente = Cliente(
                nombre=nombre, 
                direccion=direccion,
                plan=plan,
                contacto=contacto,
                nat_id=nat_seleccionada_id,
                activo=activo
            )
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash(f'Cliente "{nombre}" registrado con éxito.', 'success')
            
            if nat_destino:
                return redirect(url_for('ver_nat', nat_id=nat_destino.id))
            return redirect(url_for('listar_clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el cliente: {e}', 'danger')
            
    return render_template('agregar_cliente.html', nats=nats, nat_destino=nat_destino)

@app.route('/editar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    # Solo mostrar NAPs de distribución (no empalme)
    nats = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'distribucion').order_by(Nat.nombre).all()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        plan = request.form.get('plan')
        contacto = request.form.get('contacto')
        nat_seleccionada_id = request.form.get('nat_id')
        activo = request.form.get('activo') == 'on'
        
        if not nombre or not direccion or not nat_seleccionada_id:
            flash('Nombre, Dirección y NAT son obligatorios.', 'danger')
            return render_template('agregar_cliente.html', cliente=cliente, nats=nats)

        nat_obj = Nat.query.get(nat_seleccionada_id)
        
        if activo and nat_obj and nat_obj.puertos_usados >= nat_obj.puertos_total:
            if int(nat_seleccionada_id) == cliente.nat_id and not cliente.activo:
                 flash('Error: La NAT seleccionada está llena (100% de uso) y no permite reactivación.', 'danger')
                 return render_template('agregar_cliente.html', cliente=cliente, nats=nats)
            if int(nat_seleccionada_id) != cliente.nat_id:
                 if nat_obj.puertos_usados >= nat_obj.puertos_total:
                     flash('Error: La nueva NAT seleccionada está llena (100% de uso).', 'danger')
                     return render_template('agregar_cliente.html', cliente=cliente, nats=nats)

        try:
            cliente.nombre = nombre
            cliente.direccion = direccion
            cliente.plan = plan
            cliente.contacto = contacto
            cliente.nat_id = nat_seleccionada_id
            cliente.activo = activo
            
            db.session.commit()
            flash(f'Cliente "{nombre}" actualizado con éxito.', 'success')
            return redirect(url_for('ver_nat', nat_id=cliente.nat_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {e}', 'danger')

    return render_template('agregar_cliente.html', cliente=cliente, nats=nats)

@app.route('/cliente/toggle_activo/<int:cliente_id>', methods=['POST'])
def activar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    nat_id = cliente.nat_id

    if not cliente.activo:
        nat_obj = Nat.query.get(nat_id)
        if nat_obj and nat_obj.puertos_usados >= nat_obj.puertos_total:
            flash(f'Error: No se puede reactivar al cliente "{cliente.nombre}". La NAT {nat_obj.nombre} está al 100% de su capacidad.', 'danger')
            return redirect(url_for('ver_nat', nat_id=nat_id))

    cliente.activo = not cliente.activo
    
    try:
        db.session.commit()
        estado = "ACTIVO" if cliente.activo else "INACTIVO"
        flash(f'Estado del cliente {cliente.nombre} cambiado a {estado} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado del cliente: {e}', 'danger')
        
    return redirect(url_for('ver_nat', nat_id=nat_id))

@app.route('/eliminar_cliente/<int:cliente_id>', methods=['POST'])
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    nombre = cliente.nombre
    nat_id = cliente.nat_id
    
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Cliente "{nombre}" eliminado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el cliente: {e}', 'danger')
        
    return redirect(url_for('ver_nat', nat_id=nat_id))

# ----------------------------------------------------------------------
# RUTAS DE REPORTES Y NOTIFICACIONES
# ----------------------------------------------------------------------

@app.route('/reportes')
def reportes_avanzados():
    """Panel de reportes avanzados con métricas y gráficos"""
    
    # Métricas principales
    clientes_activos = Cliente.query.filter_by(activo=True).count()
    total_nats = Nat.query.count()
    nats_activas = sum(1 for nat in Nat.query.all() if nat.puertos_usados > 0)
    
    # Calcular ocupación promedio
    nats_con_capacidad = Nat.query.filter(Nat.puertos_total > 0).all()
    ocupacion_promedio = 0
    if nats_con_capacidad:
        ocupaciones = [nat.porcentaje_uso for nat in nats_con_capacidad]
        ocupacion_promedio = sum(ocupaciones) / len(ocupaciones)
    
    # NATs críticas
    nats_criticas = []
    for nat in Nat.query.all():
        if nat.porcentaje_uso >= 80:
            nats_criticas.append(nat)
    
    # Datos para gráficos por tipo de caja
    troncales_labels = ['Distribución', 'Empalmes']
    troncales_ocupacion = []
    troncales_colors = ['#10b981', '#6366f1']
    for tipo in ['distribucion', 'empalme']:
        nats_tipo = Nat.query.join(NapModel).filter(NapModel.tipo_caja == tipo).all()
        con_cap = [n for n in nats_tipo if n.puertos_total > 0]
        if con_cap:
            troncales_ocupacion.append(round(sum(n.porcentaje_uso for n in con_cap) / len(con_cap)))
        else:
            troncales_ocupacion.append(len(nats_tipo))
    
    # Distribución de planes (simulada)
    planes_labels = ['100 Mbps', '200 Mbps', '500 Mbps', '1 Gbps', 'Empresarial']
    planes_data = [45, 30, 15, 8, 2]
    
    # Datos de crecimiento mensual (simulados)
    meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
    meses_clientes = [85, 92, 88, 95, 102, clientes_activos]
    
    # Estado de NATs
    estado_nats_normal = len([nat for nat in Nat.query.all() if nat.porcentaje_uso < 80])
    estado_nats_critico = len([nat for nat in Nat.query.all() if 80 <= nat.porcentaje_uso < 100])
    estado_nats_saturado = len([nat for nat in Nat.query.all() if nat.porcentaje_uso >= 100])
    
    # Tipos de cajas
    modelos_distribucion = NapModel.query.filter_by(tipo_caja='distribucion').count()
    modelos_empalme = NapModel.query.filter_by(tipo_caja='empalme').count()
    
    metricas = {
        'clientes_activos': clientes_activos,
        'tendencia_clientes': 12,  # Simulado
        'ocupacion_promedio': round(ocupacion_promedio, 1),
        'nats_activas': nats_activas,
        'total_nats': total_nats,
        'ingresos_mensuales': clientes_activos * 299,  # Simulado: $299 por cliente
        'crecimiento_ingresos': 12,  # Simulado
        'nats_criticas': len(nats_criticas),
        'troncales_labels': troncales_labels,
        'troncales_ocupacion': troncales_ocupacion,
        'troncales_colors': troncales_colors,
        'planes_labels': planes_labels,
        'planes_data': planes_data,
        'meses_labels': meses_labels,
        'meses_clientes': meses_clientes,
        'estado_nats_data': [estado_nats_normal, estado_nats_critico, estado_nats_saturado],
        'modelos_distribucion': modelos_distribucion,
        'modelos_empalme': modelos_empalme
    }
    
    return render_template('reportes_avanzados.html', 
                         metricas=metricas,
                         nats_criticas=nats_criticas)

@app.route('/api/notifications/critical-nats')
def api_critical_nats():
    """API para notificaciones de NATs críticas"""
    critical_count = 0
    for nat in Nat.query.all():
        if nat.porcentaje_uso >= 80:
            critical_count += 1
    
    return jsonify({
        'critical_nats': critical_count,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/notifications/system-capacity')
def api_system_capacity():
    """API para notificaciones de capacidad del sistema"""
    total_capacity = db.session.query(func.sum(Nat.puertos_total)).scalar() or 0
    used_capacity = Cliente.query.filter_by(activo=True).count()
    usage_percentage = (used_capacity / total_capacity) * 100 if total_capacity > 0 else 0
    
    alert = usage_percentage >= 85
    message = f"Capacidad del sistema al {usage_percentage:.1f}%" if alert else ""
    
    return jsonify({
        'capacity_alert': alert,
        'usage_percentage': usage_percentage,
        'message': message,
        'timestamp': datetime.now().isoformat()
    })

# Filtro personalizado para formato de moneda
@app.template_filter('currency')
def currency_filter(value):
    """Filtro para formatear números como moneda"""
    return f"${value:,.0f}"

# ----------------------------------------------------------------------
# RUTAS PREMIUM
# ----------------------------------------------------------------------
@app.route('/personalizacion')
def personalizacion():
    """Panel de personalización de temas"""
    config = {
        'primary_color': request.args.get('primary', '#3B82F6'),
        'secondary_color': request.args.get('secondary', '#1E40AF'),
        'accent_color': request.args.get('accent', '#10B981'),
        'background_color': request.args.get('background', '#F8FAFC'),
        'text_color': request.args.get('text', '#1F2937'),
        'border_radius': request.args.get('border_radius', '12')
    }
    return render_template('tema_personalizado.html', config=config)

@app.route('/api/theme/save', methods=['POST'])
def api_save_theme():
    """API para guardar configuración de tema"""
    data = request.get_json()
    
    # Aquí guardarías la configuración en la base de datos
    # Por ahora simulamos el guardado
    theme_config = {
        'primary': data.get('primary', '#3B82F6'),
        'secondary': data.get('secondary', '#1E40AF'),
        'accent': data.get('accent', '#10B981'),
        'border_radius': data.get('border_radius', 12),
        'mode': data.get('mode', 'light'),
        'updated_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'message': 'Tema guardado exitosamente',
        'theme': theme_config
    })

@app.template_filter('datetime_format')
def datetime_format(value, format='%d/%m/%Y %H:%M'):
    """Filtro para formatear fechas"""
    if value == 'now':
        return datetime.now().strftime(format)
    return value

# Service Worker para PWA
@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

# Manifest.json
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# ----------------------------------------------------------------------
# POTENCIAS
# ----------------------------------------------------------------------
@app.route('/potencias')
def potencias_lista():
    return render_template('potencias.html')

@app.route('/potencias/nueva')
def potencias_nueva():
    return render_template('potencia_nueva.html')

@app.route('/potencias/editar/<int:id>')
def potencias_editar(id):
    return render_template('potencia_editar.html')
# ----------------------------------------------------------------------
# API PARA NAPs (NAT)
# ----------------------------------------------------------------------
@app.route('/api/nat', methods=['GET'])
def api_get_nat():
    try:
        query = text("SELECT id, nombre FROM public.nat ORDER BY nombre ASC")
        result = db.session.execute(query)
        
        naps = [{'id': r.id, 'nombre': r.nombre} for r in result]
        
        return jsonify(success=True, naps=naps, total=len(naps))
        
    except Exception as e:
        db.session.rollback()
        print("ERROR nat:", e)
        return jsonify(success=False, message=str(e)), 500


@app.route('/api/trabajadores')
def api_trabajadores():
    seed_trabajadores()
    trabajadores = (
        Trabajador.query.filter_by(activo=True)
        .order_by(Trabajador.nombre_completo)
        .all()
    )
    return jsonify({
        'success': True,
        'trabajadores': [
            {'id': t.id, 'nombre': t.nombre_completo}
            for t in trabajadores
        ],
    })


@app.route('/api/potencias/nap/<int:nap_id>/potencia-nap')
def api_potencia_nap_por_caja(nap_id):
    """Última potencia de la NAP registrada para esa caja (cualquier cliente)."""
    registro = (
        Potencia.query.filter_by(nap_id=nap_id)
        .order_by(Potencia.fecha.desc())
        .first()
    )
    if not registro:
        return jsonify(success=False, potencia_entrada=None, message='Sin mediciones previas para esta NAP')
    return jsonify(
        success=True,
        potencia_entrada=registro.potencia_entrada,
        fecha=registro.fecha.strftime('%d/%m/%Y %H:%M') if registro.fecha else None,
    )


# ----------------------------------------------------------------------
# API ENDPOINTS PARA POTENCIAS (VERSIÓN CORREGIDA)
# ----------------------------------------------------------------------
@app.route('/api/potencias', methods=['GET'])
def api_get_potencias():
    try:
        query = text("""
            SELECT 
                p.id,
                p.fecha,
                p.potencia_entrada,
                p.potencia_salida,
                p.perdida,
                p.estado,
                p.observaciones,
                p.cliente_id,
                c.nombre AS cliente_nombre,
                p.nap_id,
                n.nombre AS nap_nombre,
                p.tecnico
            FROM public.potencias p
            LEFT JOIN public.cliente c ON p.cliente_id = c.id
            LEFT JOIN public.nat n ON p.nap_id = n.id
            ORDER BY p.fecha DESC
        """)

        result = db.session.execute(query)

        potencias = [{
            'id': r.id,
            'fecha_medicion': r.fecha.isoformat() if r.fecha else None,
            'potencia_entrada': float(r.potencia_entrada or 0),
            'potencia_salida': float(r.potencia_salida or 0),
            'perdida': float(r.perdida or 0),
            'estado': r.estado or 'normal',
            'observaciones': r.observaciones or '',
            'cliente_id': r.cliente_id,
            'cliente_nombre': r.cliente_nombre or 'Cliente Desconocido',
            'nap_id': r.nap_id,
            'nap_nombre': r.nap_nombre or 'Sin NAP',
            'tecnico': r.tecnico or 'Técnico Desconocido'
        } for r in result]

        return jsonify(
            success=True,
            potencias=potencias,
            total=len(potencias)
        )

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify(
            success=False,
            message=str(e)
        ), 500

def _estado_por_perdida(perdida):
    perdida = abs(float(perdida))
    if perdida <= 1:
        return 'excelente'
    if perdida <= 2.5:
        return 'normal'
    if perdida <= 3.5:
        return 'bajo'
    return 'critico'


def _propagar_potencia_nap(nap_id, potencia_entrada):
    """
    Sincroniza potencia_entrada (potencia de la NAP) en todas las mediciones
    vinculadas a la misma caja y recalcula pérdida/estado de cada una.
    """
    if not nap_id:
        return 0

    p_in = float(potencia_entrada)
    filas = db.session.execute(
        text('SELECT id, potencia_salida FROM potencias WHERE nap_id = :nap_id'),
        {'nap_id': nap_id},
    ).fetchall()

    for fila in filas:
        p_out = float(fila.potencia_salida)
        perdida = round(abs(p_out - p_in), 2)
        estado = _estado_por_perdida(perdida)
        db.session.execute(
            text("""
                UPDATE potencias SET
                    potencia_entrada = :p_in,
                    perdida = :perdida,
                    estado = :estado
                WHERE id = :id
            """),
            {'p_in': p_in, 'perdida': perdida, 'estado': estado, 'id': fila.id},
        )

    return len(filas)


# ----------------------------------------------------------------------
# CREATE POTENCIA
# ----------------------------------------------------------------------

@app.route('/api/potencias', methods=['POST'])
def api_create_potencia():
    try:
        data = request.get_json()

        for campo in ['cliente_id', 'potencia_entrada', 'potencia_salida']:
            if campo not in data:
                return jsonify(success=False, message=f'Falta {campo}'), 400

        p_in = float(data['potencia_entrada'])
        p_out = float(data['potencia_salida'])
        perdida = round(abs(p_out - p_in), 2)
        estado = _estado_por_perdida(perdida)
        nap_id = data.get('nap_id')

        query = text("""
            INSERT INTO potencias (
                fecha, cliente_id, nap_id,
                potencia_entrada, potencia_salida,
                perdida, estado, observaciones, tecnico
            )
            VALUES (
                :fecha, :cliente_id, :nap_id,
                :p_in, :p_out,
                :perdida, :estado, :obs, :tecnico
            )
            RETURNING id
        """)

        result = db.session.execute(query, {
            'fecha': data.get('fecha_medicion') or datetime.utcnow(),
            'cliente_id': data['cliente_id'],
            'nap_id': nap_id,
            'p_in': p_in,
            'p_out': p_out,
            'perdida': perdida,
            'estado': estado,
            'obs': data.get('observaciones', ''),
            'tecnico': data.get('tecnico')
        })

        nueva_id = result.scalar()

        registros_sync = 0
        if nap_id:
            registros_sync = _propagar_potencia_nap(nap_id, p_in)

        db.session.commit()

        mensaje = 'Medición creada'
        if registros_sync > 1:
            mensaje += f'. Potencia de la NAP actualizada en {registros_sync} mediciones'

        return jsonify(success=True, id=nueva_id, message=mensaje, registros_nap_sync=registros_sync)

    except Exception as e:
        db.session.rollback()
        print("CREATE potencia error:", e)
        return jsonify(success=False, message="Error al crear potencia"), 500

# ----------------------------------------------------------------------
# UPDATE POTENCIA
# ----------------------------------------------------------------------

@app.route('/api/potencias/<int:id>', methods=['PUT'])
def api_update_potencia(id):
    try:
        data = request.get_json()

        perdida = None
        estado = None

        nap_id = data.get('nap_id')
        p_in = data.get('potencia_entrada')
        p_out = data.get('potencia_salida')

        if p_in is not None and p_out is not None:
            perdida = round(abs(float(p_out) - float(p_in)), 2)
            estado = _estado_por_perdida(perdida)

        query = text("""
            UPDATE potencias SET
                cliente_id = :cliente,
                nap_id = :nap,
                potencia_entrada = COALESCE(:p_in, potencia_entrada),
                potencia_salida = COALESCE(:p_out, potencia_salida),
                perdida = COALESCE(:perdida, perdida),
                estado = COALESCE(:estado, estado),
                observaciones = :obs,
                tecnico = :tecnico,
                fecha = :fecha
            WHERE id = :id
        """)

        db.session.execute(query, {
            'cliente': data.get('cliente_id'),
            'nap': nap_id,
            'p_in': p_in,
            'p_out': p_out,
            'perdida': perdida,
            'estado': estado,
            'obs': data.get('observaciones', ''),
            'tecnico': data.get('tecnico'),
            'fecha': data.get('fecha_medicion'),
            'id': id
        })

        registros_sync = 0
        if nap_id and p_in is not None and data.get('propagar_potencia_nap', True):
            registros_sync = _propagar_potencia_nap(nap_id, p_in)

        db.session.commit()

        mensaje = 'Medición actualizada'
        if registros_sync > 1:
            mensaje += f'. Potencia de la NAP sincronizada en {registros_sync} mediciones'

        return jsonify(success=True, message=mensaje, registros_nap_sync=registros_sync)

    except Exception as e:
        db.session.rollback()
        print("UPDATE potencia error:", e)
        return jsonify(success=False, message="Error al actualizar potencia"), 500
# ----------------------------------------------------------------------
# GET SINGLE POTENCIA (para editar)
# ----------------------------------------------------------------------
@app.route('/api/potencias/<int:id>', methods=['GET'])
def api_get_potencia(id):
    try:
        query = text("""
            SELECT 
                p.id,
                p.fecha,
                p.potencia_entrada,
                p.potencia_salida,
                p.perdida,
                p.estado,
                p.observaciones,
                p.tecnico,
                p.cliente_id,
                c.nombre AS cliente_nombre,
                p.nap_id,
                n.nombre AS nap_nombre
            FROM public.potencias p
            LEFT JOIN public.cliente c ON p.cliente_id = c.id
            LEFT JOIN public.nat n ON p.nap_id = n.id
            WHERE p.id = :id
        """)

        result = db.session.execute(query, {'id': id})
        potencia = result.fetchone()

        if not potencia:
            return jsonify(success=False, message='Medición no encontrada'), 404

        return jsonify(success=True, potencia={
            'id': potencia.id,
            'fecha_medicion': potencia.fecha.isoformat() if potencia.fecha else None,
            'potencia_entrada': float(potencia.potencia_entrada or 0),
            'potencia_salida': float(potencia.potencia_salida or 0),
            'perdida': float(potencia.perdida or 0),
            'estado': potencia.estado or 'normal',
            'observaciones': potencia.observaciones or '',
            'tecnico': potencia.tecnico or '',
            'cliente_id': potencia.cliente_id,
            'cliente_nombre': potencia.cliente_nombre or 'Cliente Desconocido',
            'nap_id': potencia.nap_id,
            'nap_nombre': potencia.nap_nombre or 'Sin NAP'
        })

    except Exception as e:
        db.session.rollback()
        print("GET potencia error:", e)
        return jsonify(success=False, message=str(e)), 500
# ----------------------------------------------------------------------
# DELETE POTENCIA
# ----------------------------------------------------------------------
@app.route('/api/potencias/<int:id>', methods=['DELETE'])
def eliminar_potencia(id):
    try:
        potencia = Potencia.query.get(id)

        if not potencia:
            return jsonify({
                'success': False,
                'message': 'Medición no encontrada'
            }), 404

        db.session.delete(potencia)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Medición eliminada correctamente'
        }), 200

    except Exception as e:
        db.session.rollback()
        print("ERROR DELETE POTENCIA:", e)
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



# ----------------------------------------------------------------------
# INVENTARIO
# ----------------------------------------------------------------------
@app.route('/inventarios')
def inventarios():
    from datetime import datetime
    
    # Obtener datos reales de la base de datos
    total_clientes = Cliente.query.count()
    clientes_activos = Cliente.query.filter_by(activo=True).count()
    
    total_naps = Nat.query.count()
    
    # Calcular puertos ocupados (clientes conectados)
    puertos_ocupados = Cliente.query.filter_by(activo=True).count()
    puertos_totales = db.session.query(db.func.sum(Nat.puertos_total)).scalar() or 0
    
    # Calcular ocupación promedio
    ocupacion_promedio = 0
    if puertos_totales > 0:
        ocupacion_promedio = round((puertos_ocupados / puertos_totales) * 100, 1)
    
    total_nats = Nat.query.count()
    cajas_distribucion = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'distribucion').count()
    cajas_empalme = Nat.query.join(NapModel).filter(NapModel.tipo_caja == 'empalme').count()
    modelos_distribucion = NapModel.query.filter_by(tipo_caja='distribucion').count()
    modelos_empalme = NapModel.query.filter_by(tipo_caja='empalme').count()

    resumen_tipos = [
        {'nombre': 'Distribución (NAP)', 'color': '#10b981', 'nats_count': cajas_distribucion},
        {'nombre': 'Empalmes', 'color': '#6366f1', 'nats_count': cajas_empalme},
    ]

    seed_trabajadores()
    total_trabajadores = Trabajador.query.filter_by(activo=True).count()
    hoy_inicio = _inicio_del_dia()
    hoy_fin = _fin_del_dia(hoy_inicio)
    registros_hoy = RegistroAsistencia.query.filter(
        RegistroAsistencia.fecha_hora >= hoy_inicio,
        RegistroAsistencia.fecha_hora <= hoy_fin,
    ).all()
    entradas_hoy = sum(1 for r in registros_hoy if r.tipo == 'entrada')
    salidas_hoy = sum(1 for r in registros_hoy if r.tipo == 'salida')
    dentro_hoy = sum(
        1 for t in Trabajador.query.filter_by(activo=True).all()
        if estado_trabajador_hoy(t.id, hoy_inicio)['en_jornada']
    )
    mes_inicio = _inicio_del_dia(datetime.now() - timedelta(days=30))
    registros_mes = RegistroAsistencia.query.filter(
        RegistroAsistencia.fecha_hora >= mes_inicio,
        RegistroAsistencia.fecha_hora <= hoy_fin,
    ).count()

    return render_template('inventario.html',
                         total_clientes=total_clientes,
                         clientes_activos=clientes_activos,
                         total_naps=total_naps,
                         puertos_totales=puertos_totales,
                         puertos_ocupados=puertos_ocupados,
                         ocupacion_promedio=ocupacion_promedio,
                         total_nats=total_nats,
                         cajas_distribucion=cajas_distribucion,
                         cajas_empalme=cajas_empalme,
                         modelos_distribucion=modelos_distribucion,
                         modelos_empalme=modelos_empalme,
                         resumen_tipos=resumen_tipos,
                         total_trabajadores=total_trabajadores,
                         dentro_hoy=dentro_hoy,
                         entradas_hoy=entradas_hoy,
                         salidas_hoy=salidas_hoy,
                         registros_mes=registros_mes,
                         fecha_actual=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))


# ----------------------------------------------------------------------
# GESTIÓN DE ASISTENCIA LABORAL (ENTRADA / SALIDA)
# ----------------------------------------------------------------------
def _inicio_del_dia(fecha=None):
    ref = fecha or datetime.now()
    return ref.replace(hour=0, minute=0, second=0, microsecond=0)


def _fin_del_dia(inicio):
    return inicio.replace(hour=23, minute=59, second=59, microsecond=999999)


def seed_trabajadores():
    if Trabajador.query.count() > 0:
        return
    for nombre in TRABAJADORES_INICIALES:
        db.session.add(Trabajador(
            nombre_completo=nombre,
            apellido_paterno=None,
            apellido_materno=None,
            activo=True,
        ))
    db.session.commit()


def estado_trabajador_hoy(trabajador_id, dia_inicio=None):
    inicio = dia_inicio or _inicio_del_dia()
    fin = _fin_del_dia(inicio)
    registros = (
        RegistroAsistencia.query.filter(
            RegistroAsistencia.trabajador_id == trabajador_id,
            RegistroAsistencia.fecha_hora >= inicio,
            RegistroAsistencia.fecha_hora <= fin,
        )
        .order_by(RegistroAsistencia.fecha_hora.asc())
        .all()
    )
    ultimo = registros[-1] if registros else None
    return {
        'registros': registros,
        'ultimo': ultimo,
        'puede_entrada': ultimo is None or ultimo.tipo == 'salida',
        'puede_salida': ultimo is not None and ultimo.tipo == 'entrada',
        'en_jornada': ultimo is not None and ultimo.tipo == 'entrada',
    }


@app.route('/gestion/asistencias')
def gestion_asistencias():
    db.create_all()
    seed_trabajadores()

    fecha_str = request.args.get('fecha') or datetime.now().strftime('%Y-%m-%d')
    try:
        dia = datetime.strptime(fecha_str, '%Y-%m-%d')
    except ValueError:
        dia = datetime.now()
        fecha_str = dia.strftime('%Y-%m-%d')

    dia_inicio = _inicio_del_dia(dia)
    dia_fin = _fin_del_dia(dia_inicio)
    es_hoy = fecha_str == datetime.now().strftime('%Y-%m-%d')

    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre_completo).all()
    tarjetas = []
    for t in trabajadores:
        est = estado_trabajador_hoy(t.id, dia_inicio)
        tarjetas.append({
            'trabajador': t,
            'registros': est['registros'],
            'puede_entrada': est['puede_entrada'] if es_hoy else False,
            'puede_salida': est['puede_salida'] if es_hoy else False,
            'en_jornada': est['en_jornada'],
        })

    registros_dia = (
        RegistroAsistencia.query.filter(
            RegistroAsistencia.fecha_hora >= dia_inicio,
            RegistroAsistencia.fecha_hora <= dia_fin,
        )
        .order_by(RegistroAsistencia.fecha_hora.desc())
        .all()
    )

    dentro = sum(1 for c in tarjetas if c['en_jornada'])
    entradas_hoy = sum(1 for r in registros_dia if r.tipo == 'entrada') if es_hoy else 0

    return render_template(
        'gestion_asistencias.html',
        tarjetas=tarjetas,
        registros_dia=registros_dia,
        fecha_consulta=fecha_str,
        es_hoy=es_hoy,
        fecha_actual=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        dentro=dentro,
        total_trabajadores=len(trabajadores),
        entradas_hoy=entradas_hoy,
    )


@app.route('/gestion/asistencias/registrar', methods=['POST'])
def registrar_asistencia_laboral():
    db.create_all()
    seed_trabajadores()

    trabajador_id = request.form.get('trabajador_id', type=int)
    tipo = request.form.get('tipo')

    if not trabajador_id or tipo not in RegistroAsistencia.TIPOS:
        flash('Datos de registro no válidos.', 'danger')
        return redirect(url_for('gestion_asistencias'))

    trabajador = Trabajador.query.filter_by(id=trabajador_id, activo=True).first()
    if not trabajador:
        flash('Trabajador no encontrado o inactivo.', 'danger')
        return redirect(url_for('gestion_asistencias'))

    est = estado_trabajador_hoy(trabajador_id)
    if tipo == 'entrada' and not est['puede_entrada']:
        flash(f'{trabajador.nombre_completo} ya tiene entrada registrada sin salida.', 'danger')
        return redirect(url_for('gestion_asistencias'))
    if tipo == 'salida' and not est['puede_salida']:
        flash(f'{trabajador.nombre_completo} debe registrar entrada antes de la salida.', 'danger')
        return redirect(url_for('gestion_asistencias'))

    ahora = datetime.now()
    registro = RegistroAsistencia(
        trabajador_id=trabajador_id,
        tipo=tipo,
        fecha_hora=ahora,
    )
    try:
        db.session.add(registro)
        db.session.commit()
        flash(
            f'{trabajador.nombre_completo}: {RegistroAsistencia.TIPOS[tipo]} registrada '
            f'a las {ahora.strftime("%H:%M:%S")} del {ahora.strftime("%d/%m/%Y")}.',
            'success',
        )
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar: {e}', 'danger')

    return redirect(url_for('gestion_asistencias'))


@app.route('/gestion/asistencias/registro/<int:registro_id>/eliminar', methods=['POST'])
def eliminar_registro_asistencia(registro_id):
    registro = RegistroAsistencia.query.get_or_404(registro_id)
    nombre = registro.trabajador.nombre_completo
    try:
        db.session.delete(registro)
        db.session.commit()
        flash(f'Registro de {nombre} eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {e}', 'danger')
    fecha = request.form.get('fecha') or datetime.now().strftime('%Y-%m-%d')
    return redirect(url_for('gestion_asistencias', fecha=fecha))


@app.route('/api/asistencias/export')
def api_asistencias_export():
    dias = request.args.get('dias', default=30, type=int)
    dias = max(1, min(dias or 30, 365))
    seed_trabajadores()
    ref_inicio = _inicio_del_dia(datetime.now() - timedelta(days=dias))
    ref_fin = _fin_del_dia(_inicio_del_dia())

    registros = (
        RegistroAsistencia.query.filter(
            RegistroAsistencia.fecha_hora >= ref_inicio,
            RegistroAsistencia.fecha_hora <= ref_fin,
        )
        .order_by(RegistroAsistencia.fecha_hora.desc())
        .all()
    )
    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre_completo).all()
    hoy_inicio = _inicio_del_dia()
    hoy_fin = _fin_del_dia(hoy_inicio)
    registros_hoy = [r for r in registros if hoy_inicio <= r.fecha_hora <= hoy_fin]

    return jsonify({
        'periodo': {
            'dias': dias,
            'desde': ref_inicio.strftime('%d/%m/%Y'),
            'hasta': datetime.now().strftime('%d/%m/%Y'),
        },
        'resumen': {
            'total_trabajadores': len(trabajadores),
            'registros_periodo': len(registros),
            'entradas_periodo': sum(1 for r in registros if r.tipo == 'entrada'),
            'salidas_periodo': sum(1 for r in registros if r.tipo == 'salida'),
            'dentro_hoy': sum(
                1 for t in trabajadores if estado_trabajador_hoy(t.id, hoy_inicio)['en_jornada']
            ),
            'entradas_hoy': sum(1 for r in registros_hoy if r.tipo == 'entrada'),
            'salidas_hoy': sum(1 for r in registros_hoy if r.tipo == 'salida'),
        },
        'trabajadores': [
            {'id': t.id, 'nombre': t.nombre_completo} for t in trabajadores
        ],
        'registros': [
            {
                'id': r.id,
                'trabajador_id': r.trabajador_id,
                'trabajador': r.trabajador.nombre_completo,
                'tipo': r.tipo,
                'tipo_label': r.tipo_label,
                'fecha': r.fecha_hora.strftime('%d/%m/%Y'),
                'hora': r.fecha_hora.strftime('%H:%M:%S'),
            }
            for r in registros
        ],
    })


@app.route('/descargar-excel-asistencias')
def descargar_excel_asistencias():
    dias = request.args.get('dias', default=30, type=int)
    hojas = _dataframes_asistencias_export(dias or 30)
    output = crear_workbook_corporativo_multihoja(hojas, hojas[0]['subtitulo'])
    fecha = datetime.now().strftime('%Y-%m-%d')
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'asistencia-laboral-{fecha}.xlsx',
    )


@app.route('/descargar-excel-clientes')
def descargar_excel_clientes():
    clientes = Cliente.query.all()
    data = []
    for cliente in clientes:
        nat_nombre = cliente.nat.nombre if cliente.nat else 'No asignado'
        data.append({
            'ID': cliente.id,
            'Nombre': cliente.nombre,
            'Dirección': cliente.direccion,
            'Plan': cliente.plan,
            'Contacto': cliente.contacto,
            'Activo': 'Sí' if cliente.activo else 'No',
            'NAP': nat_nombre,
        })

    df = pd.DataFrame(data)
    subtitulo = _excel_subtitulo_inventario()
    output = crear_workbook_corporativo_multihoja([
        {
            'sheet_name': 'Clientes',
            'df': df,
            'titulo': 'Reporte Ejecutivo de Clientes',
            'subtitulo': subtitulo,
        },
    ], subtitulo)
    fecha = datetime.now().strftime('%Y-%m-%d')

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'clientes-{fecha}.xlsx',
    )


@app.route('/descargar-excel-naps')
def descargar_excel_naps():
    naps = Nat.query.all()
    data = []
    for nap in naps:
        clientes_count = Cliente.query.filter_by(nat_id=nap.id, activo=True).count()
        porcentaje_uso = round((clientes_count / nap.puertos_total) * 100, 1) if nap.puertos_total > 0 else 0
        modelo_nombre = nap.modelo.nombre if nap.modelo else 'No especificado'
        modelo_tipo = (
            'Distribución' if nap.modelo and nap.modelo.tipo_caja == 'distribucion'
            else 'Empalme' if nap.modelo else 'No especificado'
        )
        data.append({
            'ID': nap.id,
            'Nombre': nap.nombre,
            'Tipo': modelo_tipo,
            'Puertos Totales': nap.puertos_total,
            'Puertos Usados': clientes_count,
            'Porcentaje Uso': f'{porcentaje_uso}%',
            'Hilo Conexión': nap.hilo_conexion,
            'Modelo': modelo_nombre,
            'Latitud': nap.latitud,
            'Longitud': nap.longitud,
        })

    df = pd.DataFrame(data)
    subtitulo = _excel_subtitulo_inventario()
    output = crear_workbook_corporativo_multihoja([
        {
            'sheet_name': 'Cajas NAP',
            'df': df,
            'titulo': 'Reporte Ejecutivo de Cajas NAP',
            'subtitulo': subtitulo,
        },
    ], subtitulo)
    fecha = datetime.now().strftime('%Y-%m-%d')

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'cajas-nap-{fecha}.xlsx',
    )


# ============================================
# CONFIGURACIÓN ADICIONAL PARA FLASK
# ============================================

# Agrega esto en tu configuración Flask (si no lo tienes)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo
#app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'json', 'xml'}

# Función auxiliar para verificar extensiones
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ----------------------------------------------------------------------
# MIDDLEWARE PARA DETECCIÓN MÓVIL
# ----------------------------------------------------------------------

@app.route('/health')
def health_check():
    if _db_config_error:
        return jsonify({'status': 'error', 'detail': _db_config_error}), 503
    return jsonify({'status': 'ok'})


@app.before_request
def require_database_config():
    if _db_config_error and request.endpoint not in ('health_check', 'static'):
        return (
            '<h1>Fibra Manager</h1>'
            f'<p><strong>Base de datos no configurada:</strong> {_db_config_error}</p>'
            '<p>En Vercel → Settings → Environment Variables, agrega '
            '<code>DATABASE_URL</code> o <code>DB_PASSWORD</code> y las variables de Supabase.</p>'
        ), 503


@app.before_request
def detect_mobile():
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone']
    
    request.is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
# ----------------------------------------------------------------------
# INICIO AUTOMÁTICO CON APERTURA DE NAVEGADOR
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# INICIO AUTOMÁTICO CON APERTURA DE NAVEGADOR
# ----------------------------------------------------------------------

if __name__ == '__main__':
    # Detectar si es .exe
    is_exe = getattr(sys, 'frozen', False)
    
    print("=" * 60)
    print("FIBRA MANAGER - INICIANDO SERVIDOR")
    print("=" * 60)
    
    if is_exe:
        print("MODO: Ejecutable (.exe)")
        print("URL: http://localhost:5000")
        print("=" * 60)
        
        # Abrir navegador automáticamente después de 1 segundo
        import threading
        import webbrowser
        import time
        
        def abrir_browser():
            time.sleep(1.5)
            webbrowser.open('http://localhost:5000')
        
        threading.Thread(target=abrir_browser, daemon=True).start()
    else:
        print("MODO: Desarrollo (Python)")
        print("URL: http://127.0.0.1:5000")
        print("=" * 60)
    
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1")).fetchone()
            total_clientes = Cliente.query.count()
            total_nats = Nat.query.count()
            db.create_all()
            print(f"Conexion OK | Clientes: {total_clientes} | Cajas: {total_nats}")
        except Exception as e:
            print(f"Advertencia BD: {e}")
    
    print("Rutas: /  /dashboard  /mapa_nats  /clientes  /nap_models")
    print("=" * 60)
    
    # Iniciar servidor
    try:
        app.run(
            debug=not is_exe,          # Debug solo en desarrollo
            host='0.0.0.0', 
            port=5000,
            use_reloader=not is_exe,   # Reloader solo en desarrollo
            threaded=True
        )
    except Exception as e:
        print(f"ERROR al iniciar servidor: {e}")
        print("Posibles causas:")
        print("   - Puerto 5000 en uso")
        print("   - Problemas de red")
        print("   - Firewall bloqueando")
        print("Soluciones:")
        print("   - Cierra otros programas usando puerto 5000")
        print("   - Prueba con: netstat -ano | findstr :5000")
        print("   - O ejecuta en otro puerto: port=5001")
        input("Presiona Enter para salir...")