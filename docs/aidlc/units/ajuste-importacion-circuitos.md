# Unidad: ajuste-importacion-circuitos

- **Estado:** en curso · **Épica:** E2 Inventario de soportes · **App dueña:** inventario
- **Origen:** RN-005 (ampliación del 2026-11-02), HU-009, HU-015 · **Rama:**
  `feature/inventario-importacion-circuitos`
- **Depende de:** [`importacion-inventario`](importacion-inventario.md) y el PR #111 (listado de
  carteles y decisiones), que tiene que estar mergeado antes del PR de código.

## Objetivo

Que Banderolas y PPL se importen como Séxtuples, con la capacidad igual a la cantidad de cada
dirección, y que PPL sea un formato aparte de Gran Formato, para poder cargar el listado de
carteles del 2026-11-02.

## Encuadre

- **RN-005 (`provisoria`, ampliada):** Séxtuples, Banderolas y PPL son circuitos; al importarlos,
  la capacidad es la cantidad relevada.
- **HU-009:** 8 formatos; PPL se separa de Gran Formato.
- **Qué ya existe:** el importador decide por el nombre (`es_sextuples`) si la plantilla lleva
  `slots` o `tamano`. `Cartel.nombre_visible` y su réplica en `reservas` muestran «N slots» solo
  para Séxtuples. El formato se llama «PPL/Gran Formato» en la base, los datos de ejemplo y los
  tests.
- **Capas:** backend (`inventario`: modelo, migración, servicio, serializer; `reservas`: la réplica
  del nombre) y frontend (formulario de Formatos). La importación no cambia en la pantalla.

## Cambios

- **Modelo `Formato`:** campo nuevo `por_cantidad` (booleano, por defecto falso): el formato es un
  circuito y se carga por cantidad en cada dirección. Ver la decisión de abajo.
- **Migraciones** (`inventario.0005_formato_por_cantidad` y `0006_separar_ppl`):
  - agrega `por_cantidad` y lo marca en Séxtuples y Banderolas;
  - renombra «PPL/Gran Formato» a «Gran Formato», si existe con ese nombre;
  - crea «PPL» (fijo, capacidad por defecto 1, `por_cantidad`), si no existe.
  Así local, pruebas y producción quedan iguales sin cargarlo a mano.
- **Importador:** `es_sextuples(formato)` pasa a `formato.por_cantidad`. Un circuito usa la
  plantilla con `slots` y la capacidad es esa cantidad; los demás, `tamano` y la capacidad por
  defecto.
- **Nombre del cartel:** en un circuito, «Dirección · N slots» para Séxtuples y «Dirección · N
  unidades» para los demás (Banderolas, PPL). Mismo cambio en la réplica de `reservas`.
- **Serializer y pantalla de Formatos:** `por_cantidad` editable, como casilla «Se carga por
  cantidad (circuito)», con su ayuda.
- **Datos de ejemplo y tests:** «PPL/Gran Formato» pasa a «Gran Formato».
- **Docs:** columna «Dónde vive» de RN-005, manual (importación y Formatos), README de
  importación (Banderolas y PPL usan la plantilla con `slots`).

### Decisión que falta: cómo sabe el sistema que un formato es un circuito

- **A (recomendada).** Campo `por_cantidad` en el formato, editable en la pantalla de Formatos. Si
  mañana aparece «Séptuples» o Carteleras se cargan por cantidad, se marca la casilla sin tocar
  código.
- **B.** Una lista fija de nombres en el código (Séxtuples, Banderolas, PPL). Sin migración de
  esquema, pero un cambio de nombre en la pantalla rompe la importación.

**Elegida:** A, campo `por_cantidad` (Gonza, 2026-11-02).

## Fuera de alcance

- Cargar los datos del listado (se hace con la pantalla de importación, después del merge).
- Cambiar el formato de los medianos (se hace en la ficha cuando Seba diga cuáles son).
- Reservas: la capacidad ya es la de cada cartel; no cambia cómo se cuentan los cupos.

## Migraciones

- `inventario.0005_formato_por_cantidad`: agrega la columna `por_cantidad`, falsa por defecto.
- `inventario.0006_separar_ppl`: mueve datos del catálogo (marca Séxtuples y Banderolas, renombra
  «PPL/Gran Formato» a «Gran Formato» y crea PPL). La vuelta deshace el renombre y borra PPL si no
  tiene carteles.

Van separadas porque PostgreSQL no deja quitar la columna en la misma transacción que modificó
datos de esa tabla. Probadas en la base local en los dos sentidos.

## Reglas provisorias que se usan

- RN-005: circuitos con capacidad = cantidad relevada, una reserva = un slot genérico.

## Cómo se prueba

- Backend, con `@pytest.mark.regla("RN-005")` donde corresponda:
  - `test_importar_banderolas_crea_carteles_con_capacidad_igual_a_slots`;
  - `test_importar_formato_por_cantidad_pide_la_columna_slots`;
  - `test_importar_formato_comun_pide_tamano`;
  - `test_nombre_visible_de_circuito_muestra_unidades` (y Séxtuples sigue con «slots»);
  - `test_formato_por_cantidad_es_editable` y que Lectura no puede editarlo;
  - `test_migracion_deja_gran_formato_y_ppl` (nombres y `por_cantidad` sembrados).
- Frontend: la casilla se muestra y se manda al guardar un formato.
- Revisión visual con Gonza: la casilla en Formatos y una simulación de Banderolas y PPL.
- Definition of Done completa.

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-11-02 (opción A).
