# Unidad: Marcas duplicadas

- **Estado:** mergeada · **Épica:** E3 Clientes, marcas y CRM · **App dueña:** `clientes`
  (+ `frontend`)
- **Origen:** HU-019 · **Rama:** `feature/clientes-marcas-duplicadas`

## Objetivo

Que el sistema avise cuando se guarda una marca con un nombre igual o muy parecido al de otra, y
muestre cuál es la coincidente. El operativo puede confirmar que es otra marca y guardar igual
(HU-019, criterios 1 y 2).

## Punto de partida (relevamiento del 26/10/2026)

- `Marca` (`apps/clientes/models.py`) ya guarda `nombre_busqueda`, generado con
  `config.texto.normalizar_busqueda`. Esa función pasa a minúsculas y quita tildes, pero no
  colapsa espacios.
- No hay ningún control de duplicados de marca: ni restricción en la base ni aviso. Dos marcas con
  el mismo nombre se guardan sin problema.
- La API es `MarcaViewSet` (`/api/clientes/marcas/`), con `POST` y `PATCH` y sin `DELETE`.
  `MarcaSerializer.validate` solo controla que el cliente y el rubro estén activos.
- Las marcas también se crean solas: `services.registrar_cliente` crea la marca homónima de un
  cliente directo (HU-018).
- **No existe un importador de marcas.** El criterio 3 de HU-019 ("dada una importación, los
  posibles duplicados se informan en el reporte") no tiene dónde aplicarse todavía. El README de
  importación ya prevé el caso con `confirmar_distinto`, pero solo para carteles (HU-015, que espera
  los relevamientos).
- No hay reglas `RN-xxx` sobre duplicados de marca. La historia define la comparación: ignora
  mayúsculas, tildes y espacios de más.
- En el frontend, `MarcaForm.tsx` hace el alta y la edición, y muestra los errores del servidor.

## Preguntas al equipo

1. **Qué cuenta como "muy parecido".**
   - a) **Igual después de normalizar o a un error de tipeo de distancia.** Se normaliza con
     minúsculas, sin tildes, sin signos de puntuación y con los espacios colapsados. Además avisa
     si la distancia de edición es 1, o hasta 2 en nombres de 8 caracteres o más. Ejemplos: "Coca
     Cola", "coca-cola" y "Coca  Colá" son iguales; "Coca Kola" está a distancia 1.
     **(recomendado)**
   - b) **Solo igual después de normalizar.** Es más simple, pero no detecta los errores de tipeo,
     que son el riesgo que nombra la historia.
   - c) **Similitud de trigramas de PostgreSQL** (`pg_trgm`). Exige una migración que active la
     extensión, y el umbral es menos fácil de explicar.
2. **Cómo se confirma que es otra marca.**
   - a) **En el servidor.** El `POST` o el `PATCH` responde 400 con el código `posible_duplicado` y
     las marcas coincidentes. El formulario muestra el aviso y un botón "Es otra marca, guardar
     igual", que reenvía con `confirmar_distinta: true`. Así el aviso también rige para cualquier
     otro cliente de la API. **(recomendado)**
   - b) **Solo en el frontend**, con una consulta previa. Es más liviano, pero la API sigue
     aceptando duplicados sin aviso.
3. **Contra qué marcas se compara.**
   - a) **Todas, activas e inactivas**, y el aviso muestra el estado y el cliente de cada una. Una
     inactiva duplicada se reactiva, no se carga otra vez. **(recomendado)**
   - b) Solo las activas.
4. **Cuándo avisa.** Propuesta: en el alta y cuando se cambia el nombre en una edición, sin
   comparar la marca consigo misma. Editar otros campos (rubro, activo) no avisa. ¿Está bien?
5. **La marca homónima del cliente directo (HU-018).**
   - a) **El alta del cliente directo avisa igual**, con la misma confirmación, si su marca
     homónima coincide con otra. Es el caso que la historia marca como más riesgoso.
     **(recomendado)**
   - b) No avisa: la marca homónima se crea siempre, como hoy.
6. **El criterio 3, la importación.** Propuesta: queda fuera de esta unidad porque no hay
   importador de marcas. La detección queda en un servicio (`posibles_duplicados(nombre)`) que la
   importación va a reusar cuando exista. ¿Está bien?

## Respuestas

Respondidas por Gonza el 26/10/2026: se aceptan las opciones recomendadas o propuestas.

1. Igual después de normalizar, o a distancia de edición 1 (2 en nombres de 8 caracteres o más).
2. La confirmación es en el servidor: 400 `posible_duplicado` y reenvío con `confirmar_distinta`.
3. Se compara contra todas las marcas, activas e inactivas.
4. Avisa en el alta y al cambiar el nombre, sin compararse consigo misma.
5. El alta del cliente directo avisa por su marca homónima.
6. El criterio 3 (importación) queda fuera; la detección queda en un servicio reusable.

## Cambios (con las opciones recomendadas)

- `backend/config/texto.py`: `normalizar_comparacion` (normaliza también puntuación y espacios) y
  `distancia_edicion` (Levenshtein con tope, sin dependencias nuevas).
- `backend/apps/clientes/services.py`: `posibles_duplicados(nombre, excluir=None)`, que devuelve
  las marcas coincidentes, y `describir_duplicado(marca)` para el texto del aviso.
  `registrar_cliente` no cambia: el serializer del cliente avisa antes de llamarlo.
- `backend/apps/clientes/serializers.py`: el campo de escritura `confirmar_distinta`, y en
  `validate` el error `posible_duplicado` con las coincidentes, tanto en `MarcaSerializer` como en el
  alta de un cliente directo.
- `frontend/src/features/clientes/AvisoDuplicados.tsx` (nuevo), usado por `MarcaForm.tsx` y
  `ClienteForm.tsx`: el aviso con las coincidentes y el botón "Es otra marca, guardar igual".
  Cambiar el nombre saca el aviso.

## Migraciones

Ninguna. La comparación se hace en Python sobre las marcas existentes: son cientos, no hace falta
un índice. Si la cantidad crece mucho, se evalúa `pg_trgm` en una unidad aparte.

## Reglas provisorias que se usan

Ninguna. La comparación sale de la regla de negocio de HU-019; si el umbral de la pregunta 1
resulta discutible, se puede registrar como regla nueva en un PR `docs/historias-…`.

## Cómo se prueba

- `test_marca_nombre_igual_normalizado_avisa_con_coincidente` (mayúsculas, tildes, espacios y
  puntuación; criterio 1).
- `test_marca_error_de_tipeo_avisa` y `test_marca_nombre_distinto_no_avisa` (los umbrales de la
  pregunta 1).
- `test_marca_confirmada_distinta_se_guarda` (criterio 2).
- `test_marca_avisa_contra_inactiva_con_su_estado`.
- `test_marca_edicion_sin_cambio_de_nombre_no_avisa` y
  `test_marca_edicion_no_se_compara_consigo_misma`.
- `test_cliente_directo_marca_homonima_duplicada_avisa_y_confirmado_se_guarda`.
- Los tests unitarios de `normalizar_comparacion` y `distancia_edicion`.
- Frontend: `MarcaForm` y `ClienteForm` muestran el aviso con la coincidente, y "guardar igual"
  reenvía con `confirmar_distinta`.

## Registro de gates

- Gate 1 (plan): 26/10/2026 — aprobado por Gonza
- Gate 2 (verificación): corrida el 26/10/2026 — backend 470 tests, 95,94 %; frontend 171 tests; aprobado por Gonza el 26/10/2026
- Gate 3 (PR): 26/10/2026 — PR #69 a `develop`, pedido por Gonza
