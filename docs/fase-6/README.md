# Fase 6 — Rediseño visual "Confianza cálida"

> Propuesta aprobada el 2026-10-13: [`propuesta-visual.html`](propuesta-visual.html) (maqueta interactiva). Dirección: profesional
> pero cercano, conservando la identidad azul marino / verde azulado / coral, **todas las pantallas**, solo en español por ahora.
> Copia de seguridad para volver atrás: tag git `pre-rediseno-fase-6` (ver abajo).

## Cómo volver a la apariencia anterior

- **Código:** `git checkout pre-rediseno-fase-6 -- codigo/frontend/ionic` y luego commit + push (Netlify republica).
- **Rápido, sin tocar código:** en Netlify → Deploys, abre un deploy anterior al 2026-10-13 y pulsa **Publish deploy**.
- Los cambios son solo de frontend (HTML/SCSS y algunos componentes); el backend y la base de datos no cambiaron en esta fase.

## Qué se hizo

| Área | Resultado |
|---|---|
| Accesibilidad | `lang="es"`, zoom permitido (antes bloqueado), foco visible, `prefers-reduced-motion`, `aria-label` en controles sin texto, contraste AA (botones verdes `#0C7F6D`) |
| Aprovechar el ancho | Páginas de secciones en 2 columnas balanceadas (`ks-content-cols`), layouts principal + lateral (`ks-layout-main-side`), bento grid en inicio, ficha fija en el detalle de servicio |
| Inicio | Bento grid con propuesta de valor, búsqueda, cifras de confianza, cómo funciona y CTA para proveedores |
| Acceso | Login, registro y recuperar con panel de marca + formulario (registro en rejilla de 2 columnas) |
| Verificación | Las tres vías comparten columna lateral (opciones + qué hacemos con tus datos) y la animación de éxito (anillo + visto) |
| Otras pantallas | Detalle de servicio, mensajes (con consejos de seguridad), publicar (vista previa fija), editar perfil (atajos), catálogo (insignia de identidad verificada) |
| Modo noche | Tarjetas de marca con colores fijos, logo sobre pastilla clara |
| Veracidad del texto | Se quitó "huella dactilar" donde ya no es cierto; copy alineado con las tres vías de verificación reales |
| Robustez | Imágenes rotas se ocultan sin dejar huecos; presupuestos de estilos por componente ampliados |

## Ajuste "estilo 2026" (2026-10-13, a pedido del dueño)

Tras ver el resultado, se pidió menos "cuadrado", el menú en el extremo derecho, pantalla auto-ajustable e imágenes de fondo con
texto, tomando como referencia las técnicas de ideve.cl:
- **Header a todo el ancho** con el menú y la cuenta en el extremo derecho, efecto vidrio; el contenido se adapta al ancho (hasta 1520 px).
- **Inicio inmersivo:** hero a pantalla completa con fondo generado (degradados + malla de líneas), tarjetas de vidrio flotantes, tira de
  palabras en movimiento, secciones numeradas (01 / 02...), tarjetas de categorías con ícono grande de fondo y texto encima, banda
  a sangre con ilustración de línea y texto, pasos con números grandes.
- **Banners de página oscuros** con brillo y malla en todas las pantallas internas; esquinas más redondeadas (28 px) y sombras difusas.
- **Fotos libres de derechos (CC0):** paisaje de montaña en el hero, lago en la banda y una foto por oficio en las 12 tarjetas de
  categorías y en las publicaciones demo (`assets/fotos/`, créditos en `docs/CREDITOS_IMAGENES.md`); más dibujos propios en `assets/fondos/`.
  Se cambian con las variables CSS `--ks-hero-foto` / `--ks-banda-foto`.
- **Datos de prueba:** `sembrar_datos_demo` ahora crea 24 proveedores de 24 oficios (profesores, programadora, ama de casa, jardinero,
  carpintero, cuidado de personas, cocina, contador, mecánico...), con reseñas variadas. Cada publicación lo avisa: texto de aviso en la
  descripción, etiqueta `DEMO` sobre la foto y un aviso en el detalle (la API marca `es_demo` a las cuentas `@demo.keyserv`).

## Qué NO se hizo (y por qué)

- **Textos en inglés (i18n ES/EN):** decisión del dueño, por ahora solo español.
- **Migración a componentes standalone y signals:** las ~30 páginas siguen en NgModule. Migrarlas ruta por ruta es un cambio
  estructural de riesgo sin efecto visible; se deja como trabajo aparte para no mezclarlo con el rediseño.
- **View Transitions del router:** `ion-router-outlet` ya anima las transiciones; duplicarlas chocaría (ver `plan-ajustes.md`).
- **`@defer`:** no se aplicó; el rendimiento actual no lo exige y requiere la migración a standalone para sacarle provecho.

- **Capturas en modo noche y de todas las pantallas autenticadas en el README:** solo se agregaron el inicio y el asistente.

## Verificación

Backend sin cambios. Frontend: 95 tests unitarios, build de producción, suite E2E (10) y revisión visual con capturas en
escritorio (1440 px) y móvil (390 px), modo claro y noche, de las pantallas principales.
