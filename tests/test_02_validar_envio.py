"""F2 - Validar el archivo: lo que hace POST /clasificar antes de clasificar.

Se prueba la funcion de la ruta con un cliente de Flask. El clasificador y la
base de datos son falsos (ver conftest.py), asi que solo se mide la validacion.

Ejecutar:  pytest -v tests/test_02_validar_envio.py
"""
import io
import os


def enviar(cliente, contenido, nombre):
    """Envia un archivo al campo 'imagen', como lo hace el formulario web."""
    return cliente.post(
        "/clasificar",
        data={"imagen": (io.BytesIO(contenido), nombre)},
        content_type="multipart/form-data",
    )


def test_cp_03_envio_sin_archivo_responde_400(cliente):
    """CP-03. Particion invalida: la peticion llega sin el campo 'imagen'."""
    datos = {}                                          # preparar

    respuesta = cliente.post(                           # ejecutar
        "/clasificar", data=datos, content_type="multipart/form-data"
    )

    assert respuesta.status_code == 400                 # verificar
    assert respuesta.get_json()["codigo"] == "SIN_ARCHIVO"


def test_cp_04_archivo_de_tipo_no_permitido_responde_400_y_no_se_guarda(cliente):
    """CP-04. Particion invalida: un PDF no es una imagen."""
    carpeta = cliente.application.config["UPLOAD_FOLDER"]       # preparar
    guardados_antes = os.listdir(carpeta)

    respuesta = enviar(cliente, b"contenido", "documento.pdf")  # ejecutar

    assert respuesta.status_code == 400                         # verificar
    assert respuesta.get_json()["codigo"] == "TIPO_INVALIDO"
    assert os.listdir(carpeta) == guardados_antes


def test_cp_05_archivo_de_mas_de_10_mb_responde_413(cliente, app_modulo):
    """CP-05. Valor limite: 10 MB + 1 byte debe rechazarse con 413."""
    contenido = b"0" * (app_modulo.MAX_FILE_SIZE + 1)       # preparar

    respuesta = enviar(cliente, contenido, "grande.png")    # ejecutar

    assert respuesta.status_code == 413                     # verificar
    assert respuesta.get_json()["codigo"] == "ARCHIVO_DEMASIADO_GRANDE"


def test_cp_06_archivo_de_exactamente_10_mb_es_aceptado(cliente, app_modulo):
    """CP-06. Valor limite: 10 MB exactos son validos segun el plan (F2)."""
    contenido = b"0" * app_modulo.MAX_FILE_SIZE             # preparar

    respuesta = enviar(cliente, contenido, "limite.png")    # ejecutar

    assert respuesta.status_code == 200                     # verificar


def test_cp_07_si_la_clasificacion_falla_la_respuesta_no_es_200(cliente, app_modulo):
    """CP-07. Un error de clasificacion no debe presentarse como exito HTTP."""
    app_modulo.clasificador.resultado = {                   # preparar
        "estado": "error",
        "mensaje": "Error al clasificar imagen: archivo dañado",
    }

    respuesta = enviar(cliente, b"no es una imagen", "dañada.png")  # ejecutar

    assert respuesta.status_code >= 400                     # verificar
