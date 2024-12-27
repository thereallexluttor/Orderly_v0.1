from textwrap import dedent
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from typing import Dict, Any
import json

class InventoryAnalysisSystem:
    def __init__(self):
        # Inicializar los modelos LLM con diferentes contextos
        self.llm = Ollama(model="llama3.2:3b", max_tokens=1024)
        
        # 1. Agente Analista de Datos
        self.data_analyst = Assistant(
            name="DataAnalyst",
            role="Analista de datos de inventario",
            llm=self.llm,
            description=dedent("""
                Analista especializado en interpretar patrones de uso de inventario.
                Examina tendencias históricas, patrones estacionales y anomalías en el uso de productos.
            """),
            instructions=[
                "Analizar los datos históricos de uso del producto",
                "Identificar patrones de consumo y tendencias",
                "Calcular métricas clave como tasa de uso, variabilidad y estacionalidad",
                "Proporcionar un resumen conciso de los hallazgos más relevantes"
            ],
        )

        # 2. Agente Predictor
        self.predictor = Assistant(
            name="Predictor",
            role="Especialista en predicción de demanda",
            llm=self.llm,
            description=dedent("""
                Experto en predecir necesidades futuras de inventario basándose en datos históricos y tendencias actuales.
                Considera factores estacionales y eventos especiales.
            """),
            instructions=[
                "Analizar tendencias históricas y patrones de consumo",
                "Predecir la demanda futura del producto",
                "Considerar factores estacionales y eventos especiales",
                "Proporcionar estimaciones de demanda para diferentes horizontes temporales"
            ],
        )

        # 3. Agente de Riesgo
        self.risk_analyst = Assistant(
            name="RiskAnalyst",
            role="Analista de riesgos de inventario",
            llm=self.llm,
            description=dedent("""
                Especialista en identificar y evaluar riesgos relacionados con el inventario.
                Analiza riesgos de desabastecimiento, sobrestock y pérdidas.
            """),
            instructions=[
                "Evaluar riesgos de desabastecimiento",
                "Identificar posibles pérdidas por caducidad o deterioro",
                "Analizar impacto financiero de decisiones de inventario",
                "Proporcionar recomendaciones para mitigar riesgos"
            ],
        )

        # 4. Agente Estratega Principal
        self.chief_strategist = Assistant(
            name="ChiefStrategist",
            role="Estratega principal de inventario",
            llm=self.llm,
            description=dedent("""
                Estratega principal que evalúa múltiples perspectivas y propone estrategias óptimas.
                Considera factores económicos, operativos y estratégicos.
            """),
            instructions=[
                "Integrar análisis de otros agentes",
                "Evaluar pros y contras de diferentes estrategias",
                "Considerar factores económicos y operativos",
                "Proponer la estrategia óptima con justificación"
            ],
        )

        # 5. Agente de Decisión Final
        self.decision_maker = Assistant(
            name="DecisionMaker",
            role="Tomador de decisiones final",
            llm=self.llm,
            description=dedent("""
                Responsable de tomar la decisión final sobre acciones de inventario.
                Integra todas las perspectivas y proporciona recomendaciones accionables.
            """),
            instructions=[
                "Evaluar todas las recomendaciones y análisis",
                "Considerar restricciones y limitaciones prácticas",
                "Proporcionar decisión final clara y accionable",
                "Justificar la decisión con evidencia y razonamiento"
            ],
        )

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza los datos de inventario utilizando el sistema multi-agente.
        """
        try:
            # 1. Análisis de datos históricos
            data_analysis = self.data_analyst.run(
                f"Analizar los siguientes datos de inventario: {json.dumps(inventory_data)}",
                stream=False
            )

            # 2. Predicción de demanda
            prediction = self.predictor.run(
                f"Basado en estos datos y análisis: {data_analysis}\n"
                f"Predecir la demanda futura para: {json.dumps(inventory_data)}",
                stream=False
            )

            # 3. Análisis de riesgos
            risk_analysis = self.risk_analyst.run(
                f"Evaluar riesgos considerando:\n"
                f"Datos: {json.dumps(inventory_data)}\n"
                f"Análisis: {data_analysis}\n"
                f"Predicción: {prediction}",
                stream=False
            )

            # 4. Estrategia general
            strategy = self.chief_strategist.run(
                f"Desarrollar estrategia basada en:\n"
                f"Datos: {json.dumps(inventory_data)}\n"
                f"Análisis: {data_analysis}\n"
                f"Predicción: {prediction}\n"
                f"Riesgos: {risk_analysis}",
                stream=False
            )

            # 5. Decisión final
            final_decision = self.decision_maker.run(
                f"Tomar decisión final considerando:\n"
                f"Estrategia: {strategy}\n"
                f"Datos: {json.dumps(inventory_data)}\n"
                f"Análisis: {data_analysis}\n"
                f"Predicción: {prediction}\n"
                f"Riesgos: {risk_analysis}",
                stream=False
            )

            return {
                "data_analysis": data_analysis,
                "demand_prediction": prediction,
                "risk_analysis": risk_analysis,
                "strategy": strategy,
                "final_decision": final_decision
            }

        except Exception as e:
            return {
                "error": f"Error en el análisis: {str(e)}",
                "status": "error"
            }

def main():
    # Ejemplo de uso
    inventory_system = InventoryAnalysisSystem()
    
    # Ejemplo de datos de inventario (simular datos de la API de Flutter)
    sample_data = {
        "ingredient_id": 1,
        "ingredient_name": "Ejemplo Producto",
        "current_stock": 100,
        "min_stock": 20,
        "max_stock": 200,
        "usage_history": [
            {"date": "2024-03-01", "quantity": 10},
            {"date": "2024-03-02", "quantity": 15},
            # ... más datos históricos
        ],
        "unit_cost": 25.0,
        "supplier_lead_time": 3  # días
    }

    # Realizar análisis
    results = inventory_system.analyze_inventory(sample_data)
    
    # Imprimir resultados
    print("\n=== Análisis de Inventario ===")
    print("\n1. Análisis de Datos:")
    print(results["data_analysis"])
    print("\n2. Predicción de Demanda:")
    print(results["demand_prediction"])
    print("\n3. Análisis de Riesgos:")
    print(results["risk_analysis"])
    print("\n4. Estrategia Propuesta:")
    print(results["strategy"])
    print("\n5. Decisión Final:")
    print(results["final_decision"])

if __name__ == "__main__":
    main()