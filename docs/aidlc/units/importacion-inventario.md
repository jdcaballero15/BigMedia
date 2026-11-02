# Unidad: importacion-inventario

- **Estado:** en curso · **Épica:** E2 Inventario de soportes · **App dueña:** inventario
- **Origen:** HU-015 (RN-009, RN-005, RN-008) · **Rama:** `feature/inventario-importacion`
- **Depende de:** [`inventario`](inventario.md) (formatos, zonas, estados y carteles) y el PR #108
  (dudas de Séxtuples resueltas en RN-009).

## Objetivo

Que un Administrador pueda cargar el inventario desde un CSV, con una simulación previa y un
reporte por fila, sin duplicar carteles. La primera carga es la de Séxtuples; Gran Formato usa el
mismo importador cuando llegue su planilla.

## Encuadre

- **HU-015 (Must, L):** cada fila válida crea un cartel; las inválidas o duplicadas salen en un
  reporte con el motivo y no frenan a las demás; importar dos veces no duplica.
- **Especificación:** [`inputs/importacion/README.md`](../inputs/importacion/README.md) (plantillas,
  normalización, duplicados, reporte). Esta unidad la implementa tal cual, salvo lo que se anota
  en «Cambios».
- **RN-009 (`pendiente`, dudas de Séxtuples resueltas el 2026-11-02):** departamentos normalizados
  a los de RN-008; capacidad = columna Cantidad o, si falta, la cantidad de marcas; las diferencias
  van al informe; sin bloques sueltos ni marcas como reservas. Las dos filas sin departamento
  quedan rechazadas hasta que Seba conteste.
- **RN-005 (`provisoria`):** en Séxtuples, capacidad = slots relevados.
- **App dueña:** `inventario`; usa `auditoria` por su servicio (origen `importacion`, que ya
  existe). Sin dependencias nuevas entre apps.
- **Capas:** backend (`inventario`: servicio y vista) y frontend (`features/inventario`).

## Cambios

- **Servicio `apps/inventario/services.py`** (archivo nuevo; hoy la app no tiene):
  - `importar_carteles(archivo, formato, usuario, simular)`: valida el archivo (UTF-8, separador
    `,` con aviso si es `;`, encabezado exacto de la plantilla del formato, al menos una fila) y
    después fila por fila, en el orden del README: normalización, obligatorios, tipos y rangos,
    referencias (formato, zona, proveedor, estado), duplicados dentro del archivo y contra el
    sistema.
  - Cada fila válida se guarda en su propio `transaction.atomic()`, así una que falla no frena a
    las demás. Con `simular` no se guarda nada y el reporte es el mismo.
  - Capacidad: en Séxtuples, `slots`; en Gran Formato, la capacidad por defecto del formato.
  - Duplicados: clave exacta (formato + dirección normalizada + tamaño o slots) y aproximada
    (abreviaturas, intersecciones en otro orden, distancia de edición hasta 2, misma dirección con
    otro tamaño o slots, tamaño invertido), con los resultados de la tabla del README (`creada`,
    `omitida`, `rechazada`, `en_revision`) y `confirmar_distinto`. La distancia de edición se
    escribe en el servicio, sin dependencia nueva.
  - Auditoría de cada cartel creado con origen `importacion`, el usuario, y el nombre del archivo
    y `ref_origen` en el registro.
  - Devuelve el resumen (leídas, creadas, omitidas, rechazadas, en revisión, creadas incompletas)
    y una fila de reporte por resultado o problema, con las columnas de la plantilla del reporte.
- **Vista:** `POST /api/inventario/importaciones/` (multipart: `archivo`, `formato`, `simular`),
  solo para Administrador. Responde el resumen y las filas en JSON.
- **Frontend (`features/inventario/ImportacionPage.tsx`):** pantalla «Importar carteles», solo
  para Administrador (como Usuarios). Se elige el formato y el archivo; «Simular» muestra el resumen
  y la tabla del reporte; «Importar» carga de verdad, con la misma vista. «Descargar reporte» baja
  el CSV con las columnas de la plantilla.
- **Docs:** columna «Dónde vive» de RN-009 (parte de Séxtuples), manual de uso (sección nueva de
  importación) y el README de importación donde el nombre del formato no coincide («PPL o Gran
  Formato» en el README, «PPL/Gran Formato» en el sistema: se compara sin distinguir mayúsculas,
  tildes ni signos).

### Decisiones que faltan

**1. Cómo se pasa la planilla visual de Séxtuples al CSV.**

- **A (recomendada).** Lo hago yo una vez, con un script fuera del repositorio, aplicando las
  decisiones de RN-009 (departamentos, slots). Las filas donde la cantidad de marcas no coincide
  con la de slots llevan la diferencia en `ref_origen` («Sextuples fila 12: 4 slots, 5 marcas»), así
  salen en el reporte. Ni la planilla ni el CSV entran al repositorio (datos reales).
- **B.** Un comando `convertir_sextuples` en `inventario`, con tests sobre una planilla ficticia.
  Queda en el código algo que se usa una sola vez.

**Elegida:** A, script fuera del repositorio (Gonza, 2026-11-02).

**2. Por dónde se importa.**

- **A (recomendada).** Pantalla para Administrador, como dice HU-015: Big Media puede importar
  Gran Formato y los formatos que falten sin depender de nosotros.
- **B.** Solo un comando de Django (`importar_carteles`), que corre el equipo. Más chico, sin
  frontend.

**Elegida:** A, pantalla para Administrador (Gonza, 2026-11-02).

## Fuera de alcance

- Actualizar carteles existentes desde un archivo (se hace desde la ficha).
- Importar reservas históricas, LED y los formatos sin relevamiento.
- Cargar Gran Formato: falta su planilla (RN-009).

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- RN-009: las decisiones del 2026-11-02 sobre Séxtuples (arriba).
- RN-005: capacidad = slots relevados.
- RN-008 (`confirmada`): las nueve zonas.

## Cómo se prueba

Backend, en `backend/tests/test_importacion_carteles.py`, con archivos CSV ficticios armados en
cada test y `@pytest.mark.regla` donde corresponda:

- `test_importar_sextuples_valido_crea_carteles_con_capacidad_igual_a_slots` (RN-005);
- `test_importar_gran_formato_valido_crea_carteles_con_tamano_y_zona`;
- `test_importar_dos_veces_el_mismo_archivo_no_duplica`;
- `test_importar_fila_invalida_la_rechaza_y_carga_las_demas`;
- `test_importar_fila_sin_zona_se_rechaza_con_el_campo` (RN-009);
- `test_importar_zona_sin_tildes_ni_mayusculas_usa_la_de_la_lista` (RN-008, RN-009);
- `test_importar_archivo_con_columna_desconocida_se_rechaza_entero`;
- `test_importar_archivo_con_punto_y_coma_avisa_el_separador`;
- `test_importar_tamano_y_slots_se_normalizan`;
- `test_importar_clave_exacta_existente_con_datos_distintos_se_rechaza`;
- `test_importar_coincide_con_cartel_de_baja_se_rechaza`;
- `test_importar_filas_repetidas_en_el_archivo`;
- `test_importar_posible_duplicado_queda_en_revision_y_con_confirmar_distinto_se_crea`;
- `test_importar_simulado_no_guarda_nada`;
- `test_importar_queda_auditado_con_origen_importacion`;
- `test_importar_solo_administrador`.
- Frontend: la pantalla simula, importa, muestra el resumen y el reporte, y no aparece para otros
  roles.
- Revisión visual con Gonza en el navegador y, con la decisión 1 A, simulación con el CSV real de
  Séxtuples en la base local antes de cargarlo.
- Definition of Done completa.

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-11-02 (decisiones 1 A y 2 A).
- Ajustes durante la implementación: `apiUpload` acepta el método (la importación usa `POST`); el
  README de importación aclara que el nombre del formato se compara sin distinguir mayúsculas,
  tildes ni signos, y que solo se importan formatos fijos.
- Gate 2 (verificación): 2026-11-02 — todo en verde:
  - `ruff format --check .`: 141 files already formatted; `ruff check .`: All checks passed!
  - `mypy backend`: Success: no issues found in 141 source files
  - `makemigrations --check --dry-run`: No changes detected
  - `pytest --cov`: 889 passed, ninguno salteado; Total coverage: 97.21 %
    (`apps/inventario/services.py` al 100 %)
  - Frontend: `format:check` y `lint` sin errores ni advertencias; `typecheck` OK;
    `test:coverage`: 49 archivos, 393 tests, 92,55 % de sentencias y 94,54 % de líneas; `build` OK
    (con el aviso de bundle de más de 500 kB que ya tenía `develop`)
  - `pre-commit run --all-files` (incluye gitleaks): todos Passed
- Gate 2 aprobado por Gonza el 2026-11-02, con la revisión visual de la pantalla en el navegador.
