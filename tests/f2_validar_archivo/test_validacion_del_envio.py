"""CP-ENV-01 a 06 · Validación del envío   (F2: validar el archivo)

Función probada:  POST /clasificar  en backend/app.py
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F2: "rechaza con un mensaje claro los envíos sin
                  archivo, de otro tipo...") y del README (formatos aceptados).
Precondición: la API funciona con un clasificador y una base de datos falsos; aquí se
                  mide la validación del envío, no la inteligencia artificial.

Ejecutar este archivo:  python -m pytest -v tests/f2_validar_archivo/test_validacion_del_envio.py
Ejecutar un caso:       python -m pytest -v -k cp_env_03
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
    """Stub del clasificador: siempre responde que la foto es papel."""

    def clasificar_imagen(self, ruta):
        return {
            "estado": "éxito", "categoria": "papel", "confianza": 0.9, "clase_idx": 4,
            "tiempo_prediccion": 0.1, "todas_las_clases": {"papel": 0.9, "organic": 0.1},
            "tamano_original": "10x10", "tamano_procesado": "160x160",
        }


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


# (caso, nombre del archivo, objetivo)
TIPOS_NO_PERMITIDOS = [
    ("cp_env_03", "documento.pdf", "un pdf no es una imagen"),
    ("cp_env_04", "programa.exe", "un ejecutable no es una imagen"),
]

CAMPOS_QUE_USA_LA_PAGINA = [
    "estado", "categoria", "confianza", "guia_residuo", "id_clasificacion",
    "todas_las_clases", "metadatos",
]


def test_cp_env_01_sin_el_campo_imagen_responde_400(cliente):
    """CP-ENV-01 · Objetivo: rechazar una petición que no trae el campo "imagen"."""
    respuesta = cliente.post("/clasificar", data={}, content_type="multipart/form-data")

    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "SIN_ARCHIVO"


def test_cp_env_02_archivo_con_nombre_vacio_responde_400(cliente):
    """CP-ENV-02 · Objetivo: rechazar a quien pulsó "Analizar" sin escoger una foto.

    Así lo envía el navegador: el campo "imagen" llega con el nombre del archivo vacío.
    """
    cuerpo = (
        '--FRONTERA\r\n'
        'Content-Disposition: form-data; name="imagen"; filename=""\r\n'
        'Content-Type: application/octet-stream\r\n'
        '\r\n'
        '\r\n'
        '--FRONTERA--\r\n'
    ).encode()

    respuesta = cliente.post("/clasificar", data=cuerpo,
                             content_type="multipart/form-data; boundary=FRONTERA")

    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "ARCHIVO_VACIO"


@pytest.mark.parametrize("caso, nombre, objetivo", TIPOS_NO_PERMITIDOS)
def test_tipo_de_archivo_no_permitido_responde_400(cliente, caso, nombre, objetivo):
    respuesta = enviar_foto(cliente, b"contenido", nombre)

    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "TIPO_INVALIDO"


def test_cp_env_05_una_foto_png_valida_responde_200(cliente):
    """CP-ENV-05 · Objetivo: el camino feliz, una foto permitida se clasifica."""
    respuesta = enviar_foto(cliente, b"contenido", "foto.png")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "éxito"


def test_cp_env_06_la_respuesta_trae_los_campos_que_usa_la_pagina(cliente):
    """CP-ENV-06 · Objetivo: la página necesita estos campos para mostrar el resultado."""
    datos = enviar_foto(cliente, b"contenido", "foto.png").get_json()

    assert set(CAMPOS_QUE_USA_LA_PAGINA) <= set(datos)
