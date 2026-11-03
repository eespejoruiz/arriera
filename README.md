# Arriera

Gestión documental con IA para digitalizar archivos en papel. La IA lee cada hoja y llena el índice (nombre, DNI, fecha, tipo, montos); las personas solo validan lo dudoso.

- Landing: https://arriera.tech
- Demo navegable (DATOS DEMO): https://demo.arriera.tech
- Spec: [`docs/spec/SPEC-Arriera-v1.0.md`](docs/spec/SPEC-Arriera-v1.0.md), [`adenda-01`](docs/spec/SPEC-Arriera-adenda-01.md) y [`adenda-02`](docs/spec/SPEC-Arriera-adenda-02.md). Si se contradicen, manda la adenda más reciente.

## Estado

| Parte | Estado |
|---|---|
| `web/` | Prototipo de UI en Next.js 15 con DATOS DEMO (12 pantallas y la app de captura del celular en `/m`). Es la base del frontend real. |
| `backend/` | Sprint 0 · usuarios y 7 roles, Argon2id, verificación en dos pasos (TOTP cifrado, QR), sesiones en cookie httpOnly, bloqueo tras 5 intentos y auditoría encadenada de solo inserción.<br>Sprint 1 · inventario de cajas y muestreo, lotes `L-AAAA-NNNNNN`, hoja de lote y etiqueta de caja en PDF con QR, emparejamiento del celular por QR, subida verificada con SHA-256, almacén S3/MinIO y control de calidad automático (recorte del papel, en blanco, borrosa, inclinación con enderezado, borde cortado). <br>Sprint 2 · OCR intercambiable (Tesseract multilenguaje para DATOS DEMO y modo local; Azure Read con la cuenta del cliente), índice de texto completo en español y sin tildes con prefijos, búsqueda con filtros por caja e idioma, visor con resaltado, PDF buscable del lote y costo por mil páginas. <br>Sprint 3 · al cerrar un lote la IA (Claude Haiku 5.5) separa, clasifica con el catálogo FAMENSSALUD y extrae campos; confianza combinada IA + OCR; personas por DNI cifrado; cola de validación con vista dividida; presupuesto mensual de IA; modo microformas (pasos NTP con separación de funciones, 300 dpi, manifiesto y actas); panel de accesos a datos sensibles (Ley 29733); `make eval` con set DEMO. 23 pruebas contra PostgreSQL real. |
| `capture-agent/` | Pendiente · agente de captura para Windows (TWAIN/WIA, carpeta vigilada). En la v1 se empezó por el celular. |
| `seeds/` | Pendiente · generador de DATOS DEMO y semillas por cliente. |
| `deploy/demo/` | Imagen nginx de la web. En demo.arriera.tech la web llama a la API real en `/api` (Motor, datos en Vault). |

## Periféricos soportados en la v1

- Escáneres USB con el agente de captura (TWAIN/WIA).
- Celulares como escáner: app web en `/m`, emparejada por QR, sin instalar nada.
- Multifuncionales de red: escanear a carpeta SMB, SFTP o correo.
- Lectores de QR o código de barras USB/Bluetooth en modo teclado.

## Desarrollo con Docker

```bash
cp .env.example .env      # completa CIFRADO_KEY, DNI_HMAC_KEY y ARRIERA_DEMO_CLAVE
docker compose up --build # PostgreSQL, Redis, MinIO, API (http://localhost:8000/docs) y web (http://localhost:3000)
docker compose exec api python -m arriera.seed --demo
```

Usuarios de DATOS DEMO (todos con la clave de `ARRIERA_DEMO_CLAVE`): `admin@`, `archivo@`, `captura@`, `validacion@`, `consulta@` y `auditoria@demo.arriera.tech`. Administración, archivo y auditoría piden configurar la verificación en dos pasos al primer ingreso.

## Desarrollo del backend sin Docker

```bash
cd backend
uv venv && . .venv/bin/activate && uv pip install -e ".[dev]"
alembic upgrade head
python -m pytest -q
uvicorn arriera.main:app --reload
```

## Desarrollo del prototipo

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run build      # exporta estático en web/out
```

Despliegue de la demo (desde la raíz): `docker build -f deploy/demo/Dockerfile -t arriera-demo .`

## Licencia

Software propietario de Anomaly LA S.A.C. Ver [`LICENSE`](LICENSE). Los clientes reciben una licencia de uso limitada: no pueden revender ni renombrar el sistema; sí pueden mantenerlo y mejorarlo para su uso interno.
