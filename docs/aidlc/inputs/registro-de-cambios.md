# Registro de cambios de las historias de usuario

Cada cambio a historias o reglas ([`historias-de-usuario.md`](historias-de-usuario.md) o [`reglas-de-negocio.md`](../reglas-de-negocio.md)) agrega una fila, en el mismo PR
que lo hace. Los IDs de historia nunca se reutilizan ni se renumeran: una historia eliminada se
marca `(retirada AAAA-MM-DD: motivo)` y una fusionada `(fusionada en HU-xxx)`.

| Fecha | Pedido por | Issue | HUs | Qué cambió y por qué | Reglas |
| --- | --- | --- | --- | --- | --- |
| 2026-10-16 | Equipo | — | todas | Las historias pasan a esta carpeta y este documento se vuelve la fuente de verdad. El contenido no cambia. | — |
| 2026-10-19 | Juan Diego | — | HU-016, HU-018 | El cliente no tiene datos obligatorios (ni nombre ni tipo): se completan a medida que se conocen. Se muestra por su «nombre» (deja de llamarse «nombre de fantasía»); sin nombre, como «Cliente sin nombre #id». Un cliente directo sin nombre no genera marca homónima. | — |
