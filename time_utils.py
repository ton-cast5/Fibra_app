"""Utilidades de fecha/hora — zona horaria de México (America/Mexico_City)."""
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    TZ_MEXICO = ZoneInfo('America/Mexico_City')
except Exception:
    # Fallback: México Central (UTC-6, sin horario de verano desde 2022)
    TZ_MEXICO = timezone(timedelta(hours=-6))


def ahora_mexico():
    """Hora actual en Ciudad de México como datetime naive (para guardar y mostrar)."""
    return datetime.now(TZ_MEXICO).replace(tzinfo=None)


def inicio_del_dia_mexico(fecha=None):
    ref = fecha or ahora_mexico()
    return ref.replace(hour=0, minute=0, second=0, microsecond=0)


def fin_del_dia_mexico(inicio):
    return inicio.replace(hour=23, minute=59, second=59, microsecond=999999)


def parsear_fecha_mexico(valor):
    """Interpreta fecha/hora enviada por el cliente como hora de México (naive)."""
    if not valor:
        return ahora_mexico()
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)

    texto = str(valor).strip().replace('Z', '')
    formatos = (
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    )
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            try:
                return datetime.strptime(texto[: len(fmt)], fmt)
            except ValueError:
                continue
    return ahora_mexico()
