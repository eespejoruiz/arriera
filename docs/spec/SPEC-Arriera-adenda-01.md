# Arriera · Adenda 01 al spec: API e integración con ERP, marca y licencia

**Versión:** 1.1 · 3 de noviembre de 2026
**Complementa a:** «Especificación de desarrollo · Sistema de gestión documental con IA» v1.0 (nombre de trabajo «Legajo»).
**Regla:** si esta adenda contradice al spec original, manda la adenda.

---

## 0. Decisiones tomadas con Enrique (3 nov 2026)

| Tema | Decisión |
|---|---|
| Nombre del producto | **Arriera** (reemplaza a «Legajo»). Prefijos técnicos: repositorio `arriera`, paquete `arriera`, QR `ARR1|…` en vez de `LGJ1|…`, buckets `arriera-*`. |
| Dominio | **arriera.tech** (DNS en Cloudflare, registrado en Hostinger). |
| Landing | En línea en https://arriera.tech, servida desde el VPS Vitrina (contenedor `arriera-web`, puerto interno 3740, ruta Traefik `routes.d/arriera.yaml` en Escudo). Fuente en `Personal/Arriera/landing`. |
| Nicho | Digitalización de archivos en papel. Sectores: fondos y mutuales (principal, caso FAMENSSALUD), salud, notarías y estudios, instituciones en general. |
| Identidad | Logo: escudo-documento con hormiga arriera calada (`Personal/Arriera/marca`). Tipografías: **Hanken Grotesk** (texto) + **Special Elite** (voz de la IA, efecto de máquina de escribir). Paleta oliva: noche `#11130C`, musgo `#1B1F13`, hoja `#A9B640`, lima `#DCE57A`, marfil `#F4F5EE`, óxido `#B4532A`. |
| Integración con ERP | **Entra en la v1.** Arriera se vende como módulo documental del ERP del cliente, no como sistema aislado. |
| Funciones del API | Las cuatro: enviar documentos, buscar y traer datos, avisos (webhooks) y visor embebido. |
| Conectores | Odoo, SAP Business One, ERP peruanos (Starsoft, Concar, Siscont y similares) y API genérico documentado. |
| Precio | **Módulo de integración con precio fijo.** Monto por definir (ver sección 10). |
| Marca en la interfaz | **El sistema mantiene su propia marca: nombre «Arriera», logo y paleta oliva.** No se personaliza con los colores ni el logo del cliente. El cliente aparece solo como titular de la instancia (su nombre en la barra lateral, en las actas y en las marcas de agua). Esto reemplaza la decisión 12 del spec original y la regla 6 de la sección 0 («la interfaz usa el logo y los colores del cliente»). |
| Licencia | **Licencia de uso limitada.** El cliente no puede revender, sublicenciar ni renombrar el sistema. Sí puede darle mantenimiento y hacerle mejoras. Ver sección 11. |
| Demo | Prototipo navegable en https://demo.arriera.tech (Motor, contenedor `arriera-demo`, puerto interno 3741, ruta Traefik `routes.d/arriera-demo.yaml`, con `noindex`). Fuente Next.js en `Personal/Arriera/prototipo`. |

**Cambios al spec original:**
- Sección 1.5: «Integraciones con ERP o sistemas del cliente» deja de estar fuera de alcance.
- Sección 6: el backend pasa a ser *API-first*. La web usa la API interna y los ERP usan la API pública `/v1`, con el mismo motor de permisos.
- Sección 15: se agrega el Sprint 6 (ver sección 8 de esta adenda).
- Sección 20: las decisiones 1 (nombre) y 12 (marca) quedan resueltas como se indica arriba.

---

## 1. Principios del API

1. **Mismos permisos que una persona.** Cada integración tiene un techo de permisos (serie × nivel de sensibilidad) que se aplica en el servidor y en el SQL, igual que para los usuarios (spec 2.2).
2. **N3 apagado por defecto.** Los datos de salud y otros sensibles no salen hacia un ERP salvo que el administrador lo habilite explícitamente y el oficial de datos personales lo apruebe (queda en la auditoría).
3. **Minimizar.** Los webhooks no llevan datos personales: avisan qué cambió y el ERP consulta con su credencial.
4. **Todo auditado.** Cada llamada queda en `audit_events` con `actor_type = integration`, el id de la integración y, si viene, el usuario del ERP.
5. **Contrato estable.** OpenAPI 3.1 publicado, versión en la ruta (`/v1`), cambios incompatibles solo en `/v2`.
6. **Idempotente.** Toda escritura acepta `Idempotency-Key`; reintentar no duplica documentos.

## 2. Autenticación y alcance

- **Integración:** registro en `integrations` (nombre, sistema: odoo | sap_b1 | starsoft | concar | siscont | generico, dominios permitidos para el visor, estado).
- **Llaves:** `ark_live_…` y `ark_test_…`. Se muestran una sola vez y se guarda solo el hash (HMAC con clave en secreto). Rotación sin corte (dos llaves vigentes durante la transición). Caducidad opcional y lista de IP permitidas opcional.
- **Alcances (scopes):** `documentos:escribir`, `documentos:leer`, `archivos:descargar`, `busqueda`, `personas:leer`, `expedientes:leer`, `webhooks:gestionar`, `embed:emitir`.
- **Techo de permisos:** `integration_grants` (serie o tipo documental × sensibilidad máxima, `puede_descargar`, `perfil_ocultamiento` por defecto).
- **Fase posterior (v1.x):** OAuth 2.0 *client credentials* para clientes que lo exijan.

## 3. Referencias del ERP

Tabla `external_refs (id, integration_id, sistema, entidad, id_externo, objeto_tipo, objeto_id)`. Liga personas, expedientes y documentos de Arriera con entidades del ERP; por ejemplo, `odoo · res.partner · 1842` → persona de Arriera. Permite consultar «todos los documentos del cliente 1842» sin conocer ids internos. Cuando llega un DNI, Arriera concilia con su índice por `dni_hash`.

## 4. Endpoints públicos `/v1`

Errores en formato *problem+json* (RFC 9457). Paginación por cursor. Fechas ISO 8601 en UTC.

| Método y ruta | Uso |
|---|---|
| `POST /v1/documentos` | Subir un documento (multipart, hasta 25 MB) con `referencia_erp`, `dni` opcional, `serie` o `tipo` sugeridos y `metadatos` libres. Responde `202` con `id` y `estado: recibido`. |
| `POST /v1/cargas` | Para archivos grandes o lotes: devuelve una URL firmada de subida y luego se confirma con `POST /v1/cargas/{id}/completar` (hash SHA-256 verificado). |
| `GET /v1/documentos/{id}` | Estado, tipo, fecha, campos extraídos con valor, confianza y página, versión vigente y hash. |
| `GET /v1/documentos` | Listar con filtros: `referencia_erp`, `persona`, `tipo`, `serie`, `estado`, `desde`, `hasta`, `actualizado_desde` (para sincronizar). |
| `GET /v1/documentos/{id}/archivo` | URL firmada de 60 s al PDF con marca de agua; `?ocultamiento=<perfil>` entrega la versión con datos ocultos. Requiere `archivos:descargar`. |
| `POST /v1/busqueda` | Búsqueda por filtros o en lenguaje natural (mismo motor que la web). Devuelve resultados, filtros interpretados y fragmentos. |
| `GET /v1/personas/{ref}` y `GET /v1/personas/{ref}/expedientes` | Persona por `referencia_erp` o id, y sus expedientes. |
| `GET /v1/expedientes/{id}` | Expediente con línea de tiempo y requisitos presentes y faltantes. |
| `POST /v1/referencias` | Ligar un objeto de Arriera a una entidad del ERP. |
| `GET/POST/DELETE /v1/webhooks` | Gestionar destinos de webhooks y sus eventos. |
| `POST /v1/webhooks/{id}/probar` | Envía un evento de prueba. |
| `POST /v1/embed/tokens` | Emite un token de visor (ver 6). |
| `GET /v1/estado` | Salud del servicio y versión, para monitoreo del ERP. |

**Límites por defecto:** 600 solicitudes por minuto y 10 cargas simultáneas por integración (configurables). Respuesta `429` con `Retry-After`.

## 5. Webhooks

- **Eventos:** `documento.recibido`, `documento.indexado`, `documento.requiere_validacion`, `documento.validado`, `documento.version_nueva`, `expediente.requisito_faltante`, `expediente.completo`, `lote.cerrado`, `depuracion.aprobada`.
- **Carga útil mínima:** `{ "evento", "id_evento", "fecha", "objeto": {"tipo","id"}, "referencia_erp" }`, sin datos personales.
- **Firma:** cabecera `Arriera-Firma: t=<timestamp>,v1=<HMAC-SHA256(secreto, t.cuerpo)>`. El receptor rechaza firmas con más de 5 minutos.
- **Entrega:** reintentos con espera exponencial durante 24 h; después queda «fallida» y se puede reenviar desde el panel. Tabla `webhook_deliveries` con intentos, código de respuesta y duración.

## 6. Visor embebido

- El ERP pide `POST /v1/embed/tokens` con el alcance (`persona`, `expediente` o `documento`), el usuario del ERP (`usuario_externo`) y el tiempo de vida (máximo 10 minutos).
- Arriera devuelve un token firmado de un solo uso. El ERP lo carga en un `iframe`: `https://<instancia>/embed/expediente/<id>?t=<token>`.
- El visor muestra la línea de tiempo, los requisitos, el visor de páginas y la búsqueda dentro del alcance, con los colores del cliente y sin la navegación de Arriera.
- Seguridad: `Content-Security-Policy: frame-ancestors` limitado a los dominios declarados en la integración; sesión del visor separada; cada vista queda en la auditoría con el usuario del ERP.

## 7. Conectores

| Conector | Cómo se conecta | Qué hace | Riesgos y supuestos |
|---|---|---|---|
| **Odoo 16, 17 y 18** | Addon `arriera_connector` (Python) instalado en el Odoo del cliente. | Configuración de URL y llave; botón inteligente «Documentos» y pestaña con el visor embebido en contactos (`res.partner`), facturas (`account.move`) y empleados (`hr.employee`); envío automático de adjuntos (`ir.attachment`) según reglas por modelo; los webhooks dejan una nota en el *chatter*. | Definir la licencia del addon (propietaria u LGPL). Probar en Odoo Community y Enterprise. Montar un Odoo de pruebas propio con DATOS DEMO; nunca usar el Odoo de un cliente (por ejemplo, el de Amazon Andes) como banco de pruebas. |
| **SAP Business One** | Servicio puente del lado de Arriera que usa el **Service Layer** (REST) de SAP B1. | Sincroniza socios de negocio y adjuntos (`Attachments2`) y publica en SAP el enlace al visor de Arriera. | Requiere SAP B1 10.0 o superior con Service Layer habilitado y un usuario técnico; un add-on de interfaz se cotiza aparte. |
| **ERP peruanos** (Starsoft, Concar, Siscont y similares) | Agente puente instalado en la red del cliente. | Lee vistas o tablas autorizadas de la base de datos (normalmente SQL Server) o archivos de exportación (CSV o XML) y carpetas de adjuntos, y sincroniza con el API. | Suelen ser sistemas de escritorio sin API pública: el conector depende de la versión y del acceso a la base de datos. Se cotiza tras un diagnóstico de una visita. Validar términos de uso de cada proveedor. |
| **Genérico** | API REST `/v1`. | Documentación OpenAPI, colección de Postman y ejemplos en cURL, Python y JavaScript. | Se sugiere publicar la documentación en `docs.arriera.tech`. |

## 8. Plan de trabajo

- **Semanas 1 a 5:** sin cambios, según el spec. Se agrega una condición: desde el Sprint 0, todo endpoint nuevo se diseña con su versión pública en mente (mismos servicios y permisos).
- **Sprint 6 · semana 6: API pública e integración.**
  - Integraciones, llaves, alcances y techo de permisos, con pruebas positivas y negativas.
  - Endpoints `/v1` de documentos, cargas, búsqueda, personas, expedientes y referencias.
  - Webhooks firmados con reintentos y panel de entregas.
  - Visor embebido con tokens y `frame-ancestors`.
  - OpenAPI publicado, colección de Postman y página de documentación.
  - **Conector Odoo** funcionando contra un Odoo de pruebas con DATOS DEMO.
  - **Criterio:** desde Odoo se sube un adjunto, aparece indexado en Arriera, el webhook marca el *chatter* y la ficha del contacto muestra el visor; una integración sin N3 no obtiene un informe médico por ninguna ruta.
- **Sprint 7 en adelante, o por cliente:** conector SAP Business One y conectores de ERP peruanos, después de un diagnóstico del entorno del cliente.

**Sobre FAMENSSALUD:** su pase a producción sigue en la semana 5. El módulo de integración no forma parte de su propuesta de S/ 9,900; se les ofrece aparte si lo necesitan.

## 9. Modelo de datos nuevo

- `integrations (id, nombre, sistema, dominios_embed[], estado, creado_por, created_at)`
- `api_keys (id, integration_id, prefijo, hash, entorno: live|test, ultimo_uso_at, expira_at, revocada_at, ip_permitidas[])`
- `integration_grants (integration_id, classification_node_id | document_type_id, max_sensitivity, puede_descargar, perfil_ocultamiento_id)`
- `external_refs (id, integration_id, sistema, entidad, id_externo, objeto_tipo, objeto_id, unique(integration_id, entidad, id_externo))`
- `webhook_endpoints (id, integration_id, url, eventos[], secreto_enc, activo)`
- `webhook_deliveries (id, endpoint_id, evento, id_evento, intento, estado, codigo_http, duracion_ms, siguiente_intento_at, created_at)`
- `embed_tokens (jti, integration_id, alcance, objeto_id, usuario_externo, expira_at, usado_at)`
- `idempotency_keys (integration_id, clave, hash_solicitud, respuesta, created_at)`, que se purgan a las 24 h.
- `audit_events`: se agregan `actor_type (user|integration|station|system)`, `integration_id` y `usuario_externo`.

## 10. Precio y decisiones abiertas

1. **Monto del módulo de integración** (precio fijo). Hay que definir qué incluye: API más webhooks más visor, ¿con el conector Odoo? ¿SAP B1 y peruanos con precio propio?
2. **Orden de conectores después de Odoo:** SAP B1 o un ERP peruano, según el primer cliente que lo pida.
3. **Licencia del addon de Odoo:** propietaria o LGPL-3.
4. **Documentación pública:** ¿`docs.arriera.tech` abierta o solo para clientes?
5. **OAuth 2.0** en la v1 o en la v1.x.
6. **Ajuste de la landing:** cuando haya precio, publicarlo en la sección «Integraciones» y en «Planes».

## 11. Marca y licencia de uso (reemplaza la sección 19 del spec original)

**Lo que decidió Enrique:**
- Arriera es un producto con marca propia. Todas las instancias se ven igual (nombre, logo, paleta y tipografías de Arriera).
- Cada cliente recibe una **licencia de uso limitada**:
  - **No puede** revender, sublicenciar, alquilar ni ceder el sistema a terceros.
  - **No puede** renombrarlo, quitarle la marca Arriera ni presentarlo como propio.
  - **Sí puede** darle mantenimiento y hacerle mejoras, con su equipo o con terceros, para su uso interno.
- Enrique conserva la titularidad del software y el derecho de seguir vendiéndolo a otros clientes.

**Implementación en el sistema:**
- Marca fija en el código: la configuración `settings.marca` solo permite el nombre del cliente y su logo para las actas, no cambia los colores ni el nombre del producto.
- Pie de cada pantalla, acta y exportación: «Arriera · licenciado a <cliente>».
- Archivo `LICENSE` propietario en el repositorio y aviso de licencia en el manual técnico.

**Puntos que conviene validar con un abogado antes de firmar:**
1. **Choque con la propuesta enviada a FAMENSSALUD.** La propuesta dice que «el código fuente, el sistema y los datos quedan a nombre del Fondo». Puede leerse como una cesión de la propiedad del software. Conviene aclarar en el contrato: los **datos** y la **infraestructura** son del Fondo; el **software** es de Enrique y se entrega con su código fuente bajo licencia de uso limitada.
2. **Mejoras hechas por el cliente.** Definir si Enrique puede incorporarlas al producto (por ejemplo, con una licencia de vuelta) o si quedan solo para el cliente.
3. **Mantenimiento por terceros.** Si un tercero toca el código, que firme confidencialidad y quede sujeto a la misma licencia.
4. **Plazo y alcance:** licencia perpetua, no exclusiva e intransferible, limitada a una instancia y a la razón social del cliente.

> Las referencias legales del spec original siguen vigentes: compartir datos con un ERP también es tratamiento de datos personales. Validar con un abogado el registro de destinatarios y el flujo de datos sensibles.
