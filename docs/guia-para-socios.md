# Guía del proyecto para un socio de Big Media

Esta guía explica cómo se organiza el trabajo del sistema, qué se puede usar hoy y cómo una necesidad del negocio llega a producción. No hace falta saber programar para participar en las decisiones.

**Foto del repositorio al 18 de octubre de 2026.** El sistema permite iniciar sesión y administrar el inventario de carteles y sus catálogos. Está publicado en Render, en un plan gratuito para mostrarlo y probarlo (ver [despliegue](operacion/despliegue-render.md)). Las campañas, las reservas y el cálculo de disponibilidad todavía no están implementados. Por eso, ver una función en las historias de usuario **no significa** que ya esté disponible en la aplicación.

## La idea general

El repositorio es la carpeta donde viven la aplicación, sus instrucciones y el historial de cambios. La web que usa una persona y la parte que guarda y valida los datos se desarrollan juntas. Para entender o decidir qué se construye, estos son los documentos más útiles:

| Documento | Pregunta que responde |
| --- | --- |
| [Roadmap](aidlc/roadmap.md) | ¿Qué se está haciendo y qué viene después? |
| [Historias de usuario](aidlc/inputs/historias-de-usuario.md) | ¿Qué necesita poder hacer cada persona en el sistema? |
| [Reglas de negocio](aidlc/reglas-de-negocio.md) | ¿Cómo debe comportarse el sistema en situaciones concretas? ¿Qué falta confirmar? |
| [Mapa de unidades](aidlc/units.md) | ¿Qué trabajos están pendientes, en curso, en revisión o terminados? |
| [Registro de cambios](aidlc/inputs/registro-de-cambios.md) | ¿Qué pedido cambió una historia o una regla, cuándo y por qué? |
| [Decisiones importantes (ADR)](adr/README.md) | ¿Por qué se eligió una forma de organizar o construir el sistema? |

Las **historias de usuario** describen necesidades, por ejemplo, poder crear una reserva. Cada una tiene un número `HU-xxx` que permite seguirla aunque el texto cambie. Se agrupan en grandes temas llamados *épicas*: inventario, clientes, campañas, reservas, facturación, etc. La prioridad *Must* significa indispensable para el objetivo definido; *Should* significa importante; *Could*, deseable. La prioridad no indica que algo ya esté hecho.

Las **reglas de negocio** detallan decisiones que afectan al trabajo diario. Por ejemplo: si dos reservas pueden compartir el día en que una termina y la otra comienza. Cada regla tiene un número `RN-xxx`. Una regla puede estar **pendiente** de respuesta, ser **provisoria** mientras Big Media confirma, estar **confirmada** o haber sido **reemplazada**. Si figura como provisoria, conviene revisar el valor antes de darlo por definitivo.

Un **ADR** es un registro breve de una decisión de estructura o tecnología: qué se eligió, por qué y qué alternativas se descartaron. Sirve para no volver a discutir sin contexto una decisión importante. Un cambio común en la forma de vender o reservar carteles se registra en las historias y reglas de negocio; solo requiere un ADR si también cambia una decisión técnica importante.

## De un pedido a una mejora publicada

1. **Se registra el pedido.** Si Seba o Ale comenta algo por WhatsApp, llamada o durante el uso, se carga un *issue* (una ficha de seguimiento) con la [plantilla «Pedido de Seba»](../.github/ISSUE_TEMPLATE/pedido.yml). Anota fecha, palabras del pedido, pantalla afectada, urgencia y, si hay, capturas. No se incluyen datos personales reales de clientes.
2. **Se decide qué significa.** El equipo deja constancia en el issue si cambia una regla, agrega o ajusta una historia, informa un error o se descarta con un motivo. Un pedido anotado todavía no es una promesa de entrega. Si cambia una historia o regla, se actualiza el documento correspondiente y el registro de cambios.
3. **Se prioriza y se planifica.** El [roadmap](aidlc/roadmap.md) muestra el orden de los temas. Cada trabajo concreto tiene una *unidad* con objetivo, alcance, reglas involucradas y forma de comprobarlo. Juan Diego aprueba el plan antes de modificar la aplicación.
4. **Se construye y se comprueba.** La persona que desarrolla trabaja en una rama separada. Hace pruebas, muestra los resultados reales y espera la aprobación prevista en el flujo de trabajo.
5. **Se revisa el cambio.** Se abre un *Pull Request* o **PR**: una propuesta para incorporar ese trabajo. La [plantilla de PR](../.github/pull_request_template.md) pide explicar qué resuelve, qué reglas toca, cómo se probó y qué issue cierra. Otra revisión y los controles automáticos ayudan a detectar problemas antes de incorporarlo.
6. **Se publica cuando corresponde.** Los cambios aprobados se reúnen primero en `develop`. Para llevarlos a producción se hace un PR de `develop` a `main`. [Render](operacion/despliegue-render.md) está configurado para publicar desde `main` cuando pasan los controles requeridos. No hay un entorno de prueba en línea (*staging*) separado por ahora.

Una **rama** es una copia de trabajo que permite preparar un cambio sin afectar a quienes usan el sistema. `develop` reúne trabajos en preparación; `main` representa lo listo para producción. Una corrección urgente en producción sigue un camino especial (*hotfix*) y después se incorpora también a `develop`. Incluso los cambios de documentación pasan por PR.

## Qué comprueba la integración continua (CI)

La **CI** es una serie de verificaciones automáticas que GitHub ejecuta cuando se propone o incorpora un cambio. Un resultado verde significa que **pasaron las comprobaciones configuradas**; no reemplaza la revisión de si la función resuelve la necesidad del negocio.

**Hoy, en este estado del repositorio**, cada PR hacia `develop` o `main` pasa por ocho controles automáticos: nombre de la rama y de los commits, estilo y errores comunes del código del servidor, verificación de tipos, configuración de producción, pruebas del servidor contra una base PostgreSQL con cobertura mínima del 80 %, controles de la web (formato, revisión, tipos, pruebas con cobertura mínima del 80 % y construcción), búsqueda de credenciales filtradas y construcción de la imagen de producción. Las ramas `main` y `develop` están protegidas en GitHub: no se puede incorporar un cambio con un control en rojo ni modificarlas sin PR. El detalle está en [gestión de configuración](gestion-de-configuracion.md) y en el [ADR-0004](adr/0004-gates-de-calidad-estrictos.md).

Para saber qué se verificó en un cambio puntual, mirá los resultados del **PR concreto** y su sección «Cómo se verificó». No alcanza con leer la lista de controles previstos.

## Qué puede aportar un socio sin tocar código

- **Aclarar reglas del negocio:** revisar las `RN-xxx` pendientes o provisorias, sobre todo las que afectan la disponibilidad y la confirmación de reservas. Una respuesta debería incluir un ejemplo real y quién la confirmó.
- **Describir el problema antes que la solución:** contar qué intentaba hacer la persona, qué pasó, qué esperaba y cuánta urgencia tiene. Eso permite registrar bien el pedido y decidir si es error, cambio de regla o función nueva.
- **Revisar prioridades:** mirar el roadmap y decir qué necesita Big Media primero. Hoy el inventario está disponible; clientes y marcas, campañas y luego reservas aparecen como próximos pasos por sus dependencias.
- **Validar el resultado funcional:** en un PR o demostración, comprobar con casos reales si el cambio sirve para el trabajo diario. Los controles automáticos comprueban fallas técnicas, pero no pueden decidir por Big Media cómo se vende un cartel.

**Ejemplo de recorrido:** «Necesitamos reservar el mismo cartel para dos campañas el día 15». Se registra el caso en un issue, se consulta la regla [RN-001](aidlc/reglas-de-negocio.md) sobre el día límite, Big Media confirma el comportamiento esperado, se actualizan regla e historia si corresponde, se planifica la mejora, se implementa y se revisa el PR. Solo después de integrarla y publicarla se considera disponible para usar.

## Por dónde empezar

Si solo tenés diez minutos, leé el [roadmap](aidlc/roadmap.md), revisá las reglas **pendientes** y **provisorias** en el [catálogo](aidlc/reglas-de-negocio.md), y mirá el [mapa de unidades](aidlc/units.md). Para conocer el detalle de una función, buscá su `HU-xxx` en las [historias](aidlc/inputs/historias-de-usuario.md). Para entender por qué se tomó una decisión importante, buscala en los [ADR](adr/README.md).
