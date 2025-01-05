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
                animation_delay += 0.5
                
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
                    animation: typing 2s steps(60, end) forwards;
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

                .typing-animation p:nth-child(1) { animation-delay: 0.1s; }
                .typing-animation p:nth-child(2) { animation-delay: 1.5s; }
                .typing-animation p:nth-child(3) { animation-delay: 3s; }
                .typing-animation p:nth-child(4) { animation-delay: 4.5s; }
                .typing-animation p:nth-child(5) { animation-delay: 6s; }
                .typing-animation h2 { animation-delay: 0.5s; }
                .typing-animation h3 { animation-delay: 2s; }

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
                    animation: fadeInTyping 1s ease forwards;
                }
                
                @keyframes fadeInTyping {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            """
            
            return '\n'.join(formatted_lines)

        formatted_analysis = clean_ai_text(global_analysis['analysis'])
        formatted_recommendations = clean_ai_text(global_analysis['recommendations'])

        # Create global analysis section
        global_analysis_html = f"""
        <div class="global-analysis-section">
            <h2>Análisis Global del Inventario</h2>
            <div class="insights-grid">
                <div class="insight-card analysis">
                    <h4>Análisis General</h4>
                    <div class="insight-content typing-animation">
                        {formatted_analysis}
                    </div>
                </div>
                <div class="insight-card recommendations">
                    <h4>Recomendaciones Estratégicas</h4>
                    <div class="insight-content typing-animation">
                        {formatted_recommendations}
                    </div>
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
        <script>
            // Configuración global de animaciones para Plotly
            window.addEventListener('load', function() {{
                const graphs = document.querySelectorAll('.js-plotly-plot');
                graphs.forEach(graph => {{
                    graph._context.responsive = true;
                    graph._context.displayModeBar = false;
                    
                    // Animar al hacer hover
                    graph.on('plotly_hover', function() {{
                        graph.transition {{
                            duration: 500,
                            easing: 'cubic-in-out'
                        }}
                    }});
                    
                    // Animación inicial
                    setTimeout(() => {{
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
                    }}, 500);
                }});
            }});
        </script>
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
        </style>
    </head>
    <body>
        <h1>Dashboard de Análisis de Inventario</h1>
        {global_analysis_html}
        {''.join(ingredient_sections)}
    </body>
    </html>
    """
    
    return dashboard_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 