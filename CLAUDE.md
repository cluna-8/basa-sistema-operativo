<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/001-sistema-operativo-basa/plan.md
<!-- SPECKIT END -->

## Contexto de sesión — leer siempre al abrir este proyecto

Lee estos archivos en orden antes de responder cualquier consulta sobre el proyecto:

1. **`HANDOFF.md`** — estado actual del sistema, qué funciona, qué no, decisiones técnicas tomadas, próximos pasos. Es el punto de entrada para cualquier desarrollador nuevo o sesión nueva de Claude.
2. **`docs/DESCUBRIMIENTO-BASE-DE-DATOS.md`** — cuestionario técnico para conectar la DB existente de BASA. BASA tiene millones de cajas y un ABM ya conectado. NO crear tablas nuevas sin leer esto primero.
3. **`docs/PENDIENTES-PARA-BASA.md`** — lista completa de pendientes para el equipo BASA.

## Reglas de este proyecto

- **No DELETE físicos**: usar soft-delete via campo `estado`
- **Transacciones atómicas**: todo write multi-tabla dentro de `engine.begin()`
- **No tocar la DB de BASA sin sesión de descubrimiento primero**
- **Frontend simula sin backend**: `basaFetch()` intercepta errores y retorna `{ simulated: true }`
- **Redis**: usar `redis/redis-stack-server:latest`, no `redis:7-alpine` (requiere RediSearch)
- **RedisSaver**: constructor toma URL string. **RedisStore**: constructor toma cliente Redis (APIs diferentes)
- **Todo corre en Docker**: no instalar dependencias localmente
