from phi.workflow import Workflow
from phi.agent import Agent
from phi.model.google import Gemini
from typing import Dict, Any, Optional
from pydantic import Field
import logging
import os
from dotenv import load_dotenv
import numpy as np
from scipy import stats
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY no está configurada en las variables de entorno")

def convert_numpy_types(obj):
    """Convierte tipos de NumPy a tipos nativos de Python"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

class InventoryAnalysisSystem(Workflow):
    analyst: Optional[Agent] = Field(default=None)
    advisor: Optional[Agent] = Field(default=None)

    def __init__(self):
        super().__init__()
        logger.info("Inicializando sistema de análisis técnico de inventario...")
        gemini_model = Gemini(api_key=GOOGLE_API_KEY)
        self._initialize_agents(gemini_model)

    def _initialize_agents(self, model):
        """Inicializa los agentes de análisis"""
        try:
            self.analyst = Agent(
                name="TechnicalAnalyst",
                role="Analista técnico especializado en series temporales e inventario",
                model=model,
                description="Realizo análisis estadísticos avanzados de patrones de inventario y consumo",
                instructions=[
                    "Realizar análisis estadístico detallado de patrones de uso",
                    "Calcular métricas de variabilidad y estacionalidad",
                    "Identificar anomalías y patrones significativos",
                    "Evaluar la precisión de las predicciones",
                    "Proporcionar intervalos de confianza para las estimaciones"
                ],
                add_history_to_messages=True,
                add_datetime_to_instructions=True,
                markdown=True,
                debug_mode=False,
            )

            self.advisor = Agent(
                name="StrategyAdvisor",
                role="Asesor estratégico basado en análisis cuantitativo",
                model=model,
                description="Genero recomendaciones basadas en análisis matemático y estadístico",
                instructions=[
                    "Basar recomendaciones en evidencia estadística",
                    "Calcular impacto financiero de las recomendaciones",
                    "Proponer estrategias de optimización con métricas específicas",
                    "Considerar múltiples escenarios con probabilidades"
                ],
                add_history_to_messages=True,
                add_datetime_to_instructions=True,
                markdown=True,
                debug_mode=False,
            )
            
        except Exception as e:
            logger.error(f"Error en inicialización: {str(e)}", exc_info=True)
            raise

    def _perform_statistical_analysis(self, history_data: list) -> dict:
        """Realiza análisis estadístico detallado de los datos históricos"""
        try:
            # Convertir datos históricos a DataFrame
            df = pd.DataFrame(history_data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.set_index('created_at').sort_index()
            
            # Análisis de series temporales
            usage_series = df['quantity']
            
            # Descomposición de la serie temporal
            decomposition = seasonal_decompose(usage_series, period=7, model='additive')
            
            # Calcular estadísticas descriptivas
            stats_analysis = {
                "mean": usage_series.mean(),
                "median": usage_series.median(),
                "std": usage_series.std(),
                "cv": usage_series.std() / usage_series.mean() * 100,
                "skewness": stats.skew(usage_series),
                "kurtosis": stats.kurtosis(usage_series),
                "trend_slope": np.polyfit(range(len(usage_series)), usage_series, 1)[0],
                "seasonality_strength": np.std(decomposition.seasonal) / np.std(usage_series),
                "autocorrelation": usage_series.autocorr(),
            }
            
            # Detección de anomalías
            z_scores = np.abs(stats.zscore(usage_series))
            anomalies = (z_scores > 3).sum()
            stats_analysis["anomalies_count"] = anomalies
            
            return stats_analysis
            
        except Exception as e:
            logger.error(f"Error en análisis estadístico: {str(e)}", exc_info=True)
            return {}

    def analyze_inventory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el workflow de análisis de inventario"""
        try:
            # Realizar análisis estadístico
            stats_analysis = self._perform_statistical_analysis(context["history"])
            
            # Convertir valores de NumPy a tipos nativos de Python
            stats_analysis = {k: convert_numpy_types(v) for k, v in stats_analysis.items()}
            
            # Preparar prompt para el análisis técnico
            analysis_prompt = f"""
            proporciona un análisis claro para {context['ingredient_name']} usando emojis y datos concretos.
            Usa los siguientes datos para tu análisis (evita usar asteriscos):

            📊 DATOS ESTADÍSTICOS:
            - Media de uso: {stats_analysis['mean']:.2f} {context['unit']}/día
            - Desviación estándar: {stats_analysis['std']:.2f}
            - Coeficiente de variación: {stats_analysis['cv']:.2f}%
            - Tendencia: {stats_analysis['trend_slope']:.2f}
            - Estacionalidad: {stats_analysis['seasonality_strength']:.2f}
            - Anomalías detectadas: {stats_analysis['anomalies_count']}

            📦 INVENTARIO ACTUAL:
            - Stock actual: {context['current_stock']} {context['unit']}
            - Stock total: {context['total_stock']} {context['unit']}
            - Factor de seguridad: {context['safe_factor']}%

            Proporciona:
            1. Análisis de patrones de consumo con números específicos
            2. Evaluación de la variabilidad y tendencias principales
            3. Alertas sobre anomalías y sus causas probables
            4. Proyección de consumo para próximos 7 días
            """

            # Preparar prompt para recomendaciones estratégicas
            strategy_prompt = f"""
            proporciona recomendaciones basadas en datos para {context['ingredient_name']} usando emojis.
            Evita usar asteriscos y mantén un balance entre precisión y claridad.

            📈 MÉTRICAS CLAVE:
            - Uso promedio: {stats_analysis['mean']:.2f} {context['unit']}/día
            - Variabilidad: {stats_analysis['cv']:.2f}%
            - Nivel actual: {context['current_stock']} {context['unit']}
            - Capacidad máxima: {context['total_stock']} {context['unit']}
            - Factor de seguridad: {context['safe_factor']}%

            Proporciona:
            1. 3-4 recomendaciones específicas con números y métricas
            2. Estrategia de optimización de niveles de inventario
            3. Plan de acción para manejar variabilidad
            4. Puntos de reorden sugeridos con justificación
            """

            # Obtener análisis y recomendaciones
            analysis = self.analyst.run(analysis_prompt)
            recommendations = self.advisor.run(strategy_prompt)

            return {
                "status": "success",
                "analysis": analysis.content if hasattr(analysis, 'content') else str(analysis),
                "recommendations": recommendations.content if hasattr(recommendations, 'content') else str(recommendations),
                "statistical_data": stats_analysis
            }

        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "analysis": "Error en análisis técnico",
                "recommendations": "Error en recomendaciones"
            }

