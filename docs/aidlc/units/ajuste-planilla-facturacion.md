# Unidad: ajuste-planilla-facturacion

- **Estado:** en curso · **Épica:** E11 Facturación mensual · **App dueña:** facturacion
- **Origen:** RN-024 (columnas reales, PR #104), HU-066 (criterio 3) · **Rama:**
  `feature/facturacion-ajuste-planilla`

## Objetivo

Que la planilla que se descarga de un envío tenga la forma de la planilla real de Administración:
sus siete columnas primero y en su orden, el período arriba y los totales y el neto abajo, con las
columnas propias del sistema al final.

## Encuadre

- **RN-024 (`provisoria`):** las siete columnas de la planilla real, en su orden; período arriba,
  totales y neto abajo; las nuevas van al final.
- **Qué ya existe:** `COLUMNAS_PLANILLA` y `planilla_xlsx` en `apps/facturacion/services.py`, con
  24 columnas propuestas (Mes, Cliente, CUIT, Marca, …) y una fila por ítem, sin encabezado ni
  totales. `valores_de_planilla` usa la misma lista para el aviso de reapertura (HU-067).
- **Capas:** solo backend (`facturacion`). El frontend descarga el archivo y no cambia.
- Sin migraciones ni dependencias nuevas entre apps (`facturacion` ya importa de `costos` y
  `clientes`).

## Cambios

- **Columnas (`COLUMNAS_PLANILLA`)**, en este orden:
  1. `CLIENTE (RAZON SOCIAL)`: la razón social del cliente; si no tiene, su nombre visible.
  2. `IMPORTE NETO TOTAL`: el neto del ítem.
  3. `COSTOS INCLUIDOS EN FC`: el total de costos no anulados del ítem (como hoy «Costos»).
  4. `DETALLE COSTO`: los costos no anulados del ítem, separados por «; », cada uno como
     «<tipo> <a quién se le paga o proveedor>» (por ejemplo «Comisión Agencia X»). Vacío si no hay.
  5. `TIPO DE VENTA (F/V)`: el tipo de venta.
  6. `GOB/PRIV`: el sector.
  7. `TIPO (cartel/led/ppl/sextuples)`: `tipo_soporte` y `descripcion` separados por « · » (ver
     la decisión de abajo).
  8. Después, las del sistema que no repiten a las de arriba: Mes, Cliente, CUIT, Marca,
     Descripción, Período desde, Período hasta, Cantidad, Precio unitario, Alícuota IVA, IVA,
     Total, Tipo de servicio, Notas, Orden de compra, Fecha OC, Grupo de factura, Neto final y
     Reenviado. Salen «Importe neto», «Costos», «Gob/Priv», «Tipo de venta» y «Tipo de soporte»,
     porque quedan en las siete primeras.
- **Encabezado:** fila 1 `PERIODO:` y el mes como `2026/9`; fila 2 `CARTELERIA`; fila 3 los
  títulos de columna. La planilla real empieza en la columna B; la nuestra empieza en la A.
- **Pie:** después del último ítem, una fila con `=SUM(...)` del importe neto y de los costos (en
  sus columnas, como la real), una fila vacía y una fila `Neto` con la resta de las dos sumas.
  Fórmulas y no valores, así Administración puede corregir un importe y el total se recalcula.
- **Orden de las filas:** el de hoy (por cliente y los grupos de factura juntos, HU-064).
- **`valores_de_planilla`** sigue saliendo de `COLUMNAS_PLANILLA` sin «Reenviado»: el aviso de
  reapertura pasa a usar los títulos nuevos.
- **Docs:** columna «Dónde vive» de RN-024 y el manual de uso (sección de la planilla).

### Decisión que falta: qué va en «TIPO»

En la planilla real, «TIPO (cartel/led/ppl/sextuples)» es texto libre con lo vendido y notas
(«Cartel 12 x 4 + Pantalla», «5 PP Septiembre»). El ítem tiene `tipo_soporte` (texto corto) y
`descripcion` (texto largo). Opciones:

- **A.** `tipo_soporte`. La descripción queda en «Descripción», más a la derecha.
- **B.** `descripcion`.
- **C.** Los dos: `tipo_soporte` y `descripcion` separados por « · » (solo el que tenga dato si
  falta uno).

**Elegida:** C, los dos (Gonza, 2026-10-29).

## Fuera de alcance

- Cambiar qué ítems entran en la planilla o cuándo (RN-025).
- Separar la planilla en hojas por tipo de soporte (la real tiene una sola hoja, «Cartelería»).
- Facturar una orden de compra que cruza meses (RN-027, `pendiente`).

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-024: columnas reales en su orden; período arriba, totales y neto abajo; las nuevas al final.

## Cómo se prueba

Backend (pytest contra PostgreSQL, `@pytest.mark.regla("RN-024")`), en
`backend/tests/test_planilla_facturacion.py`:

- `test_planilla_con_periodo_y_titulo_arriba`: filas 1 y 2.
- `test_planilla_con_las_siete_columnas_reales_primero`: fila 3 empieza con las siete en su orden y
  sigue con las del sistema.
- `test_planilla_cliente_sin_razon_social_usa_su_nombre`.
- `test_planilla_detalle_costo_lista_los_costos_no_anulados`.
- `test_planilla_tipo_junta_soporte_y_descripcion` y que con uno solo sale ese.
- `test_planilla_con_totales_y_neto_abajo`: las fórmulas `=SUM` apuntan al rango de los ítems y
  `Neto` resta las dos sumas.
- Se ajustan los tests que ya existen a los títulos y filas nuevos (los importes siguen siendo
  números).

## Registro de gates

- Gate 1 (plan): 2026-10-29 — aprobado por Gonza (TIPO: opción C)
- Ajustes durante la implementación: los valores que se guardan al reabrir un ítem (HU-067) usan
  los títulos de columna. Para un ítem reabierto antes de este cambio, `TITULOS_ANTERIORES`
  traduce los cuatro títulos que cambiaron de nombre y el aviso de reenvío solo compara las
  columnas que ya existían al reabrir. Test:
  `test_reenviar_con_valores_guardados_con_titulos_anteriores_compara_los_que_hay`.
- Gate 2 (verificación): 2026-10-29 — todo en verde:
  - `ruff format --check .`: 139 files already formatted; `ruff check .`: All checks passed!
  - `mypy backend`: Success: no issues found in 139 source files
  - `makemigrations --check --dry-run`: No changes detected
  - `pytest --cov`: 835 passed, ninguno salteado; Total coverage: 96.94%
  - Frontend (sin cambios): `format:check`, `lint` y `typecheck` sin errores; `test:coverage`:
    48 archivos, 385 tests, 92,48 % de sentencias y 94,47 % de líneas; `build` OK
  - `pre-commit run --all-files` (incluye gitleaks): todos Passed
