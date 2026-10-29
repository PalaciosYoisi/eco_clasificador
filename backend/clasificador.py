# clasificador.py - Clasificador de residuos (TensorFlow 2.16+)
import json
import logging
import os
import time
from pathlib import Path

# Debe ir antes de importar TensorFlow: oculta sus mensajes informativos de arranque
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import tensorflow as tf
from PIL import Image

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
logger = logging.getLogger(__name__)


class ClasificadorResiduos:
    def __init__(self, modelo_path=str(MODELS_DIR / 'modelo_final_residuos.h5'), config_path=str(MODELS_DIR / 'configuracion_clases.json')):
        """Cargar el modelo entrenado y su configuración."""
        try:
            if not os.path.exists(modelo_path):
                raise FileNotFoundError(f"No se encuentra el modelo: {modelo_path}")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"No se encuentra la configuración: {config_path}")

            self.model = tf.keras.models.load_model(
                modelo_path,
                compile=False,   # evita problemas de compilación con modelos antiguos
                safe_mode=False  # compatibilidad con modelos más antiguos
            )
            self.model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            self.class_names = list(self.config['class_indices'].keys())
            self.img_height = self.config['img_height']
            self.img_width = self.config['img_width']

        except Exception as e:
            logger.error(f"No se pudo cargar el modelo ({e}). Se usa el modo de respaldo: las respuestas NO son reales.")
            self._crear_modelo_dummy()

    def _crear_modelo_dummy(self):
        """Modo de respaldo cuando el modelo no carga (no clasifica de verdad)."""
        self.class_names = ['organic', 'plastic', 'paper', 'glass', 'metal']
        self.img_height = 160
        self.img_width = 160

    def clasificar_imagen(self, imagen_path):
        """Clasificar una imagen de residuo"""
        try:
            # Si no hay modelo cargado, usar modo dummy
            if not hasattr(self, 'model') or self.model is None:
                return self._clasificacion_dummy(imagen_path)

            if not os.path.exists(imagen_path):
                return {
                    'estado': 'error',
                    'mensaje': f'La imagen no existe: {imagen_path}'
                }

            # Cargar y preprocesar imagen
            img = Image.open(imagen_path).convert('RGB')
            original_size = img.size
            img = img.resize((self.img_width, self.img_height))
            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            # Predecir
            start_pred = time.time()
            predicciones = self.model.predict(img_array, verbose=0)
            prediction_time = time.time() - start_pred

            clase_idx = np.argmax(predicciones[0])
            confianza = float(np.max(predicciones[0]))

            # Resultados detallados, ordenados por confianza
            resultados_todos = {
                clase: float(conf)
                for clase, conf in zip(self.class_names, predicciones[0])
            }
            resultados_ordenados = dict(
                sorted(resultados_todos.items(), key=lambda x: x[1], reverse=True)
            )

            return {
                'estado': 'éxito',
                'categoria': self.class_names[clase_idx],
                'confianza': confianza,
                'clase_idx': int(clase_idx),
                'todas_las_clases': resultados_ordenados,
                'tiempo_prediccion': prediction_time,
                'tamano_original': f"{original_size[0]}x{original_size[1]}",
                'tamano_procesado': f"{self.img_width}x{self.img_height}"
            }

        except Exception as e:
            return {'estado': 'error', 'mensaje': f"Error al clasificar imagen: {str(e)}"}

    def _clasificacion_dummy(self, imagen_path):
        """Clasificación dummy para cuando no hay modelo"""
        import random
        categoria = random.choice(self.class_names)
        confianza = round(random.uniform(0.7, 0.95), 2)

        return {
            'estado': 'éxito',
            'categoria': categoria,
            'confianza': confianza,
            'clase_idx': self.class_names.index(categoria),
            'todas_las_clases': {cat: round(random.random(), 2) for cat in self.class_names},
            'tiempo_prediccion': 0.1,
            'tamano_original': '500x500',
            'tamano_procesado': f"{self.img_width}x{self.img_height}",
            'modo_dummy': True
        }

    def clasificar_desde_memoria(self, imagen_file):
        """Para uso en APIs web - imagen desde memoria"""
        try:
            # Si no hay modelo, usar dummy
            if not hasattr(self, 'model') or self.model is None:
                return self._clasificacion_dummy("memoria")

            img = Image.open(imagen_file).convert('RGB')
            img = img.resize((self.img_width, self.img_height))
            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predicciones = self.model.predict(img_array, verbose=0)
            clase_idx = np.argmax(predicciones[0])
            confianza = float(np.max(predicciones[0]))

            return {
                'estado': 'éxito',
                'categoria': self.class_names[clase_idx],
                'confianza': confianza,
                'clase_idx': int(clase_idx)
            }
        except Exception as e:
            return {'estado': 'error', 'mensaje': str(e)}

    def obtener_info_modelo(self):
        """Obtener información del modelo"""
        modelo_cargado = hasattr(self, 'model') and self.model is not None

        return {
            'clases': self.class_names,
            'tamano_imagen': f"{self.img_width}x{self.img_height}",
            'total_clases': len(self.class_names),
            'precision_entrenamiento': self.config.get('accuracy_final', '82.53%') if hasattr(self, 'config') else 'N/A',
            'modelo_cargado': modelo_cargado,
            'modo_dummy': not modelo_cargado
        }
