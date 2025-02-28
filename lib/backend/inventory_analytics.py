from fastapi import FastAPI, HTTPException, Path, Request
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
from inventory_queries import (
    get_inventory_data, 
    get_ingredient_usage,
    generate_ingredient_history_report, 
    generate_inventory_report,
    get_detailed_ingredient_data
)
from inventory_multi_agent import InventoryAnalysisSystem
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
from typing import Dict, Any

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

inventory_ai = InventoryAnalysisSystem()

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

def predict_safety_coefficients(ingredients_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Predice coeficientes de seguridad óptimos basados en patrones históricos
    """
    try:
        predictions = {}
        
        for ingredient_id, data in ingredients_data.items():
            # Preparar características para el modelo
            features = []
            usage_history = data.get('usage_history', {})
            
            if not usage_history:
                continue
                
            # Convertir historial a series temporales
            dates = sorted(usage_history.keys())
            usage_values = [usage_history[date] for date in dates]
            
            # Calcular características
            avg_usage = np.mean(usage_values)
            std_usage = np.std(usage_values)
            max_usage = np.max(usage_values)
            current_stock = data.get('current_stock', 0)
            total_stock = data.get('total_stock', 0)
            stock_ratio = current_stock / total_stock if total_stock > 0 else 0
            
            # Crear vector de características
            X = np.array([[
                avg_usage,
                std_usage,
                max_usage,
                stock_ratio,
                len(usage_values)  # número de días con datos
            ]])
            
            # Normalizar características
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Entrenar modelo
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Generar datos sintéticos para entrenamiento basados en patrones observados
            synthetic_X = []
            synthetic_y = []
            
            for _ in range(100):
                rand_avg = np.random.normal(avg_usage, std_usage/2)
                rand_std = std_usage * np.random.uniform(0.8, 1.2)
                rand_max = max_usage * np.random.uniform(0.9, 1.1)
                rand_ratio = np.random.uniform(0.1, 1.0)
                rand_days = np.random.randint(10, len(usage_values) + 20)
                
                synthetic_X.append([rand_avg, rand_std, rand_max, rand_ratio, rand_days])
                
                # Calcular coeficiente de seguridad sintético
                safety_coef = 100 * (1.5 * rand_std / rand_avg) * (1 - rand_ratio)
                safety_coef = min(max(safety_coef, 10), 50)  # limitar entre 10% y 50%
                synthetic_y.append(safety_coef)
            
            # Entrenar modelo con datos sintéticos
            model.fit(synthetic_X, synthetic_y)
            
            # Predecir coeficiente de seguridad
            predicted_coef = model.predict(X_scaled)[0]
            
            # Ajustar predicción a rango válido
            predicted_coef = min(max(predicted_coef, 10), 50)
            predictions[ingredient_id] = predicted_coef
            
        return predictions
        
    except Exception as e:
        logger.error(f"Error predicting safety coefficients: {str(e)}")
        return {}

@app.get("/ingredient-usage/{ingredient_id}")
async def get_ingredient_usage_endpoint(ingredient_id: int, current_stock: float):
    try:
        logger.info(f"Obteniendo datos para ingredient_id: {ingredient_id}")
        
        # Obtener datos detallados que incluyen el historial de uso
        detailed_data = await get_detailed_ingredient_data(ingredient_id)
        
        # Obtener datos del inventario
        inventory_items, ingredient_usage = get_inventory_data()
        item = next((item for item in inventory_items if item['ingredient_id'] == ingredient_id), None)
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el ingrediente con ID {ingredient_id}"
            )

        # Obtener el historial de uso del formato correcto del JSON
        usage_history = {}
        if detailed_data and isinstance(detailed_data, dict):
            ingredient_data = detailed_data.get(str(ingredient_id), {})
            
            # Actualizar el item con los campos exactos del JSON
            item.update({
                'ingredient_name': ingredient_data.get('ingredient_name'),
                'ingredient_id': ingredient_data.get('ingredient_id'),
                'unit': ingredient_data.get('unit'),
                'total_stock': ingredient_data.get('total_stock'),
                'safe_factor': ingredient_data.get('safe_factor'),
                'usage_history': ingredient_data.get('usage_history', {}),
                'total_usage': ingredient_data.get('total_usage'),
                'average_daily_usage': ingredient_data.get('average_daily_usage'),
                'max_daily_usage': ingredient_data.get('max_daily_usage'),
                'days_with_usage': ingredient_data.get('days_with_usage'),
                'first_usage_date': ingredient_data.get('first_usage_date'),
                'last_usage_date': ingredient_data.get('last_usage_date'),
                'current_stock': ingredient_data.get('current_stock'),
                'safe_threshold': ingredient_data.get('safe_threshold'),
                'stock_status': ingredient_data.get('stock_status')
            })
            
        logger.info(f"Historial de uso encontrado para ingrediente {ingredient_id}: {len(item.get('usage_history', {}))} registros")
        
        # Obtener datos de uso
        usage_data = get_ingredient_usage(ingredient_id, current_stock)
        
        if not usage_data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron datos de uso para el ingrediente {ingredient_id}"
            )

        # Añadir predicciones de IA
        safety_coefficients = predict_safety_coefficients({str(ingredient_id): item})
        predicted_safety_coef = safety_coefficients.get(str(ingredient_id))
        
        if predicted_safety_coef:
            item['predicted_safety_factor'] = predicted_safety_coef
            
        return {
            "status": "success",
            "data": {
                "ingredient": item,
                "usage_data": usage_data,
                "current_stock": current_stock,
                "total_usage": ingredient_usage.get(ingredient_id, 0),
                "ai_predictions": {
                    "predicted_safety_factor": predicted_safety_coef,
                    "confidence_score": model.score(synthetic_X, synthetic_y) if 'model' in locals() else None
                }
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
    # Add global AI analysis at the top
    try:
        # Prepare context with all ingredients data
        all_ingredients_context = {
            "ingredients": [
                {
                    "ingredient_name": data['ingredient_name'],
                    "current_stock": data['current_stock'],
                    "total_stock": data['total_stock'],
                    "unit": data['unit'],
                    "safe_factor": data['safe_factor'],
                    "history": [
                        {"created_at": date, "quantity": usage, "type": "usage"} 
                        for date, usage in data['usage_history'].items()
                    ],
                    "average_daily_usage": data['average_daily_usage'],
                    "max_daily_usage": data['max_daily_usage'],
                    "stock_status": data['stock_status']
                }
                for ingredient_id, data in ingredients_data.items()
            ]
        }

        # Get global AI analysis - solo una vez para todos los ingredientes
        inventory_ai = InventoryAnalysisSystem()
        global_analysis = inventory_ai.analyze_inventory_global(all_ingredients_context)

        # Format AI insights
        def clean_ai_text(text):
            # Remove emoji characters
            cleaned = ''.join(char for char in text if not (0x1F300 <= ord(char) <= 0x1F9FF))
            
            # Format markdown-style headers and text
            lines = cleaned.split('\n')
            formatted_lines = []
            in_table = False
            table_html = []
            
            # Añadir contador para los delays de animación
            animation_delay = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Handle table formatting
                if '|' in line:
                    if not in_table:
                        in_table = True
                        table_html = ['<div class="table-container"><table class="analysis-table">']
                    
                    # Skip separator lines (|----|)
                    if line.replace('|', '').replace('-', '').strip() == '':
                        continue
                        
                    # Process table row
                    cells = [cell.strip() for cell in line.split('|')]
                    cells = [cell for cell in cells if cell]  # Remove empty cells
                    
                    is_header = any('---' in cell for cell in cells)
                    if not is_header:
                        row_html = '<tr>'
                        for cell in cells:
                            # Check if it's the header row (usually the first row)
                            if table_html[-1] == '<div class="table-container"><table class="analysis-table">':
                                row_html += f'<th>{cell}</th>'
                            else:
                                # Add color coding for risk levels
                                if 'CRÍTICO' in cell:
                                    row_html += f'<td class="risk-critical">{cell}</td>'
                                elif 'PRECAUCIÓN' in cell:
                                    row_html += f'<td class="risk-warning">{cell}</td>'
                                else:
                                    row_html += f'<td>{cell}</td>'
                        row_html += '</tr>'
                        table_html.append(row_html)
                    continue
                    
                elif in_table:
                    # End table processing
                    in_table = False
                    table_html.append('</table></div>')
                    formatted_lines.append('\n'.join(table_html))
                    table_html = []
                    
                # Format headers and text with animation delays
                if '**' in line:
                    if line.startswith('**') and line.endswith('**'):
                        line = f'<h2 class="animated-text" style="animation-delay: {animation_delay}s">{line.replace("**", "")}</h2>'
                    elif line.startswith('* **') and line.endswith('**'):
                        line = f'<h3 class="animated-text" style="animation-delay: {animation_delay}s">{line.replace("* **", "").replace("**", "")}</h3>'
                    elif '*' in line:
                        while '*' in line:
                            line = line.replace('*', '<em>', 1).replace('*', '</em>', 1)
                        line = f'<p class="animated-text" style="animation-delay: {animation_delay}s">{line}</p>'
                elif line.startswith('##'):
                    line = f'<h3 class="animated-text" style="animation-delay: {animation_delay}s">{line.replace("##", "").strip()}</h3>'
                elif line.startswith('#'):
                    line = f'<h2 class="animated-text" style="animation-delay: {animation_delay}s">{line.replace("#", "").strip()}</h2>'
                elif line[0].isdigit() and line[1] == '.':
                    number = line[0]
                    rest = line[2:].strip()
                    line = f'<p class="animated-text" style="animation-delay: {animation_delay}s"><strong>{number}.</strong> {rest}</p>'
                else:
                    line = f'<p class="animated-text" style="animation-delay: {animation_delay}s">{line}</p>'
                
                # Incrementar el delay para la siguiente línea
                animation_delay += 0.8
                
                formatted_lines.append(line)
            
            # Handle case where text ends with a table
            if in_table:
                table_html.append('</table></div>')
                formatted_lines.append('\n'.join(table_html))
            
            # Add these styles to the additional_styles string
            additional_styles = """
                .table-container {
                    margin: 20px 0;
                    overflow-x: auto;
                }
                
                .analysis-table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border: 1px solid #e1e1e1;
                }
                
                .analysis-table th,
                .analysis-table td {
                    padding: 12px;
                    text-align: left;
                    border: 1px solid #e1e1e1;
                }
                
                .analysis-table th {
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #2c3e50;
                    border-bottom: 2px solid #ddd;
                }
                
                .analysis-table tr:hover {
                    background: #f8f9fa;
                }
                
                .analysis-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                .risk-critical {
                    color: #e74c3c;
                    font-weight: 600;
                }
                
                .risk-warning {
                    color: #f39c12;
                    font-weight: 600;
                }
                
                .bold-header {
                    font-weight: 700;
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    display: inline-block;
                    margin-bottom: 16px;
                }
                
                em {
                    font-style: italic;
                    color: #34495e;
                    font-weight: 500;
                }

                /* Animación de escritura estilo ChatGPT */
                .typing-animation {
                    width: 100%;
                }

                .typing-animation p,
                .typing-animation h2,
                .typing-animation h3 {
                    overflow: hidden;
                    white-space: pre-wrap;
                    border-right: 2px solid transparent;
                    margin: 0;
                    display: inline-block;
                    width: 0;
                    animation: typing 3s steps(60, end) forwards;
                }

                .typing-animation p:not(:last-child),
                .typing-animation h2:not(:last-child),
                .typing-animation h3:not(:last-child) {
                    margin-bottom: 0.5em;
                }

                @keyframes typing {
                    from { 
                        width: 0;
                        opacity: 0;
                    }
                    to { 
                        width: 100%;
                        opacity: 1;
                    }
                }

                .typing-animation p:nth-child(1) { animation-delay: 0.2s; }
                .typing-animation p:nth-child(2) { animation-delay: 2.0s; }
                .typing-animation p:nth-child(3) { animation-delay: 3.8s; }
                .typing-animation p:nth-child(4) { animation-delay: 5.6s; }
                .typing-animation p:nth-child(5) { animation-delay: 7.4s; }
                .typing-animation h2 { animation-delay: 1.0s; }
                .typing-animation h3 { animation-delay: 2.8s; }

                /* Cursor parpadeante */
                .typing-cursor {
                    display: inline-block;
                    width: 2px;
                    height: 1em;
                    background: #3498db;
                    margin-left: 2px;
                    animation: blink 1s step-end infinite;
                }

                @keyframes blink {
                    from, to { opacity: 1; }
                    50% { opacity: 0; }
                }

                /* Asegurarse que el contenedor tenga el espacio adecuado */
                .insight-content {
                    min-height: 200px;
                    position: relative;
                }

                .animated-text {
                    opacity: 0;
                    animation: fadeInTyping 1.5s ease forwards;
                }
                
                @keyframes fadeInTyping {
                    0% {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    50% {
                        opacity: 0.5;
                    }
                    100% {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            """
            
            return '\n'.join(formatted_lines)

        formatted_analysis = clean_ai_text(global_analysis['analysis'])

        # Create global analysis section
        global_analysis_html = f"""
        <div class="global-analysis-section">
            <h2>Análisis Global del Inventario</h2>
            <div class="insight-card analysis">
                <h4>Análisis General</h4>
                <div class="insight-content typing-animation">
                    {formatted_analysis}
                </div>
            </div>
        </div>
        """
    except Exception as e:
        logger.error(f"Error generating global analysis: {str(e)}")
        global_analysis_html = "<div>Error generating global analysis</div>"

    # Continue with individual ingredient sections (solo gráficas y métricas, sin análisis de IA)
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
            pred_fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Predicción'))
            pred_fig.update_layout(title="Pronóstico de Uso")

            # Calculate metrics
            safe_threshold = data['total_stock'] * (data['safe_factor'] / 100)
            current_stock = data['current_stock']
            stock_percentage = (current_stock / data['total_stock']) * 100
            days_until_empty = current_stock / data['average_daily_usage'] if data['average_daily_usage'] > 0 else float('inf')
            
            status_color = (
                '#e74c3c' if current_stock < safe_threshold else
                '#f1c40f' if current_stock < (data['total_stock'] * 0.3) else
                '#2ecc71'
            )

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

    # Add these styles to the CSS section in the HTML
    additional_styles = """
        .ai-insights {
            margin-top: 32px;
            padding-top: 24px;
            border-top: 2px solid #f0f0f0;
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-top: 16px;
        }
        
        .insight-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .insight-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .insight-card h4 {
            color: #2c3e50;
            margin: 0 0 16px 0;
            font-size: 1.1em;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 8px;
            display: inline-block;
        }
        
        .insight-content {
            color: #34495e;
            font-size: 0.95em;
            line-height: 1.6;
            font-style: italic;
            font-weight: 400;
        }
        
        .insight-content h2,
        .insight-content h3,
        .insight-content strong {
            font-style: normal;
        }
        
        .insight-content em {
            font-style: italic;
            color: #34495e;
            font-weight: 500;
        }
        
        .insight-content .analysis-table {
            font-style: normal;
        }
        
        .insight-content p {
            margin: 0 0 12px 0;
        }
        
        .insight-content p:last-child {
            margin-bottom: 0;
        }
        
        .insight-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .insight-card h4 {
            color: #2c3e50;
            margin: 0 0 16px 0;
            font-size: 1.2em;
            font-weight: 600;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 8px;
            display: inline-block;
        }
        
        .analysis h4 {
            border-color: #3498db;
        }
        
        .recommendations h4 {
            border-color: #2ecc71;
        }
        
        .insight-content h2 {
            font-size: 1.3em;
            color: #2c3e50;
            margin: 16px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }
        
        .insight-content h3 {
            font-size: 1.1em;
            color: #34495e;
            margin: 14px 0 10px 0;
        }
        
        .insight-content p {
            margin: 8px 0;
            line-height: 1.6;
        }
        
        .insight-content strong {
            color: #2c3e50;
            font-weight: 600;
        }
        
        .insight-content p strong {
            color: #e74c3c;
        }
    """

    # Add the additional_styles to your existing dashboard HTML template
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
                transition: all 0.3s ease-in-out;
            }}
            .chart-container:hover {{
                transform: translateY(-5px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
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
            {additional_styles}

            /* Add only loading and animation related styles */
            .loading-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #fff;
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                transition: opacity 0.5s ease-out;
            }}

            .loading-overlay.hidden {{
                opacity: 0;
                pointer-events: none;
            }}

            .loader {{
                width: 48px;
                height: 48px;
                border: 5px solid #3498db;
                border-bottom-color: transparent;
                border-radius: 50%;
                animation: rotation 1s linear infinite;
            }}

            @keyframes rotation {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}

            .content {{
                opacity: 0;
                transition: opacity 0.5s ease-in;
            }}

            .content.visible {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <!-- Add loading overlay -->
        <div class="loading-overlay">
            <div class="loader"></div>
        </div>

        <!-- Wrap existing content -->
        <div class="content">
            <h1>Dashboard de Análisis de Inventario</h1>
            {global_analysis_html}
            {''.join(ingredient_sections)}
        </div>

        <script>
            // Function to check if all Plotly graphs are rendered
            function areAllGraphsRendered() {{
                const graphs = document.querySelectorAll('.js-plotly-plot');
                // Si no hay gráficos, consideramos que está listo
                if (graphs.length === 0) return true;
                
                return Array.from(graphs).every(graph => {{     
                    // Verificar si el gráfico está completamente renderizado
                    return graph.querySelector('.plot-container') !== null &&
                           graph.querySelector('.main-svg') !== null;
                }});
            }}

            // Function to show content and hide loader
            function showContent() {{
                document.querySelector('.loading-overlay').classList.add('hidden');
                document.querySelector('.content').classList.add('visible');
                
                // Start text animations after content is visible
                startTextAnimations();
            }}

            // Function to handle text animations
            function startTextAnimations() {{
                const animatedTexts = document.querySelectorAll('.animated-text');
                animatedTexts.forEach((element, index) => {{
                    element.style.opacity = '0';
                    element.style.transform = 'translateY(20px)';
                    
                    setTimeout(() => {{
                        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                        element.style.opacity = '1';
                        element.style.transform = 'translateY(0)';
                    }}, index * 100);
                }});
            }}

            // Wait for everything to load
            window.addEventListener('load', function() {{
                let attempts = 0;
                const maxAttempts = 50; // 5 segundos máximo (50 * 100ms)

                // Check if Plotly is loaded and graphs are rendered
                const checkGraphs = setInterval(() => {{
                    attempts++;
                    
                    // Si los gráficos están renderizados o alcanzamos el máximo de intentos
                    if (areAllGraphsRendered() || attempts >= maxAttempts) {{
                        clearInterval(checkGraphs);
                        console.log('Graphs loaded or timeout reached');
                        showContent();
                    }}
                }}, 100);

                // Configure Plotly graphs
                const graphs = document.querySelectorAll('.js-plotly-plot');
                graphs.forEach(graph => {{
                    if (graph && graph._context) {{
                        graph._context.responsive = true;
                        graph._context.displayModeBar = false;
                        
                        graph.on('plotly_hover', function() {{
                            graph.transition({{
                                duration: 500,
                                easing: 'cubic-in-out'
                            }});
                        }});
                    }}
                }});

                // Intentar animar los gráficos después de un breve retraso
                setTimeout(() => {{
                    graphs.forEach(graph => {{
                        if (graph && graph.data) {{
                            try {{
                                Plotly.animate(graph, {{
                                    data: graph.data,
                                    traces: [0],
                                    layout: {{}},
                                }}, {{
                                    transition: {{
                                        duration: 1000,
                                        easing: 'cubic-in-out'
                                    }},
                                    frame: {{
                                        duration: 1000,
                                        redraw: true
                                    }}
                                }});
                            }} catch (e) {{
                                console.log('Animation error:', e);
                            }}
                        }}
                    }});
                }}, 1000);
            }});
        </script>
    </body>
    </html>
    """
    
    # Generar tabla de predicciones de IA
    safety_coefficients = predict_safety_coefficients(ingredients_data)
    
    ai_predictions_table = """
    <div class="ai-predictions-section">
        <h2>Predicciones de IA - Coeficientes de Seguridad</h2>
        <div class="table-container">
            <table class="analysis-table">
                <thead>
                    <tr>
                        <th>Ingrediente</th>
                        <th>Coeficiente Actual</th>
                        <th>Coeficiente Recomendado</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for ingredient_id, data in ingredients_data.items():
        predicted_coef = safety_coefficients.get(str(ingredient_id))
        current_coef = data.get('safe_factor', 0)
        
        if predicted_coef:
            difference = abs(predicted_coef - current_coef)
            status = (
                '<span class="status-critical">Ajuste Necesario</span>' if difference > 10
                else '<span class="status-warning">Revisar</span>' if difference > 5
                else '<span class="status-good">Óptimo</span>'
            )
            
            ai_predictions_table += f"""
                <tr>
                    <td>{data['ingredient_name']}</td>
                    <td>{current_coef:.1f}%</td>
                    <td>{predicted_coef:.1f}%</td>
                    <td>{status}</td>
                </tr>
            """
    
    ai_predictions_table += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    # Add these styles to the additional_styles
    additional_styles += """
        .ai-predictions-section {
            margin: 32px 0;
            padding: 24px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .status-critical {
            color: #e74c3c;
            font-weight: 600;
        }
        
        .status-warning {
            color: #f39c12;
            font-weight: 600;
        }
        
        .status-good {
            color: #2ecc71;
            font-weight: 600;
        }
    """
    
    # Insert the AI predictions table after the global analysis section
    dashboard_html = dashboard_html.replace(
        '{global_analysis_html}',
        f'{global_analysis_html}\n{ai_predictions_table}'
    )
    
    return dashboard_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 