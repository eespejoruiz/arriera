# Arriera · instrucciones para trabajar en este repositorio

Producto de Enrique Espejo Ruiz: gestión documental con IA para digitalizar archivos en papel. Primer cliente: FAMENSSALUD (fondo de ayuda mutua, archivo 2015–2025 con datos de salud).

## Reglas de trabajo con Enrique
1. Responder siempre en español.
2. No asumir: preguntar antes de decidir lo que no esté resuelto en `docs/spec/`. Agrupar preguntas en una sola ronda con una opción recomendada.
3. Avanzar rápido con entregas pequeñas, demostrables y verificadas (compila, prueba y muestra).
4. Nunca usar datos reales de pacientes o asociados en desarrollo ni en la demo: solo DATOS DEMO, marcados como tales.
5. Nada de secretos en el repositorio. Usar `.env` (ignorado) y secretos de despliegue.

## Fuente de verdad
- `docs/spec/SPEC-Arriera-v1.0.md`: spec original (nombre de trabajo «Legajo»).
- `docs/spec/SPEC-Arriera-adenda-01.md`: nombre Arriera, API para ERP en la v1, marca fija y licencia. Si contradice al spec, manda la adenda.

## Marca y UI
- La interfaz usa siempre la marca de Arriera: nombre, logo (`docs/marca/`) y paleta oliva. No se personaliza con los colores del cliente; el cliente aparece solo como titular de la licencia.
- Tokens: noche `#0F110B`, musgo `#1B1F13`, hoja `#A9B640`, lima `#DCE57A`, marfil `#F4F5EE`, óxido `#E07A4E` (faltantes), ámbar `#E8C25A` (por validar).
- Tipografías: Hanken Grotesk (interfaz) y Special Elite (todo lo que «lee la IA»: datos extraídos, códigos de lote y caja).
- Enrique rechaza el look «hecho por IA»: nada de verde bosque con dorado sobre crema ni fuentes como Inter, Public Sans o JetBrains Mono.

## Stack decidido
Next.js 15 (App Router, TypeScript) · FastAPI (Python 3.12) · PostgreSQL 16 con pgvector, pg_trgm y unaccent · Redis 7 + Dramatiq · MinIO · OCR Azure Document Intelligence (prebuilt-read) · LLM Anthropic Claude (Haiku para clasificar y extraer, Sonnet para manuscritos y asistente) · embeddings locales (bge-m3) · Caddy en las instancias del cliente · una instancia por cliente.

## Infraestructura de Enrique
- Demo: VPS Motor (10.0.1.2), contenedor `arriera-demo`, puerto 3741, ruta Traefik en Escudo `routes.d/arriera-demo.yaml`.
- Landing: VPS Vitrina (10.0.1.4), contenedor `arriera-web`, puerto 3740, ruta `routes.d/arriera.yaml`.
- Motor es frágil en recursos: limitar memoria de los contenedores y no compilar imágenes pesadas ahí.
