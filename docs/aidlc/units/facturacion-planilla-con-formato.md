# Unidad: facturacion-planilla-con-formato

- **Estado:** mergeada · **Épica:** E11 Facturación mensual · **App dueña:** `facturacion`
- **Origen:** pedido de Juan Diego (2026-11-16), HU-070 y RN-024 ajustadas en el PR de historias
  `docs/historias-facturacion-sin-estados` · **Rama:** `feature/facturacion-planilla-con-formato`

## Objetivo

«Descargar Excel» baja hoy los datos correctos pero sin formato. El archivo pasa a verse como la
planilla real de Administración: colores, bordes, importes con signo pesos, totales y neto.

## Cambios

- `apps/facturacion/services.py::planilla_de_lista_xlsx`, con el formato en una función aparte
  para que cada una quede en menos de 50 líneas:
  - Fila 1 (solo si hay mes): «PERIODO:» en A1 y «2026/9» en B1, en negrita, fondo naranja
    (`FFC000`).
  - Fila de título: «CARTELERIA», combinada de A a G, en negrita y centrada, fondo verde (`92D050`).
  - Títulos de columna: negrita, centrados, con ajuste de texto, fondo amarillo claro (`FFF2CC`).
  - Celdas de la tabla, de los títulos a la fila de totales: borde fino en las cuatro caras.
  - Importe neto y costos incluidos (columnas B y C) en las filas, los totales y el neto: formato
    `"$" #,##0`, que se ve «$ 450.000». El valor guardado conserva los centavos.
  - Fila de totales: fondo durazno (`FCE4D6`) de A a G, sumas en negrita. Las sumas y el neto
    siguen siendo fórmulas.
  - Fila «Neto», como hoy, con una fila vacía antes.
  - Anchos de columna: A 30, B 18, C 18, D 40, E 12, F 12, G 50.
- No cambia qué columnas ni qué filas salen, ni el nombre del archivo.

## Fuera de alcance

- Resaltar filas en amarillo: en la planilla real es un resaltado a mano.
- La planilla del envío (`planilla_xlsx`): se retira en la unidad `facturacion-sin-estados`.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-024 (`provisoria`): las siete columnas en su orden, período arriba y totales y neto abajo,
  ahora con el formato de la planilla real.

## Cómo se prueba

- Tests nuevos en `backend/tests/test_descarga_facturacion.py`, con
  `@pytest.mark.regla("RN-024")`, escritos primero y en rojo:
  - `test_descarga_periodo_y_titulo_con_los_colores_de_la_planilla`: fondo naranja en A1 y B1, y
    «CARTELERIA» combinada de A a G con fondo verde.
  - `test_descarga_titulos_de_columna_en_negrita_centrados_y_amarillos`.
  - `test_descarga_importes_con_formato_de_pesos_sin_decimales`: formato de número de B y C en
    las filas, los totales y el neto, y el valor con sus centavos.
  - `test_descarga_tabla_con_bordes_y_totales_en_durazno`.
  - `test_descarga_sin_mes_tiene_el_titulo_en_la_primera_fila`.
- Los tests actuales de la descarga siguen pasando sin cambios.
- Verificación completa del backend (`ruff`, `mypy`, `pytest --cov`, `makemigrations --check`) y
  `pre-commit run --all-files`. El frontend no cambia.
- Prueba visual: abrir en Excel el archivo descargado en local y compararlo con la captura de la
  planilla real.

## Registro de gates

- Gate 1 (plan): 2026-11-16 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-16 — aprobado por Juan Diego. Salida de los comandos:
  - Los 5 tests nuevos fallaban antes del cambio (`5 failed, 15 passed`) y pasan después.
  - `ruff format --check` (`148 files already formatted`), `ruff check` (`All checks passed!`),
    `mypy backend` (`Success: no issues found in 148 source files`) y `makemigrations --check`
    (`No changes detected`).
  - `pytest --cov`: `957 passed in 1112.98s`, coverage total 97,40 %, ningún test salteado.
  - `pre-commit run --all-files`: todos `Passed`, incluido gitleaks.
  - Frontend sin cambios: no se volvió a correr localmente; lo corre el CI.
  - Prueba visual: Juan Diego abrió un Excel de ejemplo (datos inventados) y lo aprobó.
- Gate 3 (PR): #134 (2026-11-16), pedido por Juan Diego; mergeado el mismo día
