# Módulo de excepciones personalizadas y auditoría de logs.
# Define la jerarquía de errores del dominio de Software FJ y configura
# el registro persistente en archivo .log para garantizar la continuidad operativa.

import logging
import os


def configurar_logger() -> logging.Logger:
    # Inicializa y retorna el logger principal del sistema.
    # Crea el directorio 'logs/' automáticamente y registra eventos y errores en archivo.
    os.makedirs("logs", exist_ok=True)
    ruta_log = os.path.join("logs", "software_fj.log")

    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.DEBUG)

    # Evita duplicar salidas si el módulo es importado desde múltiples archivos.
    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        archivo_handler = logging.FileHandler(ruta_log, mode="w", encoding="utf-8")
        archivo_handler.setLevel(logging.DEBUG)
        archivo_handler.setFormatter(formato)

        logger.addHandler(archivo_handler)

    return logger


# Instancia compartida en toda la aplicación.
logger = configurar_logger()

# jerarquía de excepciones personalizadas para el dominio de Software FJ.

class SoftwareFJError(Exception):
    # Excepción base del sistema Software FJ.
    # Permite capturar cualquier error de negocio de forma polimórfica.
    def __init__(self, mensaje: str, codigo: str = "ERR-000"):
        self.codigo = codigo
        self.mensaje = mensaje
        super().__init__(f"[{codigo}] {mensaje}")


class DatoInvalidoError(SoftwareFJError):
    # Se lanza cuando un dato es nulo, vacío, negativo o incumple el formato esperado.
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-VALIDACION")


class ParametroFaltanteError(SoftwareFJError):
    # Se lanza cuando se omite un parámetro requerido para configurar o calcular un servicio.
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-PARAMETRO")


class ServicioNoDisponibleError(SoftwareFJError):
    # Se lanza al intentar reservar un servicio inactivo, ocupado o sin inventario.
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-DISPONIBILIDAD")


class OperacionNoPermitidaError(SoftwareFJError):
    # Se lanza cuando se solicita una transición de estado inválida en una reserva.
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-OPERACION")


class CalculoInconsistenteError(SoftwareFJError):
    # Se lanza cuando el cálculo de tarifas, impuestos o descuentos genera un valor ilógico.
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-CALCULO")

# Módulo de entidades generales y clientes.
# Implementa la clase abstracta base del sistema y la clase Cliente
# aplicando encapsulación estricta y validaciones de integridad de datos.

from abc import ABC, abstractmethod
from excepciones_logs import DatoInvalidoError, logger


class EntidadSistema(ABC):
    # Clase abstracta base:
    # Representa cualquier entidad identificable dentro de Software FJ
    # (Clientes, Servicios y Reservas).

    def __init__(self, id_entidad: str):
        self.id = id_entidad

    @property
    def id(self) -> str:
        # Getter del identificador único de la entidad.
        return self._id

    @id.setter
    def id(self, valor: str) -> None:
        # Setter con validación estricta: impide identificadores vacíos o no textuales.
        if not isinstance(valor, str) or not valor.strip():
            raise DatoInvalidoError("El identificador de la entidad debe ser una cadena no vacía.")
        self._id = valor.strip().upper()

    @abstractmethod
    def obtener_resumen(self) -> str:
        # Método abstracto que cada subclase debe sobrescribir (Polimorfismo).
        pass


class Cliente(EntidadSistema):
    # Clase Cliente:
    # Hereda de EntidadSistema. Encapsula los datos personales del cliente
    # (nombre, documento, correo y teléfono) protegiéndolos contra asignaciones inválidas.

    def __init__(
        self,
        id_cliente: str,
        nombre: str,
        documento: str,
        correo: str,
        telefono: str,
        activo: bool = True,
    ):
        super().__init__(id_cliente)

        # Invoca los setters encapsulados para validar cada atributo al crear el objeto.
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        self._activo = bool(activo)

        logger.info(f"Cliente registrado en memoria: {self.obtener_resumen()}")

    @property
    def nombre(self) -> str:
        # Retorna el nombre del cliente.
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        # Valida que el nombre tenga al menos 3 caracteres.
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError(f"Nombre de cliente inválido: '{valor}'. Mínimo 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def documento(self) -> str:
        # Retorna el documento de identidad.
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        # Valida que el documento sea numérico y tenga al menos 6 dígitos.
        if not isinstance(valor, str) or not valor.strip().isdigit() or len(valor.strip()) < 6:
            raise DatoInvalidoError(
                f"Documento inválido: '{valor}'. Debe contener al menos 6 dígitos numéricos."
            )
        self._documento = valor.strip()

    @property
    def correo(self) -> str:
        # Retorna el correo electrónico en minúsculas.
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        # Valida formato básico de correo electrónico.
        if (
            not isinstance(valor, str)
            or "@" not in valor
            or "." not in valor.split("@")[-1]
            or len(valor.strip()) < 6
        ):
            raise DatoInvalidoError(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()

    @property
    def telefono(self) -> str:
        # Retorna el teléfono de contacto.
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        # Valida que el teléfono contenga al menos 7 dígitos numéricos.
        limpio = str(valor).strip() if valor is not None else ""
        if not limpio.isdigit() or len(limpio) < 7:
            raise DatoInvalidoError(f"Teléfono inválido: '{valor}'. Debe tener al menos 7 dígitos.")
        self._telefono = limpio

    @property
    def activo(self) -> bool:
        # Indica si el cliente se encuentra habilitado para reservar.
        return self._activo

    def desactivar(self) -> None:
        # Inhabilita al cliente para futuras reservas conservando su historial.
        self._activo = False
        logger.warning(f"Cliente {self._id} ({self._nombre}) marcado como INACTIVO.")

    def obtener_resumen(self) -> str:
        # Implementación polimórfica del método abstracto de EntidadSistema.
        estado = "Activo" if self._activo else "Inactivo"
        return (
            f"Cliente[{self._id}] | Nombre: {self._nombre} | Doc: {self._documento} "
            f"| Email: {self._correo} | Estado: {estado}"
        )

# Módulo de catálogo de servicios (abstracción, herencia, polimorfismo y sobrecarga).
# Define la clase abstracta Servicio y sus tres especializaciones:
# ReservaSala, AlquilerEquipo y AsesoriaEspecializada.

from abc import ABC, abstractmethod
from entidades import EntidadSistema
from excepciones_logs import (
    CalculoInconsistenteError,
    DatoInvalidoError,
    ParametroFaltanteError,
    logger,
)


class Servicio(EntidadSistema, ABC):
    # Clase abstracta Servicio:
    # Hereda de EntidadSistema y establece la estructura base para los servicios
    # comercializados por Software FJ.

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True):
        super().__init__(id_servicio)
        self.nombre = nombre
        self.tarifa_base = tarifa_base
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        # Retorna el nombre del servicio.
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        # Valida que el nombre del servicio tenga al menos 3 caracteres.
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError(f"Nombre de servicio inválido: '{valor}'.")
        self._nombre = valor.strip()

    @property
    def tarifa_base(self) -> float:
        # Retorna la tarifa base del servicio.
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        # Encadenamiento de excepción si se recibe un dato no convertible a número.
        try:
            tarifa = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La tarifa base '{valor}' no es un valor numérico válido."
            ) from error_original

        if tarifa <= 0:
            raise DatoInvalidoError("La tarifa base del servicio debe ser mayor a $0.")
        self._tarifa_base = tarifa

    @property
    def disponible(self) -> bool:
        # Indica si el servicio está disponible.
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        # Actualiza el estado de disponibilidad del servicio.
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Valida las reglas de negocio específicas de cada tipo de servicio.
        pass

    @abstractmethod
    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Calcula el subtotal base según la lógica propia de cada subclase.
        pass

    # --- SOBRECARGA DE MÉTODOS (OVERLOADING) ---
    def calcular_costo(
        self,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.19,
        recargo_fijo: float = 0.0,
        **kwargs,
    ) -> float:
        # Método sobrecargado para cálculo de costos:
        # Soporta múltiples variantes de invocación mediante parámetros opcionales:
        #   1. calcular_costo(duracion) -> Tarifa estándar con IVA del 19%.
        #   2. calcular_costo(duracion, descuento_pct=10) -> Aplica descuento promocional.
        #   3. calcular_costo(duracion, descuento_pct=5, impuesto_pct=0.0) -> Exento de IVA.
        #   4. calcular_costo(duracion, recargo_fijo=50000, asistentes=12) -> Con cargos extra.
        self.validar_parametros(duracion, **kwargs)

        if not (0 <= descuento_pct < 100):
            raise CalculoInconsistenteError(
                f"Porcentaje de descuento fuera de rango (0-99%): {descuento_pct}%"
            )
        if impuesto_pct < 0 or impuesto_pct > 1:
            raise CalculoInconsistenteError(
                f"Porcentaje de impuesto inválido (rango 0.0 a 1.0): {impuesto_pct}"
            )
        if recargo_fijo < 0:
            raise CalculoInconsistenteError("El recargo fijo no puede ser negativo.")

        subtotal = self.calcular_subtotal(duracion, **kwargs)
        monto_descuento = subtotal * (descuento_pct / 100.0)
        base_gravable = (subtotal - monto_descuento) + recargo_fijo
        total = base_gravable * (1 + impuesto_pct)

        if total <= 0:
            raise CalculoInconsistenteError("El costo total calculado resultó menor o igual a cero.")

        return round(total, 2)

# CLASE DERIVADA 1: RESERVA DE SALAS

class ReservaSala(Servicio):
    # Servicio especializado para alquiler por horas de salas empresariales.

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_maxima: int,
        incluye_videobeam: bool = True,
        disponible: bool = True,
    ):
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not isinstance(capacidad_maxima, int) or capacidad_maxima <= 0:
            raise DatoInvalidoError("La capacidad máxima de la sala debe ser un entero positivo.")
        self.capacidad_maxima = capacidad_maxima
        self.incluye_videobeam = bool(incluye_videobeam)
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Sobrescritura: exige duración entre 1 y 12 horas y valida aforo de asistentes.
        if not isinstance(duracion, int) or duracion <= 0 or duracion > 12:
            raise DatoInvalidoError(
                f"Duración inválida para sala ({duracion}h). Debe estar entre 1 y 12 horas."
            )
        asistentes = kwargs.get("asistentes")
        if asistentes is None:
            raise ParametroFaltanteError(
                "Para reservar una sala debe especificar el parámetro 'asistentes'."
            )
        if not isinstance(asistentes, int) or asistentes <= 0:
            raise DatoInvalidoError("El número de asistentes debe ser un entero mayor a 0.")
        if asistentes > self.capacidad_maxima:
            raise DatoInvalidoError(
                f"Aforo excedido: se solicitaron {asistentes} asistentes pero la sala "
                f"'{self.nombre}' soporta máximo {self.capacidad_maxima}."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Sobrescritura: aplica recargo logístico del 15% si la ocupación supera el 70%.
        asistentes = kwargs.get("asistentes", 1)
        subtotal = self._tarifa_base * duracion
        if asistentes > (self.capacidad_maxima * 0.7):
            subtotal *= 1.15
        return subtotal

    def obtener_resumen(self) -> str:
        # Retorna descripción detallada de la sala.
        equipo = "Con VideoBeam" if self.incluye_videobeam else "Sin VideoBeam"
        return (
            f"Sala[{self._id}] '{self.nombre}' | Tarifa: ${self._tarifa_base:,.0f}/h "
            f"| Cap. Máx: {self.capacidad_maxima} pers. | {equipo}"
        )

# CLASE DERIVADA 2: ALQUILER DE EQUIPOS

class AlquilerEquipo(Servicio):
    # Servicio especializado para alquiler diario de equipos tecnológicos.

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_dia: float,
        stock_disponible: int,
        gama: str = "Corporativa",
        disponible: bool = True,
    ):
        super().__init__(id_servicio, nombre, tarifa_dia, disponible)
        if not isinstance(stock_disponible, int) or stock_disponible < 0:
            raise DatoInvalidoError("El stock de equipos no puede ser negativo.")
        self.stock_disponible = stock_disponible
        self.gama = gama
        if self.stock_disponible == 0:
            self._disponible = False
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Sobrescritura: valida días de alquiler y existencias en inventario.
        if not isinstance(duracion, int) or duracion <= 0:
            raise DatoInvalidoError("La duración del alquiler debe ser al menos 1 día.")
        cantidad = kwargs.get("cantidad", 1)
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise DatoInvalidoError("La cantidad de equipos a alquilar debe ser al menos 1.")
        if cantidad > self.stock_disponible:
            raise DatoInvalidoError(
                f"Stock insuficiente para '{self.nombre}': solicitados {cantidad}, "
                f"disponibles {self.stock_disponible}."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Sobrescritura: tarifa diaria * días * cantidad de equipos.
        cantidad = kwargs.get("cantidad", 1)
        return self._tarifa_base * duracion * cantidad

    def descontar_stock(self, cantidad: int) -> None:
        # Reduce el stock disponible al confirmar una reserva.
        self.stock_disponible -= cantidad
        if self.stock_disponible <= 0:
            self.stock_disponible = 0
            self._disponible = False

    def restaurar_stock(self, cantidad: int) -> None:
        # Reintegra unidades al inventario si la reserva es cancelada.
        self.stock_disponible += cantidad
        if self.stock_disponible > 0:
            self._disponible = True

    def obtener_resumen(self) -> str:
        # Retorna descripción detallada del equipo en alquiler.
        return (
            f"Equipo[{self._id}] '{self.nombre}' ({self.gama}) | "
            f"Tarifa: ${self._tarifa_base:,.0f}/día | Stock: {self.stock_disponible} unid."
        )

# CLASE DERIVADA 3: ASESORÍA ESPECIALIZADA

class AsesoriaEspecializada(Servicio):
    # Servicio de consultoría técnica en arquitectura de software, nube o seguridad.

    NIVELES_VALIDOS = {"Junior": 1.0, "Senior": 1.25, "Arquitecto": 1.5}

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        especialidad: str,
        nivel_consultor: str = "Senior",
        disponible: bool = True,
    ):
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if nivel_consultor not in self.NIVELES_VALIDOS:
            raise DatoInvalidoError(
                f"Nivel de consultor inválido: '{nivel_consultor}'. "
                f"Opciones válidas: {list(self.NIVELES_VALIDOS.keys())}"
            )
        if not especialidad or len(especialidad.strip()) < 3:
            raise DatoInvalidoError("Debe indicar una especialidad técnica válida.")

        self.especialidad = especialidad.strip()
        self.nivel_consultor = nivel_consultor
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Sobrescritura: exige un mínimo de 2 horas por sesión de consultoría.
        if not isinstance(duracion, int) or duracion < 2:
            raise DatoInvalidoError(
                f"Duración insuficiente ({duracion}h). Las asesorías requieren mínimo 2 horas."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Sobrescritura: aplica el multiplicador correspondiente al nivel del consultor.
        multiplicador = self.NIVELES_VALIDOS[self.nivel_consultor]
        return self._tarifa_base * duracion * multiplicador

    def obtener_resumen(self) -> str:
        # Retorna descripción detallada de la asesoría especializada.
        return (
            f"Asesoría[{self._id}] '{self.nombre}' | Área: {self.especialidad} "
            f"| Nivel: {self.nivel_consultor} | Base: ${self._tarifa_base:,.0f}/h"
        )

# Módulo de gestión de reservas y ciclo de estados.
# Implementa la clase Reserva que asocia un Cliente con un Servicio, calcula
# el costo total de forma polimórfica y controla las transiciones de estado.

from datetime import datetime
from entidades import Cliente, EntidadSistema
from excepciones_logs import (
    DatoInvalidoError,
    OperacionNoPermitidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
    logger,
)
from servicios import AlquilerEquipo, Servicio


class Reserva(EntidadSistema):
    # Clase Reserva:
    # Integra Cliente, Servicio, duración y estado, implementando confirmación,
    # cancelación y procesamiento con manejo estricto de excepciones.

    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_CONFIRMADA = "CONFIRMADA"
    ESTADO_CANCELADA = "CANCELADA"
    ESTADO_COMPLETADA = "COMPLETADA"

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.19,
        **parametros_servicio,
    ):
        super().__init__(id_reserva)

        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("La reserva requiere una instancia válida de Cliente.")
        if not cliente.activo:
            raise OperacionNoPermitidaError(
                f"El cliente '{cliente.nombre}' ({cliente.id}) está inactivo y no puede reservar."
            )

        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("La reserva requiere una instancia válida de Servicio.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{servicio.nombre}' ({servicio.id}) no está disponible."
            )

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._descuento_pct = descuento_pct
        self._impuesto_pct = impuesto_pct
        self._parametros_servicio = parametros_servicio
        self._estado = self.ESTADO_PENDIENTE
        self._fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Invoca el método sobrecargado del servicio para validar parámetros y calcular costo.
        self._costo_total = self._servicio.calcular_costo(
            duracion=self._duracion,
            descuento_pct=self._descuento_pct,
            impuesto_pct=self._impuesto_pct,
            **self._parametros_servicio,
        )

        logger.info(f"Reserva creada en estado PENDIENTE -> {self.obtener_resumen()}")

    @property
    def cliente(self) -> Cliente:
        # Retorna el cliente asociado a la reserva.
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        # Retorna el servicio reservado.
        return self._servicio

    @property
    def estado(self) -> str:
        # Retorna el estado actual de la reserva.
        return self._estado

    @property
    def costo_total(self) -> float:
        # Retorna el costo total calculado de la reserva.
        return self._costo_total

    def confirmar(self) -> None:
        # Confirma una reserva pendiente y bloquea disponibilidad o descuenta inventario.
        if self._estado != self.ESTADO_PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva {self._id} en estado '{self._estado}'."
            )

        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._servicio.nombre}' dejó de estar disponible."
            )

        if isinstance(self._servicio, AlquilerEquipo):
            cantidad = self._parametros_servicio.get("cantidad", 1)
            self._servicio.descontar_stock(cantidad)
        else:
            self._servicio.disponible = False

        self._estado = self.ESTADO_CONFIRMADA
        logger.info(f"Reserva {self._id} CONFIRMADA. Total: ${self._costo_total:,.2f}")

    def cancelar(self, motivo: str = "Solicitud del cliente") -> None:
        # Cancela una reserva pendiente o confirmada y libera los recursos asociados.
        if self._estado in (self.ESTADO_CANCELADA, self.ESTADO_COMPLETADA):
            raise OperacionNoPermitidaError(
                f"Imposible cancelar la reserva {self._id}: su estado actual es '{self._estado}'."
            )

        if self._estado == self.ESTADO_CONFIRMADA:
            if isinstance(self._servicio, AlquilerEquipo):
                cantidad = self._parametros_servicio.get("cantidad", 1)
                self._servicio.restaurar_stock(cantidad)
            else:
                self._servicio.disponible = True

        self._estado = self.ESTADO_CANCELADA
        logger.warning(f"Reserva {self._id} CANCELADA. Motivo: {motivo}")

    def procesar(self) -> str:
        # Procesa y finaliza una reserva confirmada.
        # Aplica captura y encadenamiento de excepciones ante fallos imprevistos.
        try:
            if self._estado != self.ESTADO_CONFIRMADA:
                raise OperacionNoPermitidaError(
                    f"Solo se procesan reservas CONFIRMADAS. Estado actual: '{self._estado}'."
                )

            if not isinstance(self._servicio, AlquilerEquipo):
                self._servicio.disponible = True

            self._estado = self.ESTADO_COMPLETADA
            comprobante = (
                f"COMPROBANTE {self._id} | Cliente: {self._cliente.nombre} | "
                f"Servicio: {self._servicio.nombre} | Total: ${self._costo_total:,.2f}"
            )
            logger.info(f"Reserva {self._id} COMPLETADA. {comprobante}")
            return comprobante

        except SoftwareFJError:
            raise
        except Exception as err:
            raise OperacionNoPermitidaError(
                f"Error inesperado durante el procesamiento de la reserva {self._id}."
            ) from err

    def obtener_resumen(self) -> str:
        # Retorna un resumen legible de la reserva.
        return (
            f"Reserva[{self._id}] | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | Duración: {self._duracion} | "
            f"Total: ${self._costo_total:,.2f} | Estado: {self._estado}"