# EcoClasificador

Clasificación de residuos con IA para Quibdó (API Flask + modelo MobileNetV2).

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | API Flask (`app.py`), clasificador, acceso a BD, configuración y chatbot de consola |
| `frontend/` | Página web (`index.html`) |
| `models/` | Modelos entrenados (`.h5`) y `configuracion_clases.json` |
| `notebooks/` | Entrenamiento y gráficas del modelo |
| `data/` | Dataset de entrenamiento (`recyclable/`) e imagen de ejemplo |
| `runtime/` | Archivos generados al ejecutar: `uploads/`, `temp/`, `logs/` |
| `docs/` | Documentación y plan de pruebas |
| `tests/` | Pruebas unitarias (pytest) |

## Ejecutar

```
pip install -r requirements.txt
python backend/app.py
```

Luego abrir `frontend/index.html` (la API responde en http://127.0.0.1:5000).
Requiere MySQL (XAMPP) con la base `ecoclasificador_db`.

## Notas

- Las rutas del backend se calculan desde la ubicación de los archivos, por lo que
  se puede ejecutar desde cualquier carpeta.
- Los notebooks usan rutas relativas (`recyclable`, `*.h5`): ajustar a `../data/recyclable`
  y `../models/` si se vuelven a ejecutar.
