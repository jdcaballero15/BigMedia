# Registro de cambios de las historias de usuario

Cada cambio a historias o reglas ([`historias-de-usuario.md`](historias-de-usuario.md) o [`reglas-de-negocio.md`](../reglas-de-negocio.md)) agrega una fila, en el mismo PR
que lo hace. Los IDs de historia nunca se reutilizan ni se renumeran: una historia eliminada se
marca `(retirada AAAA-MM-DD: motivo)` y una fusionada `(fusionada en HU-xxx)`.

| Fecha | Pedido por | Issue | HUs | Qué cambió y por qué | Reglas |
| --- | --- | --- | --- | --- | --- |
| 2026-10-16 | Equipo | — | todas | Las historias pasan a esta carpeta y este documento se vuelve la fuente de verdad. El contenido no cambia. | — |
| 2026-10-19 | Juan Diego | — | HU-016, HU-018 | El cliente no tiene datos obligatorios (ni nombre ni tipo): se completan a medida que se conocen. Se muestra por su «nombre» (deja de llamarse «nombre de fantasía»); sin nombre, como «Cliente sin nombre #id». Un cliente directo sin nombre no genera marca homónima. | — |
| 2026-10-19 | Seba | — | HU-027 | Una marca sí puede cambiar de agencia o comprarse por dos clientes, así que la campaña lleva un cliente que factura propio y opcional que reemplaza la deducción desde la marca. HU-027 no se descarta. | RN-014 pasa de «se deduce siempre de la marca» a cliente propio opcional en la campaña |
| 2026-10-19 | Seba | — | HU-028, HU-057, HU-023 | Input para E5 (reservas): en circuitos grandes (séxtuples, séptuples, PPL, banderolas, carteleras) no se obliga a cargar la posición exacta; basta cantidad + tipo de cartel + importes. Además prefiere el flujo campaña → reservas (crear las reservas desde la campaña). Queda por confirmar si «séptuples» es un formato nuevo. | RN-005 (input que respalda el slot genérico y lo amplía a otros circuitos) |
| 2026-10-19 | Juan Diego | — | HU-031 | El motor de disponibilidad cuenta los cupos por pico diario (ocupación máxima por tramo) en vez de contar todas las reservas que tocan el rango: es exacto y no rechaza reservas que en realidad entran. | RN-003 pasa de «conteo simple» a «pico diario» |
| 2026-10-23 | Gonza | — | HU-004 | Gerencia deja de ser sinónimo del rol Lectura: es un permiso aparte (ingresos y auditoría) que se suma a cualquier rol, como ya se había decidido en la unidad `permiso-ingresos`. Así Seba y Ale pueden ser Gerencia y también Operativo. | — |
| 2026-10-28 | Gonza | — | HU-017, HU-022, HU-050 | Se implementa el grupo económico: un catálogo editable de grupos, como los rubros. Cada marca pertenece a lo sumo a un grupo, opcional e independiente del cliente que factura. Lo usan la ficha de la marca y el corte por grupo del reporte. Lo editan Operativo y Administrador. Queda provisoria hasta que Seba la confirme. | RN-016 pasa de `pendiente` a `provisoria` |
| 2026-10-28 | Gonza | — | HU-020, HU-022 | Una interacción puede llevar una marca opcional, para registrar conversaciones antes de que exista la campaña. La marca tiene que ser del cliente de la interacción y, si hay campaña, la campaña tiene que ser de esa marca. La interacción aparece también en la ficha de la marca. Queda provisoria hasta que Seba la confirme. | RN-018 pasa de `pendiente` a `provisoria` |
