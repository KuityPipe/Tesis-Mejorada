"""
Almacenamiento privado para Documento — ver settings.PRIVATE_MEDIA_ROOT.

El archivo vive en PRIVATE_MEDIA_ROOT, fuera de MEDIA_ROOT: nada lo sirve por URL.
Ojo: `base_url=None` NO hace que `.url` falle (Django cae a MEDIA_URL y devuelve
`/media/...`, una ruta que no existe en disco → 404). La protección real es la
ubicación, más pasar siempre por una vista que decide según quién pide
(`documento_descargar_view`, `valoracion_imagen_view`, `ContratacionMensajeImagenView`).
"""
from django.conf import settings
from django.core.files.storage import FileSystemStorage

almacenamiento_documentos = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)
