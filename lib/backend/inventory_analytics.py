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
from inventory_queries import (
    get_inventory_data, 
    get_ingredient_usage,
    generate_ingredient_history_report, 
    generate_inventory_report
)

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
async def get_ingredient_usage_endpoint(ingredient_id: int, current_stock: float):
    try:
        logger.info(f"Obteniendo datos para ingredient_id: {ingredient_id}")
        
        # Usar la función de queries directamente
        usage_data = get_ingredient_usage(ingredient_id, current_stock)
        
        if not usage_data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron datos de uso para el ingrediente {ingredient_id}"
            )
            
        # Obtener datos del inventario usando la función de queries
        inventory_items, ingredient_usage = get_inventory_data()
        
        # Buscar el ingrediente específico
        item = next((item for item in inventory_items if item['ingredient_id'] == ingredient_id), None)
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el ingrediente con ID {ingredient_id}"
            )

        return {
            "status": "success",
            "data": {
                "ingredient": item,
                "usage_data": usage_data,
                "current_stock": current_stock,
                "total_usage": ingredient_usage.get(ingredient_id, 0)
            }
        }

    except Exception as e:
        logger.error(f"Error obteniendo datos del ingrediente: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

@app.get("/inventory-report")
async def get_inventory_report_endpoint(request: Request):
    try:
        logger.info("Iniciando generación de reporte de inventario...")
        
        # Usar las funciones de queries directamente
        inventory_items, ingredient_usage = get_inventory_data()
        
        if not inventory_items:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron datos de inventario"
            )

        # Generar reporte histórico usando la función de queries
        history_data = generate_ingredient_history_report(inventory_items, ingredient_usage)
        
        # Generar reporte general usando la función de queries
        report_data = generate_inventory_report(inventory_items, ingredient_usage)

        logger.info("Reporte generado exitosamente")
        
        return {
            "status": "success",
            "message": "Reporte generado exitosamente",
            "data": {
                "report": report_data,
                "history": history_data
            }
        }

    except Exception as e:
        logger.error(f"Error generando reporte de inventario: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte: {str(e)}"
        )

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    try:
        # Obtener datos del inventario usando las funciones de queries
        inventory_items, ingredient_usage = get_inventory_data()
        
        if not inventory_items:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron datos de inventario"
            )
            
        # Generar el historial usando la función de queries
        ingredients_data = generate_ingredient_history_report(inventory_items, ingredient_usage)
        
        if not ingredients_data:
            raise HTTPException(
                status_code=500,
                detail="Error generando el historial de ingredientes"
            )

        # Generate dashboard HTML
        dashboard_html = generate_dashboard_html(ingredients_data)
        return dashboard_html

    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating dashboard: {str(e)}"
        )

def generate_dashboard_html(ingredients_data):
    ingredient_sections = []

    for ingredient_id, data in ingredients_data.items():
        try:
            # Create usage history dataframe
            df = pd.DataFrame(
                [(date, usage) for date, usage in data['usage_history'].items()],
                columns=['ds', 'y']
            )
            df['ds'] = pd.to_datetime(df['ds'])

            # 1. Historical Usage Plot
            usage_fig = px.line(df, x='ds', y='y', 
                              title=f"Uso Histórico",
                              labels={'ds': 'Fecha', 'y': f"Uso ({data['unit']})"})
            usage_fig.update_layout(showlegend=False)
            
            # 2. Generate Prophet predictions
            m = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            m.fit(df)
            future = m.make_future_dataframe(periods=30)
            forecast = m.predict(future)
            
            pred_fig = go.Figure()
            pred_fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], name='Histórico'))
            pred_fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], 
                                        name='Predicción'))
            pred_fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], 
                                        fill=None, mode='lines', line_color='rgba(0,100,80,0.2)', 
                                        name='Límite Superior'))
            pred_fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], 
                                        fill='tonexty', mode='lines', line_color='rgba(0,100,80,0.2)', 
                                        name='Límite Inferior'))
            pred_fig.update_layout(
                title="Pronóstico de Uso",
                xaxis_title="Fecha",
                yaxis_title=f"Uso ({data['unit']})"
            )

            # 3. Generate insights
            last_30_days = df[df['ds'] > df['ds'].max() - timedelta(days=30)]
            recent_trend = last_30_days['y'].mean() - df['y'].mean()
            peak_usage = forecast[forecast['ds'] > datetime.now()]['yhat'].max()
            
            # Calculate new metrics using total_stock and safe_factor
            safe_threshold = data['total_stock'] * (data['safe_factor'] / 100)
            current_stock = data['current_stock']
            stock_percentage = (current_stock / data['total_stock']) * 100
            days_until_empty = current_stock / data['average_daily_usage'] if data['average_daily_usage'] > 0 else float('inf')
            
            # Determine stock status color
            status_color = (
                '#e74c3c' if current_stock < safe_threshold else  # red
                '#f1c40f' if current_stock < (data['total_stock'] * 0.3) else  # yellow
                '#2ecc71'  # green
            )

            # Create ingredient section
            section_html = f"""
            <div class="ingredient-section">
                <div class="ingredient-header">
                    <h2>{data['ingredient_name']}</h2>
                    <div class="header-metrics">
                        <span class="ingredient-unit">Unidad: {data['unit']}</span>
                        <span class="stock-status" style="background-color: {status_color}">
                            {data['stock_status'].upper()}
                        </span>
                    </div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Stock Total</h3>
                        <p>{data['total_stock']:.2f} {data['unit']}</p>
                        <small>Factor de Seguridad: {data['safe_factor']}%</small>
                    </div>
                    <div class="metric-card">
                        <h3>Stock Actual</h3>
                        <p>{current_stock:.2f} {data['unit']}</p>
                        <small>{stock_percentage:.1f}% del total</small>
                    </div>
                    <div class="metric-card">
                        <h3>Límite Seguro</h3>
                        <p>{safe_threshold:.2f} {data['unit']}</p>
                        <small>Nivel mínimo recomendado</small>
                    </div>
                    <div class="metric-card">
                        <h3>Días Restantes</h3>
                        <p>{min(days_until_empty, 999):.1f} días</p>
                        <small>Al ritmo actual de uso</small>
                    </div>
                    <div class="metric-card">
                        <h3>Promedio Diario</h3>
                        <p>{data['average_daily_usage']:.2f} {data['unit']}</p>
                        <small>Uso promedio por día</small>
                    </div>
                    <div class="metric-card">
                        <h3>Uso Máximo</h3>
                        <p>{data['max_daily_usage']:.2f} {data['unit']}</p>
                        <small>Pico histórico diario</small>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-container">
                        {usage_fig.to_html(full_html=False)}
                    </div>
                    <div class="chart-container">
                        {pred_fig.to_html(full_html=False)}
                    </div>
                </div>
            </div>
            """
            ingredient_sections.append(section_html)

        except Exception as e:
            logger.warning(f"Could not generate visualizations for {data['ingredient_name']}: {str(e)}")
            continue

    # Combine all sections into a dashboard
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard de Análisis de Inventario</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .ingredient-section {{
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 32px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .ingredient-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 2px solid #f0f0f0;
            }}
            .ingredient-header h2 {{
                margin: 0;
                color: #2c3e50;
            }}
            .ingredient-unit {{
                color: #7f8c8d;
                font-size: 0.9em;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 120px;
            }}
            .metric-card small {{
                color: #7f8c8d;
                font-size: 0.8em;
                margin-top: 8px;
            }}
            .metric-card h3 {{
                margin: 0 0 8px 0;
                color: #34495e;
                font-size: 0.9em;
            }}
            .metric-card p {{
                margin: 0;
                font-size: 1.2em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .metric-card p.negative {{
                color: #e74c3c;
            }}
            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 24px;
            }}
            .chart-container {{
                background: white;
                padding: 16px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                margin-bottom: 32px;
                text-align: center;
            }}
            .header-metrics {{
                display: flex;
                align-items: center;
                gap: 16px;
            }}
            
            .stock-status {{
                padding: 4px 12px;
                border-radius: 12px;
                color: white;
                font-size: 0.8em;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Dashboard de Análisis de Inventario</h1>
        {''.join(ingredient_sections)}
    </body>
    </html>
    """
    
    return dashboard_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 