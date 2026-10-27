# Unidad: Entrega y traspaso

- **Estado:** en revisión · **Épica:** E9 Entrega y traspaso · **App dueña:** docs
- **Origen:** HU-053, HU-054 · **Rama:** `docs/entrega-y-traspaso`

## Objetivo

Dejar a Big Media lista para mantener y usar el sistema sin depender del equipo de desarrollo.
Eso incluye:

- Una persona ajena al equipo puede levantar el sistema siguiendo la documentación.
- El repositorio documenta el modelo de datos y cómo contribuir.
- Hay una lista de los accesos que se transfieren.
- Los operativos tienen un manual corto y un guion para la capacitación.

Entra en la entrega del viernes 30/10.

## Decisiones

1. **Solo documentación** (propuesta): no toca `backend/` ni `frontend/`. Los archivos nuevos van
   dentro de `docs/`, así que no hay carpetas nuevas en la raíz (regla 8).
2. **Levantar el sistema en un entorno limpio** (HU-053, criterio 1):
   - Hoy `docs/operacion/desarrollo-local.md` está escrito solo para Windows y PowerShell. Se
     agregan los comandos de macOS y Linux.
   - Se valida siguiendo la guía en un clon nuevo del repositorio, en una carpeta temporal y con
     una base vacía.
   - Cualquier paso que falle o que falte se corrige en la guía, y el resultado se anota en el
     registro de gates.
3. **Modelo de datos** (HU-053, criterio 2): `docs/modelo-de-datos.md` tiene un diagrama
   entidad-relación por app (Mermaid, que GitHub muestra) y una tabla corta por modelo con sus
   campos clave y sus reglas. Se arma leyendo los modelos con un script de una sola vez que no
   queda en el repositorio, y se revisa a mano. Incluye los modelos de E10 y E11 que están en
   los PRs #76, #77 y #78; por eso este PR se mergea después de ellos.
4. **Guía de contribución** (HU-053, criterio 2): `docs/guia-de-contribucion.md` es una página
   corta que lleva de la mano a una persona nueva: preparar el entorno, el flujo de ramas y PR, el
   workflow AI-DLC, la Definition of Done y dónde están las reglas. Enlaza los documentos que ya
   existen en lugar de repetirlos.
5. **Traspaso de accesos** (HU-053, criterio 3): `docs/operacion/traspaso-de-accesos.md` es una
   lista de verificación de cada acceso a transferir: dueño del repositorio en GitHub, Render,
   Neon, dominio y correo si los hay, superusuario de Django, y rotación de `DJANGO_SECRET_KEY` y
   de las contraseñas de la base después del traspaso. Por cada acceso dice quién lo tiene hoy,
   a quién pasa y cómo se verifica. **No contiene ninguna credencial** (regla 2). Completar el
   traspaso es una tarea humana; el documento la guía y deja registro.
6. **Manual de uso** (HU-054, criterio 1): `docs/manual/manual-de-uso.md` es corto y orientado a
   tareas, en lenguaje de operativo, sin jerga técnica. Cubre:
   - Ingresar.
   - Cargar clientes y marcas.
   - Crear una campaña y sus posiciones por formato.
   - Agregar carteles en tanda y confirmar las reservas.
   - **Entender un mensaje de conflicto**, con ejemplos reales de los mensajes del sistema.
   - Ver la disponibilidad.
   - Cargar los ítems a facturar y enviar el mes.
   Al final, un apartado de preguntas frecuentes. No lleva capturas de pantalla, para entregarlo
   a tiempo; se pueden sumar después.
7. **Capacitación** (HU-054, criterio 2): `docs/manual/guion-de-capacitacion.md` es el guion para
   la sesión con Seba y Ale: recorrido en orden, datos de ejemplo a usar (los de
   `cargar_datos_ejemplo`, sin datos reales, regla 6) y las preguntas abiertas para hacer frente a
   la pantalla (RN pendientes). La sesión y su grabación son humanas; el guion indica dónde dejar
   el enlace a la grabación para que la puedan consultar.
8. **Índices:** `docs/README.md` y el `README.md` de la raíz enlazan los documentos nuevos.

## Cambios

- `docs/operacion/desarrollo-local.md`: los comandos de macOS y Linux, y las correcciones que
  surjan de la validación en limpio.
- Documentos nuevos:
  - `docs/modelo-de-datos.md`.
  - `docs/guia-de-contribucion.md`.
  - `docs/operacion/traspaso-de-accesos.md`.
  - `docs/manual/manual-de-uso.md`.
  - `docs/manual/guion-de-capacitacion.md`.
- `docs/README.md` y `README.md`: los enlaces a los documentos nuevos.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna. El manual describe el comportamiento con los valores actuales de las reglas provisorias
y lo aclara donde una regla todavía puede cambiar (por ejemplo, si una Pendiente bloquea el cupo).

## Cómo se prueba

- **Validación en limpio:** seguir `desarrollo-local.md` en un clon nuevo, con una base vacía,
  hasta tener la API y el frontend andando, y correr los tests. La salida real va al Gate 2.
- **Revisión del manual:** cada paso se coteja con la pantalla real, con los datos de ejemplo.
- **Enlaces:** se comprueba que todos los enlaces relativos de los documentos nuevos apunten a
  archivos que existen.
- **CI:** `pre-commit run --all-files` en verde (incluye gitleaks).

## Registro de gates

- Gate 1 (plan): 2026-10-27 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-27 — corrida y aprobada por Gonza.
  - **Validación en limpio** (macOS, Python 3.12.3, Node 22.23.1): clon nuevo de `develop`
    (`24caccf`) desde GitHub, en una carpeta temporal y con una base vacía aparte. Siguiendo la
    guía:
    - `migrate` aplicó todas las migraciones y `cargar_datos_ejemplo` respondió "Datos de ejemplo
      creados." y "Datos de demo creados.".
    - `/api/health/` → `{"status": "ok"}` HTTP 200. Login por la API → 200 y `/api/auth/me/` → 200.
    - `pytest --cov`: **589 passed**, coverage **96.41 %**.
    - ruff format y check, mypy (121 archivos), `makemigrations --check` y
      `pre-commit run --all-files` sin errores.
    - Frontend: `npm ci`, `format:check`, `lint`, `typecheck`, `test:coverage` (255 tests, 36
      archivos) y `build` en verde.
  - **Correcciones que salieron de la validación**, ya en la guía:
    - Faltaban los comandos de macOS y Linux.
    - Faltaba qué hacer si el puerto 5433 está ocupado (pasó en esta máquina): ahora explica el
      `compose.override.yaml`.
    - No decía que el proxy de Vite apunta fijo a `127.0.0.1:8000`.
    - No mencionaba `cargar_datos_ejemplo`.
    - El cierre describía la aplicación como solo inventario.
  - **Manual contra la pantalla real:** se combinaron #78 y `cierre-de-mes` en la copia temporal,
    se levantaron API y frontend con los datos de ejemplo y se recorrieron campañas, posiciones por
    formato, agregar carteles en tanda, confirmar reservas, disponibilidad e ítems a facturar. Los
    mensajes de conflicto del manual son los que devolvió el sistema.
  - **Modelo de datos:** se leyeron los modelos de `feature/facturacion-cierre-de-mes`, que incluye
    #77; el #78 no cambia modelos. Se leyeron a mano, sin script.
  - **Enlaces:** 0 rotos (rutas y anclas) en los ocho documentos tocados.
  - `pre-commit run --all-files` en la rama: 13 hooks en verde, salida 0.
  - Mermaid: GitHub dibuja los 10 diagramas sin errores (vista del archivo en la rama).
- Gate 3 (PR): #80, pedido por Gonza el 2026-10-27
