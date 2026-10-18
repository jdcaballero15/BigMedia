# Estándares de código

Versión larga de las secciones 3 y 5 de [`CLAUDE.md`](../CLAUDE.md). Para cada regla: qué dice, un ejemplo correcto, uno incorrecto y **cómo se verifica**. La configuración exacta vive en `pyproject.toml` (raíz) y en la configuración del frontend; la justificación, en [ADR-0004](adr/0004-gates-de-calidad-estrictos.md).

Si una regla estorba, no se desactiva para pasar el CI: se discute y, si corresponde, se cambia con un ADR.

## Python

### Tipado completo

Toda función lleva tipos en parámetros y retorno. `mypy --strict` con `django-stubs` y `djangorestframework-stubs`.

```python
# Correcto
def calcular_importe(tarifa: Decimal, dias: int) -> Decimal: ...

# Incorrecto
def calcular_importe(tarifa, dias): ...
```

Verificación: mypy en el job `tipos` del CI (no corre en pre-commit porque con los stubs de Django es lento) y ruff `ANN`.

### `type: ignore` solo con código y comentario

```python
# Correcto
valor = campo.get()  # type: ignore[attr-defined]  # el stub de DRF no declara get()

# Incorrecto
valor = campo.get()  # type: ignore
```

Verificación: mypy con `ignore-without-code` (habilitado con `enable_error_code`, porque `strict` no lo incluye) y ruff `PGH003` (`type: ignore` genérico). Tampoco se usa `# noqa` general: lo verifica ruff `PGH004`.

### Dinero con `Decimal`

Tarifas, importes y costos son `Decimal`, nunca `float`. El redondeo es explícito: `quantize(Decimal("0.01"), ROUND_HALF_UP)`.

```python
# Correcto
from decimal import ROUND_HALF_UP, Decimal
total = (tarifa * dias).quantize(Decimal("0.01"), ROUND_HALF_UP)

# Incorrecto
total = float(tarifa) * dias
```

Verificación: revisión del PR y tests de las reglas de facturación; mypy detecta mezclas de `float` y `Decimal`.

### Fechas con zona

Nada de `datetime.now()` ni `datetime.utcnow()` sin zona; se usa `django.utils.timezone.now()` o se pasa `tz`.

```python
# Correcto
from django.utils import timezone
ahora = timezone.now()

# Incorrecto
ahora = datetime.now()
```

Verificación: ruff `DTZ`.

### Sin `print`

Se usa `logging`. Nunca se registran datos personales ni credenciales.

```python
# Correcto
logger.info("Reserva confirmada", extra={"reserva_id": reserva.pk})

# Incorrecto
print("Reserva confirmada", reserva.cliente.email)
```

Verificación: ruff `T20`; los datos personales en logs, revisión del PR.

### Excepciones específicas

Se captura la excepción concreta. Sin `except Exception` ni `except:` desnudo.

```python
# Correcto
try:
    importe = Decimal(texto)
except InvalidOperation as exc:
    raise ValidationError("Importe inválido") from exc

# Incorrecto
try:
    importe = Decimal(texto)
except Exception:
    importe = Decimal(0)
```

Verificación: ruff `BLE` y `B`.

### Funciones cortas

Hasta 50 líneas y complejidad ciclomática hasta 10. Si no entra, se divide.

Verificación: ruff `C90` (`max-complexity = 10`). El límite de 50 líneas lo verifica la revisión del PR.

### Otras reglas de ruff

Se aplican `E`, `W`, `F`, `I`, `UP`, `B`, `S`, `ANN`, `PT`, `C90`, `SIM`, `RET`, `ARG`, `PTH`, `DTZ`, `T20`, `BLE`, `RUF`, `DJ` y `PGH`, con línea de 100 caracteres y Python 3.12. Verificación: `ruff format --check` y `ruff check` en el job `lint-python` y en pre-commit.

## Django

### Reglas de negocio en servicios o en el modelo

Las vistas y los serializers reciben, validan formato y delegan. La regla vive en una función de servicio (`apps/<app>/services.py`) o en el modelo.

```python
# Correcto
class ConfirmarReservaView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        reserva = servicios.confirmar_reserva(pk, usuario=request.user)
        return Response(ReservaSerializer(reserva).data)

# Incorrecto: la vista decide si hay cupo
class ConfirmarReservaView(APIView):
    def post(self, request, pk):
        if Reserva.objects.filter(cartel=...).count() < cartel.capacidad:
            ...
```

Verificación: revisión del PR y tests de servicio.

### Confirmaciones con bloqueo de fila

Todo lo que depende de disponibilidad corre dentro de `transaction.atomic()` y bloquea la fila del cartel con `select_for_update()` antes de verificar la ocupación (ver la [regla crítica](arquitectura.md#5-regla-crítica-de-disponibilidad)).

```python
# Correcto
with transaction.atomic():
    cartel = Cartel.objects.select_for_update().get(pk=cartel_id)
    verificar_ocupacion(cartel, desde, hasta)
    Reserva.objects.create(...)

# Incorrecto: verificar y crear sin bloquear
if hay_cupo(cartel_id, desde, hasta):
    Reserva.objects.create(...)
```

Verificación: tests de concurrencia contra PostgreSQL y revisión del PR.

### Baja lógica

Los datos no se borran desde la API: se marcan como inactivos. Nunca `DELETE` desde un endpoint.

```python
# Correcto
cartel.activo = False
cartel.save(update_fields=["activo"])

# Incorrecto
cartel.delete()
```

Verificación: revisión del PR; los viewsets no exponen `destroy`.

### Migraciones revisadas y comprobadas

Todo cambio de modelo trae su migración, revisada a mano antes del commit. El CI corre `makemigrations --check --dry-run` y falla si un modelo cambió sin migración. Los cambios de esquema conservan compatibilidad con la versión anterior durante el despliegue.

Verificación: job `tests-backend` y revisión del PR.

## Decisiones de configuración

Las herramientas están configuradas con estas decisiones (detalle y alternativas en [ADR-0004](adr/0004-gates-de-calidad-estrictos.md)):

- **`RUF012` ignorado.** Django y DRF declaran listas mutables como atributos de clase (`Meta.ordering`, `fields`, `permission_classes`). Pasarlas a tuplas cambia las opciones de los modelos y genera migraciones; anotarlas con `ClassVar` agrega ruido.
- **Migraciones excluidas de ruff y mypy.** Es código generado y el único código propio excluido de ruff y mypy.
- **Excepciones en tests.** En `**/tests/**/*.py` ruff ignora `S101`, `S105`, `S106`, `S603` (subprocesos con `sys.executable` en los tests de settings de producción), `ANN001` y `ANN201` (anotaciones de parámetros y retornos opcionales) y `ARG001` (fixtures de pytest que se piden solo por su efecto). mypy relaja `disallow_untyped_defs`, `disallow_incomplete_defs` y `disallow_untyped_calls` solo en `tests.*`.
- **`security.W005` y `security.W021` silenciados solo en producción.** El dominio es un subdominio de `onrender.com` que no controlamos y el preload de HSTS es difícil de revertir. Se revisa si se usa un dominio propio.
- **`PGH` en ruff y `ignore-without-code` en mypy.** Ruff suma la familia `PGH` (`PGH003` para `type: ignore` genérico, `PGH004` para `noqa` genérico) y mypy habilita `enable_error_code = ["ignore-without-code"]`, que `strict` no incluye.
- **Frontend: el umbral de 80 % aplica a líneas y sentencias.** Funciones y ramas se informan sin umbral.

## TypeScript

- `"strict": true` explícito en `tsconfig.app.json` y `tsconfig.node.json`.
- Sin `any` ni `@ts-ignore`.
- Formato con Prettier; lint con oxlint.

```ts
// Correcto
function total(items: Item[]): number { ... }

// Incorrecto
function total(items: any) { ... }   // @ts-ignore arriba
```

Verificación: Prettier y oxlint en el job `frontend` del CI; `npm run typecheck` (`tsc -b`) con `strict` detecta los `any` implícitos. Los `any` explícitos y los `@ts-ignore` no los detecta ninguna herramienta: los verifica la revisión del PR.

## Tests

- **Siempre contra PostgreSQL.** No hay modo sin base: sin PostgreSQL, `pytest` aborta con un mensaje claro. El CI falla si algún test queda salteado.
- **Sin red.** Los tests no llaman a servicios externos.
- **Nombre** `test_<qué>_<condición>_<resultado>` en código nuevo, por ejemplo `test_confirmar_reserva_sin_cupo_rechaza`.
- **Marcador `regla`.** Los tests que verifican una regla de negocio llevan `@pytest.mark.regla("RN-xxx")`; `pytest -m regla` los lista.

  ```python
  @pytest.mark.regla("RN-001")
  def test_reservas_mismo_dia_limite_comparten_cupo() -> None: ...
  ```

- **Todo bug empieza con un test que lo reproduce**, que falla antes del arreglo y pasa después.
- **Coverage mínimo:** backend 80 % (sentencias y ramas, `fail_under = 80`, sin contar migraciones); frontend 80 % de líneas y de sentencias.

Verificación: `pytest --strict-markers` y coverage en el job `tests-backend`; vitest con umbral en el job `frontend`; el nombre y el test del bug, en la revisión del PR. Bajar un umbral requiere un ADR nuevo.

## Datos y credenciales

- **Nunca datos personales reales** en desarrollo, pruebas ni logs. Se usan datos ficticios.
- **Nunca credenciales en el código.** Todo por variables de entorno; `.env`, `*.pem`, `*.key`, `*.p12` y `*.crt` no se commitean. Ver [gestión de configuración](gestion-de-configuracion.md#4-credenciales).

```python
# Correcto
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Incorrecto
SECRET_KEY = "django-insecure-abc123"
```

Verificación: gitleaks en el job `secretos` y en pre-commit, `detect-private-key` en pre-commit y revisión del PR para los datos personales.
