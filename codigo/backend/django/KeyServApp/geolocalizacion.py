"""
Geolocalización aproximada por IP para IntentoAccesoSospechoso.

Usa una base DB-IP City Lite LOCAL (ver management command
`descargar_geoip`), no un servicio externo — no se manda la IP de nadie a
un tercero en cada evento sospechoso, solo se consulta un archivo en disco.
Se eligió DB-IP sobre MaxMind GeoLite2 porque no exige crear una cuenta ni
generar una license key para descargarla (GeoLite2 sí, desde 2020) — una
cuenta de terceros es algo que solo el usuario puede crear, no algo que se
pueda automatizar acá.

Licencia CC-BY 4.0 de DB-IP: exige atribución donde se muestren resultados
— ver el pie del panel de IntentoAccesoSospechoso en /admin/ y en
templates/admin/_panel_aprobaciones.html.

Degrada con gracia si la base no está descargada (ej. clon nuevo del repo
antes de correr `manage.py descargar_geoip`, o `GEOIP_HABILITADO=False`):
`geolocalizar_ip` devuelve (None, None) en vez de reventar.
"""
import ipaddress
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

_lector = None
_ya_se_intento_cargar = False


def _obtener_lector():
    global _lector, _ya_se_intento_cargar
    if _ya_se_intento_cargar:
        return _lector
    _ya_se_intento_cargar = True

    if not getattr(settings, 'GEOIP_HABILITADO', False):
        return None

    ruta = getattr(settings, 'GEOIP_DB_PATH', None)
    if not ruta or not os.path.exists(ruta):
        logger.info('GEOIP_HABILITADO=True pero no se encontró la base en %s — correr "manage.py descargar_geoip".', ruta)
        return None

    try:
        import geoip2.database
        _lector = geoip2.database.Reader(ruta)
    except ImportError:
        logger.warning('GEOIP_HABILITADO=True pero el paquete "geoip2" no está instalado (pip install geoip2).')
    except Exception:
        logger.exception('No se pudo abrir la base GeoIP en %s', ruta)

    return _lector


def geolocalizar_ip(ip):
    """
    Devuelve (pais, ciudad) para `ip`, o (None, None) si no se puede
    determinar — IP privada/loopback (todo el desarrollo local cae acá,
    127.0.0.1 no geolocaliza a ningún lado real), base no disponible, o IP
    no encontrada en la base.
    """
    if not ip:
        return None, None

    try:
        if ipaddress.ip_address(ip).is_private:
            return None, None
    except ValueError:
        return None, None

    lector = _obtener_lector()
    if not lector:
        return None, None

    try:
        resultado = lector.city(ip)
    except Exception:
        return None, None

    return resultado.country.name, resultado.city.name
