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

Las pruebas siguen el **Plan de Pruebas** del proyecto (funcionalidades F2, validar el archivo, y F3, clasificar el residuo) y el método de la clase 03 de la Unidad 2: datos quemados, patrón preparar–ejecutar–verificar y una tabla de casos. Se hacen con **pytest**.

### Las 10 pruebas

| ID | Qué prueba | Archivo | Resultado |
|---|---|---|---|
| CP-01 | `allowed_file("foto.jpg")` devuelve True | `test_01_validar_extension.py` | Pasa |
| CP-02 | `allowed_file("foto.jpg.exe")` devuelve False | `test_01_validar_extension.py` | Pasa |
| CP-03 | Envío sin el campo `imagen` responde 400 | `test_02_validar_envio.py` | Pasa |
| CP-04 | Un PDF responde 400 y no se guarda | `test_02_validar_envio.py` | Pasa |
| CP-05 | Archivo de 10 MB + 1 byte responde 413 | `test_02_validar_envio.py` | **Falla** |
| CP-06 | Archivo de exactamente 10 MB se acepta | `test_02_validar_envio.py` | **Falla** |
| CP-07 | Si la clasificación falla, no responde HTTP 200 | `test_02_validar_envio.py` | **Falla** |
| CP-08 | Elige la categoría de mayor probabilidad | `test_03_clasificador.py` | Pasa |
| CP-09 | La imagen llega al modelo de 160×160×3 y normalizada (0 a 1) | `test_03_clasificador.py` | Pasa |
| CP-10 | Si el modelo no carga, no responde "éxito" | `test_03_clasificador.py` | **Falla** |

**Resultado: 6 pasan y 4 fallan.** Los cuatro fallos son defectos reales del código, no errores de las pruebas. Se comprobó ejecutando la API real con las mismas entradas. La fila que falla es el hallazgo: no se cambia la prueba para que pase.

### Ejecutar las pruebas

Siempre desde la carpeta raíz del proyecto.

Todas las pruebas, con el nombre de cada una:

```bash
python -m pytest -v
```

Un solo archivo:

```bash
python -m pytest -v tests/test_01_validar_extension.py
```

Una sola prueba, por su ID:

```bash
python -m pytest -v -k cp_08
```

Un hallazgo, para ver el informe del fallo (la línea `E` muestra el valor obtenido frente al esperado):

```bash
python -m pytest -k cp_05
```

Con cobertura:

```bash
python -m pytest --cov=app --cov=clasificador --cov-report=term-missing
```

Si la terminal de Windows muestra `UnicodeEncodeError` por los emojis del código, ejecutar antes en PowerShell: `$env:PYTHONIOENCODING = "utf-8"`.

Las pruebas tardan unos 2 segundos y no necesitan MySQL, ni el modelo real, ni conexión a internet.

### Qué se reemplaza en las pruebas

Una prueba unitaria debe correr sin lo que la rodea. Todo se prepara en [tests/conftest.py](tests/conftest.py):

| Qué se reemplaza | Doble de prueba | Dónde está |
|---|---|---|
| Base de datos MySQL | `BaseDeDatosFalsa` | `conftest.py`, clase `BaseDeDatosFalsa` |
| Modelo entrenado (`.h5`) | `ModeloFalso`, con probabilidades fijas | `conftest.py`, clase `ModeloFalso` |
| Clasificador completo (en las pruebas de la API) | `ClasificadorFalso` | `conftest.py`, clase `ClasificadorFalso` |
| TensorFlow | Un módulo vacío, solo mientras corre la prueba | fixture `modulo_clasificador` |
| Carpeta `runtime/uploads/` | Una carpeta temporal que pytest crea y borra | fixture `app_modulo` |

Las fixtures `app_modulo` y `crear_clasificador` arman `app.py` y `ClasificadorResiduos` con esos dobles. Son dobles de prueba, no resultados inventados: los resultados esperados salen del Plan de Pruebas.

### Cobertura

| Módulo | Cobertura |
|---|---|
| `backend/clasificador.py` | 46 % |
| `backend/app.py` | 31 % |
| Total | 35 % |

Es baja a propósito: el plan deja por fuera las rutas de información (guías, consejos, centros, noticias), EcoBot y la clasificación por URL. La cobertura dice qué líneas se ejecutaron, no si el código es correcto.

### Hallazgos de las pruebas

| ID | Caso | Severidad | Defecto |
|---|---|---|---|
| H-01 | CP-05 | Alta | Un archivo de más de 10 MB recibe `500 Error interno` en lugar de `413`, porque el `except Exception` de `/clasificar` captura el error 413 |
| H-02 | CP-06 | Media | Un archivo de exactamente 10 MB se rechaza, porque `MAX_CONTENT_LENGTH` cuenta todo el cuerpo de la petición y no solo el archivo |
| H-03 | CP-07 | Baja | Cuando la clasificación falla, la API responde HTTP 200 con `estado: "error"` |
| H-04 | CP-10 | Alta | Si el modelo no carga, el sistema responde "éxito" con una categoría al azar (modo dummy), y con solo 5 categorías en lugar de 10 |

El detalle de cada hallazgo (qué se esperaba, qué ocurrió, cómo reproducirlo, causa y corrección sugerida) está en [docs/Pruebas_unitarias_EcoClasificador.docx](docs/Pruebas_unitarias_EcoClasificador.docx), junto con la tabla de casos completa, las particiones de equivalencia y los valores límite.

Una vez corregido el código, se repiten las mismas pruebas como prueba de confirmación.
