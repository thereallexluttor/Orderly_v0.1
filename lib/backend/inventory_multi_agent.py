from textwrap import dedent
from phi.agent import Agent
from phi.model.google import Gemini
from typing import Dict, Any
import json
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY no está configurada en las variables de entorno")

class InventoryAnalysisSystem:
    def __init__(self):
        logger.info("Inicializando sistema de análisis de inventario...")
        self._initialize_agents()

    def _initialize_agents(self):
        try:
            logger.info("Configurando agentes con Gemini...")
            
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY no está configurada")
                
            # Crear una instancia del modelo
            try:
                model = Gemini(api_key=GOOGLE_API_KEY)
                logger.info("Modelo Gemini inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando modelo Gemini: {str(e)}")
                raise
            
            # Crear los agentes
            try:
                self.agents = {}
                
                # Inicializar analista
                self.agents["analyst"] = Agent(
                    name="InventoryAnalyst",
                    role="Analista experto en gestión de inventario de restaurantes",
                    model=model,
                    description="Analizo datos de inventario para identificar patrones, riesgos y oportunidades de optimización.",
                    instructions=[
                        "Analizar tendencias históricas y patrones de uso",
                        "Evaluar eficiencia de proveedores y costos",
                        "Identificar riesgos en la cadena de suministro",
                        "Considerar el impacto en las recetas y la operación"
                    ]
                )
                logger.info("Agente analista inicializado")
                
                # Inicializar asesor
                self.agents["advisor"] = Agent(
                    name="InventoryAdvisor",
                    role="Asesor estratégico de inventario gastronómico",
                    model=model,
                    description="Proporciono recomendaciones estratégicas basadas en análisis detallado del inventario.",
                    instructions=[
                        "Priorizar acciones basadas en impacto operativo",
                        "Considerar factores estacionales y tendencias",
                        "Optimizar niveles de stock y rotación",
                        "Sugerir mejoras en relaciones con proveedores"
                    ]
                )
                logger.info("Agente asesor inicializado")
                
            except Exception as e:
                logger.error(f"Error creando agentes: {str(e)}")
                raise
            
            # Verificar que los agentes se crearon correctamente
            if not all(agent in self.agents for agent in ["analyst", "advisor"]):
                raise ValueError("No se pudieron inicializar todos los agentes requeridos")
                
            logger.info("Sistema de agentes inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error en inicialización de agentes: {str(e)}", exc_info=True)
            raise ValueError(f"No se pudo inicializar el sistema de agentes: {str(e)}")

    def analyze_inventory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"Iniciando análisis para ingrediente: {context.get('ingredient_name')}")
            
            # Extraer datos relevantes del contexto
            basic_info = {
                "ingredient_name": context.get("ingredient_name"),
                "current_stock": context.get("current_stock"),
                "total_stock": context.get("total_stock"),
                "unit": context.get("unit"),
                "safe_factor": context.get("safe_factor")
            }
            
            logger.info(f"Datos básicos: {json.dumps(basic_info, indent=2)}")

            # Obtener historial y datos detallados
            history_data = context.get("history", [])
            recipe_data = context.get("recipe_usage", [])
            supplier_data = context.get("suppliers", [])
            
            logger.info(f"Datos históricos disponibles: {len(history_data)} registros")
            logger.info(f"Datos de recetas disponibles: {len(recipe_data)} registros")
            logger.info(f"Datos de proveedores disponibles: {len(supplier_data)} registros")

            # Análisis detallado
            logger.info("Solicitando análisis detallado al agente analista...")
            analysis = self._get_detailed_analysis(
                basic_info,
                history_data,
                recipe_data,
                supplier_data
            )
            logger.info("Análisis detallado completado")

            # Recomendaciones basadas en el análisis
            logger.info("Solicitando recomendaciones al agente asesor...")
            recommendations = self._get_strategic_recommendations(
                basic_info,
                analysis,
                history_data,
                recipe_data,
                supplier_data
            )
            logger.info("Recomendaciones completadas")

            result = {
                "status": "success",
                "analysis": analysis.strip() if isinstance(analysis, str) else "Error en análisis",
                "recommendations": recommendations.strip() if isinstance(recommendations, str) else "Error en recomendaciones"
            }
            
            logger.info("Análisis de inventario completado exitosamente")
            return result

        except Exception as e:
            logger.error(f"Error en análisis de inventario: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "analysis": "Error al generar análisis",
                "recommendations": "Error al generar recomendaciones"
            }

    def _get_detailed_analysis(self, basic_info: dict, history: list, recipes: list, suppliers: list) -> str:
        try:
            logger.info(f"Preparando prompt para análisis de {basic_info['ingredient_name']}")
            
            # Formatear los datos para el prompt
            history_summary = json.dumps([{
                "fecha": h.get("created_at", ""),
                "cantidad": h.get("quantity", 0),
                "tipo": h.get("type", "")
            } for h in history[:10]], indent=2, ensure_ascii=False)  # Últimos 10 registros
            
            recipes_summary = json.dumps([{
                "nombre": r.get("recipes", {}).get("name", ""),
                "cantidad": r.get("quantity", 0)
            } for r in recipes], indent=2, ensure_ascii=False)
            
            suppliers_summary = json.dumps([{
                "nombre": s.get("name", ""),
                "precio": s.get("price", 0),
                "tiempo_entrega": s.get("delivery_time", "")
            } for s in suppliers], indent=2, ensure_ascii=False)
            
            prompt = f"""
            Analiza detalladamente el ingrediente {basic_info['ingredient_name']}:

            DATOS BÁSICOS:
            - Stock actual: {basic_info['current_stock']} {basic_info['unit']}
            - Stock total: {basic_info['total_stock']} {basic_info['unit']}
            - Factor de seguridad: {basic_info['safe_factor']}%

            HISTORIAL DE MOVIMIENTOS (últimos 10):
            {history_summary}

            USO EN RECETAS:
            {recipes_summary}

            INFORMACIÓN DE PROVEEDORES:
            {suppliers_summary}

            REQUERIDO:
            1. Análisis de tendencias de uso y rotación
            2. Evaluación de la relación con proveedores
            3. Impacto en las operaciones de cocina
            4. Identificación de riesgos específicos

            Por favor, proporciona un análisis detallado y estructurado.
            """

            logger.info("Enviando prompt al agente analista")
            logger.debug(f"Prompt enviado: {prompt}")
            
            response = self.agents["analyst"].run(prompt)
            logger.info("Respuesta recibida del agente analista")
            
            if not response:
                logger.error("Respuesta del agente analista es None")
                return "Error: No se pudo generar el análisis"
            
            if not hasattr(response, 'content'):
                logger.error(f"Respuesta del agente analista no tiene contenido. Tipo de respuesta: {type(response)}")
                if isinstance(response, str):
                    return response
                return "Error: Formato de respuesta inválido"
            
            logger.debug(f"Contenido de la respuesta: {response.content}")
            return response.content

        except Exception as e:
            logger.error(f"Error en análisis detallado: {str(e)}", exc_info=True)
            return f"Error en análisis: {str(e)}"

    def _get_strategic_recommendations(self, basic_info: dict, analysis: str, 
                                    history: list, recipes: list, suppliers: list) -> str:
        try:
            logger.info(f"Preparando prompt para recomendaciones de {basic_info['ingredient_name']}")
            
            # Formatear los datos para el prompt
            history_count = len(history)
            recipes_count = len(recipes)
            suppliers_count = len(suppliers)
            
            prompt = f"""
            Basado en el análisis previo para {basic_info['ingredient_name']}:

            ANÁLISIS ACTUAL:
            {analysis}

            CONTEXTO ADICIONAL:
            - Stock actual: {basic_info['current_stock']} {basic_info['unit']}
            - Stock total: {basic_info['total_stock']} {basic_info['unit']}
            - Factor de seguridad: {basic_info['safe_factor']}%
            - Historial de movimientos: {history_count} registros
            - Recetas que usan este ingrediente: {recipes_count}
            - Proveedores disponibles: {suppliers_count}

            REQUERIDO:
            1. 2-3 recomendaciones estratégicas específicas
            2. Acciones concretas con tiempos estimados
            3. Sugerencias para optimizar costos y eficiencia
            4. Consideraciones sobre proveedores y almacenamiento

            Por favor, proporciona recomendaciones claras y accionables.
            """

            logger.info("Enviando prompt al agente asesor")
            logger.debug(f"Prompt enviado: {prompt}")
            
            response = self.agents["advisor"].run(prompt)
            logger.info("Respuesta recibida del agente asesor")
            
            if not response:
                logger.error("Respuesta del agente asesor es None")
                return "Error: No se pudieron generar recomendaciones"
            
            if not hasattr(response, 'content'):
                logger.error(f"Respuesta del agente asesor no tiene contenido. Tipo de respuesta: {type(response)}")
                if isinstance(response, str):
                    return response
                return "Error: Formato de respuesta inválido"
            
            logger.debug(f"Contenido de la respuesta: {response.content}")
            return response.content

        except Exception as e:
            logger.error(f"Error en recomendaciones: {str(e)}", exc_info=True)
            return f"Error en recomendaciones: {str(e)}"

