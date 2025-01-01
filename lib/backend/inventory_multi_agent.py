from textwrap import dedent
from phi.agent import Agent
from phi.model.ollama import Ollama
from typing import Dict, Any
import json
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_analysis_text(text: str) -> str:
    """
    Formatea el texto del análisis para una mejor presentación:
    - Convierte **texto** en texto en negrita
    - Maneja saltos de línea
    - Limpia caracteres especiales innecesarios
    - Formatea listas y enumeraciones
    """
    # Reemplazar patrones comunes
    formatted = text.strip()
    
    # Convertir **texto** en HTML bold
    formatted = formatted.replace('**', '<strong>', 1)
    while '**' in formatted:
        formatted = formatted.replace('**', '</strong>', 1)
        if '**' in formatted:
            formatted = formatted.replace('**', '<strong>', 1)
    
    # Manejar saltos de línea y secciones
    formatted = formatted.replace('\n\n', '<br><br>')
    formatted = formatted.replace('| ', '<br>')
    
    # Formatear listas numeradas y viñetas
    lines = formatted.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        # Detectar listas numeradas (1., 2., etc.)
        if line.strip().startswith(tuple(f"{i}." for i in range(1, 10))):
            if not in_list:
                formatted_lines.append('<ol>')
                in_list = True
            formatted_lines.append(f'<li>{line.split(".", 1)[1].strip()}</li>')
        # Detectar viñetas
        elif line.strip().startswith('- '):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(f'<li>{line[2:].strip()}</li>')
        else:
            if in_list:
                formatted_lines.append('</ol>' if formatted_lines[-2].startswith('<li>') else '</ul>')
                in_list = False
            formatted_lines.append(line)
    
    if in_list:
        formatted_lines.append('</ol>' if formatted_lines[-1].startswith('<li>') else '</ul>')
    
    formatted = '\n'.join(formatted_lines)
    
    # Limpiar caracteres especiales innecesarios
    formatted = formatted.replace('~~', '')
    formatted = formatted.replace('```', '')
    
    return formatted

class InventoryAnalysisSystem:
    def __init__(self):
        self.llm = Ollama(
            model="llama3.2:3b",
            max_tokens=1024
        )
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the balanced agent system with improved prompts"""

        # Conservative Analysts
        conservative_data = Agent(
                name="ConservativeDataAnalyst",
                role="Analista de datos conservador del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                description=dedent("""
                    Como parte integral del sistema de control de inventario, analizo datos con enfoque 
                    en la estabilidad y seguridad del inventario. Mi objetivo es asegurar la transparencia 
                    y confiabilidad en el manejo de existencias."""),
                instructions=[
                    "Analizar patrones históricos de uso del inventario para garantizar la continuidad operativa",
                    "Identificar tendencias de consumo y estacionalidad que afecten la seguridad del stock",
                    "Evaluar riesgos de desabastecimiento y sobrestock considerando el impacto en el negocio",
                    "Considerar factores externos que puedan afectar la estabilidad del inventario",
                    "Proponer niveles de stock de seguridad basados en datos históricos y políticas de la empresa",
                    "Asegurar que las recomendaciones apoyen la transparencia y trazabilidad del inventario",
                    "Formato de salida: Análisis estructurado con secciones claras y recomendaciones específicas"
                ],
                additional_information={
                    "analysis_type": "conservative",
                    "data_focus": "historical_patterns"
                }
            )

        # Inicializar el predictor conservador después de crear el analista de datos
        conservative_predictor = Agent(
                name="ConservativePredictor",
                role="Predictor conservador del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                team=[conservative_data],
                description=dedent("""
                    Como componente del sistema de control de inventario, genero predicciones cautelosas 
                    que priorizan la seguridad y continuidad del suministro. Mi enfoque busca mantener 
                    niveles óptimos de stock que minimicen riesgos operativos."""),
                instructions=[
                    "Analizar tendencias históricas de uso para garantizar la disponibilidad de productos",
                    "Considerar factores estacionales y cíclicos que impacten la demanda",
                    "Incluir márgenes de seguridad en las predicciones alineados con las políticas de inventario",
                    "Evaluar escenarios pesimistas y su impacto en la continuidad operativa",
                    "Recomendar puntos de reorden que aseguren la flexibilidad del sistema",
                    "Asegurar que las predicciones apoyen la adaptabilidad del inventario",
                    "Formato de salida: Predicciones numéricas con intervalos de confianza y justificación"
                ],
                additional_information={
                    "data_source": "conservative_data",
                    "prediction_type": "inventory_levels"
                }
            )

            # Aggressive Analysts
        aggressive_data = Agent(
                name="AggressiveDataAnalyst",
                role="Analista de datos agresivo del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                description=dedent("""
                    Como parte del sistema de control de inventario, optimizo la eficiencia y reducción 
                    de costos mientras mantengo la transparencia y adaptabilidad del sistema. Mi enfoque 
                    busca maximizar el rendimiento del inventario."""),
                instructions=[
                    "Identificar oportunidades de optimización del stock manteniendo la seguridad del sistema",
                    "Analizar patrones de rotación para mejorar la eficiencia del inventario",
                    "Evaluar costos de almacenamiento y oportunidad dentro del marco de control",
                    "Proponer estrategias de reducción de stock que mantengan la flexibilidad operativa",
                    "Identificar ineficiencias en la gestión actual y proponer mejoras sistemáticas",
                    "Asegurar que las optimizaciones apoyen la transparencia del sistema",
                    "Formato de salida: Análisis cuantitativo con métricas de eficiencia y recomendaciones"
                ],
                additional_information={
                    "analysis_type": "aggressive",
                    "optimization_focus": "efficiency_and_cost"
                }
            )
        aggressive_predictor = Agent(
                name="AggressivePredictor",
                role="Predictor agresivo del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                description=dedent("""
                    Como elemento del sistema de control de inventario, genero predicciones optimizadas 
                    que buscan máxima eficiencia mientras mantengo la integridad y adaptabilidad del 
                    sistema de control."""),
                instructions=[
                    "Proyectar tendencias de demanda optimistas dentro del marco de control establecido",
                    "Calcular puntos de reorden eficientes que mantengan la seguridad del sistema",
                    "Optimizar stock de seguridad considerando la flexibilidad necesaria",
                    "Proponer estrategias de just-in-time alineadas con las políticas de control",
                    "Identificar oportunidades de mejora en la cadena de suministro",
                    "Asegurar que las predicciones apoyen la transparencia del sistema",
                    "Formato de salida: Predicciones detalladas con análisis de sensibilidad"
                ]
            )

            # Risk Mediator
        risk_mediator = Agent(
                name="RiskMediator",
                role="Mediador de riesgos del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                description=dedent("""
                    Como coordinador dentro del sistema de control de inventario, equilibro la seguridad 
                    y eficiencia, asegurando que las decisiones apoyen la transparencia y adaptabilidad 
                    del sistema."""),
                instructions=[
                    "Evaluar trade-offs entre seguridad y eficiencia dentro del marco de control",
                    "Analizar riesgos y beneficios de cada enfoque considerando las políticas establecidas",
                    "Proponer soluciones balanceadas que mantengan la integridad del sistema",
                    "Considerar factores externos y contingencias que afecten el control de inventario",
                    "Recomendar estrategias de mitigación alineadas con los objetivos del sistema",
                    "Asegurar que las mediaciones apoyen la transparencia y flexibilidad",
                    "Formato de salida: Análisis comparativo con recomendaciones equilibradas"
                ]
            )
            
            # Synthesis Agent
        synthesis = Agent(
                name="SynthesisAgent",
                role="Agente de síntesis del sistema de control de inventario",
                model=Ollama(id="llama3.2:3b"),
                description=dedent("""
                    Como integrador final del sistema de control de inventario, sintetizo todos los 
                    análisis en recomendaciones accionables que aseguren la transparencia, seguridad 
                    y flexibilidad del sistema."""),
                instructions=[
                    "Sintetizar análisis conservadores y agresivos manteniendo la integridad del sistema",
                    "Identificar puntos de consenso y divergencia en el contexto del control de inventario",
                    "Proponer estrategias prácticas que apoyen los objetivos del sistema",
                    "Priorizar recomendaciones por impacto y viabilidad dentro del marco de control",
                    "Considerar restricciones y recursos disponibles del sistema",
                    "Asegurar que la síntesis promueva la transparencia y adaptabilidad",
                    "Formato de salida: Síntesis estructurada con plan de acción claro"
                ]
            )
        self.agents = {
            "conservative_data": conservative_data,
            "conservative_predictor": conservative_predictor,
            "aggressive_data": aggressive_data,
            "aggressive_predictor": aggressive_predictor,
            "risk_mediator": risk_mediator,
            "synthesis": synthesis
        }

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Enriquecer datos de entrada con métricas calculadas
            enriched_data = self._enrich_inventory_data(inventory_data)
            
            # Realizar análisis paralelos
            analyses = self._perform_parallel_analysis(enriched_data)
            
            # Realizar mediación y síntesis
            risk_mediation = self._perform_risk_mediation(analyses)
            final_synthesis = self._perform_synthesis(analyses, risk_mediation)

            # Estructura corregida para coincidir con el formato esperado
            return {
                "analyses": {
                    "conservative_analysis": {
                        "data": analyses["conservative"]["data"],
                        "prediction": analyses["conservative"]["prediction"]
                    },
                    "aggressive_analysis": {
                        "data": analyses["aggressive"]["data"],
                        "prediction": analyses["aggressive"]["prediction"]
                    },
                    "risk_mediation": risk_mediation,
                    "final_synthesis": final_synthesis
                }
            }

        except Exception as e:
            logger.error(f"Error en el análisis del inventario: {str(e)}", exc_info=True)
            return {
                "analyses": {
                    "conservative_analysis": {
                        "data": "Error en el análisis conservador",
                        "prediction": "No disponible"
                    },
                    "aggressive_analysis": {
                        "data": "Error en el análisis agresivo",
                        "prediction": "No disponible"
                    },
                    "risk_mediation": "Error en la mediación de riesgos",
                    "final_synthesis": f"Error en el análisis: {str(e)}"
                }
            }

    def _enrich_inventory_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece los datos de inventario con métricas adicionales"""
        return {
            **data,
            "analysis_timestamp": datetime.now().isoformat(),
            "metrics": {
                "stock_value": data.get("current_stock", 0),
                # Add more calculated metrics as needed
            }
        }

    def _perform_parallel_analysis(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Realiza análisis paralelos con diferentes perspectivas"""
        def get_agent_response(agent, prompt):
            """Helper function to get response from agent"""
            response = agent.run(prompt)
            # Extraer el contenido del RunResponse
            response_text = response.content if hasattr(response, 'content') else str(response)
            return format_analysis_text(response_text)

        return {
            "conservative": {
                "data": get_agent_response(
                    self.agents["conservative_data"],
                    f"""Analiza estos datos desde una perspectiva conservadora:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Proporciona un análisis detallado priorizando la seguridad del inventario."""
                ),
                "prediction": get_agent_response(
                    self.agents["conservative_predictor"],
                    f"""Realiza predicciones conservadoras para:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Enfócate en mantener niveles seguros de inventario."""
                )
            },
            "aggressive": {
                "data": get_agent_response(
                    self.agents["aggressive_data"],
                    f"""Analiza estos datos buscando eficiencia máxima:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Identifica oportunidades de optimización."""
                ),
                "prediction": get_agent_response(
                    self.agents["aggressive_predictor"],
                    f"""Realiza predicciones optimizadas para:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Busca maximizar la eficiencia del inventario."""
                )
            }
        }

    def _perform_risk_mediation(self, analyses: Dict[str, Dict[str, str]]) -> str:
        """Realiza la mediación de riesgos entre análisis"""
        response = self.agents["risk_mediator"].run(
            f"""Analiza y equilibra las siguientes perspectivas:

            Análisis Conservador:
            {analyses['conservative']['data']}
            {analyses['conservative']['prediction']}

            Análisis Agresivo:
            {analyses['aggressive']['data']}
            {analyses['aggressive']['prediction']}

            Proporciona una evaluación balanceada de riesgos y oportunidades."""
        )
        # Extraer el contenido del RunResponse
        response_text = response.content if hasattr(response, 'content') else str(response)
        return format_analysis_text(response_text)

    def _perform_synthesis(self, analyses: Dict[str, Dict[str, str]], risk_mediation: str) -> str:
        """Realiza la síntesis final de todos los análisis"""
        response = self.agents["synthesis"].run(
            f"""Sintetiza todos los análisis:

            Análisis Conservador:
            {analyses['conservative']['data']}
            {analyses['conservative']['prediction']}

            Análisis Agresivo:
            {analyses['aggressive']['data']}
            {analyses['aggressive']['prediction']}

            Mediación de Riesgos:
            {risk_mediation}

            Proporciona:
            1. Síntesis global
            2. Recomendaciones prácticas y accionables
            3. Plan de implementación priorizado
            4. Métricas clave a monitorear"""
        )
        # Extraer el contenido del RunResponse
        response_text = response.content if hasattr(response, 'content') else str(response)
        return format_analysis_text(response_text)

