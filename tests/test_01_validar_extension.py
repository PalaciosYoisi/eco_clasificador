"""F2 - Validar el archivo: revisar la extension del nombre.

Funcion bajo prueba: allowed_file(filename) en backend/app.py
Recibe un nombre de archivo y devuelve True si su extension esta permitida
(png, jpg, jpeg, gif, webp) y False en cualquier otro caso.

Ejecutar:  pytest -v tests/test_01_validar_extension.py
"""


def test_cp_01_extension_permitida_es_aceptada(app_modulo):
    """CP-01. Particion valida: un nombre con extension permitida."""
    nombre = "foto.jpg"                                 # preparar

    resultado = app_modulo.allowed_file(nombre)         # ejecutar

    assert resultado is True                            # verificar


def test_cp_02_doble_extension_peligrosa_es_rechazada(app_modulo):
    """CP-02. Valor limite: el nombre parece imagen pero termina en .exe."""
    nombre = "foto.jpg.exe"                             # preparar

    resultado = app_modulo.allowed_file(nombre)         # ejecutar

    assert resultado is False                           # verificar
