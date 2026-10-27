# EcoClasificador

Aplicación web que clasifica residuos a partir de una foto y le dice a la persona en qué caneca botarlos y cómo desecharlos. Está pensada para la comunidad de Quibdó, Chocó.

- **Modelo:** red convolucional MobileNetV2 (TensorFlow/Keras) entrenada con 10 categorías de residuos, con una exactitud de 82,5 % medida durante el entrenamiento.
- **Backend:** API en Flask (Python) con base de datos MySQL.
- **Frontend:** página web en HTML, CSS y JavaScript, sin dependencias de compilación.

**Categorías (10):** `bolsas_plastico`, `botellas_plastico`, `envases_plastico`, `organic`, `papel`, `recyclable`, `residuos_medicos`, `tetra_pack`, `vasos_papel`, `vidrio`.

---

## Estructura del proyecto

```
eco_clasificador-main/
├── backend/
│   ├── app.py              API Flask: endpoints, validación del archivo, registro de visitas
│   ├── clasificador.py     Carga el modelo y clasifica imágenes
│   ├── database.py         Acceso a MySQL
│   ├── config.py           Datos de conexión (referencia)
│   └── chatbot.py          Chatbot de consola con Gemini (no forma parte de la web)
├── frontend/
│   ├── index.html          Estructura de la página
│   ├── css/styles.css      Estilos
│   └── js/app.js           Lógica: llamadas a la API, clasificador, chat
├── models/
│   ├── modelo_final_residuos.h5       Modelo que usa la API
│   ├── mejor_modelo_mobilenet.h5      Mejor punto de control del entrenamiento
│   └── configuracion_clases.json      Clases, tamaño de imagen (160x160) y exactitud
├── notebooks/              Entrenamiento (modelo, modelo2) y gráficas
├── data/
│   ├── recyclable/         Imágenes del dataset
│   └── ejemplo.jpg         Imagen de ejemplo para probar
├── runtime/                Se genera al ejecutar: uploads/ (fotos subidas), temp/, logs/
├── docs/                   Planteamiento del proyecto y documento de pruebas unitarias
├── tests/                  Pruebas unitarias (pytest)
├── pytest.ini
├── requirements.txt
└── README.md
```

Las rutas del backend (modelo, configuración, `runtime/`) se calculan a partir de la ubicación de los archivos, así que la API se puede ejecutar desde cualquier carpeta.

---

## Requisitos

- Python 3.12 (probado con 3.12; TensorFlow 2.16 o superior).
- MySQL, por ejemplo con XAMPP. La conexión está en `backend/database.py`: host `localhost`, puerto `3307`, usuario `root`, sin contraseña y base de datos `ecoclasificador_db`. Cambia estos valores si tu instalación es distinta.
- Para el chatbot de consola (opcional): una clave de la API de Gemini.

## Instalación

Desde la carpeta raíz del proyecto:

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

**1. Encender MySQL** (en XAMPP, el módulo MySQL) y comprobar que existe la base `ecoclasificador_db`.

**2. Iniciar la API** (escucha en el puerto 5000):

```bash
python backend/app.py
```

**3. Abrir la página.** Se recomienda servirla por HTTP, porque algunos navegadores restringen los archivos externos cuando se abre `index.html` con doble clic:

```bash
python -m http.server 5500 --directory frontend
```

Luego abrir http://localhost:5500. La página llama a la API en `http://127.0.0.1:5000` (constante `API_BASE_URL` en `frontend/js/app.js`).

Si MySQL está apagado, la API arranca, pero los endpoints que usan la base de datos (guardar clasificaciones, guías, estadísticas) no funcionarán.

### Endpoints principales

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/clasificar` | Clasifica una imagen enviada en el campo `imagen` |
| GET | `/clasificaciones` | Historial de clasificaciones |
| GET | `/estadisticas` | Estadísticas del sistema |
| GET | `/guia/<categoria>`, `/guias` | Guías de cómo desechar cada residuo |
| GET | `/consejos` | Consejos ecológicos |
| GET | `/centros-reciclaje` | Centros de reciclaje |
| GET | `/noticias` | Noticias ecológicas |
| POST | `/feedback` | Recibe comentarios de los usuarios |
| GET | `/modelo/info` | Información del modelo |
| GET | `/sistema/status` | Estado del sistema |

`POST /clasificar` acepta imágenes `png`, `jpg`, `jpeg`, `gif` y `webp` de hasta 10 MB.

---

## Pruebas unitarias

Esta sección explica **qué se probó, cómo se probó, qué resultado se obtuvo y qué defectos se encontraron**. Está escrita para poder armar con ella el documento de entrega (el Word). Sigue lo visto en la Clase 02 (anatomía de un caso de prueba) y en la Clase 03 (pruebas unitarias).

### 1. Resumen

| Dato | Valor |
|---|---|
| Módulo probado | Clasificación de residuos (backend) |
| Funcionalidades del plan | F2 (validar el archivo) y F3 (clasificar el residuo) |
| Casos de prueba | **50** |
| Resultado | **43 pasan y 7 fallan** |
| Defectos encontrados | **4** (H-01 a H-04), que explican los 7 fallos |
| Cobertura | 41 % (65 % en `clasificador.py`, 33 % en `app.py`) |
| Herramienta | pytest 9.0.3 y pytest-cov 7.1.0 (Python 3.12, Windows 11) |
| Tiempo de ejecución | unos 2 segundos |

Los siete fallos son **defectos reales del código, no errores de las pruebas**. Se comprobó enviando las mismas entradas a la API real, con el modelo real, y respondió igual. Cuando una prueba falla no se cambia para que pase: la fila que falla es el hallazgo.

### 2. Qué se prueba y por qué

El Plan de Pruebas divide el módulo de clasificación en cuatro funcionalidades (F1 a F4) y asigna las **pruebas unitarias** a las dos de prioridad alta:

- **F2, validar el archivo:** "rechaza con un mensaje claro los envíos sin archivo, de otro tipo, dañados o de más de 10 MB".
- **F3, clasificar el residuo:** "devuelve una de las 10 categorías y el porcentaje de confianza".

F1 (cargar la foto) y F4 (mostrar el resultado) ocurren en la página web, así que corresponden a las pruebas de sistema, no a estas. Tampoco se prueban, porque el plan los deja por fuera: el módulo de información (guías, consejos, centros, noticias), EcoBot, la clasificación por URL y el reentrenamiento del modelo.

Una prueba unitaria comprueba **una función, sola**, sin base de datos, sin red y sin pantalla. Las funciones que cumplen esa condición y que corresponden a F2 y F3 son estas tres:

| Función | Archivo | Qué recibe | Qué devuelve |
|---|---|---|---|
| `allowed_file(nombre)` | `backend/app.py` | El nombre de un archivo (texto) | `True` si la extensión es png, jpg, jpeg, gif o webp; `False` en otro caso |
| `POST /clasificar` | `backend/app.py` | Un archivo enviado en el campo `imagen` | Un JSON con la categoría y la confianza, o un error con código y mensaje |
| `ClasificadorResiduos.clasificar_imagen(ruta)` y `clasificar_desde_memoria(archivo)` | `backend/clasificador.py` | La ruta de una imagen, o la imagen en memoria | Un diccionario con estado, categoría, confianza y todas las clases ordenadas |

Nivel de las pruebas: **unitaria**. Tipo: **funcional**. Enfoque: **caja blanca**, porque se conoce el código y se prueba por dentro (por ejemplo, el bloque `except` que convierte un error 413 en un 500).

### 3. Cómo se diseñaron los casos

**3.1 Pocos casos, bien escogidos.** No se puede probar todo: los nombres de archivo y las fotos posibles son infinitos. Como dice la Clase 03, "con cuatro particiones y cuatro límites quedan ocho casos, no cientos": el oficio está en cubrir el comportamiento del que se duda con la menor cantidad de pruebas posible. Por eso son 50 casos, escogidos con tres criterios:

- **Particiones de equivalencia:** se agrupan las entradas que el sistema debe tratar igual y se prueba un representante de cada grupo.
- **Valores límite:** se prueba justo en el borde de cada regla, porque ahí se concentran los defectos. El más importante es el tamaño: 10 MB menos 1 byte, 10 MB exactos y 10 MB más 1 byte.
- **Riesgos del plan:** se incluyeron los riesgos que el plan ya había identificado al revisar el código, por ejemplo "si el modelo no carga, el sistema puede dar categorías al azar sin avisar".

Además, el camino feliz no basta: **más de la mitad de los casos son negativos** (extensiones falsas, archivos vacíos, dañados, nombres peligrosos, modelo ausente), porque suelen encontrar más defectos.

**3.2 De dónde sale el resultado esperado.** Se escribió **antes de ejecutar** y se tomó del Plan de Pruebas y de este README (extensiones permitidas, límite de 10 MB, las 10 categorías y el tamaño 160 × 160 de la imagen). **Nunca** se tomó del comportamiento actual del código: si fuera así, la prueba solo certificaría el defecto.

**3.3 Datos quemados.** Cada prueba define dentro de su propio archivo la entrada que usa y la salida que espera, normalmente en una tabla `(caso, entrada, esperado, objetivo)`. Nada se lee de la pantalla, de la base de datos ni de archivos que puedan cambiar. Por eso la prueba da siempre el mismo resultado: si falla, el defecto está en el código y no en los datos.

**3.4 Reglas de forma** (de la Clase 03):

| Regla | Cómo se cumple aquí |
|---|---|
| Preparar, ejecutar, verificar | Todas las pruebas tienen las tres partes, con comentarios en las que tienen más de una línea |
| El nombre es documentación | El nombre dice qué se comprueba, por ejemplo `test_limite_de_tamano_del_archivo` o `test_cp_env_13_si_el_clasificador_lanza_una_excepcion_responde_500` |
| Una prueba, un caso | Ninguna prueba mezcla dos casos: cada variación es una fila de la tabla |
| Sin lógica adentro | Ninguna prueba tiene `if`, ciclos ni condiciones |
| Parametrizar | Los casos que comparten la verificación son una tabla con `@pytest.mark.parametrize`: agregar un caso es agregar una línea |
| Lo que debe fallar | `pytest.raises(TypeError)` en CP-EXT-12 |

Ejemplo real (CP-CAT-01 a 04, parametrizado):

```python
@pytest.mark.parametrize("caso, probabilidades, categoria_esperada, confianza_esperada, objetivo", GANADORAS)
def test_gana_la_categoria_de_mayor_probabilidad(
        clasificador, foto, caso, probabilidades, categoria_esperada, confianza_esperada, objetivo):
    clasificador.model.probabilidades = probabilidades              # preparar

    resultado = clasificador.clasificar_imagen(foto)                # ejecutar

    assert resultado["categoria"] == categoria_esperada             # verificar
    assert resultado["confianza"] == pytest.approx(confianza_esperada)
```

**3.5 Cinco dependencias que estorban y cómo se resolvieron.** La Clase 03 enumera cinco cosas que hacen difícil probar. En EcoClasificador aparecen así:

| Dependencia | ¿Estorba aquí? | Cómo se resolvió |
|---|---|---|
| Base de datos | Sí: `app.py` abre MySQL al importarse | `BaseDeDatosFalsa`, un *stub* que no abre ninguna conexión |
| Red y servicios externos | No en lo que se prueba | No aplica |
| El reloj | No | No aplica |
| El azar | Sí: el modo de respaldo del clasificador usa `random` | No se oculta: es el hallazgo H-04. Con el modelo falso, el resultado es fijo |
| La pantalla | Sí, en parte: el clasificador imprime mensajes con `print` | No afecta: pytest los captura |

Además estorban el modelo entrenado (`.h5`) y TensorFlow, porque cargarlos tarda y su respuesta cambia con cada foto. Todos los reemplazos son *stubs* (devuelven una respuesta fija) y se definen **dentro de cada archivo de pruebas**:

| Reemplazo | Qué hace | Dónde se usa |
|---|---|---|
| `BaseDeDatosFalsa` | Stub de MySQL | Los 4 archivos de `f2_validar_archivo` |
| `ClasificadorFalso` | Stub del clasificador: responde "papel", o lo que la prueba le indique | Los 3 archivos de la API que clasifican |
| `ClasificadorQueFalla` | Stub que siempre lanza una excepción | `test_errores_y_guardado.py` (CP-ENV-13) |
| `ModeloFalso` | Stub del modelo: devuelve probabilidades fijas y guarda lo que recibe | Los 3 archivos de `f3_clasificar_residuo` |
| `ModeloQueFalla` | Stub de un modelo que siempre se rompe | `test_errores_del_clasificador.py` (CP-CAT-09) |
| TensorFlow | Un módulo vacío, solo mientras corre la prueba | Los 7 archivos |
| Carpeta `runtime/uploads/` | Una carpeta temporal (`tmp_path`) que pytest crea y borra | Las pruebas de la API |

Como dice la Clase 03, un doble "no se usa para que la prueba pase a la fuerza: se usa para quitar del camino lo que no se está probando". Aquí se reemplaza lo que rodea a la función, no lo que se espera de ella. Evaluar los aciertos del modelo real (las 500 fotos del plan) es otro tipo de prueba, la evaluación del modelo, y no es unitaria.

**3.6 Archivos.** Las pruebas no usan archivos guardados en el proyecto. Las entradas son textos (nombres de archivo), bytes en memoria (el contenido de un envío) y unas pocas imágenes que el propio código crea con la librería PIL en una carpeta temporal, porque `clasificar_imagen()` necesita abrir una ruta real. Desaparecen al terminar la prueba.

**3.7 Una prueba que nunca ha fallado no sirve de nada.** Siguiendo la Clase 03, antes de darlas por buenas se cambió a propósito el resultado esperado de cada prueba en una copia y se confirmó que fallaban: de las 50, **49 fallaron de inmediato** y la que quedó (CP-CAT-06, los campos del resultado) falló en cuanto se le pidió un campo que no existe. Ninguna pasa "de adorno".

**3.8 Las cinco señales de alarma.**

| Señal | ¿Se cumple? |
|---|---|
| La que no verifica nada | No: todas tienen `assert` o `pytest.raises` |
| La que depende de otra | No: cada prueba arma sus datos y puede ejecutarse sola y en cualquier orden |
| La que falla día de por medio | No: no hay fechas, internet ni valores aleatorios |
| La que prueba el lenguaje | No: todas prueban funciones del proyecto |
| La que nadie entiende | No: los nombres dicen qué comprueban y cada caso tiene su objetivo |

**3.9 Identificadores.** Cada caso tiene un ID `CP-<tema>-<número>`: `EXT` (extensión), `ENV` (envío a la API), `IMG` (preparar la imagen) y `CAT` (escoger la categoría). El ID aparece en la tabla de casos y en el nombre o la tabla de datos de su prueba. Para ejecutar un caso se escribe en minúsculas y con guion bajo: `CP-ENV-10` se busca como `cp_env_10`.

### 4. Particiones de equivalencia y valores límite

#### `allowed_file(nombre)`

| Partición | Qué entradas agrupa | Resultado esperado |
|---|---|---|
| Extensión permitida | jpg, jpeg, png, gif, webp; también en mayúsculas | `True` (CP-EXT-01 a 06) |
| Extensión no permitida | pdf, exe, y `.jpg.exe` | `False` (CP-EXT-07 a 09) |
| Sin extensión | `foto` | `False` (CP-EXT-10) |
| Nombre vacío | `""` | `False` (CP-EXT-11) |
| No es un texto | `None` | Lanza `TypeError` (CP-EXT-12) |

| Valor límite | Por qué es un límite |
|---|---|
| `foto.jpg.exe` | Empieza como imagen y termina como programa: se debe mirar la última extensión |
| `foto` y `""` | No hay extensión, o no hay nada |

#### `POST /clasificar`

| Partición | Qué entradas agrupa | Resultado esperado |
|---|---|---|
| Envío sin archivo | Sin el campo `imagen`; nombre de archivo vacío | 400 (CP-ENV-01 y 02) |
| Tipo no permitido | pdf, exe | 400 `TIPO_INVALIDO` (CP-ENV-03 y 04) |
| Tipo permitido | png | 200 con los campos que usa la página (CP-ENV-05 y 06) |
| Tamaño válido | De 5 MB hasta 10 MB | 200 (CP-ENV-07 a 09) |
| Tamaño demasiado grande | Más de 10 MB | 413 (CP-ENV-10) |
| Falla la clasificación | El clasificador devuelve error o lanza una excepción | Error HTTP y mensaje (CP-ENV-11 a 13) |
| Guardado de la foto | Nombre peligroso; mismo nombre dos veces | Dentro de `uploads`; no se pisan (CP-ENV-14 y 15) |

| Valor límite | Por qué es un límite |
|---|---|
| 10 MB menos 1 byte | El último valor antes del máximo (CP-ENV-08) |
| 10 MB exactos | El máximo que el plan acepta (CP-ENV-09) |
| 10 MB más 1 byte | El primer valor que debe rechazarse (CP-ENV-10) |

#### `ClasificadorResiduos`

| Partición | Qué entradas agrupa | Resultado esperado |
|---|---|---|
| Foto de cualquier tamaño o formato | 300 × 200, 1 × 1, 4000 × 3000; png, jpg; grises y transparencia | El modelo recibe 160 × 160 × 3 (CP-IMG-01 a 06) |
| Valores de los píxeles | 255, rojo puro, transparencia | Entre 0 y 1, en orden rojo, verde, azul (CP-IMG-07 a 09) |
| Imagen en memoria | Una imagen válida; bytes que no son una imagen | Se prepara igual; estado `error` (CP-IMG-10 y 11) |
| Una categoría gana | La primera, una del medio, la última, certeza total | La de mayor probabilidad (CP-CAT-01 a 04) |
| Forma del resultado | Orden y campos | Lo que usa la API (CP-CAT-05 y 06) |
| Entradas que no se pueden clasificar | Ruta inexistente, archivo dañado, modelo que falla | Estado `error` con mensaje (CP-CAT-07 a 09) |
| El modelo no carga | El archivo del modelo no existe | Nunca `éxito` con un resultado inventado (CP-CAT-10 a 12) |

| Valor límite | Por qué es un límite |
|---|---|
| Foto de 1 × 1 y de 4000 × 3000 | La más pequeña y una de las más grandes posibles |
| Píxel en 255 | El extremo del rango, que debe quedar en 1 |
| Posición 0 y posición 9 | La primera y la última de las 10 categorías (CP-CAT-01 y 03) |
| Confianza 1.0 | La más alta posible (CP-CAT-04) |

### 5. Estructura de las pruebas

Las pruebas están en `tests/`, divididas por funcionalidad del plan y, dentro de cada una, en archivos pequeños por tema (como las carpetas numeradas de los ejemplos de la clase). Cada archivo es **independiente**: lleva dentro sus **datos quemados** (las tablas de casos) y sus propios reemplazos, y se puede ejecutar solo. No hay archivos compartidos entre ellos.

```
tests/
├── f2_validar_archivo/                    F2 · 27 casos
│   ├── test_extension_del_nombre.py       CP-EXT-01 a 12
│   ├── test_validacion_del_envio.py       CP-ENV-01 a 06
│   ├── test_limite_de_tamano.py           CP-ENV-07 a 10
│   └── test_errores_y_guardado.py         CP-ENV-11 a 15
└── f3_clasificar_residuo/                 F3 · 23 casos
    ├── test_preparar_la_imagen.py         CP-IMG-01 a 11
    ├── test_escoger_categoria.py          CP-CAT-01 a 06
    └── test_errores_del_clasificador.py   CP-CAT-07 a 12
```

Al inicio de cada archivo se indica la función probada, el nivel, el tipo, la caja, de dónde sale el resultado esperado, la precondición y cómo ejecutarlo.

### 6. Tabla de casos de prueba

Las columnas **Objetivo**, **Entrada** y **Resultado esperado** se escribieron antes de ejecutar; **Obtenido** y **Estado** se llenaron después. Estado: *Pasa* o *Falla* (ningún caso quedó *Bloqueado*). Cuando un caso pasa, lo obtenido coincide con lo esperado.

#### `tests/f2_validar_archivo/test_extension_del_nombre.py`

- **Función que se prueba:** `allowed_file(nombre)`
- **Precondición de todos los casos:** Ninguna (la función solo mira un texto)

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-EXT-01 | extensión jpg permitida | `foto.jpg` | `True` | Igual al esperado | Pasa |
| CP-EXT-02 | extensión jpeg permitida | `foto.jpeg` | `True` | Igual al esperado | Pasa |
| CP-EXT-03 | extensión png permitida | `foto.png` | `True` | Igual al esperado | Pasa |
| CP-EXT-04 | extensión gif permitida | `foto.gif` | `True` | Igual al esperado | Pasa |
| CP-EXT-05 | extensión webp permitida | `foto.webp` | `True` | Igual al esperado | Pasa |
| CP-EXT-06 | las mayúsculas no importan | `FOTO.JPG` | `True` | Igual al esperado | Pasa |
| CP-EXT-07 | un pdf no es una imagen | `documento.pdf` | `False` | Igual al esperado | Pasa |
| CP-EXT-08 | un ejecutable no es una imagen | `programa.exe` | `False` | Igual al esperado | Pasa |
| CP-EXT-09 | parece imagen pero termina en .exe | `foto.jpg.exe` | `False` | Igual al esperado | Pasa |
| CP-EXT-10 | sin extensión | `foto` | `False` | Igual al esperado | Pasa |
| CP-EXT-11 | nombre vacío | "" (vacío) | `False` | Igual al esperado | Pasa |
| CP-EXT-12 | un valor nulo no se acepta en silencio | `None` | Lanza `TypeError` | Igual al esperado | Pasa |

#### `tests/f2_validar_archivo/test_validacion_del_envio.py`

- **Función que se prueba:** `POST /clasificar`
- **Precondición de todos los casos:** API con clasificador y base de datos falsos

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-ENV-01 | rechazar una petición sin el campo `imagen` | Petición sin ningún campo | 400, código `SIN_ARCHIVO` | Igual al esperado | Pasa |
| CP-ENV-02 | rechazar a quien no escogió ninguna foto | Campo `imagen` con el nombre de archivo vacío (como lo envía el navegador) | 400, código `ARCHIVO_VACIO` | Igual al esperado | Pasa |
| CP-ENV-03 | un pdf no es una imagen | Archivo `documento.pdf` | 400, código `TIPO_INVALIDO` | Igual al esperado | Pasa |
| CP-ENV-04 | un ejecutable no es una imagen | Archivo `programa.exe` | 400, código `TIPO_INVALIDO` | Igual al esperado | Pasa |
| CP-ENV-05 | camino feliz: una foto permitida se clasifica | Archivo `foto.png` | 200, estado `éxito` | Igual al esperado | Pasa |
| CP-ENV-06 | la página necesita estos campos para mostrar el resultado | Archivo `foto.png` | La respuesta trae `estado`, `categoria`, `confianza`, `guia_residuo`, `id_clasificacion`, `todas_las_clases` y `metadatos` | Igual al esperado | Pasa |

#### `tests/f2_validar_archivo/test_limite_de_tamano.py`

- **Función que se prueba:** `POST /clasificar`
- **Precondición de todos los casos:** API con clasificador y base de datos falsos

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-ENV-07 | un tamaño normal | Archivo de 5 MB | 200 | Igual al esperado | Pasa |
| CP-ENV-08 | valor límite: un byte menos que el máximo | Archivo de 10 MB menos 1 byte (10 485 759 bytes) | 200 | 500, código `ERROR_INTERNO` (se rechaza) | **Falla** |
| CP-ENV-09 | valor límite: el máximo exacto | Archivo de exactamente 10 MB (10 485 760 bytes) | 200 | 500, código `ERROR_INTERNO` (se rechaza) | **Falla** |
| CP-ENV-10 | valor límite: un byte más que el máximo | Archivo de 10 MB más 1 byte (10 485 761 bytes) | 413, código `ARCHIVO_DEMASIADO_GRANDE` | 500, código `ERROR_INTERNO`, mensaje "Error interno del servidor" | **Falla** |

#### `tests/f2_validar_archivo/test_errores_y_guardado.py`

- **Función que se prueba:** `POST /clasificar`
- **Precondición de todos los casos:** API con clasificador y base de datos falsos; las fotos se guardan en una carpeta temporal

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-ENV-11 | un archivo dañado no debe responder 200 | El clasificador devuelve `error`: "Error al clasificar imagen: archivo dañado" | Código HTTP 400 o mayor | 200 OK con `{"estado": "error"}` en el cuerpo | **Falla** |
| CP-ENV-12 | el usuario debe ver el mensaje que explica el error | El clasificador devuelve `error` con ese mismo mensaje | La respuesta trae el mismo mensaje | Igual al esperado | Pasa |
| CP-ENV-13 | un fallo inesperado se informa como error del servidor | El clasificador lanza una excepción (`fallo inesperado`) | 500, código `ERROR_PROCESAMIENTO` | Igual al esperado | Pasa |
| CP-ENV-14 | un nombre que sube carpetas no puede escapar de `uploads` | Archivo `../../escapar.png` | La foto se guarda dentro de la carpeta de subidas | Igual al esperado | Pasa |
| CP-ENV-15 | dos personas que suben el mismo nombre no se pisan | Dos envíos de `foto.png` con contenidos distintos | Quedan dos archivos, uno con cada contenido | Igual al esperado | Pasa |

#### `tests/f3_clasificar_residuo/test_preparar_la_imagen.py`

- **Función que se prueba:** `ClasificadorResiduos.clasificar_imagen(ruta)` y `clasificar_desde_memoria(archivo)`
- **Precondición de todos los casos:** Clasificador con modelo falso; el modelo guarda lo que recibe

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-IMG-01 | una foto horizontal | Foto png de 300 × 200 | El modelo recibe forma (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-02 | un solo píxel | Foto png de 1 × 1 | El modelo recibe forma (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-03 | una foto de 12 megapíxeles | Foto png de 4000 × 3000 | El modelo recibe forma (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-04 | png en escala de grises | Foto png en modo L (grises) | El modelo recibe 3 canales: (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-05 | png con transparencia | Foto png en modo RGBA | El modelo recibe 3 canales: (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-06 | formato jpg | Foto jpg de 300 × 200 | El modelo recibe forma (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-07 | el máximo, 255, pasa a 1 | Foto blanca (255, 255, 255) | Primer píxel [rojo, verde, azul] = [1.0, 1.0, 1.0] | Igual al esperado | Pasa |
| CP-IMG-08 | el rojo es el primer canal | Foto roja (255, 0, 0) | Primer píxel = [1.0, 0.0, 0.0] | Igual al esperado | Pasa |
| CP-IMG-09 | la transparencia se descarta | Foto RGBA (255, 0, 0, 0) | Primer píxel = [1.0, 0.0, 0.0] | Igual al esperado | Pasa |
| CP-IMG-10 | la imagen en memoria se prepara igual | Imagen png de 300 × 200 en memoria | El modelo recibe forma (1, 160, 160, 3) | Igual al esperado | Pasa |
| CP-IMG-11 | un texto en lugar de una imagen no tumba el sistema | Bytes `esto no es una imagen`, en memoria | Estado `error` | Igual al esperado | Pasa |

#### `tests/f3_clasificar_residuo/test_escoger_categoria.py`

- **Función que se prueba:** `ClasificadorResiduos.clasificar_imagen(ruta)`
- **Precondición de todos los casos:** Clasificador con modelo falso; cada caso le indica al modelo qué probabilidades devolver

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-CAT-01 | gana la primera categoría de la lista | 0.91 en la posición 0 y 0.01 en el resto | `bolsas_plastico`, confianza 0.91 | Igual al esperado | Pasa |
| CP-CAT-02 | gana una del medio: residuos médicos | 0.82 en la posición 6 y 0.02 en el resto | `residuos_medicos`, confianza 0.82 | Igual al esperado | Pasa |
| CP-CAT-03 | gana la última categoría de la lista | 0.91 en la posición 9 y 0.01 en el resto | `vidrio`, confianza 0.91 | Igual al esperado | Pasa |
| CP-CAT-04 | certeza total: la confianza es 1 | 1.0 en la posición 5 y 0 en el resto | `recyclable`, confianza 1.0 | Igual al esperado | Pasa |
| CP-CAT-05 | la página muestra primero la categoría más probable | Probabilidades mezcladas (la mayor, 0.30) | `todas_las_clases` ordenado de mayor a menor | Igual al esperado | Pasa |
| CP-CAT-06 | si falta un campo, la API falla al armar su respuesta | Una foto válida | Trae `estado`, `categoria`, `confianza`, `clase_idx`, `todas_las_clases`, `tiempo_prediccion`, `tamano_original` y `tamano_procesado` | Igual al esperado | Pasa |

#### `tests/f3_clasificar_residuo/test_errores_del_clasificador.py`

- **Función que se prueba:** `ClasificadorResiduos`
- **Precondición de todos los casos:** CP-CAT-07 a 09: clasificador con modelo falso. CP-CAT-10 a 12: el archivo del modelo y el de configuración no existen

| ID | Objetivo | Entrada | Resultado esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-CAT-07 | avisar si la ruta no existe | Ruta `no_existe.png` | Estado `error`; el mensaje dice que no existe | Igual al esperado | Pasa |
| CP-CAT-08 | un `.jpg` que en realidad es texto | Archivo `danado.jpg` con texto | Estado `error` | Igual al esperado | Pasa |
| CP-CAT-09 | un fallo del modelo no tumba el sistema | Modelo que lanza `modelo roto` al predecir | Estado `error`; el mensaje incluye `modelo roto` | Igual al esperado | Pasa |
| CP-CAT-10 | sin modelo no se inventa una categoría | `clasificar_imagen` con una foto válida | Estado distinto de `éxito` | Estado `éxito` con una categoría al azar (modo dummy) | **Falla** |
| CP-CAT-11 | lo mismo por el camino de la imagen en memoria | `clasificar_desde_memoria` con una imagen válida | Estado distinto de `éxito` | Estado `éxito` con una categoría al azar (modo dummy) | **Falla** |
| CP-CAT-12 | aunque falle el modelo, las categorías son las del sistema | `class_names` del clasificador sin modelo | Las 10 categorías del README | Solo 5: `glass`, `metal`, `organic`, `paper`, `plastic` | **Falla** |

### 7. Hallazgos (defectos encontrados)

Cada caso que falló dio origen a un hallazgo. La **severidad** es una propuesta del equipo: *alta* si el usuario recibe un resultado equivocado o un error que no entiende, *media* si el sistema incumple un criterio del plan, y *baja* si el efecto no alcanza a la página web. Los cuatro hallazgos tienen algo en común: el sistema funciona cuando todo sale bien, pero cuando algo falla su respuesta no corresponde a lo que realmente pasó.

| ID | Casos que fallan | Severidad | Defecto |
|---|---|---|---|
| H-01 | CP-ENV-10 | Alta | Un archivo de más de 10 MB responde "Error interno" en lugar de "Archivo demasiado grande" |
| H-02 | CP-ENV-08, CP-ENV-09 | Media | Un archivo de 10 MB menos 1 byte o de exactamente 10 MB se rechaza |
| H-03 | CP-ENV-11 | Baja | Cuando la clasificación falla, la API responde con código HTTP 200 |
| H-04 | CP-CAT-10, CP-CAT-11, CP-CAT-12 | Alta | Sin modelo, el sistema responde "éxito" con una categoría inventada |

#### H-01 · Un archivo de más de 10 MB responde "Error interno" (severidad alta)

- **Qué se esperaba:** código 413 con el mensaje "Archivo demasiado grande. Tamaño máximo: 10MB" (el plan, F2, pide un mensaje claro).
- **Qué ocurrió:** la API respondió 500 con `ERROR_INTERNO` y "Error interno del servidor". El registro del servidor muestra "Error interno: 413 Request Entity Too Large": Flask sí detectó el exceso de tamaño, pero la respuesta correcta se perdió en el camino.
- **Causa:** en la función `clasificar_imagen()` de `backend/app.py`, la lectura del archivo está dentro de un bloque `try` que termina en `except Exception`. Ese bloque atrapa el error 413 y lo convierte en un 500, así que el manejador de errores 413 que sí existe nunca se ejecuta.
- **Por qué importa:** la persona ve un error genérico y no sabe que solo necesita subir una foto más liviana.
- **Cómo se reproduce:** `python -m pytest -k cp_env_10`.
- **Corrección sugerida:** agregar `except RequestEntityTooLarge: raise` antes del `except Exception`, para que Flask use su manejador 413.

#### H-02 · Un archivo de 10 MB (o un byte menos) se rechaza (severidad media)

- **Qué se esperaba:** que 10 MB exactos (10 485 760 bytes) y 10 MB menos 1 byte se aceptaran, porque el plan rechaza los archivos "de más de 10 MB" y el README dice "hasta 10 MB".
- **Qué ocurrió:** la API respondió 500 (el mismo error de H-01). Al corregir H-01 el rechazo seguirá, pero con código 413. Un archivo de 5 MB sí pasa.
- **Causa:** `MAX_CONTENT_LENGTH` de Flask está fijado en 10 MB, pero se aplica a **toda la petición**, no solo al archivo, y la petición incluye también las cabeceras del formulario. Por eso un archivo de 10 MB justos ya supera el límite: en la práctica el sistema acepta un poco menos de lo que promete.
- **Cómo se reproduce:** `python -m pytest -k cp_env_09`.
- **Corrección sugerida:** subir `MAX_CONTENT_LENGTH` unos kilobytes por encima de 10 MB y comprobar el tamaño del archivo por separado; o cambiar el criterio del plan a "menos de 10 MB". Lo debe decidir el equipo.

#### H-03 · Un error de clasificación responde con código 200 (severidad baja)

- **Qué se esperaba:** un código HTTP de error (400 o mayor), porque el 200 significa que todo salió bien.
- **Qué ocurrió:** la API respondió 200 OK y dejó el error escondido en el cuerpo: `{"estado": "error", "codigo": "ERROR_CLASIFICACION"}`.
- **Causa:** la rama de error de `clasificar_imagen()` termina en `return jsonify(respuesta)` sin indicar un código, y Flask usa 200 por defecto.
- **Por qué importa (y por qué es baja):** la página web no se ve afectada porque revisa tanto `response.ok` como el campo `estado`. Pero las pruebas de Postman del plan, un monitor o cualquier otra aplicación que se guíe por el código HTTP tomaría el fallo como un éxito.
- **Cómo se reproduce:** `python -m pytest -k cp_env_11`.
- **Corrección sugerida:** devolver `jsonify(respuesta), 422` en la rama de error.

#### H-04 · Sin modelo, el sistema inventa la clasificación (severidad alta)

- **Qué se esperaba:** que, sin el archivo del modelo, el sistema avisara del problema (estado distinto de "éxito"). El plan identifica este riesgo: "si el modelo no carga, el sistema puede dar categorías al azar sin avisar".
- **Qué ocurrió:** el clasificador imprimió "Creando modelo dummy para continuar..." y respondió `éxito` con una categoría elegida al azar y una confianza inventada entre 0.70 y 0.95. Solo el campo interno `modo_dummy` delata la situación, y la API no se lo muestra al usuario. Además, ese modo de respaldo solo maneja 5 categorías (`glass`, `metal`, `organic`, `paper`, `plastic`), distintas de las 10 del sistema (CP-CAT-12). Pasa tanto por `clasificar_imagen()` (CP-CAT-10) como por `clasificar_desde_memoria()` (CP-CAT-11).
- **Causa:** el constructor de `ClasificadorResiduos` (`backend/clasificador.py`) atrapa cualquier error al cargar el modelo y llama a `_crear_modelo_dummy()`; después, `_clasificacion_dummy()` escoge una categoría con `random.choice` y devuelve `éxito`. Es la dependencia "el azar" de la Clase 03, pero metida en el código de producción.
- **Por qué importa:** es el fallo más grave. La persona recibe con total seguridad una indicación equivocada y bota mal el residuo, que es justo lo que la aplicación quiere evitar.
- **Cómo se reproduce:** `python -m pytest -k cp_cat_10`. En la aplicación: renombrar `models/modelo_final_residuos.h5` y clasificar una foto.
- **Corrección sugerida:** responder con un error 503 ("servicio no disponible") cuando no hay modelo, o impedir que la API arranque sin él. Si se conserva el modo dummy, que sea solo para desarrollo y con un aviso visible.

Una vez corregido cada defecto, se vuelve a ejecutar la misma prueba, sin cambios, como **prueba de confirmación**: el hallazgo se da por cerrado cuando el caso pasa.

### 8. Cobertura

| Módulo | Sentencias | Sin probar | Cobertura | Lo que queda sin probar |
|---|---|---|---|---|
| `backend/clasificador.py` | 112 | 39 | 65 % | La carga real del modelo, `obtener_info_modelo()` y el bloque de prueba manual del final del archivo |
| `backend/app.py` | 329 | 220 | 33 % | Las rutas de información (guías, consejos, centros, noticias), historial, estadísticas, feedback y chatbot |
| **Total** | 441 | 259 | **41 %** | |

La cobertura de `app.py` es baja a propósito: el plan deja por fuera todo lo que no es clasificación. Además, la cobertura indica qué líneas se ejecutaron, **no si el código es correcto**: 100 % no significa que el programa esté bien, y subir la cifra con pruebas sin verificaciones sería engañarse. Por eso lo que se evalúa es la tabla de casos, y la cobertura sirve para encontrar el código que nadie está probando.

### 9. Cómo ejecutar las pruebas

Siempre desde la carpeta raíz del proyecto. Si es la primera vez: `pip install -r requirements.txt`.

Todas las pruebas, con el nombre de cada una:

```bash
python -m pytest -v
```

Una funcionalidad (una carpeta):

```bash
python -m pytest -v tests/f2_validar_archivo
```

Un solo archivo (cada uno corre solo):

```bash
python -m pytest -v tests/f2_validar_archivo/test_limite_de_tamano.py
```

Un solo caso, por su ID en minúsculas y con guion bajo (`CP-ENV-10` se busca como `cp_env_10`):

```bash
python -m pytest -v -k cp_env_10
```

Con cobertura:

```bash
python -m pytest --cov=app --cov=clasificador --cov-report=term-missing
```

Si la terminal de Windows muestra `UnicodeEncodeError` por los emojis del código, ejecutar antes en PowerShell: `$env:PYTHONIOENCODING = "utf-8"`.

### 10. Cómo leer los resultados

Los resultados aparecen **en la misma terminal donde se ejecuta el comando**. Un punto es una prueba que pasó y una `F` una que falló. Al final hay un resumen: con todas las pruebas, `7 failed, 43 passed`.

Cuando una prueba falla, pytest muestra un bloque con el detalle. La línea que empieza con `E` es la clave, porque muestra lo obtenido frente a lo esperado. Por ejemplo, para el caso CP-ENV-10 (`python -m pytest -k cp_env_10`) se ve `assert 500 == 413`: se esperaba un 413 y la API devolvió un 500. Esa línea es el hallazgo.

### 11. Cómo encaja en el Plan de Pruebas y cómo pasarlo al Word

La Clase 03 pide cinco elementos para las pruebas unitarias en el plan:

| Elemento | En este proyecto |
|---|---|
| Alcance | La clasificación de residuos, F2 y F3. Quedan por fuera, con su justificación, F1 y F4 (son de sistema) y todo lo que el plan excluye |
| Herramienta | pytest 9.0.3 con pytest-cov 7.1.0, sobre Python 3.12: es la más usada en Python y su complemento de cobertura muestra qué quedó probado |
| Criterio de salida | El plan pide al menos 95 % de casos aprobados y ningún defecto crítico abierto. Hoy: 43 de 50 (86 %) y dos hallazgos de severidad alta (H-01 y H-04), por lo que todavía no se cumple |
| Responsable | El equipo; la fase de pruebas unitarias del cronograma está a cargo de Yoisi Palacios |
| Evidencia | El reporte de ejecución (`python -m pytest -v`) y el de cobertura (`--cov`), junto con la tabla de la sección 6 |

El formato de la tabla sigue la plantilla del profesor (`10_taller/TABLA_DE_CASOS.md`) y la anatomía de un caso de la Clase 02:

| En el Word | Dónde está en esta sección |
|---|---|
| Función que se prueba, qué recibe y qué devuelve | Sección 2 (tabla de las tres funciones) |
| Particiones de equivalencia y valores límite | Sección 4 (una tabla de cada una por función) |
| Tabla de casos con ID, precondición, entrada, resultado esperado, obtenido y estado | Sección 6 (una tabla por archivo; la precondición está en el encabezado de cada una y en el Word se puede repetir como columna) |
| Cómo se hicieron las pruebas | Sección 3 |
| Hallazgos | Sección 7 |
| Cobertura y cómo se ejecutó | Secciones 8 y 9 |
