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

@app.get("/ingredient-usage/{ingredient_id}")
async def get_ingredient_usage(ingredient_id: int, request: Request):
    try:
        # Obtener datos de uso del ingrediente
        response = supabase.table("ingredient_usage_table") \
            .select("quantity_used, usage_date") \
            .eq("ingredient_id", ingredient_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No se encontraron datos")

        # Convertir a DataFrame
        df = pd.DataFrame(response.data)
        df['usage_date'] = pd.to_datetime(df['usage_date'])

        # Gráfico de uso por día
        daily_usage = df.groupby('usage_date')['quantity_used'].sum().reset_index()
        
        fig1 = px.line(daily_usage, 
                      x='usage_date', 
                      y='quantity_used',
                      title='Uso Diario del Ingrediente',
                      labels={'usage_date': 'Fecha', 'quantity_used': 'Cantidad Usada'})
        
        # Gráfico de uso por semana (pie)
        df['week'] = df['usage_date'].dt.strftime('%Y-%U')
        weekly_usage = df.groupby('week')['quantity_used'].sum()
        
        fig2 = px.pie(values=weekly_usage.values, 
                     names=weekly_usage.index,
                     title='Distribución de Uso por Semana')

        # Prepare data for Prophet
        prophet_df = daily_usage.rename(columns={'usage_date': 'ds', 'quantity_used': 'y'})
        
        # Create and fit Prophet model
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(prophet_df)

        # Create future dates for prediction (change from 7 to 3 days)
        future_dates = model.make_future_dataframe(periods=3)
        forecast = model.predict(future_dates)

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

        # Update stats with 3-day predictions
        stats = {
            'total_usage': float(df['quantity_used'].sum()),
            'avg_daily_usage': float(daily_usage['quantity_used'].mean()),
            'max_daily_usage': float(daily_usage['quantity_used'].max()),
            'total_days': len(daily_usage),
            'predicted_usage_3days': float(forecast['yhat'].tail(3).sum()),  # Changed from 7 to 3
            'predicted_avg_daily': float(forecast['yhat'].tail(3).mean())    # Changed from 7 to 3
        }

        # Verificar si la solicitud viene de un navegador
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            # Devolver página HTML con las gráficas
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
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #333;
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .stats-container {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }}
                    .stat-card {{
                        background-color: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        text-align: center;
                    }}
                    .stat-value {{
                        font-size: 24px;
                        font-weight: 600;
                        color: #007bff;
                    }}
                    .stat-label {{
                        color: #666;
                        margin-top: 5px;
                    }}
                    .charts-container {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                        gap: 20px;
                    }}
                    .chart {{
                        min-height: 400px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Análisis de Uso del Ingrediente</h1>
                    
                    <div class="stats-container">
                        <div class="stat-card">
                            <div class="stat-value">{stats['total_usage']:.2f}</div>
                            <div class="stat-label">Uso Total</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['avg_daily_usage']:.2f}</div>
                            <div class="stat-label">Promedio Diario</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['max_daily_usage']:.2f}</div>
                            <div class="stat-label">Máximo Diario</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['total_days']}</div>
                            <div class="stat-label">Días Registrados</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['predicted_usage_3days']:.2f}</div>
                            <div class="stat-label">Uso Predicho (3 días)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats['predicted_avg_daily']:.2f}</div>
                            <div class="stat-label">Promedio Diario Predicho</div>
                        </div>
                    </div>

                    <div class="charts-container">
                        <div class="chart" id="daily-chart"></div>
                        <div class="chart" id="weekly-chart"></div>
                        <div class="chart" id="prediction-chart"></div>
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
        
        # Si no es una solicitud del navegador, devolver JSON como antes
        return {
            'daily_usage_chart': fig1.to_json(),
            'weekly_usage_chart': fig2.to_json(),
            'prediction_chart': fig3.to_json(),
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 