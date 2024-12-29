from textwrap import dedent
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from typing import Dict, Any
import json

class InventoryAnalysisSystem:
    def __init__(self):
        self.llm = Ollama(model="llama3.2:3b", max_tokens=512)  # Reduced max tokens
        
        # Simplified agents with more focused instructions
        self.agents = {
            "data_analyst": Assistant(
                name="DataAnalyst",
                role="Analista de datos de inventario",
                llm=self.llm,
                description="Analiza patrones de uso de inventario y tendencias.",
                instructions=["Analizar datos históricos y proporcionar hallazgos clave."],
            ),
            "predictor": Assistant(
                name="Predictor",
                role="Especialista en predicción",
                llm=self.llm,
                description="Predice necesidades futuras de inventario.",
                instructions=["Proporcionar predicción concisa de demanda futura."],
            ),
            "risk_analyst": Assistant(
                name="RiskAnalyst",
                role="Analista de riesgos",
                llm=self.llm,
                description="Evalúa riesgos de inventario.",
                instructions=["Identificar principales riesgos."],
            ),
            "summarizer": Assistant(
                name="Summarizer",
                role="Sintetizador de información",
                llm=self.llm,
                description="Sintetiza todos los análisis en una recomendación final clara.",
                instructions=[
                    "Analizar las conclusiones de los otros agentes",
                    "Proporcionar UNA recomendación clara y accionable.",
                    "Incluir: Qué hacer, Por qué hacerlo, Cuándo hacerlo"
                ],
            )
        }

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            # Ejecutar análisis en paralelo (si es posible en tu entorno)
            analyses = {
                "data": self.agents["data_analyst"].run(
                    f"Analiza brevemente: {json.dumps(inventory_data)}",
                    stream=False
                ),
                "prediction": self.agents["predictor"].run(
                    f"Predice uso futuro: {json.dumps(inventory_data)}",
                    stream=False
                ),
                "risk": self.agents["risk_analyst"].run(
                    f"Evalúa riesgos: {json.dumps(inventory_data)}",
                    stream=False
                )
            }

            # Generar resumen final
            summary = self.agents["summarizer"].run(
                f"""Basado en estos análisis:
                Datos: {analyses['data']}
                Predicción: {analyses['prediction']}
                Riesgos: {analyses['risk']}
                
                Proporciona UNA recomendación clara y accionable.""",
                stream=False
            )

            return {
                "recommendation": summary
            }

        except Exception as e:
            return {
                "error": f"Error en el análisis: {str(e)}",
                "status": "error"
            }

