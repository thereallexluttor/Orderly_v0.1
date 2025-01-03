from textwrap import dedent
from phi.agent import Agent
from phi.model.ollama import Ollama
from typing import Dict, Any
import json
from datetime import datetime
import logging
from phi.model.deepseek import DeepSeekChat
from phi.model.google import Gemini
import os

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
        self.agents = {
            # Conservative Analysts
            "conservative_data": Agent(
                name="ConservativeDataAnalyst",
                role="Analista de datos conservador del sistema de control de inventario",
                model=Gemini(id="gemini-1.5-flash"),
                description=dedent("""
                    Como parte integral del sistema de control de inventario, analizo datos actuales 
                    e históricos con enfoque en la estabilidad y seguridad del inventario."""),
                instructions=[
                    "Analizar patrones históricos y actuales del uso del inventario",
                    "Comparar tendencias actuales con datos históricos para identificar patrones",
                    "Evaluar la consistencia del uso a lo largo del tiempo",
                    "Identificar desviaciones significativas del comportamiento histórico",
                    "Considerar el contexto histórico en las recomendaciones de stock",
                    "Formato de salida: Análisis estructurado comparando datos actuales e históricos"
                ]
            ),
            "conservative_predictor": Agent(
                name="ConservativePredictor",
                role="Predictor conservador del sistema de control de inventario",
                ##model=Ollama(id="llama3.2:3b"),
                ##model=DeepSeekChat(id="deepseek-chat"),
                model=Gemini(id="gemini-1.5-flash"),
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
                ]
            ),

            # Aggressive Analysts
            "aggressive_data": Agent(
                name="AggressiveDataAnalyst",
                role="Analista de datos agresivo del sistema de control de inventario",
                ##model=Ollama(id="llama3.2:3b"),
                ##model=DeepSeekChat(id="deepseek-chat"),
                model=Gemini(id="gemini-1.5-flash"),
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
                ]
            ),
            "aggressive_predictor": Agent(
                name="AggressivePredictor",
                role="Predictor agresivo del sistema de control de inventario",
                ##model=Ollama(id="llama3.2:3b"),
                ##model=DeepSeekChat(id="deepseek-chat"),
                model=Gemini(id="gemini-1.5-flash"),
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
            ),

            # Risk Mediator
            "risk_mediator": Agent(
                name="RiskMediator",
                role="Mediador de riesgos del sistema de control de inventario",
                ##model=Ollama(id="llama3.2:3b"),
                ##model=DeepSeekChat(id="deepseek-chat"),
                model=Gemini(id="gemini-1.5-flash"),
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
            ),
            
            # Synthesis Agent
            "synthesis": Agent(
                name="SynthesisAgent",
                role="Agente de síntesis del sistema de control de inventario",
                ##model=Ollama(id="llama3.2:3b"),
                ##model=DeepSeekChat(id="deepseek-chat"),
                model=Gemini(id="gemini-1.5-flash"),
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
        }

    def analyze_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Cargar datos históricos
            base_path = os.path.dirname(os.path.abspath(__file__))
            today = datetime.now().strftime('%Y-%m-%d')
            history_path = os.path.join(base_path, "inventory_data", today)
            
            historical_context = {}
            if os.path.exists(history_path):
                # Obtener el archivo más reciente
                files = [f for f in os.listdir(history_path) if f.endswith('.json')]
                if files:
                    latest_file = max(files)  # Obtiene el archivo más reciente
                    with open(os.path.join(history_path, latest_file), 'r', encoding='utf-8') as f:
                        historical_context = json.load(f)
            
            # Enriquecer datos de entrada con métricas calculadas y contexto histórico
            enriched_data = self._enrich_inventory_data(inventory_data)
            enriched_data['historical_context'] = historical_context
            
            # Realizar análisis paralelos con contexto histórico
            analyses = self._perform_parallel_analysis(enriched_data)
            
            # Realizar mediación y síntesis
            risk_mediation = self._perform_risk_mediation(analyses)
            final_synthesis = self._perform_synthesis(analyses, risk_mediation)

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
        enriched = {
            **data,
            "analysis_timestamp": datetime.now().isoformat(),
            
            "metrics": {
                "stock_value": data.get("current_stock", 0),
                "total_usage": data.get("stats", {}).get("total_usage", 0),
                "avg_daily_usage": data.get("stats", {}).get("avg_daily_usage", 0), 
                "max_daily_usage": data.get("stats", {}).get("max_daily_usage", 0),
                "total_days": data.get("stats", {}).get("total_days", 0),
                "predicted_usage_3days": data.get("stats", {}).get("predicted_usage_3days", 0),
                "predicted_avg_daily": data.get("stats", {}).get("predicted_avg_daily", 0),
                "predicted_daily_usage": data.get("stats", {}).get("restock_status", {}).get("predicted_daily_usage", 0),
                "recent_daily_average": data.get("stats", {}).get("restock_status", {}).get("recent_daily_average", 0),
                "days_remaining": data.get("stats", {}).get("restock_status", {}).get("days_remaining", 0),
                # Add more calculated metrics as needed
            }
                # Add more calculated metrics as needed
            
        }

        # Incluir datos de las gráficas si están disponibles
        if "daily_usage_chart" in data:
            enriched["daily_usage_chart"] = data["daily_usage_chart"]
        if "weekly_usage_chart" in data:
            enriched["weekly_usage_chart"] = data["weekly_usage_chart"]
        if "prediction_chart" in data:
            enriched["prediction_chart"] = data["prediction_chart"]

        return enriched

    def _perform_parallel_analysis(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Realiza análisis paralelos con diferentes perspectivas"""
        def get_agent_response(agent, prompt):
            response = agent.run(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            return format_analysis_text(response_text)

        # Extract all available data for analysis
        daily_usage = data.get('daily_usage', [])
        weekly_usage = data.get('weekly_usage', [])
        forecast_data = data.get('forecast', [])
        current_stock = data.get('current_stock', 0)
        metrics = data.get('metrics', {})
        analysis_timestamp = data.get('analysis_timestamp')
        
        # Get the detailed usage data from the graphs
        daily_usage_chart = data.get('daily_usage_chart', {})
        weekly_usage_chart = data.get('weekly_usage_chart', {})
        prediction_chart = data.get('prediction_chart', {})
        
        # Format data for agents
        data_context = {
            "stock_info": {
                "current_stock": current_stock,
                "analysis_timestamp": analysis_timestamp,
                "metrics": metrics
            },
            "usage_patterns": {
                "daily": daily_usage,
                "weekly": weekly_usage,
                "forecast": forecast_data
            },
            "detailed_analysis": {
                "daily_chart": daily_usage_chart,
                "weekly_chart": weekly_usage_chart,
                "predictions": prediction_chart
            }
        }
        
        return {
            "conservative": {
                "data": get_agent_response(
                    self.agents["conservative_data"],
                    f"""IMPORTANTE: Debes realizar el análisis incluso si los datos están incompletos o son de baja calidad. 
                    Si faltan datos, usa aproximaciones y asunciones razonables, indicando claramente cuáles usaste.

                    Analiza estos datos de inventario:
                    {json.dumps(data_context, indent=2)}

                    REQUERIDO - Debes calcular y proporcionar:
                    1. Análisis estadístico del uso (media, mediana, desviación) - usa aproximaciones si es necesario
                    2. Tendencias y patrones - incluso con datos limitados
                    3. Valores atípicos e impacto - asume valores típicos si faltan datos
                    4. Correlaciones entre variables disponibles
                    5. Intervalos de confianza - ajusta según la calidad de datos

                    Si los datos son insuficientes para algún cálculo, DEBES:
                    - Usar promedios del sector o estimaciones razonables
                    - Documentar claramente las asunciones usadas
                    - Ajustar los intervalos de confianza según la incertidumbre

                    Enfócate solo en análisis numérico y estadístico."""
                ),
                "prediction": get_agent_response(
                    self.agents["conservative_predictor"],
                    f"""IMPORTANTE: Debes generar predicciones incluso con datos limitados o de baja calidad.
                    Usa aproximaciones y asunciones conservadoras cuando sea necesario.

                    Datos disponibles:
                    {json.dumps(data_context, indent=2)}

                    REQUERIDO - Debes calcular y proporcionar:
                    1. Proyecciones con intervalos de confianza amplios para compensar incertidumbre
                    2. Probabilidad de desabastecimiento - usa estimaciones conservadoras
                    3. Análisis de series temporales - aproxima con datos disponibles
                    4. Estimación de error en predicciones
                    5. Pruebas estadísticas posibles con los datos existentes

                    Si los datos son insuficientes, DEBES:
                    - Usar datos históricos similares o promedios del sector
                    - Aumentar márgenes de error y rangos de predicción
                    - Documentar todas las asunciones y aproximaciones
                    - Ajustar predicciones al peor escenario razonable

                    Proporciona solo análisis numérico y estadístico."""
                )
            },
            "aggressive": {
                "data": get_agent_response(
                    self.agents["aggressive_data"],
                    f"""IMPORTANTE: Debes realizar análisis de eficiencia incluso con datos limitados.
                    Usa benchmarks del sector y aproximaciones cuando sea necesario.

                    Datos disponibles:
                    {json.dumps(data_context, indent=2)}

                    REQUERIDO - Debes calcular y proporcionar:
                    1. Ratios de rotación - usa aproximaciones si faltan datos
                    2. Costos de almacenamiento - estima basado en promedios del sector
                    3. Puntos de reorden optimizados - usa datos disponibles o aproximaciones
                    4. Eficiencia de espacio - calcula con información limitada
                    5. Análisis de varianza - ajusta según datos disponibles

                    Si los datos son insuficientes, DEBES:
                    - Usar benchmarks de la industria
                    - Aplicar modelos simplificados pero funcionales
                    - Documentar claramente aproximaciones y asunciones
                    - Proponer optimizaciones basadas en datos parciales

                    Solo análisis basado en métricas y cálculos."""
                ),
                "prediction": get_agent_response(
                    self.agents["aggressive_predictor"],
                    f"""IMPORTANTE: Debes generar predicciones optimizadas incluso con datos limitados.
                    Usa modelos simplificados y aproximaciones cuando sea necesario.

                    Datos disponibles:
                    {json.dumps(data_context, indent=2)}

                    REQUERIDO - Debes calcular y proporcionar:
                    1. Modelos de optimización - simplifica según datos disponibles
                    2. Análisis de sensibilidad - usa rangos amplios si hay incertidumbre
                    3. Escenarios de demanda - aproxima con datos limitados
                    4. Métricas de eficiencia - usa benchmarks si es necesario
                    5. Análisis de riesgo - ajusta según calidad de datos

                    Si los datos son insuficientes, DEBES:
                    - Usar modelos simplificados pero efectivos
                    - Aproximar con datos del sector o históricos similares
                    - Documentar claramente metodología y asunciones
                    - Mantener enfoque en optimización incluso con datos parciales

                    Solo análisis basado en datos y cálculos."""
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

