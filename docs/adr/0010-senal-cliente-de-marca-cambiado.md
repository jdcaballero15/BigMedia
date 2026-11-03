# ADR-0010 — Señal de `clientes` cuando una marca cambia de cliente

- **Estado:** Propuesto
- **Fecha:** 2026-11-03
- **Decidido por:** Gonza
- **Módulos afectados:** clientes, campanias, docs

---

## Contexto

HU-027 (criterio 3) pide que, cuando una marca cambia de cliente, las campañas que ya existían
conserven el cliente que las facturaba. El cambio se hace en `clientes` (edición de la marca), pero
lo que hay que escribir está en `campanias` (`Campania.cliente_facturacion`). La tabla de
dependencias de `CLAUDE.md` no deja que `clientes` importe de `campanias`.

## Decisión

> Vamos a declarar en `clientes` la señal `cliente_de_marca_cambiado` y a escucharla desde
> `campanias`.

`clientes` emite la señal desde su servicio de actualización de marca, dentro de la misma
transacción que guarda la marca, y no sabe quién la escucha. `campanias` conecta su receptor en
`CampaniasConfig.ready()` y estampa el cliente anterior en las campañas sin cliente propio. La
implementación entra en la unidad [cliente-que-factura](../aidlc/units/cliente-que-factura.md).

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| `pre_save` de Django sobre `Marca`, escuchado en `campanias` | Cubre cualquier guardado sin tocar `clientes` | Es implícito: cualquier guardado de una marca hace una consulta extra para comparar el cliente, y el evento de negocio no queda nombrado |
| Acción en `campanias` para cambiar el cliente de una marca | Sin señales | Cambia la API y el formulario de marca, y saca de `clientes` la edición de su propio modelo |
| Permitir que `clientes` importe de `campanias` | Directo | Crea un ciclo entre las dos apps |

## Consecuencias

**Positivas**
- La tabla de dependencias no cambia y no hay ciclo.
- El evento de negocio tiene nombre y un solo lugar donde se emite.

**Negativas / costo que aceptamos**
- Es la primera señal del repositorio: leyendo `clientes` no se ve quién reacciona. Se documenta en
  la señal y en el receptor.
- Un cambio de cliente que no pase por el servicio (por ejemplo, un `update()` masivo) no estampa.
  La vista y el admin usan el servicio.
