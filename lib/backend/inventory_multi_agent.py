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
                name="DataAnalyst",
                role="Analista de datos especializado en análisis estadístico",
                model=Gemini(id="gemini-1.5-flash"),
                description="Realizo análisis estadísticos descriptivos y de series temporales",
                instructions=[
                    "Analizar exclusivamente los datos proporcionados sin hacer suposiciones",
                    "Identificar patrones estadísticamente significativos en los datos",
                    "Calcular y reportar métricas estadísticas clave",
                    "Detectar outliers y anomalías basadas en z-scores",
                    "Reportar hallazgos con intervalos de confianza cuando sea posible",
                    "Mantener un enfoque puramente cuantitativo",
                    "Agregar emojis al mensaje para que se vea más atractivo"
                ],
            )

            self.advisor = Agent(
                name="AdvancedAnalyst",
                role="Analista de datos avanzado especializado en correlaciones y patrones complejos",
                model=Gemini(id="gemini-1.5-flash"),
                description="Analizo patrones complejos y relaciones entre variables",
                instructions=[
                    "Realizar análisis de correlaciones entre variables",
                    "Identificar patrones cíclicos y estacionales con significancia estadística",
                    "Calcular métricas avanzadas de variabilidad y tendencias",
                    "Analizar la descomposición de series temporales",
                    "Reportar hallazgos basados únicamente en evidencia estadística",
                    "Complementar el análisis base con insights más profundos",
                    "agregar emojis al mensaje para que se vea más atractivo"
                ],
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
            stats_analysis = self._perform_statistical_analysis(context["history"])
            stats_analysis = {k: convert_numpy_types(v) for k, v in stats_analysis.items()}
            
            # Prompt para análisis estadístico base
            analysis_prompt = f"""
            DATOS NUMÉRICOS PARA ANÁLISIS:
            - Serie temporal de uso: {context['history']}

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

            Métricas estadísticas calculadas:
            {stats_analysis}

            Realiza un análisis puramente estadístico de estos datos. 
            Reporta solo hallazgos respaldados por los números y tests estadísticos.
            No hagas suposiciones ni recomendaciones.
            """

            analysis = self.analyst.run(analysis_prompt)

            # Prompt para análisis avanzado
            advanced_prompt = f"""
            ANÁLISIS BASE PREVIO:
            {analysis.content if hasattr(analysis, 'content') else str(analysis)}

            DATOS ADICIONALES PARA ANÁLISIS AVANZADO:
            - Serie temporal completa: {context['history']}
            - Métricas calculadas: {stats_analysis}

            Realiza un análisis estadístico avanzado enfocándote en:
            1. Correlaciones significativas encontradas
            2. Patrones cíclicos con significancia estadística
            3. Componentes de la descomposición de series temporales
            4. Análisis de variabilidad y tendencias
            
            Reporta solo hallazgos respaldados por tests estadísticos.
            No incluyas suposiciones ni recomendaciones.
            """
            
            advanced_analysis = self.advisor.run(advanced_prompt)

            return {
                "status": "success",
                "analysis": analysis.content if hasattr(analysis, 'content') else str(analysis),
                "recommendations": advanced_analysis.content if hasattr(advanced_analysis, 'content') else str(advanced_analysis),
                "statistical_data": stats_analysis
            }

        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "analysis": "Error en análisis estadístico",
                "recommendations": "Error en análisis avanzado"
            }

