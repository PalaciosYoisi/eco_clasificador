# app_completo.py - API Completa para EcoClasificador
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import logging
from werkzeug.utils import secure_filename
from typing import Dict, Any
import uuid

# Importar nuestros módulos
# **Asegúrate de que tus módulos 'clasificador' y 'database' existen**
from clasificador import ClasificadorResiduos
from database import DatabaseManager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_ecoclasificador.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:5500", "*"])  # Permite todos los orígenes para desarrollo

# Configuración
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['JSON_SORT_KEYS'] = False

# Crear carpetas necesarias
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('temp', exist_ok=True)

# Inicializar componentes
try:
    logger.info("🚀 Inicializando sistema EcoClasificador...")
    clasificador = ClasificadorResiduos()
    db = DatabaseManager()
    logger.info("✅ Componentes inicializados correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando componentes: {e}")
    # En un entorno de producción, es posible que quieras comentar el "raise"
    # para permitir que la API se levante sin base de datos o clasificador,
    # aunque con funcionalidad limitada.
    raise

# Utilidades
def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_client_ip():
    """Obtener IP del cliente"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def registrar_visita():
    """Registrar visita en la base de datos"""
    try:
        ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Buscar visita reciente de la misma IP
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id FROM visitantes 
            WHERE ip_address = %s AND fecha_visita > %s
            ORDER BY fecha_visita DESC LIMIT 1
        ''', (ip, datetime.now() - timedelta(hours=1)))
        
        visita_existente = cursor.fetchone()
        
        if visita_existente:
            # Actualizar visita existente
            cursor.execute('''
                UPDATE visitantes 
                SET paginas_visitadas = paginas_visitadas + 1,
                    tiempo_session = tiempo_session + 1
                WHERE id = %s
            ''', (visita_existente['id'],))
        else:
            # Nueva visita
            cursor.execute('''
                INSERT INTO visitantes (ip_address, user_agent)
                VALUES (%s, %s)
            ''', (ip, user_agent))
        
        db.connection.commit()
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error registrando visita: {e}")

# Middleware para registrar visitas
@app.before_request
def before_request():
    if db.is_connected() and request.endpoint and not request.endpoint.startswith('static'):
        registrar_visita()

# =============================================
# ENDPOINTS PRINCIPALES
# =============================================

@app.route('/')
def home():
    """Endpoint principal"""
    return jsonify({
        'mensaje': '🌱 API EcoClasificador - Gestión Inteligente de Residuos',
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            '/clasificar': 'POST - Clasificar imagen de residuo',
            '/clasificar/url': 'POST - Clasificar desde URL',
            '/clasificaciones': 'GET - Historial de clasificaciones',
            '/estadisticas': 'GET - Estadísticas del sistema',
            '/guia/<categoria>': 'GET - Guía de residuos por categoría',
            '/guias': 'GET - Todas las guías de residuos',
            '/consejos': 'GET - Consejos ecológicos',
            '/centros-reciclaje': 'GET - Centros de reciclaje',
            '/noticias': 'GET - Noticias ecológicas',
            '/feedback': 'POST - Enviar feedback',
            '/chatbot/log': 'POST - Registrar conversación del Chatbot', # NUEVO
            '/modelo/info': 'GET - Información del modelo IA',
            '/sistema/status': 'GET - Estado del sistema'
        }
    })

@app.route('/clasificar', methods=['POST'])
def clasificar_imagen():
    """Clasificar imagen de residuo desde archivo"""
    try:
        # Verificar si se envió archivo (Clave esperada: 'imagen')
        if 'imagen' not in request.files:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se envió imagen',
                'codigo': 'SIN_ARCHIVO'
            }), 400
        
        archivo = request.files['imagen']
        
        # Verificar nombre de archivo
        if archivo.filename == '':
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se seleccionó archivo',
                'codigo': 'ARCHIVO_VACIO'
            }), 400
        
        if not allowed_file(archivo.filename):
            return jsonify({
                'estado': 'error',
                'mensaje': f'Tipo de archivo no permitido. Formatos aceptados: {", ".join(ALLOWED_EXTENSIONS)}',
                'codigo': 'TIPO_INVALIDO'
            }), 400
        
        # Generar nombre único para el archivo
        filename = secure_filename(archivo.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # **GUARDAR ARCHIVO LOCALMENTE (MODIFICACIÓN PARA CONSERVAR IMAGEN)**
        archivo.save(filepath)
        logger.info(f"📁 Archivo guardado permanentemente: {unique_filename}")
        
        try:
            # Clasificar imagen
            resultado = clasificador.clasificar_imagen(filepath)
            
            if resultado['estado'] == 'éxito':
                # Guardar en base de datos
                id_clasificacion = db.guardar_clasificacion(
                    unique_filename,
                    resultado['categoria'],
                    resultado['confianza'],
                    resultado
                )
                
                # Obtener información de la guía
                guia = db.obtener_guia_residuo(resultado['categoria'])
                
                # Preparar respuesta completa
                respuesta = {
                    'estado': 'éxito',
                    'id_clasificacion': id_clasificacion,
                    'categoria': resultado['categoria'],
                    'confianza': resultado['confianza'],
                    'clase_idx': resultado['clase_idx'],
                    'tiempo_prediccion': resultado['tiempo_prediccion'],
                    'guia_residuo': guia,
                    'todas_las_clases': resultado['todas_las_clases'],
                    'metadatos': {
                        'tamano_original': resultado['tamano_original'],
                        'tamano_procesado': resultado['tamano_procesado'],
                        'nombre_archivo_guardado': unique_filename,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                logger.info(f"✅ Clasificación exitosa: {resultado['categoria']} ({resultado['confianza']:.2%})")
                
            else:
                respuesta = {
                    'estado': 'error',
                    'mensaje': resultado['mensaje'],
                    'codigo': 'ERROR_CLASIFICACION'
                }
                logger.error(f"❌ Error en clasificación: {resultado['mensaje']}")
            
            # **NOTA:** La imagen NO se elimina (se guarda localmente como se solicitó)
            
            return jsonify(respuesta)
            
        except Exception as e:
            # En caso de error, el archivo queda guardado para auditoría.
            
            logger.error(f"❌ Error procesando imagen: {str(e)}")
            return jsonify({
                'estado': 'error',
                'mensaje': f'Error procesando imagen: {str(e)}',
                'codigo': 'ERROR_PROCESAMIENTO'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error interno: {str(e)}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO'
        }), 500

@app.route('/clasificar/url', methods=['POST'])
def clasificar_desde_url():
    """Clasificar imagen desde URL (para implementación futura)"""
    return jsonify({
        'estado': 'desarrollo',
        'mensaje': 'Endpoint en desarrollo. Próximamente podrás clasificar imágenes desde URLs.',
        'codigo': 'EN_DESARROLLO'
    }), 501

@app.route('/clasificaciones', methods=['GET'])
def obtener_clasificaciones():
    """Obtener historial de clasificaciones"""
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = request.args.get('por_pagina', 20, type=int)
        offset = (pagina - 1) * por_pagina
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Obtener clasificaciones
        cursor.execute('''
            SELECT id, nombre_archivo, categoria_predicha, confianza, fecha_clasificacion
            FROM clasificaciones 
            ORDER BY fecha_clasificacion DESC 
            LIMIT %s OFFSET %s
        ''', (por_pagina, offset))
        
        clasificaciones = cursor.fetchall()
        
        # Contar total
        cursor.execute('SELECT COUNT(*) as total FROM clasificaciones')
        total = cursor.fetchone()['total']
        
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'clasificaciones': clasificaciones,
            'paginacion': {
                'pagina_actual': pagina,
                'por_pagina': por_pagina,
                'total': total,
                'paginas_totales': (total + por_pagina - 1) // por_pagina
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo clasificaciones'
        }), 500

@app.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtener estadísticas completas del sistema"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        
        # Estadísticas básicas
        cursor.execute('SELECT COUNT(*) as total FROM clasificaciones')
        total_clasificaciones = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM visitantes')
        total_visitantes = cursor.fetchone()['total']
        
        cursor.execute('SELECT AVG(confianza) as promedio FROM clasificaciones')
        confianza_promedio = cursor.fetchone()['promedio'] or 0
        
        # Clasificaciones por categoría
        cursor.execute('''
            SELECT categoria_predicha, COUNT(*) as cantidad, 
                   AVG(confianza) as confianza_promedio
            FROM clasificaciones 
            GROUP BY categoria_predicha 
            ORDER BY cantidad DESC
        ''')
        por_categoria = cursor.fetchall()
        
        # Clasificaciones hoy
        cursor.execute('''
            SELECT COUNT(*) as hoy 
            FROM clasificaciones 
            WHERE DATE(fecha_clasificacion) = CURDATE()
        ''')
        clasificaciones_hoy = cursor.fetchone()['hoy']
        
        # Clasificaciones última semana
        cursor.execute('''
            SELECT COUNT(*) as semana 
            FROM clasificaciones 
            WHERE fecha_clasificacion >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ''')
        clasificaciones_semana = cursor.fetchone()['semana']
        
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'estadisticas': {
                'total_clasificaciones': total_clasificaciones,
                'total_visitantes': total_visitantes,
                'confianza_promedio': round(confianza_promedio, 4),
                'clasificaciones_hoy': clasificaciones_hoy,
                'clasificaciones_semana': clasificaciones_semana,
                'por_categoria': por_categoria
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo estadísticas'
        }), 500

@app.route('/guia/<categoria>', methods=['GET'])
def obtener_guia(categoria):
    """Obtener guía específica para una categoría (Endpoint principal)"""
    try:
        guia = db.obtener_guia_residuo(categoria)
        if guia:
            return jsonify({
                'estado': 'éxito',
                'guia': guia
            })
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': f'Categoría no encontrada: {categoria}',
                'codigo': 'CATEGORIA_NO_ENCONTRADA'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo guía: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo guía'
        }), 500

@app.route('/guias', methods=['GET'])
def obtener_todas_guias():
    """Obtener todas las guías de residuos"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM guia_residuos ORDER BY categoria')
        guias = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'guias': guias,
            'total': len(guias)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo guías: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo guías'
        }), 500

@app.route('/consejos', methods=['GET'])
def obtener_consejos():
    """Obtener consejos ecológicos"""
    try:
        categoria = request.args.get('categoria', '')
        limite = request.args.get('limite', 10, type=int)
        
        cursor = db.connection.cursor(dictionary=True)
        
        if categoria:
            cursor.execute('''
                SELECT * FROM consejos_ecologicos 
                WHERE categoria = %s AND activo = TRUE
                ORDER BY RAND()
                LIMIT %s
            ''', (categoria, limite))
        else:
            cursor.execute('''
                SELECT * FROM consejos_ecologicos 
                WHERE activo = TRUE
                ORDER BY RAND()
                LIMIT %s
            ''', (limite,))
        
        consejos = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'consejos': consejos,
            'total': len(consejos)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo consejos: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo consejos'
        }), 500

@app.route('/centros-reciclaje', methods=['GET'])
def obtener_centros_reciclaje():
    """Obtener centros de reciclaje"""
    try:
        ciudad = request.args.get('ciudad', '')
        tipo_residuo = request.args.get('tipo_residuo', '')
        
        cursor = db.connection.cursor(dictionary=True)
        
        if ciudad and tipo_residuo:
            cursor.execute('''
                SELECT * FROM centros_reciclaje 
                WHERE ciudad = %s AND activo = TRUE
                AND JSON_CONTAINS(tipos_residuos, %s)
                ORDER BY nombre
            ''', (ciudad, f'"{tipo_residuo}"'))
        elif ciudad:
            cursor.execute('''
                SELECT * FROM centros_reciclaje 
                WHERE ciudad = %s AND activo = TRUE
                ORDER BY nombre
            ''', (ciudad,))
        elif tipo_residuo:
            cursor.execute('''
                SELECT * FROM centros_reciclaje 
                WHERE activo = TRUE
                AND JSON_CONTAINS(tipos_residuos, %s)
                ORDER BY ciudad, nombre
            ''', (f'"{tipo_residuo}"',))
        else:
            cursor.execute('''
                SELECT * FROM centros_reciclaje 
                WHERE activo = TRUE
                ORDER BY ciudad, nombre
            ''')
        
        centros = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'centros': centros,
            'total': len(centros)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo centros: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo centros de reciclaje'
        }), 500

@app.route('/noticias', methods=['GET'])
def obtener_noticias():
    """Obtener noticias ecológicas"""
    try:
        destacadas = request.args.get('destacadas', 'false').lower() == 'true'
        limite = request.args.get('limite', 5, type=int)
        
        cursor = db.connection.cursor(dictionary=True)
        
        if destacadas:
            cursor.execute('''
                SELECT * FROM noticias_ecologicas 
                WHERE destacada = TRUE AND activa = TRUE
                ORDER BY fecha_publicacion DESC
                LIMIT %s
            ''', (limite,))
        else:
            cursor.execute('''
                SELECT * FROM noticias_ecologicas 
                WHERE activa = TRUE
                ORDER BY fecha_publicacion DESC
                LIMIT %s
            ''', (limite,))
        
        noticias = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'noticias': noticias,
            'total': len(noticias)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo noticias: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo noticias'
        }), 500

@app.route('/feedback', methods=['POST'])
def recibir_feedback():
    """Recibir feedback sobre clasificaciones"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'estado': 'error',
                'mensaje': 'Datos JSON requeridos'
            }), 400
        
        clasificacion_id = data.get('clasificacion_id')
        fue_correcta = data.get('fue_correcta')
        categoria_correcta = data.get('categoria_correcta')
        comentario = data.get('comentario', '')
        
        if clasificacion_id is None or fue_correcta is None:
            return jsonify({
                'estado': 'error',
                'mensaje': 'clasificacion_id y fue_correcta son requeridos'
            }), 400
        
        cursor = db.connection.cursor()
        cursor.execute('''
            INSERT INTO feedback_clasificaciones 
            (clasificacion_id, fue_correcta, categoria_correcta, comentario)
            VALUES (%s, %s, %s, %s)
        ''', (clasificacion_id, fue_correcta, categoria_correcta, comentario))
        
        db.connection.commit()
        cursor.close()
        
        logger.info(f"✅ Feedback recibido para clasificación {clasificacion_id}")
        
        return jsonify({
            'estado': 'éxito',
            'mensaje': 'Feedback registrado correctamente',
            'id_feedback': cursor.lastrowid
        })
        
    except Exception as e:
        logger.error(f"Error registrando feedback: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error registrando feedback'
        }), 500

@app.route('/chatbot/log', methods=['POST'])
def log_chatbot_conversation():
    """Recibir y guardar el log de la conversación del chatbot en la base de datos."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'estado': 'error',
                'mensaje': 'Datos JSON requeridos para el log del chatbot'
            }), 400
        
        # Datos esperados del frontend/chatbot
        user_input = data.get('user_input', '')
        bot_response = data.get('bot_response', '')
        endpoint_hit = data.get('endpoint_hit', '') # Ruta específica de la API usada (ej. /guias/Plastico)
        
        if not user_input and not bot_response:
             return jsonify({
                'estado': 'error',
                'mensaje': 'Se requiere al menos la entrada del usuario o la respuesta del bot para el log.'
            }), 400
        
        # Llamar a la función de la base de datos (se asume su existencia en database.py)
        log_id = db.guardar_conversacion_chatbot(
            datetime.now().isoformat(), # Se pasa como primer argumento la fecha y hora
            user_input,
            bot_response,
            endpoint_hit
        )
        
        logger.info(f"💬 Log de chatbot guardado. ID: {log_id}")
        
        return jsonify({
            'estado': 'éxito',
            'mensaje': 'Log de conversación de chatbot registrado correctamente',
            'id_log': log_id
        })
        
    except AttributeError:
        # Esto ocurre si db.guardar_conversacion_chatbot() no existe
        logger.error("❌ Error: Función 'guardar_conversacion_chatbot' no definida en database.py. Asumiendo retorno 0.")
        return jsonify({
            'estado': 'advertencia',
            'mensaje': 'Log de chatbot no guardado. La función "guardar_conversacion_chatbot" no está implementada en database.py.',
            'id_log': 0
        }), 200
    except Exception as e:
        logger.error(f"❌ Error registrando log del chatbot: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error registrando log del chatbot'
        }), 500


@app.route('/modelo/info', methods=['GET'])
def info_modelo():
    """Obtener información del modelo de IA"""
    try:
        info = clasificador.obtener_info_modelo()
        return jsonify({
            'estado': 'éxito',
            'modelo': info
        })
    except Exception as e:
        logger.error(f"Error obteniendo info del modelo: {e}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Error obteniendo información del modelo'
        }), 500

@app.route('/sistema/status', methods=['GET'])
def status_sistema():
    """Verificar estado del sistema"""
    try:
        # Verificar conexión a base de datos
        db_status = 'desconectado'
        if db.is_connected():
            cursor = db.connection.cursor()
            cursor.execute('SELECT 1')
            db_status = 'conectado'
            cursor.close()
        
        # Verificar modelo
        modelo_status = 'cargado' if clasificador.model else 'error'
        
        return jsonify({
            'estado': 'éxito',
            'sistema': 'operativo',
            'componentes': {
                'base_datos': db_status,
                'modelo_ia': modelo_status,
                'api': 'operativa'
            },
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - start_time)
        })
        
    except Exception as e:
        logger.error(f"Error en status del sistema: {e}")
        return jsonify({
            'estado': 'error',
            'sistema': 'degradado',
            'mensaje': 'Problemas en algunos componentes'
        }), 500

# =============================================
# ENDPOINTS ADICIONALES PARA CHATBOT (FIX 404)
# =============================================
# (Estas rutas fueron añadidas para resolver el problema de 'Endpoint no encontrado')

@app.route('/guias/<nombre_residuo>', methods=['GET'])
def obtener_guia_chatbot(nombre_residuo):
    """Obtener guía específica para una categoría, usado por el chatbot."""
    try:
        # Reutiliza la función existente para obtener la guía
        guia = db.obtener_guia_residuo(nombre_residuo.capitalize()) 
        
        if guia:
            # Formato esperado por el JS del chatbot
            return jsonify({
                'residuo': guia.get('categoria', nombre_residuo),
                'contenedor_nombre': guia.get('contenedor_nombre', 'N/A'),
                'contenedor_color': guia.get('contenedor_color', 'N/A'),
                'instrucciones': guia.get('instrucciones', 'Consulta la guía principal.'),
                'residuos_ejemplo': guia.get('ejemplos', ['No disponibles'])
            }), 200
        else:
            logger.warning(f"Guía de residuo no encontrada para chatbot: {nombre_residuo}")
            return jsonify({'estado': 'error', 'mensaje': f'Guía para "{nombre_residuo}" no encontrada.'}), 404
    except Exception as e:
        logger.error(f"Error obteniendo guía para chatbot: {e}")
        return jsonify({'estado': 'error', 'mensaje': 'Error interno del servidor.'}), 500

@app.route('/consejos/<slug_consejo>', methods=['GET'])
def obtener_consejo_chatbot(slug_consejo):
    """Obtener un consejo específico por slug, usado por el chatbot."""
    try:
        # Simula la búsqueda por slug/categoría
        categoria_simulada = slug_consejo.split('-')[0].capitalize()
        
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM consejos_ecologicos 
            WHERE categoria = %s AND activo = TRUE
            ORDER BY fecha_publicacion DESC
            LIMIT 1
        ''', (categoria_simulada,))
        consejo = cursor.fetchone()
        cursor.close()

        if consejo:
            # Formato esperado por el JS del chatbot
            return jsonify({
                'titulo': consejo.get('titulo', 'Consejo Ecológico'),
                'contenido': consejo.get('contenido', 'Contenido del consejo no disponible.'),
                'fecha': consejo.get('fecha_publicacion', datetime.now()).strftime('%Y-%m-%d')
            }), 200
        else:
            logger.warning(f"Consejo no encontrado para slug: {slug_consejo}")
            return jsonify({'estado': 'error', 'mensaje': f'Consejo con slug "{slug_consejo}" no encontrado.'}), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo consejo para chatbot: {e}")
        return jsonify({'estado': 'error', 'mensaje': 'Error interno del servidor.'}), 500

@app.route('/centros-reciclaje/<ciudad>', methods=['GET'])
def obtener_centros_reciclaje_ciudad_chatbot(ciudad):
    """Obtener centros de reciclaje por ciudad usando la ruta dinámica del chatbot."""
    try:
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM centros_reciclaje 
            WHERE ciudad = %s AND activo = TRUE
            ORDER BY nombre
        ''', (ciudad.capitalize(),)) 
        
        centros = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'estado': 'éxito',
            'centros': centros,
            'total': len(centros)
        }), 200
    except Exception as e:
        logger.error(f"Error obteniendo centros para chatbot: {e}")
        return jsonify({'estado': 'error', 'mensaje': 'Error interno del servidor.'}), 500

# =============================================
# MANEJO DE ERRORES
# =============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'estado': 'error',
        'mensaje': 'Endpoint no encontrado',
        'codigo': 'ENDPOINT_NO_ENCONTRADO'
    }), 404

@app.errorhandler(413)
def too_large(error):
    return jsonify({
        'estado': 'error',
        'mensaje': f'Archivo demasiado grande. Tamaño máximo: {MAX_FILE_SIZE // 1024 // 1024}MB',
        'codigo': 'ARCHIVO_DEMASIADO_GRANDE'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({
        'estado': 'error',
        'mensaje': 'Error interno del servidor',
        'codigo': 'ERROR_INTERNO'
    }), 500

# =============================================
# INICIALIZACIÓN
# =============================================

if __name__ == '__main__':
    start_time = datetime.now()
    
    print("🌱 " + "="*50)
    print("🚀 API EcoClasificador v2.0 Iniciando...")
    print("📡 Endpoints disponibles:")
    print("   POST /clasificar          - Clasificar imagen (Ahora guarda localmente)")
    print("   POST /chatbot/log         - Registrar log de conversaciones (NUEVO)")
    print("   GET  /clasificaciones     - Historial")
    print("   GET  /estadisticas        - Estadísticas")
    print("   GET  /guias               - Guías de residuos")
    print("   GET  /consejos            - Consejos ecológicos")
    print("   GET  /centros-reciclaje   - Centros de reciclaje")
    print("   GET  /modelo/info         - Info del modelo IA")
    print("   GET  /sistema/status      - Estado del sistema")
    print("🌱 " + "="*50)
    
    # Ejecutar servidor
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True
    )