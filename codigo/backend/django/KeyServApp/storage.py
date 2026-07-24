"""
Almacenamiento privado para Documento — ver settings.PRIVATE_MEDIA_ROOT.

`base_url=None` es lo que importa acá: sin él, FileSystemStorage cae al
MEDIA_URL público por defecto. Con `base_url=None`, cualquier intento de
leer `documento.archivo_subido.url` levanta un error en vez de devolver
silenciosamente una URL que nadie protege — fuerza a pasar siempre por
`documento_descargar_view` (views.py), que es el único lugar que decide si
mostrar el archivo según quién lo pide.
"""
from django.conf import settings
from django.core.files.storage import FileSystemStorage

almacenamiento_documentos = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)
