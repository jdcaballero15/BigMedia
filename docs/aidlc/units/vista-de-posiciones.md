# Unidad: Vista de posiciones

- **Estado:** en curso · **Épica:** E10 Armado de campañas y reserva masiva · **App dueña:** `reservas`
- **Origen:** HU-071 · **Rama:** `feature/reservas-vista-de-posiciones`

## Objetivo

Que "Agregar carteles" tenga una vista **Posiciones** con el aspecto de la planilla de posiciones
de Seba (`posiciones 8-10.xlsx`, hoja Séxtuples): una fila por dirección y un casillero por slot,
con la marca que lo ocupa pintada de su color. Seba asigna desde ahí, mirando cuántos slots
quedan libres.

## Decisiones

1. **Para asignar, dentro de "Agregar carteles"** (Juan Diego, 16/11/2026). No hay vista de
   consulta suelta.
2. **Solo importa cuántos slots quedan libres** (Juan Diego, 16/11/2026). El slot sigue siendo
   genérico (RN-005): no se guarda la posición física ni las anotaciones ("esquina", "mala
   visual").
3. **Endpoint nuevo** (Juan Diego, 16/11/2026, alternativa A): se crea
   `GET /api/reservas/posiciones/` y `carteles-para-tanda` y la tabla quedan sin tocar. Se
   descartaron dos alternativas:
   - **B**, ampliar `carteles-para-tanda`, porque cambia el contrato de la tabla.
   - **Calcularlo en el frontend**, porque la ocupación quedaría calculada fuera del servidor.
4. **Aspecto parecido a la planilla** (Juan Diego, 16/11/2026):
   - columnas Dirección · Departamento · Cantidad y, a la derecha, los casilleros;
   - cada casillero ocupado va relleno con el color de la marca y su nombre;
   - los libres quedan en blanco con borde;
   - orden por departamento y dirección.
5. **Mismo criterio de ocupado que la validación dura** (propuesta): para cada cartel se usan el
   pico diario (RN-003), el día de borde (RN-001) y las Pendientes según el parámetro (RN-002), con
   las mismas funciones que `carteles_para_tanda`. Los casilleros ocupados son exactamente
   `ocupados` (el pico), así que la vista y el bloqueo de sobreventa nunca se contradicen.
6. **Dos reservas que se suceden comparten casillero** (propuesta). Ejemplo: A ocupa del 1 al 10 y
   B del 15 al 31. El servidor reparte las reservas que bloquean en casilleros con el algoritmo
   clásico de partición de intervalos: las ordena por inicio y pone cada una en el primer
   casillero que ya se liberó. Salen exactamente `pico` casilleros. El casillero muestra "A · B" y
   cada nombre lleva sus fechas en el tooltip.
7. **Las tentativas no ocupan casillero** (propuesta): son las Pendientes de otras campañas cuando
   no bloquean. Se informan como hoy, con "· N tentativas" junto a la dirección, y la marca y las
   fechas van en el tooltip.
8. **Color por marca, automático** (propuesta): una paleta fija de 12 colores con texto legible en
   modo claro (la app no tiene modo oscuro). A cada marca le toca `marca_id mod 12`, así que siempre tiene el mismo
   color. No se agrega un campo de color a la marca. La campaña actual va con el color de acento y
   el texto "Esta campaña"; una campaña sin marca muestra "Sin marca" en gris.
9. **Click en un slot libre** (propuesta): elige el cartel, con el mismo `Map` de selección que la
   tabla, y el primer casillero libre pasa a mostrar "Esta campaña" con borde punteado, porque
   todavía no está reservado. Un segundo click lo quita. Los carteles llenos y los que ya están en
   la campaña (`en_campania`) no se pueden elegir; los llenos se ven atenuados.
10. **Selector Tabla | Posiciones** (propuesta): arriba de la lista, con Tabla por defecto. La
    elección se recuerda por navegador (`localStorage`, con try/catch). Al cambiar de vista se
    conservan las fechas, los filtros, la selección y el contador.
11. **Ancho** (propuesta): los casilleros tienen ancho fijo, de unos 110 px. Si una fila no entra
    en pantalla, la tabla se desplaza horizontalmente dentro de su contenedor, sin que se mueva la
    página.

## Cambios

- `reservas/services.py`: `posiciones_de_formato(campania, formato, desde, hasta, filtros)`.
  - Reusa los filtros y el cálculo de `carteles_para_tanda`, extraídos a funciones comunes sin
    cambiar su comportamiento.
  - Incluye los carteles llenos.
  - Por cartel devuelve `id`, `nombre_visible`, `direccion`, `zona_nombre`, `capacidad`,
    `ocupados`, `lleno`, `en_campania`, `tentativas` (lista) y `slots`. `slots` tiene `capacidad`
    elementos y cada uno es una lista de ocupantes con `marca_id`, `marca_nombre`, `campania_id`,
    `campania_nombre`, `es_esta_campania`, `estado`, `fecha_inicio` y `fecha_fin`.
  - Una función aparte, `repartir_en_slots`, hace la partición de intervalos (decisión 6).
- `reservas/views.py` y `urls.py`: `PosicionesView` en `/api/reservas/posiciones/`, con los mismos
  parámetros, validaciones y permisos que `CartelesParaTandaView`.
- Frontend `features/reservas/`:
  - `VistaPosiciones.tsx` arma la grilla y los casilleros.
  - `colores.ts` tiene la paleta y el color de cada marca.
  - `AgregarCarteles.tsx` suma el selector, comparte la selección y llama al endpoint nuevo solo
    en la vista Posiciones.
  - `types.ts` agrega los tipos nuevos.
- Estilos con los tokens existentes de `estilo-base`, que ya traen colores para modo claro y
  oscuro.

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-001: día de borde, según el parámetro.
- RN-002: las Pendientes bloquean según el parámetro `tentativa_bloquea`.
- RN-003: pico diario.
- RN-005: una reserva ocupa un slot genérico.

Ninguna cambia de valor.

## Cómo se prueba

- Backend (`backend/tests/test_posiciones.py`):
  - `test_posiciones_cartel_lleno_se_incluye_marcado_lleno` (`regla("RN-005")`).
  - `test_repartir_reservas_sucesivas_comparten_slot` (`regla("RN-003")`).
  - `test_posiciones_pendiente_que_no_bloquea_va_a_tentativas` (`regla("RN-002")`).
  - `test_repartir_dia_de_borde_segun_parametro` (`regla("RN-001")`).
  - Tests de filtros, de la campaña actual, de "Sin marca", de los carteles fuera de servicio
    excluidos, del endpoint con parámetros inválidos y de permisos.
  - `carteles_para_tanda` sigue pasando sus tests sin cambios.
- Frontend (`VistaPosiciones.test.tsx` y `AgregarCarteles.test.tsx`):
  - la grilla tiene un casillero por slot;
  - un cartel lleno no se puede elegir;
  - el click elige y libera;
  - la selección se conserva al cambiar de vista;
  - una marca siempre tiene el mismo color.
- Prueba manual con los Séxtuples importados en staging, al lado de la planilla.

## Registro de gates

- Gate 1 (plan): 2026-11-16 — aprobado por Juan Diego
- Gate 2 (verificación): 2026-11-16 — rama `feature/reservas-vista-de-posiciones`:
  - `ruff format --check`: 145 files already formatted; `ruff check`: All checks passed!
  - `mypy backend`: Success: no issues found in 145 source files
  - `makemigrations --check --dry-run`: No changes detected
  - `pytest --cov`: 907 passed in 1133.57s; Required test coverage of 80.0% reached. Total
    coverage: 97.32%
  - `pre-commit run --all-files` (incluye gitleaks): todos Passed
  - Frontend: `format:check` OK, `lint` OK, `typecheck` OK, `test:coverage` 51 archivos y 416 tests
    passed (sentencias 92,86 %, líneas 94,78 %), `build` OK
  - Revisión final de la rama: 0 críticos, 2 importantes corregidos (respuestas viejas que pisaban
    a las nuevas; tentativas fuera de vista) y 7 menores anotados para decidir.
  - Pendiente de aprobación de Juan Diego o Gonza.
- Gate 3 (PR): pendiente
