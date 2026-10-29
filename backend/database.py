# database.py - Conexión simple a MySQL
import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self._aviso_mostrado = False    # el aviso de "sin MySQL" se muestra una sola vez
        self.connect()
    
    def connect(self):
        """Conectar a la base de datos existente"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                port=3307,
                user='root',      # Cambia si es necesario
                password='',      # Cambia si es necesario
                database='ecoclasificador_db',
                autocommit=True
            )
        except Error as e:
            if not self._aviso_mostrado:
                logger.warning(f"No se pudo conectar a MySQL: {e}")
                self._aviso_mostrado = True
            self.connection = None
    
    def is_connected(self):
        """Verificar si la conexión está activa"""
        if self.connection and self.connection.is_connected():
            return True
        return False
    
    def reconnect(self):
        """Reconectar si la conexión se perdió"""
        try:
            if not self.is_connected():
                self.connect()
            return self.is_connected()
        except Error as e:
            logger.error(f"Error reconectando: {e}")
            return False
    
    def guardar_clasificacion(self, nombre_archivo, categoria, confianza, datos_resultado):
        """Guardar resultado de clasificación"""
        if not self.reconnect():
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO clasificaciones (nombre_archivo, categoria_predicha, confianza, datos_resultado)
                VALUES (%s, %s, %s, %s)
            ''', (nombre_archivo, categoria, confianza, json.dumps(datos_resultado)))
            
            id_clasificacion = cursor.lastrowid
            cursor.close()
            return id_clasificacion
            
        except Error as e:
            logger.error(f"Error guardando clasificación: {e}")
            return None
    
    def obtener_guia_residuo(self, categoria):
        """Obtener información de la guía para una categoría"""
        if not self.reconnect():
            return None
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM guia_residuos WHERE categoria = %s
            ''', (categoria,))
            
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
            
        except Error as e:
            logger.error(f"Error obteniendo guía: {e}")
            return None
    
    def obtener_estadisticas(self):
        """Obtener estadísticas básicas"""
        if not self.reconnect():
            return None
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Total de clasificaciones
            cursor.execute('SELECT COUNT(*) as total FROM clasificaciones')
            total = cursor.fetchone()['total']
            
            # Clasificaciones por categoría
            cursor.execute('''
                SELECT categoria_predicha, COUNT(*) as cantidad, 
                       AVG(confianza) as confianza_promedio
                FROM clasificaciones 
                GROUP BY categoria_predicha 
                ORDER BY cantidad DESC
            ''')
            por_categoria = cursor.fetchall()
            
            cursor.close()
            
            return {
                'total_clasificaciones': total,
                'por_categoria': por_categoria
            }
            
        except Error as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
    
    def obtener_consejos(self, limite=10, categoria=None):
        """Obtener consejos ecológicos"""
        if not self.reconnect():
            return []
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
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
            return consejos
            
        except Error as e:
            logger.error(f"Error obteniendo consejos: {e}")
            return []
    
    def obtener_centros_reciclaje(self, ciudad=None):
        """Obtener centros de reciclaje"""
        if not self.reconnect():
            return []
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if ciudad:
                cursor.execute('''
                    SELECT * FROM centros_reciclaje 
                    WHERE ciudad = %s AND activo = TRUE
                    ORDER BY nombre
                ''', (ciudad,))
            else:
                cursor.execute('''
                    SELECT * FROM centros_reciclaje 
                    WHERE activo = TRUE
                    ORDER BY ciudad, nombre
                ''')
            
            centros = cursor.fetchall()
            cursor.close()
            return centros
            
        except Error as e:
            logger.error(f"Error obteniendo centros: {e}")
            return []
    
    def obtener_noticias(self, limite=5, destacadas=False):
        """Obtener noticias ecológicas"""
        if not self.reconnect():
            return []
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
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
            return noticias
            
        except Error as e:
            logger.error(f"Error obteniendo noticias: {e}")
            return []
    
    def guardar_feedback(self, clasificacion_id, fue_correcta, categoria_correcta=None, comentario=None):
        """Guardar feedback de clasificación"""
        if not self.reconnect():
            return False
            
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO feedback_clasificaciones 
                (clasificacion_id, fue_correcta, categoria_correcta, comentario)
                VALUES (%s, %s, %s, %s)
            ''', (clasificacion_id, fue_correcta, categoria_correcta, comentario))
            
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error guardando feedback: {e}")
            return False
    
    def close(self):
        """Cerrar conexión"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def guardar_conversacion_chatbot(self, fecha_log, user_input, bot_response, endpoint_hit):
        """Guarda un registro de la conversación del chatbot."""
        try:
            if not self.reconnect():
                return 0
                
            cursor = self.connection.cursor()
            
            # Obtener IP (opcional, podrías pasarlo desde app.py)
            # Aquí se asume que esta lógica se ejecutará solo a través del nuevo endpoint
            # y que app.py manejará la IP si es necesario, por simplicidad no la incluimos aquí
            
            cursor.execute('''
                INSERT INTO log_chatbot (fecha_log, user_input, bot_response, endpoint_hit)
                VALUES (NOW(), %s, %s, %s)
            ''', (user_input, bot_response, endpoint_hit))
            
            self.connection.commit()
            log_id = cursor.lastrowid
            cursor.close()
            return log_id
            
        except Error as e:
            logger.error(f"Error guardando log del chatbot: {e}")
            return 0
