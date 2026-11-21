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