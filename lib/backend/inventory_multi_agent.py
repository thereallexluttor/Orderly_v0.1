from phi.workflow import Workflow
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.pandas import PandasTools
from phi.tools.python import PythonTools
from typing import Dict, Any, Optional
from pydantic import Field
import logging
import os
from dotenv import load_dotenv
import numpy as np
from scipy import stats
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
import json

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
                role="Analista especializado en detección de riesgos de inventario y patrones de consumo",
                model=Gemini(id="gemini-1.5-flash"),
                description="Analizo patrones críticos de consumo y genero alertas tempranas de desabastecimiento",
                instructions=[
                    "Identificar INMEDIATAMENTE cualquier riesgo de desabastecimiento",
                    "Calcular agresivamente puntos de reorden y niveles críticos de stock",
                    "Detectar y reportar urgentemente patrones anormales de consumo",
                    "Generar alertas cuando el consumo supere 2 desviaciones estándar",
                    "Priorizar análisis de ingredientes con mayor impacto en operaciones",
                    "Calcular probabilidades específicas de desabastecimiento",
                    "Proporciona una tabla con los datos de los ingredientes y las recomendaciones.",
                    "Identificar desperdicios y sobrestock con métricas precisas",
                    "Agregar niveles de urgencia (🔴CRÍTICO, 🟡PRECAUCIÓN, 🟢NORMAL) a cada hallazgo",
                    "Realizar análisis avanzados basados en estadísticas y matemáticas",
                    "Explorar correlaciones y tendencias en los datos",
                    "Calcular intervalos de confianza para proyecciones",
                    "Detectar comportamientos anómalos usando métricas estadísticas",
                    "no ejemplos de codigo o ejemplos de implementaciones.",
                    "Usar los datos proporcionados para realizar los calculos matematicos y estadisticos.",
                    "genera algunas tablas con tus hallazgos y recomendaciones."
                ],
                tools=[PythonTools()]
                


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

    def analyze_inventory_global(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el workflow de análisis global de inventario"""
        try:
            # Calcular estadísticas globales
            all_stats = []
            for ingredient in context['ingredients']:
                stats = self._perform_statistical_analysis(ingredient['history'])
                stats['ingredient_name'] = ingredient['ingredient_name']
                all_stats.append(stats)

            # Convertir a tipos nativos de Python
            all_stats = [{k: convert_numpy_types(v) for k, v in stats.items()} 
                        for stats in all_stats]

            analysis_prompt = f"""
            ANÁLISIS GLOBAL DEL INVENTARIO

            Datos generales:
            - Total de ingredientes: {len(context['ingredients'])}
            - Ingredientes en estado crítico: {sum(1 for i in context['ingredients'] if i['stock_status'] == 'crítico')}
            - Ingredientes en estado normal: {sum(1 for i in context['ingredients'] if i['stock_status'] == 'normal')}

            ESTADÍSTICAS POR INGREDIENTE:
            {json.dumps(all_stats, indent=2)}

            DATOS DE INVENTARIO ACTUAL:
            {json.dumps([{
                'nombre': i['ingredient_name'],
                'stock_actual': i['current_stock'],
                'stock_total': i['total_stock'],
                'unidad': i['unit'],
                'uso_promedio': i['average_daily_usage'],
                'uso_máximo': i['max_daily_usage'],
                'historial': i['history']
            } for i in context['ingredients']], indent=2)}
            Realiza un análisis global del inventario para los próximos 7 días
            """

            analysis = self.analyst.run(analysis_prompt)

            return {
                "status": "success",
                "analysis": analysis.content if hasattr(analysis, 'content') else str(analysis),
                "recommendations": "",  # Empty since we removed the advisor
                "statistical_data": all_stats
            }

        except Exception as e:
            logger.error(f"Error en análisis global: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "analysis": "Error en análisis estadístico global",
                "recommendations": ""
            }
