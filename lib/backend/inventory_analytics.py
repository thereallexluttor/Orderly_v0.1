from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from prophet import Prophet
import json
import logging
from inventory_multi_agent import InventoryAnalysisSystem
from functools import lru_cache
from pathlib import Path
import numpy as np
from inventory_queries import get_inventory_data, generate_ingredient_history_report, generate_inventory_report

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar variables de entorno
load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

inventory_system = InventoryAnalysisSystem()

# Add caching to prevent duplicate analysis
@lru_cache(maxsize=128)
def get_cached_agent_analysis(ingredient_id: int, current_stock: float, cache_key: str, data: str) -> dict:
    """Cache the agent analysis results for 5 minutes"""
    return inventory_system.analyze_inventory({
        "ingredient_id": ingredient_id,
        "current_stock": current_stock,
        "daily_usage": data
    })

def ensure_daily_directory() -> Path:
    """Create and return path to today's data directory"""
    today = datetime.now().strftime('%Y-%m-%d')
    base_dir = Path(__file__).parent / 'analytics_data'
    daily_dir = base_dir / today
    
    # Create directories if they don't exist
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    return daily_dir

def convert_to_serializable(obj):
    """Convierte objetos NumPy a tipos nativos de Python"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    return obj

@app.get("/ingredient-usage/{ingredient_id}")
async def get_ingredient_usage(ingredient_id: int, current_stock: float, request: Request):
    try:
        logger.info(f"Obteniendo datos para ingredient_id: {ingredient_id}, stock actual: {current_stock}")
        
        # Verificar si la solicitud viene del navegador
        accept_header = request.headers.get("accept", "")
        is_browser_request = "text/html" in accept_header

        # Obtener datos de uso del ingrediente
        usage_response = supabase.table("ingredient_usage_table") \
            .select("quantity_used, usage_date") \
            .eq("ingredient_id", ingredient_id) \
            .execute()
        
        logger.info(f"Datos de uso obtenidos: {len(usage_response.data) if usage_response.data else 0} registros")

        if not usage_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron datos de uso para el ingrediente {ingredient_id}"
            )

        # Convertir a DataFrame y validar datos
        df = pd.DataFrame(usage_response.data)
        
        # Validar y convertir fechas
        if not pd.api.types.is_datetime64_any_dtype(df['usage_date']):
            logger.warning("usage_date no está en formato datetime, intentando convertir...")
            df['usage_date'] = pd.to_datetime(df['usage_date'], errors='coerce')
            if df['usage_date'].isna().any():
                logger.error("Algunas fechas no pudieron ser convertidas")
        df = df.dropna(subset=['usage_date'])  # Eliminar filas con fechas inválidas
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No hay datos válidos después de la limpieza"
            )

        # Validar cantidad usada
        df['quantity_used'] = pd.to_numeric(df['quantity_used'], errors='coerce')
        df = df.dropna(subset=['quantity_used'])  # Eliminar filas con cantidades inválidas

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No hay datos válidos de cantidad usada"
            )

        # Calcular estadísticas básicas
        daily_usage = df.groupby('usage_date')['quantity_used'].sum().reset_index()
        
        # Calcular predicciones usando Prophet
        prophet_df = daily_usage.rename(columns={'usage_date': 'ds', 'quantity_used': 'y'})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(prophet_df)
        
        future_dates = model.make_future_dataframe(periods=3)
        forecast = model.predict(future_dates)

        # Calcular recomendaciones basadas en el uso promedio
        predicted_daily_usage = float(forecast['yhat'].tail(3).mean())
        recent_usage = df[df['usage_date'] >= (df['usage_date'].max() - pd.Timedelta(days=7))]
        recent_daily_avg = float(recent_usage.groupby('usage_date')['quantity_used'].sum().mean())

        # Calcular días estimados de stock restante
        days_remaining = float('inf') if predicted_daily_usage == 0 else current_stock / predicted_daily_usage

        # Ahora que hemos hecho todos los cálculos, convertimos las fechas a formato ISO
        daily_usage['usage_date'] = daily_usage['usage_date'].dt.strftime('%Y-%m-%d')
        df['usage_date'] = df['usage_date'].dt.strftime('%Y-%m-%d')
        forecast['ds'] = forecast['ds'].dt.strftime('%Y-%m-%d')
        future_dates['ds'] = future_dates['ds'].dt.strftime('%Y-%m-%d')

        restock_status = {
            'predicted_daily_usage': round(predicted_daily_usage, 2),
            'recent_daily_average': round(recent_daily_avg, 2),
            'current_stock': current_stock,
            'days_remaining': round(days_remaining, 1),
            'recommendation': '',
            'urgency': 'medium'
        }

        # Ajustar recomendaciones basadas en stock actual y uso predicho
        if days_remaining < 3:
            restock_status['recommendation'] = '¡URGENTE! Stock crítico. Reabastecer inmediatamente.'
            restock_status['urgency'] = 'high'
        elif days_remaining < 7:
            restock_status['recommendation'] = 'Stock bajo. Programar reabastecimiento esta semana.'
            restock_status['urgency'] = 'medium'
        elif predicted_daily_usage > recent_daily_avg * 1.2:
            restock_status['recommendation'] = 'El uso está aumentando. Considerar aumentar el stock.'
            restock_status['urgency'] = 'medium'
        else:
            restock_status['recommendation'] = 'Niveles de stock adecuados para el uso actual.'
            restock_status['urgency'] = 'low'

        # Actualizar stats
        stats = {
            'total_usage': float(df['quantity_used'].sum()),
            'avg_daily_usage': float(daily_usage['quantity_used'].mean()),
            'max_daily_usage': float(daily_usage['quantity_used'].max()),
            'total_days': len(daily_usage),
            'predicted_usage_3days': float(forecast['yhat'].tail(3).sum()),
            'predicted_avg_daily': predicted_daily_usage,
            'restock_status': restock_status
        }

        # Gráfico de uso por día
        fig1 = px.line(daily_usage, 
                      x='usage_date', 
                      y='quantity_used',
                      title='Uso Diario del Ingrediente',
                      labels={'usage_date': 'Fecha', 'quantity_used': 'Cantidad Usada'})
        
        # Gráfico de uso por semana (pie)
        df['usage_date'] = pd.to_datetime(df['usage_date'])  # Convertir explícitamente a datetime
        df['week'] = df['usage_date'].dt.strftime('%Y-%U')
        weekly_usage = df.groupby('week')['quantity_used'].sum()
        
        fig2 = px.pie(values=weekly_usage.values, 
                     names=weekly_usage.index,
                     title='Distribución de Uso por Semana')

        # Create prediction chart
        fig3 = go.Figure()
        
        # Add actual values
        fig3.add_trace(go.Scatter(
            x=prophet_df['ds'],
            y=prophet_df['y'],
            name='Datos Históricos',
            line=dict(color='blue')
        ))
        
        # Add predictions (change from tail(7) to tail(3))
        fig3.add_trace(go.Scatter(
            x=forecast['ds'].tail(3),
            y=forecast['yhat'].tail(3),
            name='Predicción',
            line=dict(color='red', dash='dash')
        ))
        
        # Add uncertainty intervals (change from tail(7) to tail(3))
        fig3.add_trace(go.Scatter(
            x=forecast['ds'].tail(3),
            y=forecast['yhat_upper'].tail(3),
            fill=None,
            mode='lines',
            line=dict(color='rgba(255,0,0,0)'),
            showlegend=False
        ))
        
        fig3.add_trace(go.Scatter(
            x=forecast['ds'].tail(3),
            y=forecast['yhat_lower'].tail(3),
            fill='tonexty',
            mode='lines',
            line=dict(color='rgba(255,0,0,0)'),
            name='Intervalo de Confianza'
        ))
        
        fig3.update_layout(
            title='Predicción de Uso del Ingrediente (Próximos 3 días)',
            xaxis_title='Fecha',
            yaxis_title='Cantidad Usada',
            hovermode='x unified'
        )

        # Solo ejecutar análisis de agentes si es una solicitud del navegador
        agent_analysis = None
        if is_browser_request:
            # Generate a cache key that expires every 5 minutes
            cache_time = datetime.now().replace(second=0, microsecond=0)
            cache_time = cache_time - timedelta(minutes=cache_time.minute % 5)
            cache_key = f"{cache_time.isoformat()}"

            # Use cached agent analysis instead of direct call
            agent_data = {
                "ingredient_id": ingredient_id,
                "current_stock": float(current_stock),  # Asegurar que sea float nativo
                "daily_usage": convert_to_serializable(daily_usage),
                "weekly_usage": convert_to_serializable(weekly_usage),
                "forecast": convert_to_serializable(forecast),
                "daily_usage_chart": json.loads(fig1.to_json()),
                "weekly_usage_chart": json.loads(fig2.to_json()),
                "prediction_chart": json.loads(fig3.to_json())
            }

            # Use cached_agent_analysis with the complete data
            agent_analysis = get_cached_agent_analysis(
                ingredient_id, 
                current_stock,
                cache_key,
                json.dumps(agent_data)
            )
            stats['agent_analysis'] = agent_analysis

        # Prepare the analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'ingredient_id': ingredient_id,
            'current_stock': current_stock,
            'daily_usage_chart': fig1.to_json(),
            'weekly_usage_chart': fig2.to_json(),
            'prediction_chart': fig3.to_json(),
            'stats': stats
        }

        # Solo incluir análisis de agentes si está disponible
        if agent_analysis:
            analysis_data['agent_analysis'] = agent_analysis

        # Save to JSON file
        daily_dir = ensure_daily_directory()
        timestamp = datetime.now().strftime('%H-%M-%S')
        filename = f'ingredient_{ingredient_id}_{timestamp}.json'
        
        with open(daily_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Analysis saved to {daily_dir / filename}")

        # Si es una solicitud del navegador, devolver HTML
        if is_browser_request:
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Análisis de Uso del Ingrediente</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Poppins', sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f0f2f5;
                        color: #1a1f36;
                    }}
                    .container {{
                        max-width: 1400px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                    }}
                    h1 {{
                        color: #1a1f36;
                        text-align: center;
                        margin-bottom: 40px;
                        font-size: 2.2em;
                        font-weight: 600;
                    }}
                    .stats-container {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 25px;
                        margin-bottom: 40px;
                    }}
                    .stat-card {{
                        background-color: #ffffff;
                        padding: 25px;
                        border-radius: 12px;
                        text-align: center;
                        transition: transform 0.2s ease;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                        border: 1px solid #e5e9f2;
                    }}
                    .stat-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }}
                    .stat-value {{
                        font-size: 28px;
                        font-weight: 600;
                        color: #2d3748;
                        margin-bottom: 8px;
                    }}
                    .stat-label {{
                        color: #718096;
                        font-size: 0.95em;
                        font-weight: 500;
                    }}
                    .charts-container {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
                        gap: 30px;
                        margin-top: 40px;
                    }}
                    .chart {{
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        min-height: 450px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                        border: 1px solid #e5e9f2;
                    }}
                    .restock-alert {{
                        padding: 25px;
                        border-radius: 12px;
                        margin: 30px 0;
                        text-align: center;
                        transition: all 0.3s ease;
                    }}
                    .restock-alert h3 {{
                        margin: 0 0 15px 0;
                        font-size: 1.5em;
                        font-weight: 600;
                    }}
                    .restock-alert p {{
                        margin: 0;
                        font-size: 1.1em;
                        line-height: 1.5;
                    }}
                    .high {{
                        background-color: #fff5f5;
                        color: #c53030;
                        border: 1px solid #feb2b2;
                    }}
                    .medium {{
                        background-color: #fffaf0;
                        color: #975a16;
                        border: 1px solid #fbd38d;
                    }}
                    .low {{
                        background-color: #f0fff4;
                        color: #2f855a;
                        border: 1px solid #9ae6b4;
                    }}
                    @media (max-width: 768px) {{
                        .container {{
                            padding: 20px;
                        }}
                        .stats-container {{
                            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 15px;
                        }}
                        .charts-container {{
                            grid-template-columns: 1fr;
                        }}
                        .stat-value {{
                            font-size: 24px;
                        }}
                        h1 {{
                            font-size: 1.8em;
                        }}
                    }}
                    .header-section {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    .subtitle {{
                        color: #718096;
                        font-size: 1.1em;
                        margin-top: -20px;
                    }}
                    .agent-analysis-container {{
                        margin: 40px 0;
                        padding: 20px;
                        background-color: #ffffff;
                        border-radius: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                        border: 1px solid #e5e9f2;
                    }}
                    .agent-cards {{
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                        margin-top: 20px;
                    }}
                    .agent-card {{
                        background-color: #f8fafc;
                        padding: 20px;
                        border-radius: 8px;
                        border: 1px solid #e5e9f2;
                        opacity: 0;
                        animation: fadeIn 0.5s ease forwards;
                    }}
                    .agent-card h3 {{
                        color: #2d3748;
                        margin-top: 0;
                        margin-bottom: 15px;
                        font-size: 1.2em;
                        border-bottom: 2px solid #e5e9f2;
                        padding-bottom: 8px;
                    }}
                    .typing-animation {{
                        overflow: hidden;
                        border-right: 2px solid #2d3748;
                        white-space: pre-wrap;
                        margin: 0;
                        letter-spacing: 0.15em;
                        animation: typing 3.5s steps(40, end),
                                 blink-caret 0.75s step-end infinite;
                    }}
                    @keyframes typing {{
                        from {{ max-height: 0; }}
                        to {{ max-height: 1000px; }}
                    }}
                    @keyframes blink-caret {{
                        from, to {{ border-color: transparent }}
                        50% {{ border-color: #2d3748; }}
                    }}
                    @keyframes fadeIn {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    .agent-card:nth-child(1) {{ animation-delay: 0.2s; }}
                    .agent-card:nth-child(2) {{ animation-delay: 0.4s; }}
                    .agent-card:nth-child(3) {{ animation-delay: 0.6s; }}
                    .agent-card:nth-child(4) {{ animation-delay: 0.8s; }}
                    .agent-card:nth-child(5) {{ animation-delay: 1.0s; }}
                    .agent-card:nth-child(6) {{ animation-delay: 1.2s; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header-section">
                        <h1>Dashboard de Análisis de Ingrediente</h1>
                        <p class="subtitle">Análisis predictivo y recomendaciones de reabastecimiento</p>
                    </div>
                    
                    <div class="restock-alert {stats['restock_status']['urgency']}">
                        <h3>Estado de Reabastecimiento</h3>
                        <p>{stats['restock_status']['recommendation']}</p>
                    </div>

                    <div class="stats-container">
                        <div class="stat-card">
                            <div class="stat-value">{stats['predicted_usage_3days']:.1f}</div>
                            <div class="stat-label">Uso Predicho (Próx. 3 días)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['avg_daily_usage']:.1f}</div>
                            <div class="stat-label">Promedio Diario</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['max_daily_usage']:.1f}</div>
                            <div class="stat-label">Máximo Diario</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['predicted_avg_daily']:.1f}</div>
                            <div class="stat-label">Uso Diario Predicho</div>
                        </div>
                    </div>

                    <div class="agent-analysis-container">
                        <h2>Análisis Cuantitativo Multi-Agente</h2>
                        <div class="agent-cards">
                            <div class="agent-card">
                                <h3>Análisis Conservador de Datos</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['conservative_analysis']['data']}
                                </div>
                            </div>
                            <div class="agent-card">
                                <h3>Predicciones Conservadoras</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['conservative_analysis']['prediction']}
                                </div>
                            </div>
                            <div class="agent-card">
                                <h3>Análisis Agresivo de Datos</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['aggressive_analysis']['data']}
                                </div>
                            </div>
                            <div class="agent-card">
                                <h3>Predicciones Agresivas</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['aggressive_analysis']['prediction']}
                                </div>
                            </div>
                            <div class="agent-card">
                                <h3>Mediación de Riesgos</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['risk_mediation']}
                                </div>
                            </div>
                            <div class="agent-card">
                                <h3>Síntesis Cuantitativa</h3>
                                <div class="typing-animation">
                                    {agent_analysis['analyses']['final_synthesis']}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="charts-container">
                        <div class="chart" id="daily-chart"></div>
                        <div class="chart" id="prediction-chart"></div>
                        <div class="chart" id="weekly-chart"></div>
                    </div>
                </div>

                <script>
                    var dailyChart = {fig1.to_json()};
                    var weeklyChart = {fig2.to_json()};
                    var predictionChart = {fig3.to_json()};
                    
                    Plotly.newPlot('daily-chart', dailyChart.data, dailyChart.layout);
                    Plotly.newPlot('weekly-chart', weeklyChart.data, weeklyChart.layout);
                    Plotly.newPlot('prediction-chart', predictionChart.data, predictionChart.layout);
                </script>
            </body>
            </html>
            """)
        
        # Si no es una solicitud del navegador, devolver JSON sin el análisis de agentes
        return {
            'daily_usage_chart': fig1.to_json(),
            'weekly_usage_chart': fig2.to_json(),
            'prediction_chart': fig3.to_json(),
            'stats': {k: v for k, v in stats.items() if k != 'agent_analysis'}
        }

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        
        # Also log errors to file
        daily_dir = ensure_daily_directory()
        timestamp = datetime.now().strftime('%H-%M-%S')
        error_filename = f'error_ingredient_{ingredient_id}_{timestamp}.json'
        
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'ingredient_id': ingredient_id,
            'current_stock': current_stock,
            'error': str(e)
        }
        
        with open(daily_dir / error_filename, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
            
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/inventory-report")
async def get_inventory_report(request: Request):
    try:
        # Verificar si la solicitud viene del navegador
        accept_header = request.headers.get("accept", "")
        is_browser_request = "text/html" in accept_header

        # Obtener datos del inventario
        inventory_items, ingredient_usage = get_inventory_data()
        
        if not inventory_items:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron datos de inventario"
            )

        # Generar reporte histórico
        history_data = generate_ingredient_history_report(inventory_items, ingredient_usage)
        
        # Generar reporte general
        report_data = generate_inventory_report(inventory_items, ingredient_usage)

        # Inicializar sistema de análisis
        analysis_system = InventoryAnalysisSystem()

        # Análisis detallado por ingrediente usando Prophet
        detailed_analysis = {}
        for item in inventory_items:
            ingredient_id = item['ingredient_id']
            
            # Obtener datos de uso del ingrediente
            usage_response = supabase.table("ingredient_usage_table") \
                .select("quantity_used, usage_date") \
                .eq("ingredient_id", ingredient_id) \
                .execute()
            
            if usage_response.data:
                # Convertir a DataFrame para Prophet
                df = pd.DataFrame(usage_response.data)
                df['usage_date'] = pd.to_datetime(df['usage_date'])
                daily_usage = df.groupby('usage_date')['quantity_used'].sum().reset_index()
                
                # Preparar datos para Prophet
                prophet_df = daily_usage.rename(columns={'usage_date': 'ds', 'quantity_used': 'y'})
                model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
                model.fit(prophet_df)
                
                future_dates = model.make_future_dataframe(periods=7)  # Predicción a 7 días
                forecast = model.predict(future_dates)
                
                # Crear gráficas específicas del ingrediente
                usage_history_fig = go.Figure()
                usage_history_fig.add_trace(go.Scatter(
                    x=prophet_df['ds'],
                    y=prophet_df['y'],
                    name='Uso Real',
                    line=dict(color='blue')
                ))
                usage_history_fig.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat'],
                    name='Predicción',
                    line=dict(color='red', dash='dash')
                ))
                usage_history_fig.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat_upper'],
                    fill=None,
                    mode='lines',
                    line=dict(color='rgba(255,0,0,0)'),
                    showlegend=False
                ))
                usage_history_fig.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat_lower'],
                    fill='tonexty',
                    mode='lines',
                    line=dict(color='rgba(255,0,0,0)'),
                    name='Intervalo de Confianza'
                ))
                usage_history_fig.update_layout(
                    title=f'Histórico y Predicción de Uso - {item["ingredient_name"]}',
                    xaxis_title='Fecha',
                    yaxis_title=f'Cantidad ({item["unit"]})',
                    hovermode='x unified'
                )
                
                # Análisis multi-agente específico del ingrediente
                ingredient_data = {
                    "ingredient_id": ingredient_id,
                    "current_stock": item['total_stock'] - ingredient_usage.get(ingredient_id, 0),
                    "daily_usage": daily_usage.to_dict('records'),
                    "forecast": forecast.to_dict('records'),
                    "historical_data": history_data.get(ingredient_id, {})
                }
                
                agent_analysis = analysis_system.analyze_inventory(ingredient_data)
                
                detailed_analysis[ingredient_id] = {
                    "name": item["ingredient_name"],
                    "unit": item["unit"],
                    "current_stock": item['total_stock'] - ingredient_usage.get(ingredient_id, 0),
                    "total_usage": ingredient_usage.get(ingredient_id, 0),
                    "forecast": {
                        "next_7_days": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7).to_dict('records'),
                        "trend": forecast['trend'].mean(),
                        "weekly_pattern": model.weekly.mean() if hasattr(model, 'weekly') else None,
                    },
                    "usage_history_chart": usage_history_fig.to_json(),
                    "agent_analysis": agent_analysis
                }

        # Preparar datos para análisis multi-agente general
        enriched_data = {
            "inventory_items": inventory_items,
            "ingredient_usage": ingredient_usage,
            "history_data": history_data,
            "report_data": report_data,
            "detailed_analysis": detailed_analysis
        }

        # Realizar análisis multi-agente general
        agent_analysis = analysis_system.analyze_inventory(enriched_data)

        if is_browser_request:
            # Generar gráficas generales
            usage_fig = px.bar(
                x=[item['ingredient_name'] for item in inventory_items],
                y=[ingredient_usage.get(item['ingredient_id'], 0) for item in inventory_items],
                title='Uso Total por Ingrediente',
                labels={'x': 'Ingrediente', 'y': 'Cantidad Usada'}
            )

            stock_fig = px.bar(
                x=[item['ingredient_name'] for item in inventory_items],
                y=[(item['total_stock'] - ingredient_usage.get(item['ingredient_id'], 0)) for item in inventory_items],
                title='Stock Disponible por Ingrediente',
                labels={'x': 'Ingrediente', 'y': 'Stock Disponible'}
            )

            avg_usage = []
            for item in inventory_items:
                if item['ingredient_id'] in history_data:
                    hist = history_data[item['ingredient_id']]
                    avg_usage.append(hist['average_daily_usage'])
                else:
                    avg_usage.append(0)

            avg_fig = px.bar(
                x=[item['ingredient_name'] for item in inventory_items],
                y=avg_usage,
                title='Uso Promedio Diario por Ingrediente',
                labels={'x': 'Ingrediente', 'y': 'Uso Promedio Diario'}
            )

            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reporte de Inventario</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Poppins', sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f0f2f5;
                        color: #1a1f36;
                    }}
                    .container {{
                        max-width: 1400px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                    }}
                    h1, h2, h3 {{
                        color: #1a1f36;
                        margin-bottom: 20px;
                    }}
                    .stats-container {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }}
                    .stat-card {{
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 12px;
                        border: 1px solid #e5e9f2;
                    }}
                    .charts-container {{
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 30px;
                        margin-top: 30px;
                    }}
                    .chart {{
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        border: 1px solid #e5e9f2;
                        height: 500px;
                    }}
                    .analysis-section {{
                        margin-top: 30px;
                        padding: 20px;
                        background-color: #ffffff;
                        border-radius: 12px;
                        border: 1px solid #e5e9f2;
                    }}
                    .critical-items {{
                        margin-top: 20px;
                        padding: 20px;
                        background-color: #fff5f5;
                        border-radius: 12px;
                        border: 1px solid #feb2b2;
                    }}
                    .ingredient-detail {{
                        margin-top: 40px;
                        padding: 20px;
                        background-color: #ffffff;
                        border-radius: 12px;
                        border: 1px solid #e5e9f2;
                    }}
                    .forecast-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    .forecast-table th, .forecast-table td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #e5e9f2;
                    }}
                    .forecast-table th {{
                        background-color: #f8fafc;
                        font-weight: 600;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Reporte General de Inventario</h1>
                    
                    <div class="stats-container">
                        <div class="stat-card">
                            <h3>Estadísticas Generales</h3>
                            <p>Total de Ingredientes: {report_data['total_ingredients']}</p>
                            <p>Valor Total del Stock: {report_data['total_stock_value']:.2f}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Distribución por Unidades</h3>
                            {''.join(f'<p>{unit}: {count}</p>' for unit, count in report_data['units_distribution'].items())}
                        </div>
                    </div>

                    <div class="critical-items">
                        <h3>Ingredientes en Estado Crítico</h3>
                        {''.join(f'<p>{item["name"]}: {item["available"]:.2f} {item["unit"]} disponibles</p>' for item in report_data["critical_stock_items"])}
                    </div>

                    <div class="analysis-section">
                        <h2>Análisis Multi-Agente General</h2>
                        <div class="agent-analysis">
                            <h3>Análisis Conservador</h3>
                            <p>{agent_analysis['analyses']['conservative_analysis']['data']}</p>
                            <p>{agent_analysis['analyses']['conservative_analysis']['prediction']}</p>
                            
                            <h3>Análisis Agresivo</h3>
                            <p>{agent_analysis['analyses']['aggressive_analysis']['data']}</p>
                            <p>{agent_analysis['analyses']['aggressive_analysis']['prediction']}</p>
                            
                            <h3>Mediación de Riesgos</h3>
                            <p>{agent_analysis['analyses']['risk_mediation']}</p>
                            
                            <h3>Síntesis Final</h3>
                            <p>{agent_analysis['analyses']['final_synthesis']}</p>
                        </div>
                    </div>

                    <div class="charts-container">
                        <div class="chart" id="usage-chart"></div>
                        <div class="chart" id="stock-chart"></div>
                        <div class="chart" id="avg-chart"></div>
                    </div>

                    <h2>Análisis Detallado por Ingrediente</h2>
                    {''.join(f"""
                    <div class="ingredient-detail">
                        <h3>{analysis['name']}</h3>
                        <div class="stats-container">
                            <div class="stat-card">
                                <p>Stock Actual: {analysis['current_stock']:.2f} {analysis['unit']}</p>
                                <p>Uso Total: {analysis['total_usage']:.2f} {analysis['unit']}</p>
                                <p>Tendencia: {analysis['forecast']['trend']:.2f}</p>
                            </div>
                        </div>
                        
                        <h4>Predicción próximos 7 días</h4>
                        <table class="forecast-table">
                            <tr>
                                <th>Fecha</th>
                                <th>Predicción</th>
                                <th>Mínimo</th>
                                <th>Máximo</th>
                            </tr>
                            {''.join(f'''
                            <tr>
                                <td>{pd.to_datetime(day['ds']).strftime('%Y-%m-%d')}</td>
                                <td>{day['yhat']:.2f}</td>
                                <td>{day['yhat_lower']:.2f}</td>
                                <td>{day['yhat_upper']:.2f}</td>
                            </tr>
                            ''' for day in analysis['forecast']['next_7_days'])}
                        </table>

                        <div class="chart" id="ingredient-chart-{ingredient_id}"></div>

                        <div class="analysis-section">
                            <h4>Análisis Multi-Agente del Ingrediente</h4>
                            <p>{analysis['agent_analysis']['analyses']['conservative_analysis']['data']}</p>
                            <p>{analysis['agent_analysis']['analyses']['conservative_analysis']['prediction']}</p>
                            <p>{analysis['agent_analysis']['analyses']['aggressive_analysis']['data']}</p>
                            <p>{analysis['agent_analysis']['analyses']['aggressive_analysis']['prediction']}</p>
                            <p>{analysis['agent_analysis']['analyses']['risk_mediation']}</p>
                            <p>{analysis['agent_analysis']['analyses']['final_synthesis']}</p>
                        </div>
                    </div>
                    """ for ingredient_id, analysis in detailed_analysis.items())}
                </div>

                <script>
                    var usageChart = {usage_fig.to_json()};
                    var stockChart = {stock_fig.to_json()};
                    var avgChart = {avg_fig.to_json()};
                    
                    Plotly.newPlot('usage-chart', usageChart.data, usageChart.layout);
                    Plotly.newPlot('stock-chart', stockChart.data, stockChart.layout);
                    Plotly.newPlot('avg-chart', avgChart.data, avgChart.layout);

                    {' '.join(f"""
                    var ingredientChart{ingredient_id} = {analysis['usage_history_chart']};
                    Plotly.newPlot('ingredient-chart-{ingredient_id}', ingredientChart{ingredient_id}.data, ingredientChart{ingredient_id}.layout);
                    """ for ingredient_id, analysis in detailed_analysis.items())}
                </script>
            </body>
            </html>
            """)
        
        return {
            "report_data": report_data,
            "agent_analysis": agent_analysis,
            "detailed_analysis": detailed_analysis
        }

    except Exception as e:
        logger.error(f"Error generando reporte de inventario: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 