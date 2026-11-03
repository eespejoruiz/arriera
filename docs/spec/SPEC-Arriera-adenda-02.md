# Arriera · Adenda 02 al spec: precios, microformas y roadmap del benchmark

**Versión:** 1.2 · 3 de noviembre de 2026
**Complementa a:** el spec v1.0 y la adenda 01.
**Regla:** si esta adenda contradice al spec o a la adenda 01, manda esta adenda.
**Origen:** benchmark de mercado del 3 nov 2026 (doc «Arriera · Benchmark y propuesta de valor») y decisiones de Enrique ese mismo día.

---

## 1. Decisiones

| Tema | Decisión |
|---|---|
| Modelo de cobro | Dos planes por institución, nunca por usuario (sección 2). Reemplaza el esquema «pago único + bolsas de horas de soporte». |
| Usuarios | Usuarios de consulta ilimitados en los dos planes. |
| Titular del software | **Anomaly LA S.A.C.** es la titular del software y de la licencia (LICENSE). Aparece solo en la licencia y en los contratos; la marca pública sigue siendo Arriera, sin mención en la landing ni en el sistema. |
| Valor legal | Línea de microformas propia, pero **la certificación (NTP 392.030-2) se tramita cuando un cliente la exija**. El modo microformas del software se construye completo en el Sprint 3. Mientras no haya línea certificada, el lote queda listo para que el fedatario de un tercero lo convierta en microforma. |
| Mensaje principal | Titular: «Tu archivo en papel, indexado por IA y listo para microformas». Bajada: «Diez años de papel, encontrados en segundos». |
| Alcance funcional | Se adopta todo lo que los competidores hacen mejor, incluidos el OCR multilenguaje, el editor de flujos sin código y la automatización tipo RPA (sección 4). |
| Prioridad | El modo microformas y el panel de la Ley 29733 van antes del asistente. |

## 2. Planes (montos sin IGV)

| | Pago único | Mensual |
|---|---|---|
| Al iniciar | S/ 9,900 (50% al iniciar, 50% al pasar a producción) | S/ 3,400 |
| Cada mes | Mantenimiento **opcional** S/ 400: actualizaciones, parches de seguridad, copias vigiladas y hasta 5 h de soporte | S/ 800: servidor dedicado, copias diarias, actualizaciones y soporte |
| Servidor | Lo paga el cliente al proveedor (US$ 20–40 al mes), a nombre de la institución | Incluido; lo operamos nosotros |
| IA | Con la cuenta y la llave del cliente | Con la cuenta y la llave del cliente |
| Licencia | De uso, permanente y limitada (adenda 01, sección 11) | De uso mientras esté vigente la suscripción |
| Permanencia | — | 12 meses. Después puede pasar al pago único abonando S/ 6,500 |
| Salida | — | Se entregan los documentos en PDF y el índice completo exportado; luego se apaga la instancia |

- **Digitalización por página**, adicional a cualquier plan: S/ 0.18 hasta 50 mil páginas, S/ 0.16 hasta 150 mil y S/ 0.14 desde ahí.
- **Garantía:** 3 meses en los dos planes.
- La landing ya no ofrece «código fuente a tu nombre»; se alinea con la licencia de uso limitada.
- **Pendiente:** precio del módulo de integración con ERP (adenda 01, sección 10).

Referencia del costo para el cliente (solo sistema; el pago único sin servidor): primer año S/ 14,700 con mantenimiento contra S/ 13,000 en el mensual; a 3 años S/ 24,300 contra S/ 32,200; a 5 años S/ 33,900 contra S/ 51,400. Desde el mes 17 el mensual sale más caro.

**Impacto en el producto:** el plan mensual exige operar instancias de clientes. Arriera actúa como encargado del tratamiento de datos personales (Ley 29733), lo que pide un contrato de encargo y un registro de incidentes. Cada instancia sigue siendo dedicada a un solo cliente (spec, sección 6).

## 3. Microformas con línea propia

- **Marco:** DL 681 y sus modificatorias, DL 827, NTP 392.030-2:2015, Ley 27269 de firmas y certificados digitales, y las directivas del AGN para eliminar originales.
- **Qué se certifica:** la organización que administra el sistema de producción y almacenamiento de microformas: local, equipos, personal, procedimientos y software. El software solo no basta.
- **El fedatario informático sigue siendo obligatorio** por lote: actas de apertura y cierre, conformidad y firma digital.
- **Certificación:** se tramita cuando un cliente la exija. Antes de contratar a la certificadora, verificar en el directorio de INACAL que esté acreditada con alcance en la NTP 392.030-2.

**Modo microformas en el sistema (Sprint 3):**
- El lote sigue los pasos de la NTP como estados: recepción, preparación, digitalización, control de calidad, indización y grabación.
- Roles en el lote: supervisor, digitalizador, controlador e indizador, con separación de funciones.
- Se verifica la resolución mínima de 300 dpi. En las fotos del celular, la resolución se calcula sobre el tamaño del papel detectado.
- Actas de apertura y cierre en PDF, generadas a partir del inventario y la cadena de auditoría.
- Sprint 6: el fedatario firma digitalmente el manifiesto del lote, con las huellas SHA-256 de todas sus páginas.

## 4. Roadmap

| Sprint | Ya previsto | Se agrega |
|---|---|---|
| 2 | OCR, PDF buscable, primera búsqueda | OCR multilenguaje con detección del idioma por página. Azure Read lista unas 300 entradas de idiomas impresos; en la demo se usa Tesseract con paquetes de idioma. |
| 3 | Separación, clasificación, extracción, validación | Modo microformas (sección 3). Correcciones por campo y su tendencia. Panel de accesos a datos sensibles, exportable para el Oficial de Datos Personales. |
| 4 | Búsqueda en lenguaje natural, asistente con citas, conservación, panel | Tablas de retención y eliminación del AGN. |
| 5 | Endurecimiento, respaldos, marcha blanca | Registro de incidentes con el plazo de 48 h a la vista (nuevo reglamento de la Ley 29733, DS 016-2024-JUS). |
| 6 | API pública, webhooks, visor embebido, conector Odoo | Firma digital del fedatario sobre el manifiesto del lote. |
| 7 | — | Editor de reglas y flujos sin código (disparadores: documento indexado, validado o faltante; acciones: avisar, asignar tarea, llamar a un webhook o a un conector). Buzón de correo como entrada. «Documentos similares» en la búsqueda. |
| 8 | Conectores SAP B1 y ERP peruanos | Robots tipo RPA para sistemas sin API: navegador automatizado (Playwright) con usuario técnico, disparado por el editor de flujos, con capturas de cada paso en la auditoría. |

- FAMENSSALUD pasa a producción al cerrar el Sprint 5. Los Sprints 3 y 5 llevan más carga que en el spec: es el riesgo a vigilar.
- Los robots RPA solo actúan con credenciales técnicas que entrega el cliente. Cada ejecución queda en la cadena de auditoría.

## 5. Cambios del 3 nov 2026, 17:17

- El titular del software es Anomaly LA S.A.C. (no es la certificadora). Se corrigieron LICENSE, README y CLAUDE.md.
- La certificación queda pospuesta hasta que un cliente la exija; el modo microformas se mantiene completo en el Sprint 3.
- El titular de la landing, «listo para microformas», se mantiene.
