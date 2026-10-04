"""Autenticación: usuarios, login/logout, protección de rutas y cabeceras de seguridad."""
from datetime import timedelta
from urllib.parse import urlparse

from flask import (
    Blueprint, abort, flash, g, jsonify, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15
LONGITUD_MINIMA_PASSWORD = 10
DURACION_SESION = timedelta(hours=12)

ENDPOINTS_PUBLICOS = {'auth.login', 'static', 'health_check', 'service_worker', 'manifest'}
METODOS_SEGUROS = {'GET', 'HEAD', 'OPTIONS'}

# Hash de referencia para que un usuario inexistente tarde lo mismo que uno real.
_HASH_FALSO = generate_password_hash('fibra-manager-usuario-inexistente')


def _validar_password(password, confirmacion):
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        return f'La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres.'
    if password != confirmacion:
        return 'Las contraseñas no coinciden.'
    return None


def _destino_seguro(destino):
    if destino and destino.startswith('/') and not destino.startswith('//') and '\\' not in destino:
        return destino
    return None


def _quiere_json():
    return (
        request.path.startswith('/api/')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.accept_mimetypes.best == 'application/json'
    )


def init_auth(app, db, ahora, en_produccion):
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=en_produccion,
        PERMANENT_SESSION_LIFETIME=DURACION_SESION,
    )

    class Usuario(db.Model):
        __tablename__ = 'usuario'

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), unique=True, nullable=False)
        nombre = db.Column(db.String(120), nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)
        activo = db.Column(db.Boolean, nullable=False, default=True)
        intentos_fallidos = db.Column(db.Integer, nullable=False, default=0)
        bloqueado_hasta = db.Column(db.DateTime, nullable=True)
        ultimo_acceso = db.Column(db.DateTime, nullable=True)
        sesion_version = db.Column(db.Integer, nullable=False, default=1)
        creado_en = db.Column(db.DateTime, nullable=False, default=ahora)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
            # Cierra las sesiones abiertas con la contraseña anterior.
            self.sesion_version = (self.sesion_version or 0) + 1

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    bp = Blueprint('auth', __name__)

    def _iniciar_sesion(usuario):
        session.clear()
        session.permanent = True
        session['uid'] = usuario.id
        session['sv'] = usuario.sesion_version

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            if session.get('uid'):
                return redirect(url_for('dashboard'))
            return render_template('login.html', next=_destino_seguro(request.args.get('next')))

        username = (request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''
        destino = _destino_seguro(request.form.get('next'))
        usuario = Usuario.query.filter_by(username=username).first() if username else None
        momento = ahora()

        if usuario and usuario.bloqueado_hasta and usuario.bloqueado_hasta > momento:
            minutos = max(1, int((usuario.bloqueado_hasta - momento).total_seconds() // 60) + 1)
            flash(f'Demasiados intentos fallidos. Intenta de nuevo en {minutos} min.', 'danger')
            return render_template('login.html', next=destino, username=username), 429

        valido = usuario.check_password(password) if usuario else check_password_hash(_HASH_FALSO, password)
        if usuario and valido and usuario.activo:
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            usuario.ultimo_acceso = momento
            db.session.commit()
            _iniciar_sesion(usuario)
            return redirect(destino or url_for('dashboard'))

        if usuario:
            usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
            if usuario.intentos_fallidos >= MAX_INTENTOS:
                usuario.intentos_fallidos = 0
                usuario.bloqueado_hasta = momento + timedelta(minutes=MINUTOS_BLOQUEO)
            db.session.commit()
        flash('Usuario o contraseña incorrectos.', 'danger')
        return render_template('login.html', next=destino, username=username), 401

    @bp.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        flash('Sesión cerrada.', 'success')
        return redirect(url_for('auth.login'))

    @bp.route('/usuarios')
    def usuarios():
        lista = Usuario.query.order_by(Usuario.activo.desc(), Usuario.nombre).all()
        return render_template(
            'usuarios.html', usuarios=lista, longitud_minima=LONGITUD_MINIMA_PASSWORD, ahora=ahora(),
        )

    @bp.route('/usuarios/nuevo', methods=['POST'])
    def crear_usuario():
        username = (request.form.get('username') or '').strip().lower()
        nombre = (request.form.get('nombre') or '').strip()
        password = request.form.get('password') or ''
        error = _validar_password(password, request.form.get('password_confirmacion') or '')
        if not username or not nombre:
            error = 'Usuario y nombre son obligatorios.'
        elif len(username) > 50 or not username.replace('.', '').replace('_', '').replace('-', '').isalnum():
            error = 'El usuario solo puede tener letras, números, punto, guion y guion bajo.'
        elif Usuario.query.filter_by(username=username).first():
            error = f'El usuario "{username}" ya existe.'
        if error:
            flash(error, 'danger')
            return redirect(url_for('auth.usuarios'))

        nuevo = Usuario(username=username, nombre=nombre[:120])
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()
        flash(f'Usuario "{username}" creado.', 'success')
        return redirect(url_for('auth.usuarios'))

    @bp.route('/usuarios/<int:usuario_id>/activo', methods=['POST'])
    def cambiar_activo(usuario_id):
        usuario = db.get_or_404(Usuario, usuario_id)
        if usuario.id == g.usuario.id:
            flash('No puedes desactivar tu propio usuario.', 'danger')
            return redirect(url_for('auth.usuarios'))
        usuario.activo = not usuario.activo
        usuario.sesion_version += 1
        db.session.commit()
        estado = 'activado' if usuario.activo else 'desactivado'
        flash(f'Usuario "{usuario.username}" {estado}.', 'success')
        return redirect(url_for('auth.usuarios'))

    @bp.route('/usuarios/<int:usuario_id>/password', methods=['POST'])
    def cambiar_password(usuario_id):
        usuario = db.get_or_404(Usuario, usuario_id)
        es_propio = usuario.id == g.usuario.id
        if es_propio and not usuario.check_password(request.form.get('password_actual') or ''):
            flash('La contraseña actual no es correcta.', 'danger')
            return redirect(url_for('auth.usuarios'))
        password = request.form.get('password') or ''
        error = _validar_password(password, request.form.get('password_confirmacion') or '')
        if error:
            flash(error, 'danger')
            return redirect(url_for('auth.usuarios'))

        usuario.set_password(password)
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.session.commit()
        if es_propio:
            _iniciar_sesion(usuario)
        flash(f'Contraseña de "{usuario.username}" actualizada.', 'success')
        return redirect(url_for('auth.usuarios'))

    app.register_blueprint(bp)

    @app.before_request
    def proteger_rutas():
        if request.method not in METODOS_SEGUROS:
            origen = request.headers.get('Origin') or request.headers.get('Referer')
            if origen and urlparse(origen).netloc != request.host:
                abort(403)

        if request.endpoint in ENDPOINTS_PUBLICOS or request.endpoint is None:
            return None

        uid = session.get('uid')
        usuario = db.session.get(Usuario, uid) if uid else None
        if not usuario or not usuario.activo or usuario.sesion_version != session.get('sv'):
            session.clear()
            if _quiere_json():
                return jsonify({'error': 'Sesión expirada. Vuelve a iniciar sesión.'}), 401
            destino = request.full_path.rstrip('?') if request.method == 'GET' else None
            return redirect(url_for('auth.login', next=destino))
        g.usuario = usuario
        return None

    @app.after_request
    def cabeceras_seguridad(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        # Los servidores de mapas exigen Referer; a sitios externos solo se envía el dominio.
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        if en_produccion:
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.context_processor
    def usuario_actual():
        return {'usuario_actual': getattr(g, 'usuario', None)}

    return Usuario
