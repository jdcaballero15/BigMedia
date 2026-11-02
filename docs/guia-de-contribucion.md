# Guía de contribución

Para quien llega a mantener Big Media sin haber estado en el equipo original. Esta página es un
recorrido de diez minutos: dice qué leer y en qué orden. Lo que ya está documentado se enlaza,
no se repite.

## 1. Entendé el sistema

1. [`README.md`](../README.md) de la raíz: qué es Big Media y qué hay hecho.
2. [`arquitectura.md`](arquitectura.md): un monolito Django con una app por área de negocio, y
   qué app puede importar de cuál.
3. [`modelo-de-datos.md`](modelo-de-datos.md): qué guarda cada app y sus reglas.
4. [`aidlc/reglas-de-negocio.md`](aidlc/reglas-de-negocio.md): las reglas `RN-xxx`, su estado
   (confirmada, provisoria o pendiente) y dónde vive cada una en el código.

Lo más delicado está en `reservas`: un cartel no puede venderse por encima de su capacidad. La
confirmación de reservas ocurre solo en el servidor, dentro de una transacción con el cartel
bloqueado (regla 7 de [`CLAUDE.md`](../CLAUDE.md#3-reglas-absolutas)).

## 2. Prepará el entorno

Seguí [`operacion/desarrollo-local.md`](operacion/desarrollo-local.md). Tiene los comandos para
Windows, macOS y Linux, y deja andando base, API, frontend y tests. Con `cargar_datos_ejemplo`
tenés datos inventados para probar.

## 3. Aprendé las reglas del repositorio

[`CLAUDE.md`](../CLAUDE.md) es normativo: si algo choca con otro documento, gana `CLAUDE.md`. Lo
mínimo:

- **Idioma:** documentación, PRs y mensajes en español; asuntos de commit en inglés.
- **Reglas absolutas** (§3): nada directo en `main` ni en `develop`, ninguna credencial en el
  código, `Decimal` para dinero, ningún dato personal real, nunca `--no-verify`.
- **Estándares de código** (§5), con ejemplos en
  [`estandares-de-codigo.md`](estandares-de-codigo.md).

## 4. Hacé un cambio

1. **De dónde sale el trabajo:** una épica de [`aidlc/roadmap.md`](aidlc/roadmap.md) o un issue
   triado. Los pedidos de Big Media se cargan con la plantilla
   [«Pedido de Seba»](../.github/ISSUE_TEMPLATE/pedido.yml).
2. **Plan de unidad:** antes de tocar código se escribe el plan en `docs/aidlc/units/` y alguien
   del equipo lo aprueba. Pasos y plantilla en
   [`.claude/aidlc/workflow.md`](../.claude/aidlc/workflow.md).
3. **Rama:** desde `develop`, con el patrón `feature/<modulo>-<descripcion>`,
   `fix/<modulo>-<descripcion>`, `docs/<descripcion>` o `chore/<descripcion>`. Detalle en
   [`gestion-de-configuracion.md`](gestion-de-configuracion.md).
4. **Tests primero** para un bug: el test que lo reproduce va antes del arreglo. Convenciones en
   [`backend/tests/README.md`](../backend/tests/README.md).
5. **Commits:** `<tipo>(<modulo>): <qué hace>`, en inglés (§6 de `CLAUDE.md`). El CI rechaza los
   que no cumplen.
6. **Verificá** con los comandos de la Definition of Done (§7 de `CLAUDE.md`, y en
   [desarrollo local](operacion/desarrollo-local.md#verificación-completa)). Coverage mínimo 80 %
   en backend y frontend.
7. **Pull Request a `develop`**, con la
   [plantilla](../.github/pull_request_template.md) completa. El CI repite todos los controles.

## 5. Cambiar una historia o una regla

Las historias y las reglas cambian con el uso. Un cambio de valor o de estado de una regla va en
su propio PR `docs/historias-<descripcion>`, sin código, con una entrada en
[`aidlc/inputs/registro-de-cambios.md`](aidlc/inputs/registro-de-cambios.md). Ver la sección 9 de
[`workflow.md`](../.claude/aidlc/workflow.md).

## 6. Decisiones técnicas

Una decisión que cambia la estructura, suma una dependencia o se aparta de una regla lleva un ADR
en [`adr/`](adr/README.md), con la plantilla `0000-plantilla.md`. No se crean carpetas nuevas en
la raíz sin un ADR aprobado.

## 7. Publicar

`develop` corre solo CI y actualiza staging; `main` es producción. Un release es un PR de
`develop` a `main`. Cómo se despliega, se verifica y se recupera:
[`operacion/despliegue-render.md`](operacion/despliegue-render.md).
