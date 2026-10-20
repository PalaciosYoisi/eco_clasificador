"""F3 - Clasificar el residuo: preparar la imagen y escoger la categoria.

Unidad bajo prueba: ClasificadorResiduos en backend/clasificador.py.
El modelo es un doble de prueba (ModeloFalso) que devuelve probabilidades
fijas, asi que el resultado esperado se conoce de antemano.

Ejecutar:  pytest -v tests/test_03_clasificador.py
"""
import pytest
from PIL import Image


def guardar_imagen(ruta, tamano=(300, 200), color=(255, 255, 255)):
    Image.new("RGB", tamano, color).save(ruta)
    return str(ruta)


def test_cp_08_escoge_la_categoria_de_mayor_probabilidad(crear_clasificador, tmp_path):
    """CP-08. El modelo da 0.70 a 'organic' (indice 3) y el resto se reparte."""
    resto = 0.30 / 9                                        # preparar
    probabilidades = [0.70 if i == 3 else resto for i in range(10)]
    clasificador = crear_clasificador(probabilidades)
    imagen = guardar_imagen(tmp_path / "residuo.png")

    resultado = clasificador.clasificar_imagen(imagen)      # ejecutar

    assert resultado["estado"] == "éxito"                   # verificar
    assert resultado["categoria"] == "organic"
    assert resultado["clase_idx"] == 3
    assert resultado["confianza"] == pytest.approx(0.70)


def test_cp_09_la_imagen_llega_al_modelo_de_160x160x3_y_normalizada(crear_clasificador, tmp_path):
    """CP-09. Una foto blanca de 300x200 se redimensiona y sus pixeles van de 0 a 1."""
    clasificador = crear_clasificador([0.1] * 10)           # preparar
    imagen = guardar_imagen(tmp_path / "blanca.png", tamano=(300, 200), color=(255, 255, 255))

    resultado = clasificador.clasificar_imagen(imagen)      # ejecutar

    entrada = clasificador.model.entrada_recibida           # verificar
    assert entrada.shape == (1, 160, 160, 3)
    assert entrada.max() == pytest.approx(1.0)
    assert resultado["tamano_original"] == "300x200"
    assert resultado["tamano_procesado"] == "160x160"


def test_cp_10_si_el_modelo_no_carga_no_responde_exito(modulo_clasificador, tmp_path):
    """CP-10. Riesgo del plan: sin modelo, el sistema no debe inventar una categoria."""
    clasificador = modulo_clasificador.ClasificadorResiduos(    # preparar
        modelo_path=str(tmp_path / "no_hay_modelo.h5"),
        config_path=str(tmp_path / "no_hay_config.json"),
    )
    imagen = guardar_imagen(tmp_path / "residuo.png")

    resultado = clasificador.clasificar_imagen(imagen)          # ejecutar

    assert resultado["estado"] != "éxito"                       # verificar
