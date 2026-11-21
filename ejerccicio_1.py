# Sistema integral de gestión de clientes, servicios y reservas para Software FJ.
# Funciona sin base de datos: gestiona entidades en listas en memoria y registra
# eventos y errores en un archivo de logs manteniendo la ejecución estable[cite: 1, 2, 3].

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import os


def configurar_logger() -> logging.Logger:
    # Crea la carpeta 'logs' si aún no existe para almacenar el archivo de auditoría[cite: 2, 3].
    os.makedirs("logs", exist_ok=True)
    # Define la ruta completa del archivo de registro de eventos y errores[cite: 2, 3].
    ruta_log = os.path.join("logs", "software_fj.log")

    # Obtiene o crea un logger nombrado 'SoftwareFJ' y permite capturar desde nivel DEBUG.
    log = logging.getLogger("SoftwareFJ")
    log.setLevel(logging.DEBUG)

    # Verifica que no existan manejadores previos para evitar líneas duplicadas en el log.
    if not log.handlers:
        # Define el formato de cada línea: fecha/hora, nivel, módulo y mensaje.
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Configura el manejador de archivo con codificación UTF-8 y modo sobrescritura por ejecución.
        archivo_handler = logging.FileHandler(ruta_log, mode="w", encoding="utf-8")
        archivo_handler.setLevel(logging.DEBUG)
        archivo_handler.setFormatter(formato)
        # Asocia el manejador de archivo al logger.
        log.addHandler(archivo_handler)

    return log


# Instancia global del logger utilizada por todas las clases y métodos del sistema.
logger = configurar_logger()


# ==============================================================================
# JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==============================================================================

class SoftwareFJError(Exception):
    # Excepción base del sistema; agrupa los errores del dominio bajo un código y mensaje[cite: 2].
    def __init__(self, mensaje: str, codigo: str = "ERR-000"):
        # Guarda el código identificador del error.
        self.codigo = codigo
        # Guarda la descripción legible del error.
        self.mensaje = mensaje
        # Inicializa la clase base Exception con el mensaje formateado.
        super().__init__(f"[{codigo}] {mensaje}")


class DatoInvalidoError(SoftwareFJError):
    # Excepción lanzada ante datos vacíos, fuera de rango, negativos o con formato incorrecto[cite: 2].
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-VALIDACION")


class ParametroFaltanteError(SoftwareFJError):
    # Excepción lanzada cuando falta un parámetro requerido para validar o calcular un servicio[cite: 2].
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-PARAMETRO")


class ServicioNoDisponibleError(SoftwareFJError):
    # Excepción lanzada cuando un servicio está ocupado, inactivo o sin stock suficiente[cite: 2].
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-DISPONIBILIDAD")


class OperacionNoPermitidaError(SoftwareFJError):
    # Excepción lanzada ante operaciones inválidas o transiciones de estado prohibidas[cite: 2].
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-OPERACION")


class CalculoInconsistenteError(SoftwareFJError):
    # Excepción lanzada cuando un cálculo de costos, descuentos o impuestos produce valores inválidos[cite: 2].
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-CALCULO")


# ==============================================================================
# ENTIDADES GENERALES Y CLIENTE
# ==============================================================================

class EntidadSistema(ABC):
    # Clase abstracta general del sistema para entidades con identificador único[cite: 2].
    def __init__(self, id_entidad: str):
        # Asigna el ID a través de la propiedad para ejecutar su validación.
        self.id = id_entidad

    @property
    def id(self) -> str:
        # Retorna el identificador normalizado de la entidad.
        return self._id

    @id.setter
    def id(self, valor: str) -> None:
        # Verifica que el ID sea un string no vacío y lo normaliza en mayúsculas sin espacios externos.
        if not isinstance(valor, str) or not valor.strip():
            raise DatoInvalidoError("El identificador de la entidad debe ser una cadena no vacía.")
        self._id = valor.strip().upper()

    @abstractmethod
    def obtener_resumen(self) -> str:
        # Método abstracto obligatorio que cada subclase implementa según su naturaleza[cite: 2].
        pass


class Cliente(EntidadSistema):
    # Representa a un cliente de Software FJ con encapsulación de datos personales y validaciones[cite: 2].
    def __init__(
        self,
        id_cliente: str,
        nombre: str,
        documento: str,
        correo: str,
        telefono: str,
        activo: bool = True,
    ):
        # Inicializa el ID heredado de EntidadSistema.
        super().__init__(id_cliente)
        # Valida y asigna cada atributo personal mediante sus setters encapsulados.
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        # Almacena el estado de actividad del cliente como booleano.
        self._activo = bool(activo)
        # Registra en el archivo de logs la creación exitosa del cliente[cite: 2, 3].
        logger.info(f"Cliente registrado en memoria: {self.obtener_resumen()}")

    @property
    def nombre(self) -> str:
        # Devuelve el nombre del cliente.
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        # Exige que el nombre sea texto y tenga al menos 3 caracteres útiles.
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError(f"Nombre de cliente inválido: '{valor}'. Mínimo 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def documento(self) -> str:
        # Devuelve el número de documento del cliente.
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        # Exige que el documento sea una cadena numérica de mínimo 6 dígitos.
        if not isinstance(valor, str) or not valor.strip().isdigit() or len(valor.strip()) < 6:
            raise DatoInvalidoError(
                f"Documento inválido: '{valor}'. Debe contener al menos 6 dígitos numéricos."
            )
        self._documento = valor.strip()

    @property
    def correo(self) -> str:
        # Devuelve el correo electrónico normalizado en minúsculas.
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        # Valida presencia de '@', dominio con punto y longitud mínima básica.
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
        # Devuelve el número telefónico del cliente.
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        # Limpia espacios y verifica que el teléfono tenga al menos 7 dígitos numéricos.
        limpio = str(valor).strip() if valor is not None else ""
        if not limpio.isdigit() or len(limpio) < 7:
            raise DatoInvalidoError(f"Teléfono inválido: '{valor}'. Debe tener al menos 7 dígitos.")
        self._telefono = limpio

    @property
    def activo(self) -> bool:
        # Indica si el cliente está habilitado para realizar reservas.
        return self._activo

    def desactivar(self) -> None:
        # Deshabilita al cliente para nuevas reservas y deja advertencia en el log.
        self._activo = False
        logger.warning(f"Cliente {self._id} ({self._nombre}) marcado como INACTIVO.")

    def obtener_resumen(self) -> str:
        # Construye una cadena descriptiva con los datos principales y estado del cliente.
        estado = "Activo" if self._activo else "Inactivo"
        return (
            f"Cliente[{self._id}] | Nombre: {self._nombre} | Doc: {self._documento} "
            f"| Email: {self._correo} | Estado: {estado}"
        )


# ==============================================================================
# SERVICIOS Y SUBCLASES
# ==============================================================================

class Servicio(EntidadSistema, ABC):
    # Clase abstracta base para los servicios ofrecidos por Software FJ[cite: 1, 2].
    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True):
        # Inicializa el ID heredado de EntidadSistema.
        super().__init__(id_servicio)
        # Valida y asigna nombre y tarifa base mediante sus propiedades.
        self.nombre = nombre
        self.tarifa_base = tarifa_base
        # Define si el servicio está disponible inicialmente.
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        # Devuelve el nombre del servicio.
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        # Exige que el nombre del servicio tenga al menos 3 caracteres.
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError(f"Nombre de servicio inválido: '{valor}'.")
        self._nombre = valor.strip()

    @property
    def tarifa_base(self) -> float:
        # Devuelve la tarifa base numérica del servicio.
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        # Intenta convertir la tarifa a float; encadena la excepción original si falla[cite: 2].
        try:
            tarifa = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La tarifa base '{valor}' no es un valor numérico válido."
            ) from error_original

        # Verifica que la tarifa base sea estrictamente positiva.
        if tarifa <= 0:
            raise DatoInvalidoError("La tarifa base del servicio debe ser mayor a $0.")
        self._tarifa_base = tarifa

    @property
    def disponible(self) -> bool:
        # Devuelve True si el servicio se encuentra disponible.
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        # Actualiza el estado de disponibilidad del servicio.
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Método abstracto que cada servicio sobrescribe para validar sus parámetros propios[cite: 2].
        pass

    @abstractmethod
    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Método abstracto que cada servicio sobrescribe para calcular su subtotal base[cite: 2].
        pass

    # Método sobrecargado mediante parámetros opcionales para calcular costos con descuentos,
    # impuestos o recargos adicionales[cite: 2].
    def calcular_costo(
        self,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.19,
        recargo_fijo: float = 0.0,
        **kwargs,
    ) -> float:
        # Valida primero los parámetros específicos de la duración y argumentos extra.
        self.validar_parametros(duracion, **kwargs)

        # Valida que el porcentaje de descuento esté en el rango permitido (0% a <100%).
        if not (0 <= descuento_pct < 100):
            raise CalculoInconsistenteError(
                f"Porcentaje de descuento fuera de rango (0-99%): {descuento_pct}%"
            )
        # Valida que el impuesto esté expresado en proporción válida (0.0 a 1.0).
        if impuesto_pct < 0 or impuesto_pct > 1:
            raise CalculoInconsistenteError(
                f"Porcentaje de impuesto inválido (rango 0.0 a 1.0): {impuesto_pct}"
            )
        # Impide recargos fijos negativos.
        if recargo_fijo < 0:
            raise CalculoInconsistenteError("El recargo fijo no puede ser negativo.")

        # Calcula el subtotal polimórfico del servicio y aplica descuento, recargo e impuesto.
        subtotal = self.calcular_subtotal(duracion, **kwargs)
        monto_descuento = subtotal * (descuento_pct / 100.0)
        base_gravable = (subtotal - monto_descuento) + recargo_fijo
        total = base_gravable * (1 + impuesto_pct)

        # Verifica consistencia matemática del resultado final.
        if total <= 0:
            raise CalculoInconsistenteError("El costo total calculado resultó menor o igual a cero.")

        return round(total, 2)


class ReservaSala(Servicio):
    # Servicio especializado para reserva de salas por horas con control de aforo[cite: 1, 2].
    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_maxima: int,
        incluye_videobeam: bool = True,
        disponible: bool = True,
    ):
        # Inicializa atributos comunes de Servicio.
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        # Valida que la capacidad máxima de la sala sea un entero positivo.
        if not isinstance(capacidad_maxima, int) or capacidad_maxima <= 0:
            raise DatoInvalidoError("La capacidad máxima de la sala debe ser un entero positivo.")
        self.capacidad_maxima = capacidad_maxima
        self.incluye_videobeam = bool(incluye_videobeam)
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Exige duración entre 1 y 12 horas para salas.
        if not isinstance(duracion, int) or duracion <= 0 or duracion > 12:
            raise DatoInvalidoError(
                f"Duración inválida para sala ({duracion}h). Debe estar entre 1 y 12 horas."
            )
        # Verifica que se haya enviado el parámetro obligatorio 'asistentes'.
        asistentes = kwargs.get("asistentes")
        if asistentes is None:
            raise ParametroFaltanteError(
                "Para reservar una sala debe especificar el parámetro 'asistentes'."
            )
        # Valida que 'asistentes' sea un entero positivo y no supere la capacidad máxima.
        if not isinstance(asistentes, int) or asistentes <= 0:
            raise DatoInvalidoError("El número de asistentes debe ser un entero mayor a 0.")
        if asistentes > self.capacidad_maxima:
            raise DatoInvalidoError(
                f"Aforo excedido: se solicitaron {asistentes} asistentes pero la sala "
                f"'{self.nombre}' soporta máximo {self.capacidad_maxima}."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Calcula tarifa por horas y añade un 15% si los asistentes superan el 70% de la capacidad.
        asistentes = kwargs.get("asistentes", 1)
        subtotal = self._tarifa_base * duracion
        if asistentes > (self.capacidad_maxima * 0.7):
            subtotal *= 1.15
        return subtotal

    def obtener_resumen(self) -> str:
        # Retorna la descripción resumida de la sala.
        equipo = "Con VideoBeam" if self.incluye_videobeam else "Sin VideoBeam"
        return (
            f"Sala[{self._id}] '{self.nombre}' | Tarifa: ${self._tarifa_base:,.0f}/h "
            f"| Cap. Máx: {self.capacidad_maxima} pers. | {equipo}"
        )


class AlquilerEquipo(Servicio):
    # Servicio especializado para alquiler diario de equipos con control de inventario[cite: 1, 2].
    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_dia: float,
        stock_disponible: int,
        gama: str = "Corporativa",
        disponible: bool = True,
    ):
        # Inicializa atributos comunes de Servicio.
        super().__init__(id_servicio, nombre, tarifa_dia, disponible)
        # Valida que el inventario inicial no sea negativo.
        if not isinstance(stock_disponible, int) or stock_disponible < 0:
            raise DatoInvalidoError("El stock de equipos no puede ser negativo.")
        self.stock_disponible = stock_disponible
        self.gama = gama
        # Si no hay stock disponible, marca el servicio como no disponible.
        if self.stock_disponible == 0:
            self._disponible = False
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Exige al menos 1 día de alquiler.
        if not isinstance(duracion, int) or duracion <= 0:
            raise DatoInvalidoError("La duración del alquiler debe ser al menos 1 día.")
        # Valida que la cantidad solicitada sea positiva y no exceda el stock actual.
        cantidad = kwargs.get("cantidad", 1)
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise DatoInvalidoError("La cantidad de equipos a alquilar debe ser al menos 1.")
        if cantidad > self.stock_disponible:
            raise DatoInvalidoError(
                f"Stock insuficiente para '{self.nombre}': solicitados {cantidad}, "
                f"disponibles {self.stock_disponible}."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Calcula el subtotal multiplicando tarifa diaria por días y por cantidad de equipos.
        cantidad = kwargs.get("cantidad", 1)
        return self._tarifa_base * duracion * cantidad

    def descontar_stock(self, cantidad: int) -> None:
        # Descuenta las unidades alquiladas al confirmar una reserva y actualiza disponibilidad.
        self.stock_disponible -= cantidad
        if self.stock_disponible <= 0:
            self.stock_disponible = 0
            self._disponible = False

    def restaurar_stock(self, cantidad: int) -> None:
        # Devuelve unidades al stock al cancelar una reserva confirmada.
        self.stock_disponible += cantidad
        if self.stock_disponible > 0:
            self._disponible = True

    def obtener_resumen(self) -> str:
        # Retorna la descripción resumida del equipo.
        return (
            f"Equipo[{self._id}] '{self.nombre}' ({self.gama}) | "
            f"Tarifa: ${self._tarifa_base:,.0f}/día | Stock: {self.stock_disponible} unid."
        )


class AsesoriaEspecializada(Servicio):
    # Servicio especializado de consultoría técnica por horas según nivel de seniority[cite: 1, 2].
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
        # Inicializa atributos comunes de Servicio.
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        # Verifica que el nivel del consultor esté dentro de los niveles permitidos.
        if nivel_consultor not in self.NIVELES_VALIDOS:
            raise DatoInvalidoError(
                f"Nivel de consultor inválido: '{nivel_consultor}'. "
                f"Opciones válidas: {list(self.NIVELES_VALIDOS.keys())}"
            )
        # Exige una especialidad técnica válida.
        if not especialidad or len(especialidad.strip()) < 3:
            raise DatoInvalidoError("Debe indicar una especialidad técnica válida.")

        self.especialidad = especialidad.strip()
        self.nivel_consultor = nivel_consultor
        logger.info(f"Servicio registrado -> {self.obtener_resumen()}")

    def validar_parametros(self, duracion: int, **kwargs) -> None:
        # Exige un mínimo de 2 horas para cada sesión de asesoría.
        if not isinstance(duracion, int) or duracion < 2:
            raise DatoInvalidoError(
                f"Duración insuficiente ({duracion}h). Las asesorías requieren mínimo 2 horas."
            )

    def calcular_subtotal(self, duracion: int, **kwargs) -> float:
        # Aplica el multiplicador según el nivel del consultor y la duración en horas.
        multiplicador = self.NIVELES_VALIDOS[self.nivel_consultor]
        return self._tarifa_base * duracion * multiplicador

    def obtener_resumen(self) -> str:
        # Retorna la descripción resumida de la asesoría.
        return (
            f"Asesoría[{self._id}] '{self.nombre}' | Área: {self.especialidad} "
            f"| Nivel: {self.nivel_consultor} | Base: ${self._tarifa_base:,.0f}/h"
        )


# ==============================================================================
# GESTIÓN DE RESERVAS Y CICLO DE ESTADOS
# ==============================================================================

class Reserva(EntidadSistema):
    # Integra un Cliente, un Servicio, duración, estado y costo calculado[cite: 2].
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
        # Inicializa el ID heredado de EntidadSistema.
        super().__init__(id_reserva)

        # Valida que el cliente sea instancia de Cliente y esté activo.
        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("La reserva requiere una instancia válida de Cliente.")
        if not cliente.activo:
            raise OperacionNoPermitidaError(
                f"El cliente '{cliente.nombre}' ({cliente.id}) está inactivo y no puede reservar."
            )

        # Valida que el servicio sea instancia de Servicio y esté disponible.
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("La reserva requiere una instancia válida de Servicio.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{servicio.nombre}' ({servicio.id}) no está disponible."
            )

        # Guarda referencias y parámetros de la reserva.
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._descuento_pct = descuento_pct
        self._impuesto_pct = impuesto_pct
        self._parametros_servicio = parametros_servicio
        self._estado = self.ESTADO_PENDIENTE
        self._fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calcula el costo total invocando el método sobrecargado del servicio[cite: 2].
        self._costo_total = self._servicio.calcular_costo(
            duracion=self._duracion,
            descuento_pct=self._descuento_pct,
            impuesto_pct=self._impuesto_pct,
            **self._parametros_servicio,
        )

        logger.info(f"Reserva creada en estado PENDIENTE -> {self.obtener_resumen()}")

    @property
    def cliente(self) -> Cliente:
        # Devuelve el cliente asociado a la reserva.
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        # Devuelve el servicio reservado.
        return self._servicio

    @property
    def estado(self) -> str:
        # Devuelve el estado actual de la reserva.
        return self._estado

    @property
    def costo_total(self) -> float:
        # Devuelve el costo total calculado de la reserva.
        return self._costo_total

    def confirmar(self) -> None:
        # Confirma la reserva si está PENDIENTE y reserva/descuenta los recursos del servicio[cite: 2].
        if self._estado != self.ESTADO_PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva {self._id} en estado '{self._estado}'."
            )

        # Revisa disponibilidad justo antes de confirmar.
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._servicio.nombre}' dejó de estar disponible."
            )

        # Descuenta stock si es equipo o marca ocupada si es sala/asesoría.
        if isinstance(self._servicio, AlquilerEquipo):
            cantidad = self._parametros_servicio.get("cantidad", 1)
            self._servicio.descontar_stock(cantidad)
        else:
            self._servicio.disponible = False

        self._estado = self.ESTADO_CONFIRMADA
        logger.info(f"Reserva {self._id} CONFIRMADA. Total: ${self._costo_total:,.2f}")

    def cancelar(self, motivo: str = "Solicitud del cliente") -> None:
        # Cancela una reserva si no está ya CANCELADA ni COMPLETADA, liberando recursos[cite: 2].
        if self._estado in (self.ESTADO_CANCELADA, self.ESTADO_COMPLETADA):
            raise OperacionNoPermitidaError(
                f"Imposible cancelar la reserva {self._id}: su estado actual es '{self._estado}'."
            )

        # Si estaba confirmada, reintegra el inventario o libera la disponibilidad del servicio.
        if self._estado == self.ESTADO_CONFIRMADA:
            if isinstance(self._servicio, AlquilerEquipo):
                cantidad = self._parametros_servicio.get("cantidad", 1)
                self._servicio.restaurar_stock(cantidad)
            else:
                self._servicio.disponible = True

        self._estado = self.ESTADO_CANCELADA
        logger.warning(f"Reserva {self._id} CANCELADA. Motivo: {motivo}")

    def procesar(self) -> str:
        # Finaliza una reserva CONFIRMADA y genera su comprobante; encadena fallos inesperados[cite: 2].
        try:
            if self._estado != self.ESTADO_CONFIRMADA:
                raise OperacionNoPermitidaError(
                    f"Solo se procesan reservas CONFIRMADAS. Estado actual: '{self._estado}'."
                )

            # Libera salas o asesorías al completarse el servicio.
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
            # Propaga excepciones propias del sistema sin perder su tipo ni mensaje.
            raise
        except Exception as err:
            # Encadena cualquier error imprevisto dentro de una excepción controlada[cite: 2].
            raise OperacionNoPermitidaError(
                f"Error inesperado durante el procesamiento de la reserva {self._id}."
            ) from err

    def obtener_resumen(self) -> str:
        # Retorna un resumen textual con los datos clave de la reserva.
        return (
            f"Reserva[{self._id}] | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | Duración: {self._duracion} | "
            f"Total: ${self._costo_total:,.2f} | Estado: {self._estado}"
        )


# ==============================================================================
# GESTOR EN MEMORIA Y SIMULACIÓN INTEGRAL
# ==============================================================================

class GestorSoftwareFJ:
    # Administra clientes, servicios y reservas en listas en memoria (sin base de datos)[cite: 1, 2, 3].
    def __init__(self):
        # Listas internas en memoria para almacenar los objetos creados.
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []
        # Contadores de seguimiento de operaciones exitosas y errores controlados.
        self._operaciones_exitosas = 0
        self._operaciones_fallidas = 0
        logger.info("=== INICIO DEL SISTEMA INTEGRAL SOFTWARE FJ ===")

    def buscar_cliente(self, id_cliente: str) -> Cliente:
        # Busca un cliente por ID en la lista interna; lanza excepción si no existe.
        for cli in self._clientes:
            if cli.id == id_cliente.strip().upper():
                return cli
        raise DatoInvalidoError(f"No existe ningún cliente registrado con ID '{id_cliente}'.")

    def buscar_servicio(self, id_servicio: str) -> Servicio:
        # Busca un servicio por ID en la lista interna; lanza excepción si no existe.
        for srv in self._servicios:
            if srv.id == id_servicio.strip().upper():
                return srv
        raise DatoInvalidoError(f"No existe ningún servicio registrado con ID '{id_servicio}'.")

    def buscar_reserva(self, id_reserva: str) -> Reserva:
        # Busca una reserva por ID en la lista interna; lanza excepción si no existe.
        for res in self._reservas:
            if res.id == id_reserva.strip().upper():
                return res
        raise DatoInvalidoError(f"No existe ninguna reserva registrada con ID '{id_reserva}'.")

    def registrar_cliente(
        self,
        id_cliente: str,
        nombre: str,
        documento: str,
        correo: str,
        telefono: str,
    ) -> Cliente | None:
        # Registra un cliente usando bloques try / except / else / finally[cite: 2].
        try:
            # Evita IDs duplicados dentro de la lista de clientes.
            if any(c.id == id_cliente.strip().upper() for c in self._clientes):
                raise DatoInvalidoError(f"El ID de cliente '{id_cliente}' ya está registrado.")

            nuevo_cliente = Cliente(id_cliente, nombre, documento, correo, telefono)

        except SoftwareFJError as exc:
            # Registra el error controlado en el log y continúa sin detener la aplicación[cite: 2].
            self._operaciones_fallidas += 1
            logger.error(f"[FALLO REGISTRO CLIENTE] {exc}")
            print(f"  [X] Error controlado al registrar cliente: {exc}")
            return None

        else:
            # Agrega el cliente a la lista en memoria solo si no hubo errores.
            self._clientes.append(nuevo_cliente)
            self._operaciones_exitosas += 1
            print(f"  [OK] {nuevo_cliente.obtener_resumen()}")
            return nuevo_cliente

        finally:
            # Registra siempre una traza de auditoría al finalizar el intento[cite: 2].
            logger.debug(
                f"Auditoría registro cliente ({id_cliente}) | "
                f"Total clientes en memoria: {len(self._clientes)}"
            )

    def registrar_servicio(self, clase_servicio, *args, **kwargs) -> Servicio | None:
        # Instancia y registra un servicio con try / except / else y encadenamiento de excepciones[cite: 2].
        try:
            nuevo_servicio = clase_servicio(*args, **kwargs)
            if any(s.id == nuevo_servicio.id for s in self._servicios):
                raise DatoInvalidoError(f"El ID de servicio '{nuevo_servicio.id}' ya existe.")

        except SoftwareFJError as exc:
            self._operaciones_fallidas += 1
            logger.error(f"[FALLO REGISTRO SERVICIO] {exc}")
            print(f"  [X] Error controlado al crear servicio: {exc}")
            return None

        except Exception as exc_inesperada:
            # Encadena excepciones no previstas dentro de un DatoInvalidoError[cite: 2].
            self._operaciones_fallidas += 1
            error_encadenado = DatoInvalidoError(
                f"Error estructural al instanciar servicio: {exc_inesperada}"
            )
            logger.error(f"[FALLO ENCADENADO SERVICIO] {error_encadenado} | Causa: {exc_inesperada}")
            print(f"  [X] Error encadenado al crear servicio: {error_encadenado}")
            return None

        else:
            self._servicios.append(nuevo_servicio)
            self._operaciones_exitosas += 1
            print(f"  [OK] {nuevo_servicio.obtener_resumen()}")
            return nuevo_servicio

        finally:
            logger.debug(
                f"Auditoría registro servicio | Total servicios en memoria: {len(self._servicios)}"
            )

    def crear_y_confirmar_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.19,
        **parametros_servicio,
    ) -> Reserva | None:
        # Busca cliente y servicio, crea la reserva, la confirma y usa try / except / else / finally[cite: 2].
        try:
            cliente = self.buscar_cliente(id_cliente)
            servicio = self.buscar_servicio(id_servicio)

            reserva = Reserva(
                id_reserva=id_reserva,
                cliente=cliente,
                servicio=servicio,
                duracion=duracion,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
                **parametros_servicio,
            )
            reserva.confirmar()

        except SoftwareFJError as exc:
            self._operaciones_fallidas += 1
            logger.error(f"[FALLO RESERVA {id_reserva}] {exc}")
            print(f"  [X] Error controlado en reserva {id_reserva}: {exc}")
            return None

        else:
            self._reservas.append(reserva)
            self._operaciones_exitosas += 1
            print(f"  [OK] {reserva.obtener_resumen()}")
            return reserva

        finally:
            logger.debug(
                f"Fin transacción reserva {id_reserva} | "
                f"Reservas almacenadas en memoria: {len(self._reservas)}"
            )

    def gestionar_estado_reserva(self, id_reserva: str, accion: str) -> None:
        # Procesa o cancela una reserva existente controlando errores de estado y validaciones[cite: 2].
        try:
            reserva = self.buscar_reserva(id_reserva)
            if accion == "PROCESAR":
                comprobante = reserva.procesar()
                self._operaciones_exitosas += 1
                print(f"  [OK] {comprobante}")
            elif accion == "CANCELAR":
                reserva.cancelar("Cancelación solicitada en simulación")
                self._operaciones_exitosas += 1
                print(f"  [OK] Reserva {id_reserva} cancelada y recursos liberados.")
            else:
                raise DatoInvalidoError(f"Acción de reserva desconocida: '{accion}'.")

        except SoftwareFJError as exc:
            self._operaciones_fallidas += 1
            logger.error(f"[FALLO GESTIÓN RESERVA {id_reserva}] {exc}")
            print(f"  [X] Error controlado al gestionar reserva {id_reserva}: {exc}")

    def mostrar_reporte_final(self) -> None:
        # Muestra el resumen final de listas en memoria y métricas de ejecución en consola y log[cite: 2, 3].
        print("\n" + "=" * 75)
        print("REPORTE FINAL EN MEMORIA - SOFTWARE FJ (SIN BASE DE DATOS)")
        print("=" * 75)
        print(f"Clientes registrados : {len(self._clientes)}")
        print(f"Servicios en catálogo: {len(self._servicios)}")
        print(f"Reservas almacenadas : {len(self._reservas)}")
        print(f"Operaciones exitosas : {self._operaciones_exitosas}")
        print(f"Errores controlados  : {self._operaciones_fallidas}")
        print("Archivo de auditoría : logs/software_fj.log")
        print("=" * 75)
        logger.info(
            f"=== FIN DE EJECUCIÓN | Exitosas: {self._operaciones_exitosas} | "
            f"Fallidas controladas: {self._operaciones_fallidas} ==="
        )


def ejecutar_simulacion():
    # Ejecuta 14 operaciones (válidas e inválidas) para probar estabilidad y manejo de errores[cite: 3].
    sistema = GestorSoftwareFJ()

    print("\n--- BLOQUE 1: REGISTRO DE CLIENTES (VÁLIDOS E INVÁLIDOS) ---")
    # Operación 1 (válida): registra el primer cliente.
    sistema.registrar_cliente("CLI-01", "Laura Mendoza", "1020304050", "laura@empresa.co", "3105551234")
    # Operación 2 (válida): registra el segundo cliente.
    sistema.registrar_cliente("CLI-02", "Carlos Ramírez", "80901020", "carlos.r@tech.com", "3204449876")
    # Operación 3 (inválida): dispara DatoInvalidoError por documento corto y correo sin '@'.
    sistema.registrar_cliente("CLI-03", "Ana", "123", "correo_invalido.com", "3001112233")

    print("\n--- BLOQUE 2: CREACIÓN DE SERVICIOS (POLIMORFISMO Y VALIDACIÓN) ---")
    # Operación 4 (válida): registra servicio de sala.
    sistema.registrar_servicio(
        ReservaSala, "SRV-S01", "Sala Innovación Bogotá", 120000, capacidad_maxima=15, incluye_videobeam=True
    )
    # Operación 5 (válida): registra servicio de alquiler de equipos.
    sistema.registrar_servicio(
        AlquilerEquipo, "SRV-E01", "Workstation Dell Precision", 85000, stock_disponible=4, gama="Workstation"
    )
    # Operación 6 (válida): registra servicio de asesoría especializada.
    sistema.registrar_servicio(
        AsesoriaEspecializada, "SRV-A01", "Consultoría Arquitectura Cloud", 180000,
        especialidad="AWS & Kubernetes", nivel_consultor="Arquitecto"
    )
    # Operación 7 (inválida): dispara DatoInvalidoError encadenado por tarifa no numérica.
    sistema.registrar_servicio(
        ReservaSala, "SRV-S99", "Sala Defectuosa", "tarifa_erronea", capacidad_maxima=10
    )

    print("\n--- BLOQUE 3: RESERVAS (SOBRECARGA DE COSTOS Y CONTROL DE ERRORES) ---")
    # Operación 8 (válida): reserva sala con descuento y recargo por ocupación mayor al 70%.
    sistema.crear_y_confirmar_reserva(
        "RES-001", "CLI-01", "SRV-S01", duracion=4, descuento_pct=10.0, asistentes=12
    )
    # Operación 9 (inválida): dispara ServicioNoDisponibleError al intentar reservar sala ocupada.
    sistema.crear_y_confirmar_reserva(
        "RES-002", "CLI-02", "SRV-S01", duracion=2, asistentes=5
    )
    # Operación 10 (válida): alquila 3 equipos por 5 días con descuento y sin IVA (impuesto_pct=0.0).
    sistema.crear_y_confirmar_reserva(
        "RES-003", "CLI-02", "SRV-E01", duracion=5, descuento_pct=5.0, impuesto_pct=0.0, cantidad=3
    )
    # Operación 11 (inválida): dispara DatoInvalidoError por stock insuficiente (solo queda 1 equipo).
    sistema.crear_y_confirmar_reserva(
        "RES-004", "CLI-01", "SRV-E01", duracion=2, cantidad=3
    )

    print("\n--- BLOQUE 4: PROCESAMIENTO Y TRANSICIONES DE ESTADO ---")
    # Operación 12 (válida): procesa RES-001 y libera la sala SRV-S01.
    sistema.gestionar_estado_reserva("RES-001", "PROCESAR")
    # Operación 13 (inválida): dispara OperacionNoPermitidaError al cancelar una reserva ya completada.
    sistema.gestionar_estado_reserva("RES-001", "CANCELAR")
    # Operación 14 (válida): crea y confirma una asesoría especializada de 3 horas con 15% de descuento.
    sistema.crear_y_confirmar_reserva(
        "RES-005", "CLI-01", "SRV-A01", duracion=3, descuento_pct=15.0
    )

    # Muestra el resumen final del sistema.
    sistema.mostrar_reporte_final()


if __name__ == "__main__":
    # Ejecuta la simulación al correr el archivo directamente.
    ejecutar_simulacion()