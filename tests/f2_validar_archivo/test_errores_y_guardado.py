"""CP-ENV-11 a 15 · Errores al clasificar y guardado de la foto   (F2: validar el archivo)

Función probada:  POST /clasificar  en backend/app.py
Nivel: unitaria · Tipo: funcional (seguridad) · Caja blanca
Resultado esperado: del Plan de Pruebas (F2: rechazar "con un mensaje claro" los archivos
                  "dañados"; el alcance incluye "la seguridad al subir archivos"). Un error
                  debe comunicarse con un código HTTP de error: el 200 significa que todo
                  salió bien.
Precondición: la API funciona con un clasificador y una base de datos falsos; cada prueba le
                  indica al clasificador falso qué responder, o lo cambia por uno que falla. Las fotos se guardan en una
                  carpeta temporal.

Ejecutar este archivo:  python -m pytest -v tests/f2_validar_archivo/test_errores_y_guardado.py
Ejecutar un caso:       python -m pytest -v -k cp_env_11
"""
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))   # para importar el código


# ----------------------------------------------------------------------
# Reemplazos de lo que estorba: MySQL y el clasificador
# ----------------------------------------------------------------------
class BaseDeDatosFalsa:
    """Stub de MySQL: no abre ninguna conexión."""

    def is_connected(self):
        return False

    def guardar_clasificacion(self, *argumentos, **opciones):
        return 1

    def obtener_guia_residuo(self, categoria):
        return {"categoria": categoria}


class ClasificadorFalso:
    """Stub del clasificador: devuelve el resultado que la prueba le indique."""

    def __init__(self):
        self.resultado = {
            "estado": "éxito", "categoria": "papel", "confianza": 0.9, "clase_idx": 4,
            "tiempo_prediccion": 0.1, "todas_las_clases": {"papel": 0.9, "organic": 0.1},
            "tamano_original": "10x10", "tamano_procesado": "160x160",
        }
        self.rutas_recibidas = []       # rutas donde la API guardó las fotos

    def clasificar_imagen(self, ruta):
        self.rutas_recibidas.append(ruta)
        return self.resultado


class ClasificadorQueFalla:
    """Stub de un clasificador que siempre lanza una excepción."""

    def clasificar_imagen(self, ruta):
        raise RuntimeError("fallo inesperado")


# app.py abre MySQL y carga el modelo apenas se importa: se importa con reemplazos.
sys.modules["tensorflow"] = SimpleNamespace()
sys.modules["database"] = SimpleNamespace(DatabaseManager=BaseDeDatosFalsa)
import app                                                  # noqa: E402


@pytest.fixture
def cliente(tmp_path):
    """Cliente HTTP de Flask; las fotos se guardan en la carpeta temporal tmp_path."""
    app.app.config["TESTING"] = True
    app.app.config["UPLOAD_FOLDER"] = str(tmp_path)
    app.clasificador = ClasificadorFalso()
    app.db = BaseDeDatosFalsa()
    return app.app.test_client()


def enviar_foto(cliente, contenido, nombre):
    """Envía una foto como lo hace el formulario de la página."""
    return cliente.post("/clasificar", content_type="multipart/form-data",
                        data={"imagen": (io.BytesIO(contenido), nombre)})


def test_cp_env_11_si_la_clasificacion_falla_la_respuesta_es_un_error_http(cliente):
    """CP-ENV-11 · Objetivo: un archivo dañado no debe responder 200."""
    app.clasificador.resultado = {
        "estado": "error", "mensaje": "Error al clasificar imagen: archivo dañado",
    }

    respuesta = enviar_foto(cliente, b"contenido", "foto.png")

    assert respuesta.status_code >= 400


def test_cp_env_12_el_mensaje_del_error_llega_al_usuario(cliente):
    """CP-ENV-12 · Objetivo: el usuario debe ver el mensaje que explica el error."""
    app.clasificador.resultado = {
        "estado": "error", "mensaje": "Error al clasificar imagen: archivo dañado",
    }

    datos = enviar_foto(cliente, b"contenido", "foto.png").get_json()

    assert datos["mensaje"] == "Error al clasificar imagen: archivo dañado"


def test_cp_env_13_si_el_clasificador_lanza_una_excepcion_responde_500(cliente):
    """CP-ENV-13 · Objetivo: un fallo inesperado se informa como error del servidor."""
    app.clasificador = ClasificadorQueFalla()

    respuesta = enviar_foto(cliente, b"contenido", "foto.png")

    assert respuesta.status_code == 500
    assert respuesta.get_json()["codigo"] == "ERROR_PROCESAMIENTO"


def test_cp_env_14_un_nombre_peligroso_se_guarda_dentro_de_la_carpeta_de_subidas(cliente, tmp_path):
    """CP-ENV-14 · Objetivo: un nombre como ../../x.png no puede escapar de la carpeta."""
    enviar_foto(cliente, b"contenido", "../../escapar.png")

    ruta_guardada = Path(app.clasificador.rutas_recibidas[0])
    assert ruta_guardada.resolve().parent == tmp_path.resolve()


def test_cp_env_15_dos_envios_con_el_mismo_nombre_no_se_sobrescriben(cliente, tmp_path):
    """CP-ENV-15 · Objetivo: dos personas que suben "foto.png" no se pisan."""
    enviar_foto(cliente, b"primera foto", "foto.png")                    # preparar

    enviar_foto(cliente, b"segunda foto", "foto.png")                    # ejecutar

    contenidos = sorted(archivo.read_bytes() for archivo in tmp_path.iterdir())
    assert contenidos == [b"primera foto", b"segunda foto"]             # verificar
