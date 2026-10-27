"""CP-EXT-01 a 12 · Extensión del archivo   (F2: validar el archivo)

Función probada:  allowed_file(nombre)  en backend/app.py
                  Recibe el nombre de un archivo y devuelve True si su extensión es
                  png, jpg, jpeg, gif o webp, y False en cualquier otro caso.
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F2: "solo acepta imágenes") y del README
                  ("acepta png, jpg, jpeg, gif y webp").
Precondición: ninguna (la función solo mira un texto).

Ejecutar este archivo:  python -m pytest -v tests/f2_validar_archivo/test_extension_del_nombre.py
Ejecutar un caso:       python -m pytest -v -k cp_ext_09
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))   # para importar el código


# app.py abre MySQL apenas se importa, así que se importa con una base de datos falsa.
class BaseDeDatosFalsa:
    """Stub de MySQL: no abre ninguna conexión."""

    def is_connected(self):
        return False


sys.modules["tensorflow"] = SimpleNamespace()      # tarda en cargar y no hace falta
sys.modules["database"] = SimpleNamespace(DatabaseManager=BaseDeDatosFalsa)
import app                                         # noqa: E402


# (caso, nombre del archivo, resultado esperado, objetivo)
NOMBRES = [
    ("cp_ext_01", "foto.jpg", True, "extensión jpg permitida"),
    ("cp_ext_02", "foto.jpeg", True, "extensión jpeg permitida"),
    ("cp_ext_03", "foto.png", True, "extensión png permitida"),
    ("cp_ext_04", "foto.gif", True, "extensión gif permitida"),
    ("cp_ext_05", "foto.webp", True, "extensión webp permitida"),
    ("cp_ext_06", "FOTO.JPG", True, "las mayúsculas no importan"),
    ("cp_ext_07", "documento.pdf", False, "un pdf no es una imagen"),
    ("cp_ext_08", "programa.exe", False, "un ejecutable no es una imagen"),
    ("cp_ext_09", "foto.jpg.exe", False, "parece imagen pero termina en .exe"),
    ("cp_ext_10", "foto", False, "sin extensión"),
    ("cp_ext_11", "", False, "nombre vacío"),
]


@pytest.mark.parametrize("caso, nombre, esperado, objetivo", NOMBRES)
def test_extension_del_nombre(caso, nombre, esperado, objetivo):
    resultado = app.allowed_file(nombre)                    # ejecutar

    assert resultado is esperado                            # verificar


def test_cp_ext_12_algo_que_no_es_un_texto_lanza_error():
    """CP-EXT-12 · Objetivo: un valor nulo no se acepta en silencio."""
    with pytest.raises(TypeError):
        app.allowed_file(None)
