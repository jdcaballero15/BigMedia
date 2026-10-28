# Unidad: pantallas-rediseno

- **Estado:** en curso · **Épica:** E12 Rediseño visual · **App dueña:** frontend
- **Origen:** pedido de Gonza del 2026-10-28 · **Rama:** `feature/frontend-pantallas-rediseno`
- **Depende de:** [`estilo-base`](estilo-base.md) (usa sus tokens, tablas y menú de fila).

## Objetivo

Reordenar las pantallas que Gonza marcó como confusas o feas, con el estilo de `estilo-base`,
mostrando los mismos datos que hoy pero mejor organizados.

## Cambios por pantalla

- **Panel:** cuatro cifras arriba (carteles libres, en azul lleno como cifra principal; carteles
  ocupados con el % de ocupación; campañas activas; «Por vencer» en ámbar con la cantidad de
  reservas de la lista). Debajo, las reservas por vencer como lista: campaña en negrita, cartel en
  gris y fecha de fin a la derecha; la que vence hoy, con etiqueta ámbar «Vence hoy». Todo sale de
  `GET /api/reservas/panel/`, sin cambios de API.
- **Ficha de cliente como página propia:** «Ver ficha» reemplaza la lista por la ficha (sin router:
  estado de la página, como hoy). La ruta de la barra superior pasa a `Clientes / <cliente>`, con
  «Clientes» como enlace para volver, y hay un botón «← Volver a clientes».
  - Encabezado en un bloque azul: círculo con las iniciales, tipo de cliente en mayúsculas, nombre
    grande, razón social · correo · estado, y a la derecha las cantidades de marcas, campañas,
    contactos e interacciones.
  - Debajo, dos columnas: a la izquierda las secciones (Campañas, Marcas, Interacciones) con su
    contador, y la sección elegida en azul lleno; y, si es Intermediario formal, la card de
    contactos (avatar con iniciales, nombre, cargo, «principal» si lo es) con «Nuevo contacto». A
    la derecha, el contenido de la sección elegida.
  - Campañas como cards celestes con filtro por estado; ninguna destacada en azul.
  - La ficha de marca (`MarcasPage`) sigue el mismo patrón, más chica.
- **Ingresos, Por rubro o grupo y Ocupación:**
  - Cifras arriba (total del período y, según el reporte, días-cupo u ocupación promedio).
  - Selector de período propio (`shared/SelectorPeriodo.tsx`): dos selectores «Mes» y «Año» por
    extremo, con los meses escritos («Enero 2026»), en lugar del `input type="month"` del
    navegador, que se lee mal.
  - Encabezados de meses abreviados y legibles («Ene 2026»), primera columna fija al desplazar.
  - Ocupación: títulos de sección («Evolución por modalidad», «Mapa de calor por cartel») como
    encabezados de card con su bajada.
- **Ítems a facturar:** el resumen (ítems, neto, IVA, total, costos, neto final) pasa a una fila de
  cifras alineadas; «Envíos a facturar» y la tabla de ítems, debajo, en cards.
- **Disponibilidad:**
  - Pestañas «Hoy» y «Calendario» en el encabezado de la página, como filtros tipo píldora.
  - Calendario: cada celda pasa de la cajita «1/1» a una barra de ocupación con el texto
    `ocupados/capacidad`: celeste según el porcentaje y ámbar cuando está lleno; vacía cuando está
    libre. Al tocar una celda ocupada se sigue viendo la campaña, como hoy.
- **Parámetros:** cada opción en una card con interruptor, título y explicación en gris; el botón
  Guardar abajo a la derecha.

## Fuera de alcance

- Datos nuevos: ninguna cifra que el sistema no calcule hoy (por ejemplo, facturación en el Panel)
  ni campos nuevos.
- Cambios de API o de reglas.
- Navegación con URL (router).

## Migraciones

Ninguna.

## Reglas provisorias que se usan

Ninguna nueva; se muestran las que ya se aplican (RN-001 y RN-002 en Parámetros).

## Cómo se prueba

- Tests por pantalla de lo nuevo: las cifras del Panel salen de la respuesta de la API y «Vence
  hoy» se marca solo para la fecha de hoy; la ficha de cliente abre y vuelve a la lista (botón y
  ruta); `SelectorPeriodo` arma `AAAA-MM` y no permite fin anterior al inicio; el calendario
  muestra la barra y el texto `ocupados/capacidad`, y ámbar si está lleno; Parámetros guarda con
  los interruptores.
- Los tests existentes siguen pasando con los cambios de estructura mínimos.
- Revisión visual con Gonza en el navegador.
- Definition of Done completa.

## Registro de gates

- Gate 1 (plan): aprobado por Gonza el 2026-10-28.
- Gate 2 (verificación): 2026-10-28, ruff, mypy, makemigrations y pre-commit (gitleaks) limpios; pytest 787 passed, 96,90 %; frontend format, lint, typecheck, 365 tests (92,32 % sentencias, 94,36 % líneas) y build en verde. Revisión visual aprobada por Gonza el 2026-10-28.
- Gate 3 (PR):
