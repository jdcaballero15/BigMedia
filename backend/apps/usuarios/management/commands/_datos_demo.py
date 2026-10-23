"""Lote «demo» de `cargar_datos_ejemplo`: datos inventados para mostrar todas las pantallas.

Tiene su propio centinela, así se suma a un staging que ya tiene el primer lote sin duplicarlo.
Las fechas son relativas al mes en que corre: de 5 meses atrás a 3 meses adelante.
"""

import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.auditoria.services import registrar_cambios
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca, Rubro
from apps.costos.models import Costo
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva
from apps.reservas.services import sumar_meses, validar_disponibilidad

SENTINELA_DEMO = "Distribuidora Andina"

PROVEEDORES = (
    ("Imprenta Cuyo", "Impresión de lonas y vinilos"),
    ("Fijaciones del Oeste", "Colocación y fijación"),
    ("ElectroLED Andes", "Mantenimiento de pantallas"),
    ("Estructuras Andinas", "Dueño de estructuras"),
)

RUBROS = ("Bebidas", "Indumentaria", "Alimentos", "Automotor", "Servicios financieros", "Salud")

# Rubro para las marcas del primer lote, que se crearon sin rubro.
RUBROS_PRIMER_LOTE = {
    "Bebida Fresca": "Bebidas",
    "Moda Urbana": "Indumentaria",
    "Panadería del Barrio": "Alimentos",
}

# (formato, departamento, dirección, capacidad, tarifa, código de estado, proveedor)
CARTELES = (
    ("LED", "Ciudad", "Av. Las Heras 450", 6, "180000", "activo", "ElectroLED Andes"),
    ("LED", "Godoy Cruz", "Av. San Martín Sur 2200", 6, "160000", "activo", "ElectroLED Andes"),
    ("LED", "Guaymallén", "Acceso Este km 3", 4, "150000", "mantenimiento", "ElectroLED Andes"),
    (
        "PPL/Gran Formato",
        "Luján de Cuyo",
        "Ruta 7 km 1020",
        1,
        "320000",
        "activo",
        "Estructuras Andinas",
    ),
    (
        "PPL/Gran Formato",
        "Las Heras",
        "Av. Champagnat 1500",
        1,
        "280000",
        "activo",
        "Estructuras Andinas",
    ),
    ("PPL/Gran Formato", "Maipú", "Ruta 7 km 1035", 1, "300000", "apagado", "Estructuras Andinas"),
    ("Séxtuples", "Ciudad", "Calle Colón 300", 6, "60000", "activo", ""),
    ("Séxtuples", "Godoy Cruz", "Calle Perú 1200", 6, "55000", "activo", ""),
    ("Banderolas", "Ciudad", "Av. Mitre 800", 1, "40000", "activo", ""),
    ("Banderolas", "Guaymallén", "Bandera de los Andes 2400", 1, "35000", "activo", ""),
    ("Mediano Formato", "Luján de Cuyo", "Av. Acceso Sur 5000", 1, "90000", "activo", ""),
    ("Mediano Formato", "Las Heras", "Av. Regalado Olguín 900", 1, "85000", "activo", ""),
    ("Monocolumnas", "Ciudad", "Av. Belgrano 1100", 1, "120000", "activo", ""),
    ("Monocolumnas", "Godoy Cruz", "Av. Godoy Cruz 600", 1, "110000", "baja", ""),
    ("Carteleras", "Maipú", "Calle Padre Vázquez 400", 1, "70000", "activo", ""),
    ("Carteleras", "Guaymallén", "Calle Mitre 2100", 1, "65000", "activo", ""),
)

# (nombre, razón social, tipo, correo)
CLIENTES = (
    (
        SENTINELA_DEMO,
        "Distribuidora Andina S.A.",
        Cliente.Tipo.INTERMEDIARIO,
        "compras@example.com",
    ),
    (
        "Agencia Cordillera",
        "Cordillera Medios S.R.L.",
        Cliente.Tipo.INTERMEDIARIO_FORMAL,
        "medios@example.com",
    ),
    ("Medios del Sol", "", Cliente.Tipo.INTERMEDIARIO, "hola@example.com"),
    ("Bodega Los Álamos", "Bodega Los Álamos S.A.", Cliente.Tipo.DIRECTO, "marketing@example.com"),
    ("Concesionaria Ruta 40", "", Cliente.Tipo.DIRECTO, "ventas@example.com"),
    ("Clínica Parque", "", Cliente.Tipo.DIRECTO, ""),
)

# (marca, cliente, rubro)
MARCAS = (
    ("Agua Cumbre", SENTINELA_DEMO, "Bebidas"),
    ("Snack Pirca", SENTINELA_DEMO, "Alimentos"),
    ("Banco Horizonte", "Agencia Cordillera", "Servicios financieros"),
    ("Zapatillas Viento", "Agencia Cordillera", "Indumentaria"),
    ("Yogur Valle", "Agencia Cordillera", "Alimentos"),
    ("Gaseosa Ola", "Medios del Sol", "Bebidas"),
    ("Seguros Brújula", "Medios del Sol", "Servicios financieros"),
    ("Los Álamos", "Bodega Los Álamos", "Bebidas"),
    ("Ruta 40 Autos", "Concesionaria Ruta 40", "Automotor"),
    ("Clínica Parque", "Clínica Parque", "Salud"),
)

R = Reserva.Estado


@dataclass(frozen=True)
class CampaniaDemo:
    nombre: str
    marca: str
    desde: int  # meses desde el mes actual
    hasta: int  # mes en que ya terminó (exclusivo)
    estado: str
    # (índice en CARTELES, estado de la reserva, precio de alquiler)
    reservas: tuple[tuple[int, str, str], ...]


CAMPANIAS = (
    CampaniaDemo(
        "Verano Agua Cumbre",
        "Agua Cumbre",
        -5,
        -3,
        Campania.Estado.CONFIRMADA,
        ((0, R.FINALIZADA, "360000"), (3, R.FINALIZADA, "640000")),
    ),
    CampaniaDemo(
        "Lanzamiento Zapatillas Viento",
        "Zapatillas Viento",
        -4,
        -2,
        Campania.Estado.CONFIRMADA,
        ((8, R.FINALIZADA, "80000"), (12, R.FINALIZADA, "240000"), (6, R.FINALIZADA, "120000")),
    ),
    CampaniaDemo(
        "Banco Horizonte invierno",
        "Banco Horizonte",
        -3,
        0,
        Campania.Estado.CONFIRMADA,
        ((4, R.FINALIZADA, "300000"), (1, R.FINALIZADA, "480000"), (10, R.FINALIZADA, "270000")),
    ),
    CampaniaDemo(
        "Vendimia Los Álamos",
        "Los Álamos",
        -1,
        2,
        Campania.Estado.CONFIRMADA,
        (
            (3, R.CONFIRMADA, "960000"),
            (0, R.CONFIRMADA, "540000"),
            (14, R.CONFIRMADA, "210000"),
            (7, R.CONFIRMADA, "165000"),
        ),
    ),
    CampaniaDemo(
        "Ruta 40 Autos 0 km",
        "Ruta 40 Autos",
        0,
        3,
        Campania.Estado.CONFIRMADA,
        (
            (4, R.CONFIRMADA, "840000"),
            (12, R.CONFIRMADA, "360000"),
            (1, R.CONFIRMADA, "480000"),
            (11, R.CONFIRMADA, "255000"),
        ),
    ),
    CampaniaDemo(
        "Clínica Parque prevención",
        "Clínica Parque",
        0,
        1,
        Campania.Estado.CONFIRMADA,
        ((9, R.CONFIRMADA, "35000"), (15, R.CONFIRMADA, "65000"), (6, R.CONFIRMADA, "60000")),
    ),
    CampaniaDemo(
        "Gaseosa Ola primavera",
        "Gaseosa Ola",
        1,
        3,
        Campania.Estado.COTIZADA,
        ((10, R.PENDIENTE, "180000"), (8, R.PENDIENTE, "80000"), (0, R.PENDIENTE, "360000")),
    ),
    CampaniaDemo(
        "Seguros Brújula",
        "Seguros Brújula",
        1,
        2,
        Campania.Estado.PERDIDA,
        ((12, R.CANCELADA, "120000"),),
    ),
    CampaniaDemo(
        "Snack Pirca escolar",
        "Snack Pirca",
        -2,
        -1,
        Campania.Estado.CANCELADA,
        ((14, R.CANCELADA, "70000"), (7, R.CANCELADA, "55000")),
    ),
    CampaniaDemo(
        "Yogur Valle",
        "Yogur Valle",
        2,
        3,
        Campania.Estado.COTIZADA,
        ((15, R.PENDIENTE, "65000"), (1, R.PENDIENTE, "160000")),
    ),
)

USUARIOS_DEMO = (
    ("demo-operativo", ("Operativo",)),
    ("demo-gerencia", ("Operativo", "Gerencia")),
    ("demo-lectura", ("Lectura",)),
)

CENTAVOS = Decimal("0.01")


def cargar() -> bool:
    """Carga el lote demo si todavía no está (idempotente). Devuelve si cargó algo."""
    if Cliente.objects.filter(nombre=SENTINELA_DEMO).exists():
        return False
    with transaction.atomic():
        usuarios = _usuarios()
        proveedores = _proveedores()
        rubros = _rubros()
        carteles = _carteles(proveedores)
        marcas = _marcas(rubros)
        campanias = [_campania(datos, marcas, carteles) for datos in CAMPANIAS]
        _costos(proveedores)
        _auditoria(carteles, campanias, usuarios)
    return True


def _usuarios() -> list[User]:
    """Usuarios por rol (HU-004). Sin `DJANGO_DEMO_PASSWORD` no se crea ninguno."""
    clave = os.environ.get("DJANGO_DEMO_PASSWORD", "")
    if not clave:
        return []
    usuarios = []
    for username, grupos in USUARIOS_DEMO:
        usuario, creado = User.objects.get_or_create(username=username)
        if creado:
            usuario.set_password(clave)
            usuario.save()
        usuario.groups.set(Group.objects.filter(name__in=grupos))
        usuarios.append(usuario)
    return usuarios


def _proveedores() -> dict[str, Proveedor]:
    return {
        nombre: Proveedor.objects.get_or_create(nombre=nombre, defaults={"servicio": servicio})[0]
        for nombre, servicio in PROVEEDORES
    }


def _rubros() -> dict[str, Rubro]:
    rubros = {nombre: Rubro.objects.get_or_create(nombre=nombre)[0] for nombre in RUBROS}
    for marca, rubro in RUBROS_PRIMER_LOTE.items():
        Marca.objects.filter(nombre=marca, rubro__isnull=True).update(rubro=rubros[rubro])
    return rubros


def _carteles(proveedores: dict[str, Proveedor]) -> list[Cartel]:
    carteles = []
    for formato, zona, direccion, capacidad, tarifa, estado, proveedor in CARTELES:
        carteles.append(
            Cartel.objects.create(
                formato=Formato.objects.get(nombre=formato),
                zona=Zona.objects.get(nombre=zona),
                estado=EstadoCartel.objects.get(codigo=estado),
                proveedor=proveedores.get(proveedor),
                direccion=direccion,
                capacidad=capacidad,
                tarifa_lista=Decimal(tarifa),
            )
        )
    return carteles


def _marcas(rubros: dict[str, Rubro]) -> dict[str, Marca]:
    clientes = {
        nombre: Cliente.objects.create(
            nombre=nombre, razon_social=razon_social, tipo=tipo, correo=correo
        )
        for nombre, razon_social, tipo, correo in CLIENTES
    }
    return {
        nombre: Marca.objects.create(nombre=nombre, cliente=clientes[cliente], rubro=rubros[rubro])
        for nombre, cliente, rubro in MARCAS
    }


def _mes(meses: int) -> date:
    return sumar_meses(timezone.localdate().replace(day=1), meses)


def _campania(datos: CampaniaDemo, marcas: dict[str, Marca], carteles: list[Cartel]) -> Campania:
    inicio, fin = _mes(datos.desde), _mes(datos.hasta) - timedelta(days=1)
    campania = Campania.objects.create(
        nombre=datos.nombre,
        marca=marcas[datos.marca],
        fecha_inicio=inicio,
        fecha_fin=fin,
        estado=datos.estado,
    )
    for indice, estado, alquiler in datos.reservas:
        cartel = carteles[indice]
        impresion = Decimal("0.00")
        if cartel.formato.modalidad == Formato.Modalidad.FIJA:
            impresion = (Decimal(alquiler) * Decimal("0.10")).quantize(CENTAVOS)
        reserva = Reserva(
            campania=campania,
            cartel=cartel,
            fecha_inicio=inicio,
            fecha_fin=fin,
            estado=estado,
            precio_alquiler=Decimal(alquiler),
            precio_impresion=impresion,
        )
        # Ni en la demo se sobrevende un cartel; una cancelada no ocupa cupo.
        if estado != R.CANCELADA:
            validar_disponibilidad(reserva)
        reserva.save()
    return campania


def _costos(proveedores: dict[str, Proveedor]) -> None:
    """Impresión y fijación en las reservas que ocupan cupo; una con margen negativo."""
    reservas = Reserva.objects.filter(
        campania__nombre__in=[datos.nombre for datos in CAMPANIAS],
        estado__in=[R.CONFIRMADA, R.FINALIZADA],
    ).select_related("cartel__formato")
    for reserva in reservas:
        _costo(reserva, Costo.Tipo.IMPRESION, "0.30", proveedores["Imprenta Cuyo"])
        if reserva.cartel.formato.modalidad == Formato.Modalidad.FIJA:
            _costo(reserva, Costo.Tipo.FIJACION, "0.08", proveedores["Fijaciones del Oeste"])
    negativa = reservas.filter(cartel__direccion="Bandera de los Andes 2400").first()
    if negativa is not None:
        _costo(negativa, Costo.Tipo.OTRO, "1.20", proveedores["Estructuras Andinas"])
    anulable = reservas.filter(cartel__direccion="Calle Colón 300").first()
    if anulable is not None:
        Costo.objects.create(
            reserva=anulable,
            tipo=Costo.Tipo.IMPRESION,
            proveedor=proveedores["Imprenta Cuyo"],
            monto=Decimal("18000.00"),
            fecha=anulable.fecha_inicio,
            anulado=True,
            motivo_anulacion="Carga duplicada",
        )


def _costo(reserva: Reserva, tipo: str, proporcion: str, proveedor: Proveedor) -> None:
    Costo.objects.create(
        reserva=reserva,
        tipo=tipo,
        proveedor=proveedor,
        monto=(reserva.precio_alquiler * Decimal(proporcion)).quantize(CENTAVOS),
        fecha=reserva.fecha_inicio,
    )


def _auditoria(carteles: list[Cartel], campanias: list[Campania], usuarios: list[User]) -> None:
    """Cambios que se ven en la pantalla de auditoría, atribuidos a los usuarios de demo."""
    operativo = usuarios[0] if usuarios else None
    gerencia = usuarios[1] if usuarios else None
    origen = RegistroAuditoria.Origen.USUARIO if usuarios else RegistroAuditoria.Origen.SISTEMA
    por_nombre = {campania.nombre: campania for campania in campanias}

    def reserva(campania: str, direccion: str) -> Reserva:
        return Reserva.objects.get(campania=por_nombre[campania], cartel__direccion=direccion)

    cambios: list[tuple[str, int, str, str, str, User | None]] = [
        ("cartel", carteles[0].pk, "tarifa_lista", "165000.00", "180000.00", gerencia),
        ("cartel", carteles[3].pk, "tarifa_lista", "300000.00", "320000.00", gerencia),
        ("cartel", carteles[12].pk, "tarifa_lista", "110000.00", "120000.00", operativo),
        (
            "reserva",
            reserva("Vendimia Los Álamos", "Ruta 7 km 1020").pk,
            "estado",
            R.PENDIENTE,
            R.CONFIRMADA,
            operativo,
        ),
        (
            "reserva",
            reserva("Ruta 40 Autos 0 km", "Av. San Martín Sur 2200").pk,
            "estado",
            R.PENDIENTE,
            R.CONFIRMADA,
            operativo,
        ),
        (
            "reserva",
            reserva("Snack Pirca escolar", "Calle Padre Vázquez 400").pk,
            "estado",
            R.CONFIRMADA,
            R.CANCELADA,
            operativo,
        ),
        (
            "campania",
            por_nombre["Seguros Brújula"].pk,
            "estado",
            Campania.Estado.COTIZADA,
            Campania.Estado.PERDIDA,
            gerencia,
        ),
        (
            "campania",
            por_nombre["Snack Pirca escolar"].pk,
            "estado",
            Campania.Estado.CONFIRMADA,
            Campania.Estado.CANCELADA,
            gerencia,
        ),
    ]
    for entidad, entidad_id, campo, anterior, nuevo, usuario in cambios:
        registrar_cambios(
            entidad, entidad_id, {campo: str(anterior)}, {campo: str(nuevo)}, usuario, origen
        )
