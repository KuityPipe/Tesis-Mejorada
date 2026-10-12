# Análisis del PDF de Tesis — KeyServ

Fuente: `docs/plantilla/Plantilla_Tesis.pdf` (238 páginas). **Importante:** a pesar del nombre del archivo, este NO es una plantilla vacía — es el informe de tesis completo entregado a INACAP ("Informe Proyecto Seminario de Grado", Abril 2023), con todo el contenido técnico del proyecto KeyServ. Las referencias `(PAGE N)` corresponden al número de página que asignó el extractor de texto (portadas + numeración romana al inicio hacen que no coincida 1:1 con la numeración impresa del documento).

## 1. Resumen ejecutivo

KeyServ es una plataforma web de intermediación de servicios (cuidado de niños, remodelaciones, reparaciones del hogar, etc.) cuyo diferenciador es la **verificación biométrica obligatoria** (huella dactilar + reconocimiento facial) de clientes y proveedores, para combatir estafas en la contratación informal de servicios en Chile (PAGE 12, 17-21). El objetivo general es "aumentar la satisfacción del cliente hasta en un 90%" (PAGE 12) mediante autenticidad verificada. **Por decisión explícita de los autores, KeyServ NO incluye compra/venta de productos, solo contratación de servicios** (PAGE 38): *"el sitio web KeyServ por el momento no tiene la opción de compra y venta de productos"*.

## 2. Requisitos funcionales

Extraídos de la sección IEEE 830 (PAGE 124-127):

| ID | Nombre | Descripción resumida | Prioridad |
|---|---|---|---|
| RF001 | Verificación de registro | Registro validado por huella, Face ID o clave única | Muy alta |
| RF002 | Creación de perfiles | Perfil con experiencia, habilidades, áreas de servicio | Alta |
| RF003 | Iniciar sesión | Login estándar | Alta |
| RF004 | Búsqueda de servicios | Buscar publicaciones de otros usuarios | Alta |
| RF005 | Cerrar sesión | — | Media |
| RF006 | Inicio de sesión obligatorio | Requerido para funciones principales | Alta |
| RF007 | Correcto funcionamiento | Sin errores de enlace entre botones | Alta |
| RF008 | Almacenamiento | Guardar cuentas en base de datos | Alta |
| RF009 | Interfaz progresiva | Responsive, compatible con navegadores actuales | Alta |
| RF010 | Contratación de servicios | Contratar proveedores con términos y condiciones | Media |
| RF011 | Manipulación de la web sin sesión | Navegar sin cuenta (salvo función principal) | Media |
| RF012 | **Gestión de pagos** | "Api de pago asociada" — pagos seguros según tipo de usuario | Media |

**Nota:** el código actual (`codigo/backend/django/KeyServApp/`) solo implementa registro (`register_view`) y carga AJAX de comunas (`load_comunas`) — ver `docs/CODE_ANALYSIS_FINDINGS.md`. RF003–RF012 no tienen vista Django funcional hoy.

## 3. Requisitos no funcionales

(PAGE 128-133)

| ID | Nombre | Descripción | Prioridad |
|---|---|---|---|
| RNF001 | Inicio de sesión igualitario | Mismo flujo intuitivo para cliente/proveedor/premium/lite/admin | Alta |
| RNF002 | Tiempo de respuesta | < 5 segundos por operación | Media |
| RNF003 | Usabilidad | Usuario productivo en < 1 día | Media |
| RNF004 | Compatibilidad web | Adaptable a PC, tablet, móvil | Alta |
| RNF005 | Seguridad de datos | Confidencialidad de datos personales y transacciones financieras | Media |
| RNF006 | Diseño del sistema | Paleta llamativa (blanco, azul, celeste) | Media |
| RNF007 | Almacenamiento | Soportar gran volumen de información | Alta |
| RNF008 | Idioma | Español (traducible a futuro) | Alta |
| RNF009 | Manejo de errores | Mensajes de error claros | Alta |
| RNF010 | Contraseña | Mínimo 6 caracteres | Alta |
| RNF011 | Tipos de usuario válidos | Mayor de edad, RUT válido, contraseña correcta | Alta |
| RNF012 | Rendimiento | Tiempos de carga óptimos | Alta |
| RNF013 | Disponibilidad | Casi 24/7 (excepto mantención) | Alta |
| RNF014 | Escalabilidad | Soportar crecimiento de usuarios/transacciones sin degradar | Alta |

**Discrepancia de seguridad crítica:** RNF010 exige contraseña mínima de 6 caracteres **sin exigir complejidad**, y el código actual hashea con SHA-256 **sin salt** (confirmado en `models.py`, `Usuario.save()`) — cumple la letra del requisito de la tesis, pero el requisito mismo ya es débil para 2026; conviene endurecerlo en la Fase 3.

## 4. Restricciones del proyecto

(PAGE 133-134) — estas son literalmente las decisiones de stack que ya están reflejadas en el código actual:

- Frontend: HTML, CSS3, JavaScript.
- Backend: **Django** (framework obligatorio, coincide con `codigo/backend/django/`).
- Base de datos: **MySQL**.
- Hosting: servidores de **AWS**.
- IDE: Visual Studio Code 1.79.
- Tiempo de respuesta: **no debe exceder 3 segundos** por operación (más estricto que RNF002 de 5s — usar 3s como objetivo).
- Seguridad: **cifrado SSL/TLS** obligatorio cliente-servidor (no implementado hoy — `DEBUG=True`, sin HTTPS configurado).
- Compatibilidad: Chrome, Firefox, Safari, Edge (últimas versiones).
- Diseño responsivo para móviles y tablets.

## 5. Integraciones requeridas (biometría, gobierno, pagos, otras)

De la cadena de valor y arquitectura tecnológica (PAGE 10-11, 27):

| Integración | Detalle en el PDF | Estado en el código |
|---|---|---|
| **Biometría — huella dactilar** | Método de verificación obligatorio en registro (RF001) | `codigo/biometria/huella/IMAGEN_HUELLA.py` — funcional standalone, pero no conectado a Django |
| **Biometría — reconocimiento facial** | Segundo método de verificación (RF001), wireframe "Reconocimiento facial" (PAGE 170) | `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` — **archivo corrupto**, no ejecutable |
| **ChileGob / Clave Única** | "Se realizará un convenio con ChileGob para poder comprobar la identidad del usuario mediante el sistema de clave única" + firma electrónica (PAGE 11); SLA dedicado "Servicio de Comprobación de Identidad" con "chilegob" como proveedor responsable (PAGE 51); proveedor listado: **e-certchile** | **No existe ninguna integración en el código.** Ni llamadas a API de ClaveÚnica, ni a e-certchile, en ningún archivo Python del repo. |
| **Pagos** | RF012 "Api de pago asociada"; proveedores listados: **Transbank** y **PayPal** (PAGE 11) | No existe ningún cliente de pago en el código. Sí existe un template huérfano `tarjeta credito.html` (0 bytes, vacío) en `codigo/backend/django/.../templates/` y en `assets/mockups/pag_html/` — la pantalla fue mockeada pero nunca implementada ni con contenido. |
| **SII (acreditación tributaria)** | Mencionado en OLA de oficina virtual, "Acreditación en el SII" (PAGE 51) | Es una obligación administrativa de la empresa, no una integración de software — no aplica al código. |

## 6. Modelo de datos según el PDF

El diccionario de datos (PAGE 129-137+) describe, entre otras, las tablas: `usuario`, `usuario_administrativo`, `usuario_conversacion`, `valoracion`, `autentificacion`, `comuna`, `consulta`, `conversacion`, `django_session`, `documento`, `estado_autentificacion`, `estado_consulta` (la lectura se detuvo antes de cubrir el diccionario completo de las ~24 tablas por extensión, pero el patrón de nombres y columnas coincide exactamente con el `models.py` real).

**Coincidencia confirmada con el código:** los nombres de tabla/columna en mayúsculas con prefijo `FK_`/`ID_` que aparecen en `codigo/backend/django/KeyServApp/models.py` son una traducción directa y fiel de este diccionario de datos — el modelo de datos SÍ se implementó como fue diseñado en la tesis. Esto es una señal fuerte de que el trabajo de base de datos está completo y no requiere rediseño, solo depuración (ver hallazgo de doble hasheo de contraseña en `docs/CODE_ANALYSIS_FINDINGS.md`).

**Tabla `django_session` está en el diccionario de datos** — indica que los autores ya contemplaban usar el sistema de sesiones nativo de Django (`django.contrib.sessions`), consistente con usar Django como framework de autenticación en vez de reinventar sesiones a mano.

## 7. Diagramas y procesos (BPMN/UML)

Todos los diagramas están embebidos como imágenes en el PDF (no extraíbles como texto); se listan por descripción y página:

- **BPMN "AS IS"** (PAGE 39): proceso actual de contratación de servicios sin KeyServ — cliente y proveedor negocian sin verificación, terminando a veces sin acuerdo o con resultado no esperado.
- **BPMN "TO BE" parte 1 y 2** (PAGE 40-41): proceso propuesto con KeyServ — mismos actores, pero ahora registrados y validados por el sistema antes de poder contratar.
- **BPMN — proceso "Crear perfil"** (PAGE 134): registro → espera aprobación → repetición hasta satisfacción.
- **BPMN — proceso "Login"** (PAGE 135): ingreso de cuenta → validación de credenciales → éxito o recuperación de contraseña vía validación de contacto.
- **BPMN — proceso "Crear publicación"** (PAGE 135-136): usuario validado crea publicación → enviada a moderador → aprobada o rechazada. **Implica un rol de moderador/aprobación de contenido que no existe en el código actual** (no hay campo de estado de moderación en `Publicaciones`, ni vista de admin para aprobar/rechazar).
- **BPMN — "Proceso de contratación"** (PAGE 136-137, "anexado por superar el tamaño de la hoja"): colaborador en espera → match con cliente → ambos se re-autentican → tras el trabajo, calificación por estrellas + reseña/foto. Coincide con los modelos `Valoracion`/`Ranking` existentes.
- **UML — Casos de uso**: "Registro e inicio de sesión", "Publicar y contratar servicios", "Visita y creación de perfiles", "Página de inicio", "Página principal con sesión iniciada", "Mensajería" (PAGE 137-141) — actores: Cliente y Proveedor de servicios.
- **UML — Diseño estructural (componentes/interacción)**: sección 1.3.5 mencionada en la tabla de contenido pero sin contenido desarrollado en el cuerpo (título solo, PAGE 142) — **no se llegó a diseñar formalmente**, útil saberlo si se quiere generar este diagrama recién ahora sobre el código real.

## 8. Casos de uso / flujos de usuario

Dos actores: **Cliente** y **Proveedor de servicios** (colaborador). Flujos descritos en texto (no solo diagrama):

1. Registro con verificación biométrica (huella o facial) → aprobación → reintento si falla.
2. Login con validación de credenciales → recuperación de contraseña vía validación de contacto si falla.
3. Creación de publicación de servicio → moderación → aprobación/rechazo.
4. Match cliente-proveedor → re-autenticación de ambos → contratación → calificación final por estrellas + reseña/foto tras completar el trabajo.

## 9. Especificaciones de UI/UX

**Árbol de contenido** (PAGE 161): título mencionado, sin desarrollo textual explícito más allá del wireframing.

**Wireframes listados** (PAGE 161-170, imágenes): página de inicio con/sin sesión, login, crear publicación, registro de usuario, "Acerca de nosotros", contacto, ingreso de info de usuario, avisos en página principal, preferencias de cuenta, recuperar contraseña, detalle de servicios contratados, búsqueda de servicios, **transacciones de pago**, perfil de usuario, publicación de servicio, **ingreso de huella digital**, **reconocimiento facial**. Esta lista coincide casi 1:1 con los archivos HTML que ya existen en `assets/mockups/pag_html/` y `codigo/backend/django/.../templates/`.

**Guía de estilos** (PAGE 171-172):
- Paleta: encabezados Powder Blue `#B0E0E6`, texto negro `#000000`, botones Cornflower Blue `#6495ED`, enlaces azul oscuro `#0000FF`.
- Tipografía: Arial/sans-serif para todo (títulos en negrita).
- Iconografía: estilo "plano", celeste y negro.
- Navegación: menú desplegable horizontal, barra de búsqueda centrada arriba.
- Imágenes: calidad HD, formatos JPEG/PNG/GIF.
- Diseño responsivo con reajuste automático de elementos.

**Discrepancia:** no verifiqué contra el CSS real si esta paleta se aplicó consistentemente — recomendado como chequeo rápido en Fase 3 (los nombres de archivo CSS existen por página, no hay una hoja de estilos global/design system).

## 10. Endpoints/APIs mencionados

El PDF no especifica rutas HTTP concretas (no es una tesis con documentación de API tipo OpenAPI/Swagger). Lo único explícito es:
- RF012 menciona "Api de pago asociada" sin nombrar el proveedor de API en el requisito (los proveedores Transbank/PayPal aparecen solo en la sección de arquitectura, PAGE 11).
- El "Servicio de Comprobación de Identidad" contra ChileGob se describe como acceso a "una base de datos gubernamental" (PAGE 51) sin detalle técnico de API/protocolo (no se menciona OAuth, SAML, ni el endpoint real de ClaveÚnica).

Esto significa que **la integración de pagos y de ChileGob quedaron a nivel de intención/documentación de negocio, sin especificación técnica de API** — cualquier implementación futura deberá investigar las APIs reales de Transbank (Webpay Plus) y del proveedor de ClaveÚnica desde cero.

## 11. Requisitos de rendimiento y KPIs

- Objetivo general: elevar satisfacción del cliente **hasta 90%** (PAGE 12, resumen).
- Objetivos específicos (PAGE 52): aumentar adquisición de servicios **10% mensual**; disminuir desconfianza **20%**; **100% de clientes verificados biométricamente**; disminuir tiempo de consecución de un proveedor (métrica cortada en la extracción, sin número final visible).
- Restricción técnica: tiempo de respuesta **≤ 3 segundos** por operación (más estricta que RNF002 de 5s).
- RNF013: disponibilidad "casi 24/7" excepto mantención — sin SLA numérico (no se especifica 99.9% ni similar).
- No hay requisitos de carga/concurrencia (usuarios simultáneos, throughput) especificados en ninguna parte del documento — es una omisión notable para un sistema pensado para escalar.

## 12. Metodología de desarrollo (Scrum)

(PAGE 172-173) Se evaluaron metodologías tradicionales, XP, Lean, Kanban y Scrum; se eligió **Scrum** por adaptabilidad y capacidad de iterar rápido. El documento no detalla la cadencia real de sprints ni el backlog, pero sí hay evidencia externa consistente: el historial de commits del repo (`TesisAntigua/repositories/SrKuity/ProyectoTesis.git`, y la nomenclatura de commits descrita en PAGE 185: `"YYYY-MM-DD Nombre del responsable"`) confirma que se usó GitHub con convención de mensajes de commit por fecha+autor, que es justamente el patrón visto en el `git log` real del repo (`2023-06-03 Felipe`, etc.).

Control de versiones descrito explícitamente (PAGE 185): repositorio original `https://github.com/SrKuity/ProyectoTesis` — coincide con el backup encontrado en `TesisAntigua/repositories/SrKuity/ProyectoTesis.git` de la Fase 1.

Plan de pruebas (PAGE 200-201+): pruebas de software definidas para registro biométrico (PT-001), login (PT-002), crear/editar/eliminar publicación (PT-003 a PT-005) con formato ID/Descripción/Resultado esperado/Responsable — **ninguna de estas pruebas tiene equivalente automatizado en el código** (`tests.py` está vacío en el proyecto Django).

## 13. Discrepancias PDF vs. código actual

Esta es la sección más importante para priorizar la Fase 3:

| # | Lo que el PDF promete/diseña | Lo que existe hoy en `codigo/` |
|---|---|---|
| 1 | RF001: registro con verificación biométrica obligatoria (huella o facial) antes de poder usar el sistema | `register_view` en Django **no invoca ni huella ni reconocimiento facial** — es un registro de formulario plano con hash SHA-256; los scripts de biometría existen pero corren aislados, sin integración HTTP con Django |
| 2 | RF003/RF005/RF006: login/logout funcionales | **No existe vista de login/logout en Django** (`sesion_view` existe pero solo renderiza el template, no autentica) |
| 3 | RF004/RF010: búsqueda y contratación de servicios | **No implementado** — no hay vista para listar/buscar `Publicaciones`, ni flujo de contratación |
| 4 | RF012: gestión de pagos vía Transbank/PayPal | **No implementado en absoluto** — cero código de integración de pagos, el template de pago está vacío |
| 5 | Integración ChileGob / Clave Única / firma electrónica | **No implementado en absoluto** — no hay ninguna mención a ClaveÚnica ni e-certchile en el código |
| 6 | Reconocimiento facial (PT-001, wireframe dedicado) | El único script existente (`probando_face_recognition.py`) está **corrupto** (byte-dump, no es Python válido) |
| 7 | Biometría de huella dactilar | `IMAGEN_HUELLA.py` es funcional como script standalone, pero **no está conectado a la app Django** ni a un endpoint HTTP |
| 8 | Flujo de moderación de publicaciones (BPMN "Crear publicación") | No hay campo de estado de moderación en el modelo `Publicaciones`, ni panel de administración para aprobar/rechazar |
| 9 | Mensajería (caso de uso UML) | Modelos `Mensaje`/`Conversacion` existen en la base de datos, pero no hay vistas ni endpoints de chat implementados |
| 10 | RNF010 (seguridad de contraseña) y cifrado SSL/TLS (restricción) | Contraseñas hasheadas con SHA-256 **sin salt**, y **`DEBUG=True`** + `SECRET_KEY` hardcodeado, sin HTTPS configurado — no cumple el espíritu de "prácticas de seguridad estándar" de la restricción del PDF |
| 11 | Plan de pruebas formal (PT-001 a PT-005+) | `tests.py` vacío, cero automatización de pruebas |

**Conclusión clave:** la tesis diseñó un sistema considerablemente más completo de lo que el código implementa. El código actual cubre, en el mejor de los casos, el ~15-20% de los requisitos funcionales documentados (esencialmente solo RF002/RF008: creación de perfil y almacenamiento de usuario). Las features de mayor valor diferencial para el negocio — biometría end-to-end, pagos, e integración gubernamental — existen únicamente como diseño/documentación, no como código funcional. Esto debe ser el eje central del roadmap de la Fase 3.
