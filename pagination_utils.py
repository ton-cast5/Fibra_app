"""Utilidades de paginación para listados y APIs."""
from flask import request

DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100
API_DEFAULT_PER_PAGE = 50


def paginacion_desde_request(default=DEFAULT_PER_PAGE, max_per=MAX_PER_PAGE):
    page = request.args.get('page', 1, type=int) or 1
    per_page = request.args.get('per_page', default, type=int) or default
    page = max(1, page)
    per_page = max(1, min(per_page, max_per))
    return page, per_page


def api_devolver_todo():
    """?all=1 conserva respuestas completas para exportaciones e inventario."""
    return request.args.get('all', '').lower() in ('1', 'true', 'yes')


def meta_paginacion(total, page, per_page):
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages else None,
    }


def paginar_query(query, page, per_page):
    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(max(1, page), pages)
    items = (
        query.offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, meta_paginacion(total, page, per_page)
