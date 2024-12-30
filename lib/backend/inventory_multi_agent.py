from textwrap import dedent
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
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
        self.llm = Ollama(model="llama3.2:3b", max_tokens=1024)
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the balanced agent system with improved prompts"""
        self.agents = {
            # Conservative Analysts
            "conservative_data": Assistant(
                name="ConservativeDataAnalyst",
                role="Analista de datos conservador",
                llm=self.llm,
                description="Analiza datos con enfoque en la estabilidad y seguridad del inventario.",
                instructions=[
                    "Analizar patrones históricos de uso del inventario",
                    "Identificar tendencias de consumo y estacionalidad",
                    "Evaluar riesgos de desabastecimiento y sobrestock",
                    "Considerar factores externos que puedan afectar el inventario",
                    "Proponer niveles de stock de seguridad basados en datos históricos",
                    "Formato de salida: Análisis estructurado con secciones claras y recomendaciones específicas"
                ],
            ),
            "conservative_predictor": Assistant(
                name="ConservativePredictor",
                role="Predictor conservador",
                llm=self.llm,
                description="Genera predicciones cautelosas basadas en datos históricos.",
                instructions=[
                    "Analizar tendencias históricas de uso",
                    "Considerar factores estacionales y cíclicos",
                    "Incluir márgenes de seguridad en las predicciones",
                    "Evaluar escenarios pesimistas y su impacto",
                    "Recomendar puntos de reorden conservadores",
                    "Formato de salida: Predicciones numéricas con intervalos de confianza y justificación"
                ],
            ),

            # Aggressive Analysts
            "aggressive_data": Assistant(
                name="AggressiveDataAnalyst",
                role="Analista de datos agresivo",
                llm=self.llm,
                description="Optimiza el inventario para máxima eficiencia y reducción de costos.",
                instructions=[
                    "Identificar oportunidades de optimización del stock",
                    "Analizar patrones de rotación de inventario",
                    "Evaluar costos de almacenamiento y oportunidad",
                    "Proponer estrategias de reducción de stock",
                    "Identificar ineficiencias en la gestión actual",
                    "Formato de salida: Análisis cuantitativo con métricas de eficiencia y recomendaciones"
                ],
            ),
            "aggressive_predictor": Assistant(
                name="AggressivePredictor",
                role="Predictor agresivo",
                llm=self.llm,
                description="Genera predicciones optimizadas para máxima eficiencia.",
                instructions=[
                    "Proyectar tendencias de demanda optimistas",
                    "Calcular puntos de reorden eficientes",
                    "Minimizar stock de seguridad",
                    "Proponer estrategias de just-in-time",
                    "Identificar oportunidades de mejora en la cadena de suministro",
                    "Formato de salida: Predicciones detalladas con análisis de sensibilidad"
                ],
            ),

            # Risk Mediator
            "risk_mediator": Assistant(
                name="RiskMediator",
                role="Mediador de riesgos",
                llm=self.llm,
                description="Equilibra seguridad y eficiencia en la gestión de inventario.",
                instructions=[
                    "Evaluar trade-offs entre seguridad y eficiencia",
                    "Analizar riesgos y beneficios de cada enfoque",
                    "Proponer soluciones balanceadas",
                    "Considerar factores externos y contingencias",
                    "Recomendar estrategias de mitigación de riesgos",
                    "Formato de salida: Análisis comparativo con recomendaciones equilibradas"
                ],
            ),
            
            # Synthesis Agent
            "synthesis": Assistant(
                name="SynthesisAgent",
                role="Agente de síntesis",
                llm=self.llm,
                description="Integra todos los análisis en recomendaciones accionables.",
                instructions=[
                    "Sintetizar análisis conservadores y agresivos",
                    "Identificar puntos de consenso y divergencia",
                    "Proponer estrategias prácticas y balanceadas",
                    "Priorizar recomendaciones por impacto y viabilidad",
                    "Considerar restricciones y recursos disponibles",
                    "Formato de salida: Síntesis estructurada con plan de acción claro"
                ],
            )
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
            """Helper function to get response from agent and convert to string"""
            response = agent.run(prompt, stream=False)  # Aseguramos que stream=False
            # Si es un generador, convertimos a string
            if hasattr(response, '__iter__') and not isinstance(response, str):
                return ''.join(list(response))
            return response

        return {
            "conservative": {
                "data": format_analysis_text(get_agent_response(
                    self.agents["conservative_data"],
                    f"""Analiza estos datos desde una perspectiva conservadora:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Proporciona un análisis detallado priorizando la seguridad del inventario."""
                )),
                "prediction": format_analysis_text(get_agent_response(
                    self.agents["conservative_predictor"],
                    f"""Realiza predicciones conservadoras para:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Enfócate en mantener niveles seguros de inventario."""
                ))
            },
            "aggressive": {
                "data": format_analysis_text(get_agent_response(
                    self.agents["aggressive_data"],
                    f"""Analiza estos datos buscando eficiencia máxima:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Identifica oportunidades de optimización."""
                )),
                "prediction": format_analysis_text(get_agent_response(
                    self.agents["aggressive_predictor"],
                    f"""Realiza predicciones optimizadas para:
                    ID: {data['ingredient_id']}
                    Stock Actual: {data['current_stock']}
                    Métricas: {json.dumps(data['metrics'], indent=2)}
                    
                    Busca maximizar la eficiencia del inventario."""
                ))
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

            Proporciona una evaluación balanceada de riesgos y oportunidades.""",
            stream=False
        )
        if hasattr(response, '__iter__') and not isinstance(response, str):
            response = ''.join(list(response))
        return format_analysis_text(response)

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
            4. Métricas clave a monitorear""",
            stream=False
        )
        if hasattr(response, '__iter__') and not isinstance(response, str):
            response = ''.join(list(response))
        return format_analysis_text(response)

