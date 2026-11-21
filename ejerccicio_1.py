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