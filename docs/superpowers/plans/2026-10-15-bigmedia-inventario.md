# Big Media Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que un usuario operativo cargue, edite y busque el inventario de carteles de Big Media desde la web, con datos persistidos en PostgreSQL.

**Architecture:** Django REST Framework expone autenticación por sesión y recursos de inventario bajo `/api/`. PostgreSQL guarda catálogos y carteles; React consume la API con cookies de sesión y CSRF. Las reglas se validan en el servidor y las pantallas muestran sus errores.

**Tech Stack:** Python 3.12, Django 5.2, Django REST Framework, PostgreSQL 17, React 19, TypeScript 6, Vite 8, pytest-django, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-15-bigmedia-inventario-design.md`.

## Global Constraints

- No inventar carteles ni tarifas. Sembrar solo los siete formatos, nueve departamentos y cinco estados confirmados o descritos en la especificación.
- «Todos» es únicamente el filtro sin zona seleccionada.
- Capacidad y tarifa se validan en el servidor; la capacidad inicial de un cartel se copia del formato y puede editarse.
- No crear endpoints `DELETE`; la baja es lógica y el histórico queda consultable.
- Las escrituras exigen usuario administrador o miembro del grupo Operativo.
- No agregar campañas, cotizaciones, reservas, importación CSV ni reportes en esta entrega.
- No tocar `docs/decisiones/`, `docs/importacion/` ni `docs/ux/`, que pueden pertenecer al trabajo paralelo de Claude.

## Review Focus

1. Una petición anónima o sin CSRF no puede modificar catálogos ni carteles; verificar 401/403 y que no se crea el registro.
2. Una referencia a formato, zona o proveedor inactivo no se acepta en un cartel nuevo; una referencia histórica puede permanecer al editar otro campo.
3. Un cartel de baja no aparece en la lista ordinaria, pero sí con `incluir_bajas=1` y por su detalle.
4. La búsqueda `Martin` encuentra una dirección con `Martín`, y los filtros simultáneos restringen mediante intersección.
5. Un nombre duplicado, capacidad 0 o tarifa negativa devuelve un error de campo y no deja una escritura parcial.

---

## Mapa de archivos

- `backend/config/auth_views.py`: sesión, CSRF, login y logout.
- `backend/apps/inventario/models.py`: proveedores, formatos, zonas, estados y carteles; propiedades legibles y normalización de dirección.
- `backend/apps/inventario/serializers.py`: validaciones de entrada y representación de salida.
- `backend/apps/inventario/views.py`: colecciones, detalle, filtros y permisos.
- `backend/apps/inventario/urls.py`: rutas del módulo.
- `backend/apps/inventario/migrations/`: esquema y datos iniciales idempotentes.
- `backend/tests/test_auth.py`, `test_inventory_catalogs.py`, `test_carteles.py`: pruebas de API y reglas con PostgreSQL.
- `frontend/src/shared/api.ts`: fetch JSON, cookies, CSRF y errores de campos.
- `frontend/src/features/inventario/`: lista, filtros, formularios y catálogos.
- `frontend/src/app/`: login y navegación; `frontend/src/App.tsx` integra pantallas.
- `docs/operacion/desarrollo-local.md`: alta del primer usuario y uso del módulo.

### Task 1: Sesión operativa protegida

**Files:** Create `backend/config/auth_views.py`, `backend/tests/test_auth.py`; modify `backend/config/urls.py`, `backend/config/settings.py`.

**Interfaces:** Produces `GET /api/auth/me/` (usuario o 401), `POST /api/auth/login/` (`username`, `password`), `POST /api/auth/logout/`. `GET /api/auth/me/` entrega cookie CSRF. Las vistas de inventario consumen la sesión Django y el grupo `Operativo`.

- [ ] **Step 1: Write the failing tests.** `test_me_anonymous`, `test_login_and_me`, `test_login_rejects_wrong_password`, `test_post_without_csrf_is_rejected`, `test_logout_revokes_session` usan `Client(enforce_csrf_checks=True)` y `User.objects.create_user`. Ejemplo:

```python
@pytest.mark.django_db
def test_me_anonymous():
    response = Client().get('/api/auth/me/')
    assert response.status_code == 401
```

- [ ] **Step 2: Run RED.** Desde `backend/`: `.\.venv\Scripts\python.exe -m pytest tests/test_auth.py -q`. Expected: 404 en `/api/auth/me/`.
- [ ] **Step 3: Implement.** Usar `authenticate`, `login`, `logout`, `ensure_csrf_cookie` y `csrf_protect`. Respuestas JSON sin información sensible; no desactivar middleware CSRF. Registrar tres rutas en `config/urls.py`.

```python
@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Iniciá sesión.'}, status=401)
    return JsonResponse({'username': request.user.username})
```

- [ ] **Step 4: Run GREEN.** `python -m pytest tests/test_auth.py -q`; Expected: las cinco pruebas pasan. `python manage.py check`; Expected: cero errores.
- [ ] **Step 5: Commit.** `git add backend/config backend/tests/test_auth.py` y `git commit -m "feat: add session authentication"`.

### Task 2: Catálogos de inventario y datos iniciales

**Files:** Create `backend/apps/__init__.py`, `backend/apps/inventario/{__init__,apps,models,serializers,views,urls}.py`, migraciones y `backend/tests/test_inventory_catalogs.py`; modify `backend/config/settings.py`, `backend/config/urls.py`, `backend/pyproject.toml` para incluir el paquete `apps*`.

**Interfaces:** Produces modelos `Proveedor`, `Formato`, `Zona`, `EstadoCartel`; endpoints `/api/inventario/proveedores/`, `/formatos/`, `/zonas/`, `/estados/`. Todos soportan GET/POST, detalle GET/PATCH y rechazan DELETE. `Formato` expone `modalidad` y `capacidad_predeterminada`; `EstadoCartel` expone `operativo` y `es_baja`.

- [ ] **Step 1: Write failing tests.** Probar migración con nueve zonas exactas y siete formatos, nombres únicos, capacidad predeterminada >=1, lista de activos por defecto, anónimo sin escritura, Operativo con escritura y método DELETE 405. Ejemplo:

```python
@pytest.mark.django_db
def test_seeded_zones():
    assert set(Zona.objects.values_list('nombre', flat=True)) == {
        'Ciudad', 'Godoy Cruz', 'Maipú', 'Luján de Cuyo', 'Guaymallén',
        'Las Heras', 'San Martín', 'Rivadavia', 'San Carlos',
    }
```

- [ ] **Step 2: Run RED.** `python -m pytest tests/test_inventory_catalogs.py -q`; Expected: falla importación de `apps.inventario`.
- [ ] **Step 3: Implement models and migrations.** Crear `AppConfig`, modelos con `UniqueConstraint(Lower('nombre'))`, `CheckConstraint` para capacidad, y migración de datos `RunPython` con claves estables. Sembrar los siete formatos exactos del spec, las nueve zonas de la captura y los cinco estados físicos; crear grupo Operativo y asignar permisos `view/add/change` a los cuatro modelos. `python manage.py makemigrations inventario`; inspeccionar la migración; `python manage.py migrate --noinput`.

```python
class Formato(models.Model):
    nombre = models.CharField(max_length=80)
    modalidad = models.CharField(max_length=10, choices=[('fija', 'Fija'), ('digital', 'Digital')])
    capacidad_predeterminada = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)
```

- [ ] **Step 4: Implement API.** Serializers validan nombre no vacío y capacidad. Viewsets usan `IsAuthenticated`, permiso de modelo para escrituras y `http_method_names = ['get', 'post', 'patch', 'head', 'options']`; el listado admite `?incluir_inactivos=1`. Registrar rutas con router DRF.
- [ ] **Step 5: Run GREEN.** `python -m pytest tests/test_inventory_catalogs.py -q`; Expected: todas pasan. `python manage.py check`; Expected: cero errores.
- [ ] **Step 6: Commit.** Agregar solo archivos del módulo, configuración y prueba; `git commit -m "feat: add inventory catalogs"`.

### Task 3: Carteles, reglas y búsqueda

**Files:** Modify `backend/apps/inventario/models.py`, `serializers.py`, `views.py`, `urls.py`; create migración y `backend/tests/test_carteles.py`.

**Interfaces:** Produces `Cartel` con `nombre_visible` y `direccion_busqueda`; `GET/POST /api/inventario/carteles/`, `GET/PATCH /api/inventario/carteles/{id}/`. Filtros `zona`, `formato`, `modalidad`, `estado`, `q`, `incluir_bajas`. La baja se aplica con PATCH de estado.

- [ ] **Step 1: Write failing tests.** Cubrir alta con capacidad heredada; capacidad editable; dirección/formato/zona obligatorios; tarifa negativa y capacidad 0 rechazadas; nombre legible; referencias inactivas rechazadas en alta pero permitidas si no cambian al editar; filtros combinados; búsqueda sin tilde; baja oculta por defecto; DELETE 405. Ejemplo:

```python
@pytest.mark.django_db
def test_cartel_inherits_format_capacity(operativo_client, formato, zona):
    response = operativo_client.post('/api/inventario/carteles/', {
        'formato': formato.pk, 'zona': zona.pk, 'direccion': 'Av. San Martín 1234',
        'tarifa_lista': '150000.00', 'estado': EstadoCartel.objects.get(codigo='activo').pk,
    })
    assert response.status_code == 201
    assert response.json()['capacidad'] == formato.capacidad_predeterminada
```

- [ ] **Step 2: Run RED.** `python -m pytest tests/test_carteles.py -q`; Expected: falta `Cartel` o su endpoint.
- [ ] **Step 3: Implement.** Campos y constraints en modelo; `save()` calcula `direccion_busqueda` con `unicodedata.normalize('NFKD', ...)` y `casefold()`. El serializer toma capacidad del formato al crear, valida catálogos activos y no altera capacidad al cambiar formato de un cartel existente. El queryset usa `select_related` y filtros exactos combinados; `q` busca en `direccion_busqueda`. La migración asigna permisos `view/add/change` de Cartel al grupo Operativo.

```python
def normalizar_busqueda(valor: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', valor.casefold())
                   if not unicodedata.combining(c))
```

- [ ] **Step 4: Run GREEN.** `python manage.py makemigrations inventario`, revisar SQL/esquema, `python manage.py migrate --noinput`, `python -m pytest tests/test_carteles.py -q`; Expected: todas pasan. Ejecutar la suite backend completa con `BIGMEDIA_RUN_DB_TESTS=1`; Expected: sin fallos.
- [ ] **Step 5: Commit.** `git commit -m "feat: add posters and inventory search"` con archivos explícitos.

### Task 4: Inicio de sesión y listado de carteles en React

**Files:** Create `frontend/src/shared/api.ts`, `frontend/src/app/Login.tsx`, `frontend/src/features/inventario/CartelesPage.tsx` y sus pruebas; modify `frontend/src/App.tsx`, `App.css`, `index.css`.

**Interfaces:** `apiGet<T>(path): Promise<T>` y `apiWrite<T>(path, method, body): Promise<T>` envían cookies; `apiWrite` incluye `X-CSRFToken`. `CartelesPage` consume catálogos y `GET /api/inventario/carteles/`.

- [ ] **Step 1: Write failing tests.** Probar que usuario anónimo ve login; login correcto muestra Carteles; filtros Zona/Formato/Estado y búsqueda cambian la consulta; el listado muestra nombre visible, capacidad y tarifa; error de red aparece sin pantalla en blanco. Ejemplo:

```tsx
test('muestra el inventario luego de iniciar sesión', async () => {
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Carteles' })).toBeDefined()
})
```

- [ ] **Step 2: Run RED.** `npm test -- --reporter=dot`; Expected: prueba nueva falla porque App solo muestra salud de API.
- [ ] **Step 3: Implement.** Cliente HTTP con errores tipados y CSRF, login, navegación y tabla con filtros. El filtro Todos omite el parámetro `zona`. La tabla no muestra IDs como nombre. Mantener estados de carga, vacío y error.
- [ ] **Step 4: Run GREEN.** `npm test -- --reporter=dot`, `npm run lint`, `npm run build`; Expected: sin fallos.
- [ ] **Step 5: Commit.** `git commit -m "feat: show authenticated inventory"`.

### Task 5: Formularios operativos y guía de uso

**Files:** Create `frontend/src/features/inventario/CartelForm.tsx`, `CatalogosPage.tsx` y pruebas; modify `CartelesPage.tsx`, `frontend/src/App.tsx`, `docs/operacion/desarrollo-local.md`.

**Interfaces:** Alta/edición de cartel con validaciones de API; administración de proveedores, formatos, zonas y estados; inactivación sin borrar. La capacidad se precarga al elegir formato solo al crear un cartel.

- [ ] **Step 1: Write failing tests.** Probar cartel nuevo con capacidad predeterminada, edición sin pisar capacidad, errores de campo, inactivar proveedor, dar de baja cartel y consultar bajas con el filtro. Ejemplo:

```tsx
test('precarga capacidad al elegir formato en un cartel nuevo', async () => {
  render(<CartelForm formatos={[{ id: 1, nombre: 'Séxtuples', capacidad_predeterminada: 6 }]} />)
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '1' } })
  expect((screen.getByLabelText('Capacidad') as HTMLInputElement).value).toBe('6')
})
```

- [ ] **Step 2: Run RED.** `npm test -- --reporter=dot`; Expected: falla importación de `CartelForm`.
- [ ] **Step 3: Implement.** Formularios con campos del spec, mensajes de validación, confirmación explícita de baja y recarga de lista tras guardar. Documentar en la guía cómo crear superusuario, asignar grupo Operativo, iniciar API/web y registrar el primer cartel; indicar que capacidad LED/séxtuples se verifica al cargar datos reales.
- [ ] **Step 4: Run GREEN.** `npm test -- --reporter=dot`, `npm run lint`, `npm run build`; Expected: sin fallos. Correr `python -m pytest tests -q` y `python manage.py check` con PostgreSQL; Expected: sin fallos.
- [ ] **Step 5: Commit.** `git commit -m "feat: edit inventory from web"` con los archivos del task.

## Verificación final

Desde una base vacía, `python manage.py migrate --noinput` siembra exactamente las nueve zonas de la captura. Con un usuario Operativo se crea un cartel, aparece en la lista y se encuentra con filtros. Se puede editar, inactivar y consultar su ficha; no se puede borrar. Ejecutar suite backend con PostgreSQL real, suite frontend, lint y build. Revisar que `git status` conserve intactos los documentos paralelos sin agregarlos a commits de este plan.
