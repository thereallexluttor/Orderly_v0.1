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
        # Initialize LLM once
        self.llm = Ollama(model="llama3.2:3b", max_tokens=512)
        
        # Create agents once and reuse them
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize agents once during system startup"""
        self.agents = {
            "data_analyst": Assistant(
                name="DataAnalyst",
                role="Analista de datos de inventario",
                llm=self.llm,
                description="Analiza patrones de uso de inventario y tendencias.",
                instructions=[
                    "Analizar datos y proporcionar hallazgos clave.",
                    "Identificar patrones de consumo y anomalías.",
                    "Proporcionar insights sobre la eficiencia del inventario."
                ],
            ),
            "predictor": Assistant(
                name="Predictor",
                role="Especialista en predicción",
                llm=self.llm,
                description="Predice necesidades futuras de inventario.",
                instructions=[
                    "Proporcionar predicción concisa de demanda futura.",
                    "Identificar tendencias estacionales si existen.",
                    "Estimar puntos de reorden óptimos."
                ],
            ),
            "risk_analyst": Assistant(
                name="RiskAnalyst",
                role="Analista de riesgos",
                llm=self.llm,
                description="Evalúa riesgos de inventario.",
                instructions=[
                    "Identificar principales riesgos.",
                    "Evaluar impacto potencial en operaciones.",
                    "Sugerir medidas de mitigación."
                ],
            ),
            "cognitive_analyst": Assistant(
                name="CognitiveAnalyst",
                role="Analista cognitivo",
                llm=self.llm,
                description="Razona y contrasta los análisis de los otros agentes.",
                instructions=[
                    "Analizar la coherencia entre los diferentes análisis.",
                    "Identificar posibles contradicciones o puntos de acuerdo.",
                    "Proporcionar una perspectiva integrada basada en el razonamiento crítico.",
                    "Sugerir áreas que requieren más investigación o atención."
                ],
            )
        }

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            # Ejecutar análisis en paralelo con prompts más específicos
            analyses = {
                "data": format_analysis_text(self.agents["data_analyst"].run(
                    f"""Analiza estos datos de inventario:
                    ID: {inventory_data['ingredient_id']}
                    Stock Actual: {inventory_data['current_stock']}
                    
                    Proporciona un análisis detallado de los patrones históricos,
                    incluyendo tendencias de consumo y eficiencia del inventario.""",
                    stream=False
                )),
                "prediction": format_analysis_text(self.agents["predictor"].run(
                    f"""Analiza estos datos de inventario:
                    ID: {inventory_data['ingredient_id']}
                    Stock Actual: {inventory_data['current_stock']}
                    
                    Predice la demanda futura, tendencias estacionales y 
                    determina puntos óptimos de reorden.""",
                    stream=False
                )),
                "risk": format_analysis_text(self.agents["risk_analyst"].run(
                    f"""Analiza estos datos de inventario:
                    ID: {inventory_data['ingredient_id']}
                    Stock Actual: {inventory_data['current_stock']}
                    
                    Identifica riesgos potenciales, evalúa su impacto y
                    sugiere medidas de mitigación.""",
                    stream=False
                ))
            }

            # Análisis cognitivo basado en los resultados de los otros agentes
            cognitive_analysis = format_analysis_text(self.agents["cognitive_analyst"].run(
                f"""Analiza y contrasta los siguientes análisis de inventario:

                Análisis de Datos: {analyses['data']}
                Predicciones: {analyses['prediction']}
                Análisis de Riesgos: {analyses['risk']}

                Proporciona:
                1. Evaluación de coherencia entre análisis
                2. Identificación de contradicciones o confirmaciones
                3. Perspectiva integrada y razonada
                4. Áreas que requieren más atención""",
                stream=False
            ))

            return {
                "analyses": {
                    "data_analysis": analyses["data"],
                    "prediction_analysis": analyses["prediction"],
                    "risk_analysis": analyses["risk"],
                    "cognitive_analysis": cognitive_analysis
                }
            }

        except Exception as e:
            return {
                "error": f"Error en el análisis: {str(e)}",
                "status": "error"
            }

