"""CP-ENV-07 a 10 · Límite de tamaño de 10 MB   (F2: validar el archivo)

Función probada:  POST /clasificar  en backend/app.py
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F2: rechaza "los envíos de más de 10 MB"; valores
                  límite: "un archivo de exactamente 10 MB y otro con un poco más") y del
                  README ("hasta 10 MB").
Precondición: la API funciona con un clasificador y una base de datos falsos.

Valores límite: 10 MB menos 1 byte, exactamente 10 MB y 10 MB más 1 byte.

Ejecutar este archivo:  python -m pytest -v tests/f2_validar_archivo/test_limite_de_tamano.py
Ejecutar un caso:       python -m pytest -v -k cp_env_09
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


UN_MB = 1024 * 1024

# (caso, tamaño del archivo en bytes, código HTTP esperado, objetivo)
TAMANOS = [
    ("cp_env_07", 5 * UN_MB, 200, "un tamaño normal, 5 MB"),
    ("cp_env_08", 10 * UN_MB - 1, 200, "valor límite: 10 MB menos 1 byte"),
    ("cp_env_09", 10 * UN_MB, 200, "valor límite: exactamente 10 MB"),
    ("cp_env_10", 10 * UN_MB + 1, 413, "valor límite: 10 MB más 1 byte"),
]


@pytest.mark.parametrize("caso, tamano, codigo_esperado, objetivo", TAMANOS)
def test_limite_de_tamano_del_archivo(cliente, caso, tamano, codigo_esperado, objetivo):
    contenido = b"0" * tamano                                           # preparar

    respuesta = cliente.post("/clasificar", content_type="multipart/form-data",  # ejecutar
                             data={"imagen": (io.BytesIO(contenido), "foto.png")})

    assert respuesta.status_code == codigo_esperado                     # verificar
