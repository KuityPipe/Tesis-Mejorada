# codigo/database/

El esquema real de KeyServ lo gestionan las migraciones de Django
(`codigo/backend/django/KeyServApp/migrations/0001_initial.py`), no un
script SQL a mano — esta carpeta existe como referencia/onboarding, no como
fuente de verdad.

`schema.sql` (SQL plano generado desde la migración) **todavía no se generó**:
requiere una conexión viva a Postgres (`manage.py sqlmigrate` la necesita
para leer la tabla de historial de migraciones), y no hay ningún servidor
Postgres corriendo en el entorno donde se hizo este refactor. Para generarlo
una vez que tengas Postgres disponible (local o en la nube — ver
`docs/SETUP_INSTRUCTIONS.md`):

```powershell
cd codigo/backend/django
python manage.py migrate          # crea las tablas reales
python manage.py sqlmigrate KeyServApp 0001 > ../../database/schema.sql
```

Ver `docs/DATABASE_DOCUMENTATION.md` para la documentación de tablas y
relaciones (esa sí está completa, generada a mano a partir de `models.py`).
