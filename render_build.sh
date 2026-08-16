#!/usr/bin/env bash
# Build command del servicio backend en Render (ver render.yaml, demo
# desplegado — docs/PLAN_PORTAFOLIO.md Nivel 2.2). Corre una sola vez por
# deploy, desde la raíz del repo (mismo layout que requirements*.txt).
#
# Orden importa: `migrate` aplica la migración 0027 (coordenadas de las 9
# comunas geocodificadas) antes de que exista la fila de Comuna real —
# `loaddata` después la sobreescribe (bug real, encontrado con
# SembrarDatosDemoCommandTests) porque el fixture original no trae
# latitud/longitud. `sembrar_datos_demo` reaplica esas mismas coordenadas él
# mismo al arrancar, así que este orden es seguro pase lo que pase.
set -o errexit

pip install -r requirements-render.txt

cd codigo/backend/django

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py loaddata catalogos_iniciales
python manage.py sembrar_datos_demo
