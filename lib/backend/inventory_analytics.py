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
async def get_ingredient_usage(ingredient_id: int, current_stock: float):
    try:
        logger.info(f"Obteniendo datos para ingredient_id: {ingredient_id}")
        
        # Obtener datos del inventario
        inventory_items, ingredient_usage = get_inventory_data()
        
        # Buscar el ingrediente específico
        item = next((item for item in inventory_items if item['ingredient_id'] == ingredient_id), None)
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el ingrediente con ID {ingredient_id}"
            )

        # Obtener el historial de uso
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
async def get_inventory_report(request: Request):
    try:
        logger.info("Iniciando generación de reporte de inventario...")
        
        # Obtener datos del inventario usando las funciones de queries
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 