from textwrap import dedent
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from typing import Dict, Any
import json

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
        self.llm = Ollama(model="llama3.2:3b", max_tokens=512)
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the new balanced agent system"""
        self.agents = {
            # Conservative Analysts
            "conservative_data": Assistant(
                name="ConservativeDataAnalyst",
                role="Analista de datos conservador",
                llm=self.llm,
                description="Analiza datos con enfoque en la estabilidad y minimización de riesgos.",
                instructions=[
                    "Priorizar la estabilidad del inventario sobre la eficiencia.",
                    "Enfocarse en patrones históricos probados.",
                    "Identificar riesgos de desabastecimiento.",
                    "Sugerir niveles de stock seguros."
                ],
            ),
            "conservative_predictor": Assistant(
                name="ConservativePredictor",
                role="Predictor conservador",
                llm=self.llm,
                description="Realiza predicciones cautelosas priorizando la seguridad del inventario.",
                instructions=[
                    "Generar predicciones conservadoras de demanda.",
                    "Mantener márgenes de seguridad amplios.",
                    "Considerar escenarios pesimistas.",
                    "Recomendar puntos de reorden seguros."
                ],
            ),

            # Aggressive Analysts
            "aggressive_data": Assistant(
                name="AggressiveDataAnalyst",
                role="Analista de datos agresivo",
                llm=self.llm,
                description="Analiza datos buscando optimización y eficiencia máxima.",
                instructions=[
                    "Priorizar la eficiencia y reducción de costos.",
                    "Identificar oportunidades de optimización.",
                    "Buscar patrones para reducir stock.",
                    "Maximizar rotación de inventario."
                ],
            ),
            "aggressive_predictor": Assistant(
                name="AggressivePredictor",
                role="Predictor agresivo",
                llm=self.llm,
                description="Realiza predicciones optimistas buscando eficiencia.",
                instructions=[
                    "Generar predicciones optimizadas.",
                    "Minimizar stock de seguridad.",
                    "Considerar escenarios optimistas.",
                    "Buscar puntos de reorden eficientes."
                ],
            ),

            # Balancing Agents
            "risk_mediator": Assistant(
                name="RiskMediator",
                role="Mediador de riesgos",
                llm=self.llm,
                description="Equilibra las perspectivas conservadoras y agresivas.",
                instructions=[
                    "Contrastar análisis conservadores y agresivos.",
                    "Proponer soluciones balanceadas.",
                    "Evaluar trade-offs entre seguridad y eficiencia.",
                    "Mediar entre diferentes perspectivas."
                ],
            ),
            
            # Synthesis Agent
            "synthesis": Assistant(
                name="SynthesisAgent",
                role="Agente de síntesis",
                llm=self.llm,
                description="Sintetiza todos los análisis en una perspectiva coherente.",
                instructions=[
                    "Integrar análisis de todos los agentes.",
                    "Identificar puntos de consenso y divergencia.",
                    "Proporcionar recomendaciones balanceadas.",
                    "Presentar una visión unificada y práctica."
                ],
            )
        }

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            # Realizar análisis paralelos con diferentes perspectivas
            analyses = {
                "conservative": {
                    "data": format_analysis_text(self.agents["conservative_data"].run(
                        f"""Analiza estos datos desde una perspectiva conservadora:
                        ID: {inventory_data['ingredient_id']}
                        Stock Actual: {inventory_data['current_stock']}
                        
                        Proporciona un análisis detallado priorizando la seguridad del inventario.""",
                        stream=False
                    )),
                    "prediction": format_analysis_text(self.agents["conservative_predictor"].run(
                        f"""Realiza predicciones conservadoras para:
                        ID: {inventory_data['ingredient_id']}
                        Stock Actual: {inventory_data['current_stock']}
                        
                        Enfócate en mantener niveles seguros de inventario.""",
                        stream=False
                    ))
                },
                "aggressive": {
                    "data": format_analysis_text(self.agents["aggressive_data"].run(
                        f"""Analiza estos datos buscando eficiencia máxima:
                        ID: {inventory_data['ingredient_id']}
                        Stock Actual: {inventory_data['current_stock']}
                        
                        Identifica oportunidades de optimización.""",
                        stream=False
                    )),
                    "prediction": format_analysis_text(self.agents["aggressive_predictor"].run(
                        f"""Realiza predicciones optimizadas para:
                        ID: {inventory_data['ingredient_id']}
                        Stock Actual: {inventory_data['current_stock']}
                        
                        Busca maximizar la eficiencia del inventario.""",
                        stream=False
                    ))
                }
            }

            # Mediación de riesgos
            risk_mediation = format_analysis_text(self.agents["risk_mediator"].run(
                f"""Analiza y equilibra las siguientes perspectivas:

                Análisis Conservador:
                Datos: {analyses['conservative']['data']}
                Predicciones: {analyses['conservative']['prediction']}

                Análisis Agresivo:
                Datos: {analyses['aggressive']['data']}
                Predicciones: {analyses['aggressive']['prediction']}

                Proporciona una evaluación balanceada de riesgos y oportunidades.""",
                stream=False
            ))

            # Síntesis final
            final_synthesis = format_analysis_text(self.agents["synthesis"].run(
                f"""Sintetiza todos los análisis:

                Perspectiva Conservadora:
                {analyses['conservative']['data']}
                {analyses['conservative']['prediction']}

                Perspectiva Agresiva:
                {analyses['aggressive']['data']}
                {analyses['aggressive']['prediction']}

                Mediación de Riesgos:
                {risk_mediation}

                Proporciona:
                1. Síntesis global
                2. Recomendaciones prácticas
                3. Puntos clave de consenso""",
                stream=False
            ))

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
            return {
                "error": f"Error en el análisis: {str(e)}",
                "status": "error"
            }

