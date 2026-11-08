"""API JSON versionada /api/v1 para la app Android (auth, CRUD y sync offline)."""
from datetime import datetime
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 días
TOKEN_SALT = 'tonylex-api-v1'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def emitir_token(usuario):
    return _serializer().dumps({'uid': usuario.id, 'sv': usuario.sesion_version})


def verificar_token(token, Usuario):
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    usuario = Usuario.query.get(data.get('uid'))
    if not usuario or not usuario.activo:
        return None
    if usuario.sesion_version != data.get('sv'):
        return None
    return usuario


def _iso(dt):
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _parse_since(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace('Z', '+00:00').replace('+00:00', ''))
    except ValueError:
        return None


def init_api_v1(app, db, Usuario, models, ahora):
    """models: dict con NapModel, Nat, Cliente, Potencia, Trabajador, RegistroAsistencia, Archivo."""
    NapModel = models['NapModel']
    Nat = models['Nat']
    Cliente = models['Cliente']
    Potencia = models['Potencia']
    Trabajador = models['Trabajador']
    RegistroAsistencia = models['RegistroAsistencia']
    Archivo = models['Archivo']

    bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

    def require_api_auth(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            usuario = getattr(g, 'usuario', None)
            if not usuario:
                auth = request.headers.get('Authorization', '')
                token = auth[7:].strip() if auth.lower().startswith('bearer ') else None
                if token:
                    usuario = verificar_token(token, Usuario)
                    if usuario:
                        g.usuario = usuario
            if not usuario:
                return jsonify({'error': 'No autorizado'}), 401
            return fn(*args, **kwargs)
        return wrapper

    # ----- serialización -----
    def ser_nap_model(m):
        return {
            'id': m.id,
            'nombre': m.nombre,
            'tipo_caja': m.tipo_caja,
            'capacidad_max': m.capacidad_max,
            'imagen_url': m.imagen_url,
        }

    def ser_nat(n):
        return {
            'id': n.id,
            'nombre': n.nombre,
            'latitud': n.latitud,
            'longitud': n.longitud,
            'descripcion': n.descripcion,
            'region': n.region,
            'puertos_total': n.puertos_total,
            'hilo_conexion': n.hilo_conexion,
            'nap_model_id': n.nap_model_id,
            'tipo_caja': n.tipo_caja,
        }

    def ser_cliente(c):
        return {
            'id': c.id,
            'nombre': c.nombre,
            'direccion': c.direccion,
            'plan': c.plan,
            'contacto': c.contacto,
            'ip': c.ip,
            'servicio': c.servicio,
            'activo': bool(c.activo),
            'nat_id': c.nat_id,
        }

    def ser_potencia(p):
        return {
            'id': p.id,
            'fecha': _iso(p.fecha),
            'cliente_id': p.cliente_id,
            'nap_id': p.nap_id,
            'potencia_entrada': p.potencia_entrada,
            'potencia_salida': p.potencia_salida,
            'perdida': p.perdida,
            'estado': p.estado,
            'observaciones': p.observaciones,
            'tecnico': p.tecnico,
            'equipo_medicion': p.equipo_medicion,
        }

    def ser_trabajador(t):
        return {
            'id': t.id,
            'nombre_completo': t.nombre_completo,
            'apellido_paterno': t.apellido_paterno,
            'apellido_materno': t.apellido_materno,
            'activo': bool(t.activo),
            'nfc_uid': t.nfc_uid,
        }

    def ser_asistencia(r):
        return {
            'id': r.id,
            'trabajador_id': r.trabajador_id,
            'tipo': r.tipo,
            'fecha_hora': _iso(r.fecha_hora),
        }

    def ser_archivo(a):
        return {
            'id': a.id,
            'nombre': a.nombre,
            'nombre_original': a.nombre_original,
            'extension': a.extension,
            'tamano': a.tamano,
            'fecha_subida': _iso(a.fecha_subida),
            'categoria': a.categoria,
            'etiquetas': a.etiquetas,
            'descripcion': a.descripcion,
            'url_storage': a.url_storage,
            'fecha_actualizacion': _iso(a.fecha_actualizacion),
        }

    # ----- auth -----
    @bp.route('/auth/login', methods=['POST'])
    def login():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip().lower()
        password = data.get('password') or ''
        usuario = Usuario.query.filter_by(username=username).first() if username else None
        if not usuario or not usuario.activo or not usuario.check_password(password):
            return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401
        usuario.ultimo_acceso = ahora()
        db.session.commit()
        token = emitir_token(usuario)
        return jsonify({
            'token': token,
            'user': {
                'id': usuario.id,
                'username': usuario.username,
                'nombre': usuario.nombre,
            },
        })

    @bp.route('/auth/logout', methods=['POST'])
    @require_api_auth
    def logout():
        # Token es stateless; el cliente debe borrarlo. Invalidación fuerte = cambio de password.
        return jsonify({'ok': True})

    @bp.route('/auth/me', methods=['GET'])
    @require_api_auth
    def me():
        u = g.usuario
        return jsonify({'id': u.id, 'username': u.username, 'nombre': u.nombre})

    # ----- nap models -----
    @bp.route('/nap-models', methods=['GET'])
    @require_api_auth
    def list_nap_models():
        rows = NapModel.query.order_by(NapModel.nombre).all()
        return jsonify({'data': [ser_nap_model(m) for m in rows]})

    @bp.route('/nap-models', methods=['POST'])
    @require_api_auth
    def create_nap_model():
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'error': 'nombre requerido'}), 400
        m = NapModel(
            nombre=nombre[:100],
            tipo_caja=data.get('tipo_caja') or 'distribucion',
            capacidad_max=data.get('capacidad_max'),
            imagen_url=data.get('imagen_url'),
        )
        db.session.add(m)
        db.session.commit()
        return jsonify(ser_nap_model(m)), 201

    @bp.route('/nap-models/<int:item_id>', methods=['PUT', 'PATCH'])
    @require_api_auth
    def update_nap_model(item_id):
        m = db.get_or_404(NapModel, item_id)
        data = request.get_json(silent=True) or {}
        for field in ('nombre', 'tipo_caja', 'capacidad_max', 'imagen_url'):
            if field in data:
                setattr(m, field, data[field])
        db.session.commit()
        return jsonify(ser_nap_model(m))

    @bp.route('/nap-models/<int:item_id>', methods=['DELETE'])
    @require_api_auth
    def delete_nap_model(item_id):
        m = db.get_or_404(NapModel, item_id)
        db.session.delete(m)
        db.session.commit()
        return jsonify({'ok': True})

    # ----- nats / cajas -----
    @bp.route('/nats', methods=['GET'])
    @require_api_auth
    def list_nats():
        rows = Nat.query.order_by(Nat.nombre).all()
        return jsonify({'data': [ser_nat(n) for n in rows]})

    @bp.route('/nats', methods=['POST'])
    @require_api_auth
    def create_nat():
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'error': 'nombre requerido'}), 400
        n = Nat(
            nombre=nombre[:100],
            latitud=data.get('latitud'),
            longitud=data.get('longitud'),
            descripcion=data.get('descripcion'),
            region=data.get('region'),
            puertos_total=int(data.get('puertos_total') or 8),
            hilo_conexion=data.get('hilo_conexion'),
            nap_model_id=data.get('nap_model_id'),
        )
        db.session.add(n)
        db.session.commit()
        return jsonify(ser_nat(n)), 201

    @bp.route('/nats/<int:item_id>', methods=['PUT', 'PATCH'])
    @require_api_auth
    def update_nat(item_id):
        n = db.get_or_404(Nat, item_id)
        data = request.get_json(silent=True) or {}
        for field in (
            'nombre', 'latitud', 'longitud', 'descripcion', 'region',
            'puertos_total', 'hilo_conexion', 'nap_model_id',
        ):
            if field in data:
                setattr(n, field, data[field])
        db.session.commit()
        return jsonify(ser_nat(n))

    @bp.route('/nats/<int:item_id>', methods=['DELETE'])
    @require_api_auth
    def delete_nat(item_id):
        n = db.get_or_404(Nat, item_id)
        db.session.delete(n)
        db.session.commit()
        return jsonify({'ok': True})

    # ----- clientes -----
    @bp.route('/clientes', methods=['GET'])
    @require_api_auth
    def list_clientes():
        rows = Cliente.query.order_by(Cliente.nombre).all()
        return jsonify({'data': [ser_cliente(c) for c in rows]})

    @bp.route('/clientes', methods=['POST'])
    @require_api_auth
    def create_cliente():
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        direccion = (data.get('direccion') or '').strip()
        nat_id = data.get('nat_id')
        if not nombre or not direccion or not nat_id:
            return jsonify({'error': 'nombre, direccion y nat_id son requeridos'}), 400
        c = Cliente(
            nombre=nombre[:150],
            direccion=direccion,
            plan=data.get('plan'),
            contacto=data.get('contacto'),
            ip=data.get('ip'),
            servicio=data.get('servicio'),
            activo=bool(data.get('activo', True)),
            nat_id=int(nat_id),
        )
        db.session.add(c)
        db.session.commit()
        return jsonify(ser_cliente(c)), 201

    @bp.route('/clientes/<int:item_id>', methods=['PUT', 'PATCH'])
    @require_api_auth
    def update_cliente(item_id):
        c = db.get_or_404(Cliente, item_id)
        data = request.get_json(silent=True) or {}
        for field in ('nombre', 'direccion', 'plan', 'contacto', 'ip', 'servicio', 'activo', 'nat_id'):
            if field in data:
                setattr(c, field, data[field])
        db.session.commit()
        return jsonify(ser_cliente(c))

    @bp.route('/clientes/<int:item_id>', methods=['DELETE'])
    @require_api_auth
    def delete_cliente(item_id):
        c = db.get_or_404(Cliente, item_id)
        db.session.delete(c)
        db.session.commit()
        return jsonify({'ok': True})

    # ----- potencias -----
    @bp.route('/potencias', methods=['GET'])
    @require_api_auth
    def list_potencias():
        q = Potencia.query.order_by(Potencia.fecha.desc())
        since = _parse_since(request.args.get('updated_since'))
        if since:
            q = q.filter(Potencia.fecha >= since)
        rows = q.limit(int(request.args.get('limit') or 500)).all()
        return jsonify({'data': [ser_potencia(p) for p in rows]})

    @bp.route('/potencias', methods=['POST'])
    @require_api_auth
    def create_potencia():
        data = request.get_json(silent=True) or {}
        try:
            entrada = float(data['potencia_entrada'])
            salida = float(data['potencia_salida'])
            cliente_id = int(data['cliente_id'])
        except (KeyError, TypeError, ValueError):
            return jsonify({'error': 'cliente_id, potencia_entrada y potencia_salida requeridos'}), 400
        p = Potencia(
            cliente_id=cliente_id,
            nap_id=data.get('nap_id'),
            potencia_entrada=entrada,
            potencia_salida=salida,
            observaciones=data.get('observaciones'),
            tecnico=data.get('tecnico'),
            equipo_medicion=data.get('equipo_medicion'),
            fecha=ahora(),
        )
        p.calcular_perdida()
        p.determinar_estado()
        db.session.add(p)
        db.session.commit()
        return jsonify(ser_potencia(p)), 201

    @bp.route('/potencias/<int:item_id>', methods=['PUT', 'PATCH'])
    @require_api_auth
    def update_potencia(item_id):
        p = db.get_or_404(Potencia, item_id)
        data = request.get_json(silent=True) or {}
        for field in (
            'cliente_id', 'nap_id', 'potencia_entrada', 'potencia_salida',
            'observaciones', 'tecnico', 'equipo_medicion',
        ):
            if field in data:
                setattr(p, field, data[field])
        p.calcular_perdida()
        p.determinar_estado()
        db.session.commit()
        return jsonify(ser_potencia(p))

    @bp.route('/potencias/<int:item_id>', methods=['DELETE'])
    @require_api_auth
    def delete_potencia(item_id):
        p = db.get_or_404(Potencia, item_id)
        db.session.delete(p)
        db.session.commit()
        return jsonify({'ok': True})

    # ----- asistencias -----
    @bp.route('/trabajadores', methods=['GET'])
    @require_api_auth
    def list_trabajadores():
        rows = Trabajador.query.order_by(Trabajador.nombre_completo).all()
        return jsonify({'data': [ser_trabajador(t) for t in rows]})

    @bp.route('/asistencias', methods=['GET'])
    @require_api_auth
    def list_asistencias():
        q = RegistroAsistencia.query.order_by(RegistroAsistencia.fecha_hora.desc())
        since = _parse_since(request.args.get('updated_since'))
        if since:
            q = q.filter(RegistroAsistencia.fecha_hora >= since)
        rows = q.limit(int(request.args.get('limit') or 500)).all()
        return jsonify({'data': [ser_asistencia(r) for r in rows]})

    @bp.route('/asistencias', methods=['POST'])
    @require_api_auth
    def create_asistencia():
        data = request.get_json(silent=True) or {}
        try:
            trabajador_id = int(data['trabajador_id'])
            tipo = data.get('tipo') or 'entrada'
        except (KeyError, TypeError, ValueError):
            return jsonify({'error': 'trabajador_id requerido'}), 400
        if tipo not in RegistroAsistencia.TIPOS:
            return jsonify({'error': 'tipo inválido'}), 400
        r = RegistroAsistencia(
            trabajador_id=trabajador_id,
            tipo=tipo,
            fecha_hora=ahora(),
        )
        db.session.add(r)
        db.session.commit()
        return jsonify(ser_asistencia(r)), 201

    @bp.route('/asistencias/<int:item_id>', methods=['DELETE'])
    @require_api_auth
    def delete_asistencia(item_id):
        r = db.get_or_404(RegistroAsistencia, item_id)
        db.session.delete(r)
        db.session.commit()
        return jsonify({'ok': True})

    # ----- documentos (metadatos) -----
    @bp.route('/documentos', methods=['GET'])
    @require_api_auth
    def list_documentos():
        rows = Archivo.query.order_by(Archivo.fecha_subida.desc()).limit(500).all()
        return jsonify({'data': [ser_archivo(a) for a in rows]})

    # ----- resumen inventario / reportes -----
    @bp.route('/resumen', methods=['GET'])
    @require_api_auth
    def resumen():
        total_nats = Nat.query.count()
        total_clientes = Cliente.query.count()
        clientes_activos = Cliente.query.filter_by(activo=True).count()
        total_potencias = Potencia.query.count()
        return jsonify({
            'total_nats': total_nats,
            'total_clientes': total_clientes,
            'clientes_activos': clientes_activos,
            'total_potencias': total_potencias,
            'total_nap_models': NapModel.query.count(),
            'total_trabajadores': Trabajador.query.filter_by(activo=True).count(),
            'server_time': _iso(ahora()),
        })

    # ----- sync -----
    @bp.route('/sync/pull', methods=['GET'])
    @require_api_auth
    def sync_pull():
        since = _parse_since(request.args.get('updated_since'))
        pot_q = Potencia.query.order_by(Potencia.fecha.desc())
        asis_q = RegistroAsistencia.query.order_by(RegistroAsistencia.fecha_hora.desc())
        if since:
            pot_q = pot_q.filter(Potencia.fecha >= since)
            asis_q = asis_q.filter(RegistroAsistencia.fecha_hora >= since)

        payload = {
            'server_time': _iso(ahora()),
            'nap_models': [ser_nap_model(m) for m in NapModel.query.order_by(NapModel.id).all()],
            'nats': [ser_nat(n) for n in Nat.query.order_by(Nat.id).all()],
            'clientes': [ser_cliente(c) for c in Cliente.query.order_by(Cliente.id).all()],
            'potencias': [ser_potencia(p) for p in pot_q.limit(1000).all()],
            'trabajadores': [ser_trabajador(t) for t in Trabajador.query.order_by(Trabajador.id).all()],
            'asistencias': [ser_asistencia(r) for r in asis_q.limit(1000).all()],
            'documentos': [ser_archivo(a) for a in Archivo.query.order_by(Archivo.id).all()],
            # Sin updated_at en tablas base: snapshot completo de maestros; deltas en potencias/asistencias.
            'full_snapshot': since is None,
        }
        return jsonify(payload)

    def _apply_mutation(mut):
        """Aplica una mutación del outbox. Retorna (ok, result_dict)."""
        entity = (mut.get('entity') or '').lower()
        op = (mut.get('op') or '').lower()
        data = mut.get('data') or {}
        remote_id = mut.get('remote_id') or data.get('id')

        try:
            if entity == 'nat':
                if op == 'create':
                    n = Nat(
                        nombre=(data.get('nombre') or 'SIN-NOMBRE')[:100],
                        latitud=data.get('latitud'),
                        longitud=data.get('longitud'),
                        descripcion=data.get('descripcion'),
                        region=data.get('region'),
                        puertos_total=int(data.get('puertos_total') or 8),
                        hilo_conexion=data.get('hilo_conexion'),
                        nap_model_id=data.get('nap_model_id'),
                    )
                    db.session.add(n)
                    db.session.flush()
                    return True, {'id': n.id, 'entity': entity}
                if op == 'update' and remote_id:
                    n = Nat.query.get(int(remote_id))
                    if not n:
                        return False, {'error': 'nat no encontrado'}
                    for field in (
                        'nombre', 'latitud', 'longitud', 'descripcion', 'region',
                        'puertos_total', 'hilo_conexion', 'nap_model_id',
                    ):
                        if field in data:
                            setattr(n, field, data[field])
                    return True, {'id': n.id, 'entity': entity}
                if op == 'delete' and remote_id:
                    n = Nat.query.get(int(remote_id))
                    if n:
                        db.session.delete(n)
                    return True, {'id': remote_id, 'entity': entity, 'deleted': True}

            if entity == 'cliente':
                if op == 'create':
                    c = Cliente(
                        nombre=(data.get('nombre') or '')[:150],
                        direccion=data.get('direccion') or '',
                        plan=data.get('plan'),
                        contacto=data.get('contacto'),
                        ip=data.get('ip'),
                        servicio=data.get('servicio'),
                        activo=bool(data.get('activo', True)),
                        nat_id=int(data['nat_id']),
                    )
                    db.session.add(c)
                    db.session.flush()
                    return True, {'id': c.id, 'entity': entity}
                if op == 'update' and remote_id:
                    c = Cliente.query.get(int(remote_id))
                    if not c:
                        return False, {'error': 'cliente no encontrado'}
                    for field in ('nombre', 'direccion', 'plan', 'contacto', 'ip', 'servicio', 'activo', 'nat_id'):
                        if field in data:
                            setattr(c, field, data[field])
                    return True, {'id': c.id, 'entity': entity}
                if op == 'delete' and remote_id:
                    c = Cliente.query.get(int(remote_id))
                    if c:
                        db.session.delete(c)
                    return True, {'id': remote_id, 'entity': entity, 'deleted': True}

            if entity == 'potencia':
                if op == 'create':
                    p = Potencia(
                        cliente_id=int(data['cliente_id']),
                        nap_id=data.get('nap_id'),
                        potencia_entrada=float(data['potencia_entrada']),
                        potencia_salida=float(data['potencia_salida']),
                        observaciones=data.get('observaciones'),
                        tecnico=data.get('tecnico'),
                        equipo_medicion=data.get('equipo_medicion'),
                        fecha=ahora(),
                    )
                    p.calcular_perdida()
                    p.determinar_estado()
                    db.session.add(p)
                    db.session.flush()
                    return True, {'id': p.id, 'entity': entity}
                if op == 'update' and remote_id:
                    p = Potencia.query.get(int(remote_id))
                    if not p:
                        return False, {'error': 'potencia no encontrada'}
                    for field in (
                        'cliente_id', 'nap_id', 'potencia_entrada', 'potencia_salida',
                        'observaciones', 'tecnico', 'equipo_medicion',
                    ):
                        if field in data:
                            setattr(p, field, data[field])
                    p.calcular_perdida()
                    p.determinar_estado()
                    return True, {'id': p.id, 'entity': entity}
                if op == 'delete' and remote_id:
                    p = Potencia.query.get(int(remote_id))
                    if p:
                        db.session.delete(p)
                    return True, {'id': remote_id, 'entity': entity, 'deleted': True}

            if entity == 'asistencia':
                if op == 'create':
                    r = RegistroAsistencia(
                        trabajador_id=int(data['trabajador_id']),
                        tipo=data.get('tipo') or 'entrada',
                        fecha_hora=ahora(),
                    )
                    db.session.add(r)
                    db.session.flush()
                    return True, {'id': r.id, 'entity': entity}
                if op == 'delete' and remote_id:
                    r = RegistroAsistencia.query.get(int(remote_id))
                    if r:
                        db.session.delete(r)
                    return True, {'id': remote_id, 'entity': entity, 'deleted': True}

            if entity == 'nap_model':
                if op == 'create':
                    m = NapModel(
                        nombre=(data.get('nombre') or '')[:100],
                        tipo_caja=data.get('tipo_caja') or 'distribucion',
                        capacidad_max=data.get('capacidad_max'),
                        imagen_url=data.get('imagen_url'),
                    )
                    db.session.add(m)
                    db.session.flush()
                    return True, {'id': m.id, 'entity': entity}
                if op == 'update' and remote_id:
                    m = NapModel.query.get(int(remote_id))
                    if not m:
                        return False, {'error': 'modelo no encontrado'}
                    for field in ('nombre', 'tipo_caja', 'capacidad_max', 'imagen_url'):
                        if field in data:
                            setattr(m, field, data[field])
                    return True, {'id': m.id, 'entity': entity}
                if op == 'delete' and remote_id:
                    m = NapModel.query.get(int(remote_id))
                    if m:
                        db.session.delete(m)
                    return True, {'id': remote_id, 'entity': entity, 'deleted': True}

            return False, {'error': f'operación no soportada: {entity}/{op}'}
        except Exception as exc:
            return False, {'error': str(exc)}

    @bp.route('/sync/push', methods=['POST'])
    @require_api_auth
    def sync_push():
        body = request.get_json(silent=True) or {}
        mutations = body.get('mutations') or []
        results = []
        for mut in mutations:
            client_id = mut.get('client_id') or mut.get('local_id')
            ok, detail = _apply_mutation(mut)
            results.append({
                'client_id': client_id,
                'ok': ok,
                **detail,
            })
            if not ok:
                db.session.rollback()
                return jsonify({
                    'ok': False,
                    'server_time': _iso(ahora()),
                    'results': results,
                }), 409
        db.session.commit()
        return jsonify({
            'ok': True,
            'server_time': _iso(ahora()),
            'results': results,
        })

    @app.before_request
    def _api_v1_bearer_auth():
        if not request.path.startswith('/api/v1/'):
            return None
        if request.endpoint in ('api_v1.login',):
            return None
        auth = request.headers.get('Authorization', '')
        if auth.lower().startswith('bearer '):
            usuario = verificar_token(auth[7:].strip(), Usuario)
            if usuario:
                g.usuario = usuario
        return None

    app.register_blueprint(bp)
    return bp
