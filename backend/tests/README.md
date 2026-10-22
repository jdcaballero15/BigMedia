# Convenciones de tests del backend

- **Siempre contra PostgreSQL.** No hay modo SQLite ni tests opcionales. Levantá la base con `docker compose up -d --wait db` y corré `pytest` desde la raíz.
- **Sin red.** Ningún test llama a servicios externos; si algo lo necesita, se reemplaza por un doble.
- **Nombres:** los tests nuevos se llaman `test_<qué>_<condición>_<resultado>`.
- **Marcador `regla`:** el test que verifica una regla de negocio lleva `@pytest.mark.regla("RN-xxx")`, con el id de [`docs/aidlc/reglas-de-negocio.md`](../../docs/aidlc/reglas-de-negocio.md).
- **Todo bug empieza con su test:** primero un test que falle por el bug, después el arreglo.
- **Coverage mínimo 80 %** (sentencias y ramas). No se baja el umbral ni se excluyen archivos para que pase.
- **Fixtures comunes** en `conftest.py`; no las dupliques en cada archivo de test.
