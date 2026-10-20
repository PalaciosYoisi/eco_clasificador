#!/usr/bin/env python3
"""
Chatbot para Gestión de Residuos en Quibdó
Versión funcional y limpia
"""

import os
import google.generativeai as genai

# Configurar API Key
API_KEY = "AIzaSyBYnOIujosnZQzi9V-rKo2oorLWuoZFc9A"
genai.configure(api_key=API_KEY)

# Conocimiento especializado sobre Quibdó
CONOCIMIENTO_QUIBDO = """
INFORMACIÓN ESPECÍFICA SOBRE GESTIÓN DE RESIDUOS EN QUIBDÓ, CHOCÓ:

SISTEMA DE RECOLECCIÓN:
- 🔵 CONTENEDOR AZUL: Plásticos (botellas PET, envases HDPE) - deben lavarse y secarse
- ⚫ CONTENEDOR GRIS: Papel y cartón limpios y secos
- 🟢 CONTENEDOR VERDE: Residuos orgánicos (restos de comida, podas) para compostaje
- ⚪ CONTENEDOR BLANCO: Vidrio (botellas, frascos) - manejar con cuidado
- ⚫ CONTENEDOR NEGRO: Residuos no reciclables (pañales, toallas sanitarias, barrido)

PROBLEMAS AMBIENTALES EN QUIBDÓ:
- Contaminación del Río Atrato por residuos sólidos
- Acumulación en quebradas urbanas
- Falta de cultura de separación en origen
- Disposición inadecuada en espacios públicos

PUNTOS DE ACOPIO PRINCIPALES:
- Parque Manuel Mosquera Garcés (Parque Central)
- Universidad Tecnológica del Chocó
- Alcaldía Municipal
- Algunos centros comerciales locales

RECOMENDACIONES ESPECÍFICAS:
- Aprovechar la humedad alta para compostaje doméstico
- Usar canastos tradicionales en lugar de bolsas plásticas
- Participar en jornadas de limpieza del Río Atrato
- Separar los residuos desde el hogar
- Reportar puntos críticos de acumulación a la alcaldía

CONTACTO Y RECURSOS:
- Línea de atención ambiental: 123
- Oficina de servicios públicos municipal
- Jornadas de reciclaje los primeros sábados de cada mes
"""

def crear_prompt(pregunta):
    """Crea el prompt contextualizado para Quibdó"""
    return f"""
Eres EcoBot Quibdó, un asistente especializado exclusivamente en gestión de residuos sólidos, 
reciclaje y prácticas ambientales sostenibles para la ciudad de Quibdó, departamento del Chocó, Colombia.

INFORMACIÓN OFICIAL SOBRE QUIBDÓ:
{CONOCIMIENTO_QUIBDO}

INSTRUCCIONES ESTRICTAS:
1. Responde ÚNICAMENTE sobre gestión de residuos, reciclaje y medio ambiente en Quibdó
2. Usa SIEMPRE la información específica proporcionada sobre Quibdó
3. Sé preciso, práctico y orientado a soluciones locales
4. Si la pregunta no está relacionada con Quibdó o residuos, responde educadamente que solo puedes ayudar con temas ambientales de Quibdó
5. Proporciona información verificada y prácticas realizables en la comunidad
6. Incluye recomendaciones prácticas específicas para Quibdó

PREGUNTA DEL USUARIO: {pregunta}

RESPUESTA ESPECIALIZADA PARA QUIBDÓ:
"""

def main():
    print("=" * 60)
    print("🤖 ECOBOT QUIBDÓ - GESTIÓN INTELIGENTE DE RESIDUOS")
    print("=" * 60)
    print("💬 Asistente especializado en reciclaje para la comunidad de Quibdó")
    print("-" * 60)
    
    try:
        # Verificar que la API Key funcione
        modelo = genai.GenerativeModel('gemini-pro')
        print("✅ Conexión con IA establecida")
        print("✅ Conocimiento cargado: Gestión de residuos Quibdó")
        print("\n💬 Escribe tus preguntas sobre residuos en Quibdó")
        print("   Ejemplos:")
        print("   - ¿En qué contenedor van los plásticos?")
        print("   - ¿Dónde están los puntos de acopio?")
        print("   - ¿Qué problemas ambientales hay en Quibdó?")
        print("   - ¿Cómo puedo hacer compostaje en Quibdó?")
        print("   - 'salir' para terminar")
        print("-" * 60)
        
        while True:
            try:
                pregunta = input("\n👤 Tú: ").strip()
                
                if pregunta.lower() in ['salir', 'exit', 'quit', 'q']:
                    print("👋 ¡Gracias por usar EcoBot Quibdó!")
                    break
                
                if not pregunta:
                    continue
                
                # Crear prompt contextualizado
                prompt_completo = crear_prompt(pregunta)
                
                # Generar respuesta
                respuesta = modelo.generate_content(prompt_completo)
                
                print(f"\n🤖 EcoBot: {respuesta.text}")
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta pronto!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("💡 Intenta con otra pregunta")
                
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        print("💡 Verifica tu conexión a internet y la API Key")

if __name__ == "__main__":
    main()