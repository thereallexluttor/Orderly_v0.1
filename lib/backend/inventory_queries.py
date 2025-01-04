from supabase import create_client, Client
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json

# Cargar variables de entorno
load_dotenv()

# Configurar cliente Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_inventory_data():
    """
    Obtiene los datos del inventario incluyendo el uso de ingredientes
    Replica exacta de la consulta en inventory_screen.dart
    """
    try:
        print("Iniciando get_inventory_data()...")
        
        print("Ejecutando consulta a Supabase...")
        response = supabase.from_('inventory_table').select('''
            *,
            ingredient_usage_table(
                quantity_used,
                usage_date
            )
        ''').order('ingredient_name').execute()

        print("Consulta ejecutada exitosamente")
        items = response.data
        ingredient_usage = {}

        print("Procesando datos de uso de ingredientes...")
        # Calcular uso total por ingrediente
        for item in items:
            try:
                ingredient_id = item['ingredient_id']
                # Verificar si ingredient_usage_table existe y tiene datos
                usage_list = item.get('ingredient_usage_table', [])
                if usage_list is None:
                    usage_list = []
                
                total_usage = 0
                for usage in usage_list:
                    total_usage += usage['quantity_used']
                
                ingredient_usage[ingredient_id] = total_usage
                
            except Exception as e:
                print(f"Error procesando ingrediente {item.get('ingredient_id', 'desconocido')}: {e}")
                # Si hay error, establecer uso en 0
                ingredient_id = item.get('ingredient_id')
                if ingredient_id:
                    ingredient_usage[ingredient_id] = 0

        print("\n=== Datos del Inventario ===")
        print(f"Total de ingredientes: {len(items)}")
        
        print("Calculando stocks disponibles...")
        for item in items:
            try:
                ingredient_id = item['ingredient_id']
                # Obtener uso del ingrediente, si no existe usar 0
                total_usage = ingredient_usage.get(ingredient_id, 0)
                available_stock = item['total_stock'] - total_usage
                
                print(f"\nIngrediente: {item['ingredient_name']}")
                print(f"ID: {ingredient_id}")
                print(f"Stock inicial: {item['total_stock']} {item['unit']}")
                print(f"Stock disponible: {abs(available_stock)} {item['unit']}")
                print(f"Uso total: {total_usage} {item['unit']}")
            except Exception as e:
                print(f"Error mostrando datos del ingrediente {item.get('ingredient_id', 'desconocido')}: {e}")

        return items, ingredient_usage

    except Exception as e:
        print(f"Error general en get_inventory_data(): {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return [], {}

def get_ingredient_usage(ingredient_id: int, current_stock: float):
    """
    Obtiene el historial de uso de un ingrediente específico
    Replica exacta de la consulta en inventory_analytics.py
    """
    try:
        print(f"\nIniciando get_ingredient_usage() para ingrediente {ingredient_id}...")
        
        print("Ejecutando consulta de uso...")
        response = supabase.table("ingredient_usage_table") \
            .select("quantity_used, usage_date") \
            .eq("ingredient_id", ingredient_id) \
            .execute()

        usage_data = response.data
        print(f"Datos obtenidos: {len(usage_data)} registros")

        if not usage_data:
            print(f"\nNo se encontraron datos de uso para el ingrediente {ingredient_id}")
            return []

        print("Procesando datos con pandas...")
        try:
            # Convertir a DataFrame para mejor análisis
            df = pd.DataFrame(usage_data)
            df['usage_date'] = pd.to_datetime(df['usage_date'])
            
            # Agrupar por fecha para obtener uso diario
            daily_usage = df.groupby('usage_date')['quantity_used'].sum()

            print("Análisis completado exitosamente")
            print(f"\n=== Uso del Ingrediente {ingredient_id} ===")
            print(f"Stock actual: {current_stock}")
            print(f"Total de registros: {len(usage_data)}")
            print(f"Uso total: {df['quantity_used'].sum()}")
            print(f"Promedio diario: {daily_usage.mean():.2f}")
            print(f"Máximo uso diario: {daily_usage.max()}")
            print("\nRegistros de uso más recientes:")
            print(df.tail().to_string())

        except Exception as e:
            print(f"Error en el procesamiento de datos con pandas: {e}")
            print(f"Tipo de error: {type(e).__name__}")

        return usage_data

    except Exception as e:
        print(f"Error general en get_ingredient_usage(): {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return []

def generate_inventory_report(items, ingredient_usage):
    """
    Genera un informe detallado del inventario para análisis de AI
    """
    try:
        print("\n========= REPORTE DE INVENTARIO PARA ANÁLISIS DE AI =========\n")
        
        # Estadísticas generales
        print("=== ESTADÍSTICAS GENERALES ===")
        print(f"Total de ingredientes en inventario: {len(items)}")
        total_stock_value = sum(item['total_stock'] for item in items)
        print(f"Stock total acumulado: {total_stock_value}")
        
        # Análisis por unidades
        print("\n=== ANÁLISIS POR UNIDADES DE MEDIDA ===")
        units_count = {}
        for item in items:
            unit = item['unit']
            units_count[unit] = units_count.get(unit, 0) + 1
        for unit, count in units_count.items():
            print(f"Ingredientes medidos en {unit}: {count}")

        # Top ingredientes por uso
        print("\n=== TOP 10 INGREDIENTES MÁS UTILIZADOS ===")
        sorted_usage = sorted(ingredient_usage.items(), key=lambda x: x[1], reverse=True)
        for ingredient_id, usage in sorted_usage[:10]:
            item = next((item for item in items if item['ingredient_id'] == ingredient_id), None)
            if item:
                print(f"- {item['ingredient_name']}: {usage} {item['unit']}")

        # Análisis de stock crítico
        print("\n=== ANÁLISIS DE STOCK CRÍTICO ===")
        critical_stock = []
        for item in items:
            ingredient_id = item['ingredient_id']
            total_usage = ingredient_usage.get(ingredient_id, 0)
            available_stock = item['total_stock'] - total_usage
            
            # Consideramos crítico si el stock disponible es menor al 20% del stock inicial
            if available_stock < (item['total_stock'] * 0.2):
                critical_stock.append({
                    'name': item['ingredient_name'],
                    'available': available_stock,
                    'unit': item['unit'],
                    'usage_rate': total_usage
                })
        
        print(f"Ingredientes en estado crítico: {len(critical_stock)}")
        for item in critical_stock:
            print(f"- {item['name']}: {item['available']} {item['unit']} disponibles")

        # Análisis temporal de uso
        print("\n=== ANÁLISIS TEMPORAL DE USO ===")
        for item in items[:5]:  # Analizamos los primeros 5 ingredientes como muestra
            ingredient_id = item['ingredient_id']
            usage_data = get_ingredient_usage(ingredient_id, 0)
            
            if usage_data:
                df = pd.DataFrame(usage_data)
                df['usage_date'] = pd.to_datetime(df['usage_date'])
                daily_usage = df.groupby('usage_date')['quantity_used'].sum()
                
                print(f"\nIngrediente: {item['ingredient_name']}")
                print(f"Días con registros de uso: {len(daily_usage)}")
                print(f"Uso promedio diario: {daily_usage.mean():.2f} {item['unit']}")
                print(f"Día de mayor uso: {daily_usage.idxmax().strftime('%Y-%m-%d')} ({daily_usage.max()} {item['unit']})")
                
                # Tendencia de uso (últimos 7 días vs promedio general)
                recent_avg = daily_usage.tail(7).mean()
                total_avg = daily_usage.mean()
                trend = "AUMENTANDO" if recent_avg > total_avg else "DISMINUYENDO"
                print(f"Tendencia de uso: {trend} (Reciente: {recent_avg:.2f} vs Promedio: {total_avg:.2f})")

        # Datos para modelo predictivo
        print("\n=== DATOS PARA MODELO PREDICTIVO ===")
        print("Variables disponibles para análisis:")
        print("- Histórico de uso diario por ingrediente")
        print("- Patrones de uso temporal")
        print("- Tasas de consumo")
        print("- Niveles de stock crítico")
        print("- Correlaciones entre ingredientes")
        
        return {
            "total_ingredients": len(items),
            "total_stock_value": total_stock_value,
            "units_distribution": units_count,
            "top_used_ingredients": sorted_usage[:10],
            "critical_stock_items": critical_stock,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error generando reporte: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return None

def generate_ingredient_history_report(items, ingredient_usage):
    """
    Genera un reporte histórico detallado para cada ingrediente
    """
    try:
        print("\n=== GENERANDO HISTÓRICO DE USO POR INGREDIENTE ===")
        
        all_ingredients_history = {}
        
        for item in items:
            try:
                ingredient_id = item['ingredient_id']
                ingredient_name = item['ingredient_name']
                unit = item['unit']
                total_stock = item['total_stock']
                safe_factor = item['safe_factor']
                
                print(f"\nProcesando ingrediente: {ingredient_name} (ID: {ingredient_id})")
                
                # Obtener historial de uso
                usage_data = get_ingredient_usage(ingredient_id, 0)
                
                if usage_data:
                    df = pd.DataFrame(usage_data)
                    df['usage_date'] = pd.to_datetime(df['usage_date'])
                    daily_usage = df.groupby('usage_date')['quantity_used'].sum()
                    
                    # Crear diccionario con el historial del ingrediente
                    ingredient_history = {
                        'ingredient_name': ingredient_name,
                        'ingredient_id': ingredient_id,
                        'unit': unit,
                        'total_stock': float(total_stock),
                        'safe_factor': float(safe_factor),
                        'usage_history': {
                            str(date.date()): float(quantity)
                            for date, quantity in daily_usage.items()
                        },
                        'total_usage': float(daily_usage.sum()),
                        'average_daily_usage': float(daily_usage.mean()),
                        'max_daily_usage': float(daily_usage.max()),
                        'days_with_usage': len(daily_usage),
                        'first_usage_date': str(daily_usage.index.min().date()),
                        'last_usage_date': str(daily_usage.index.max().date())
                    }
                    
                    # Calcular stock actual y estado
                    current_stock = total_stock - float(daily_usage.sum())
                    safe_threshold = total_stock * (safe_factor / 100)
                    
                    # Agregar información de estado del stock
                    ingredient_history['current_stock'] = float(current_stock)
                    ingredient_history['safe_threshold'] = float(safe_threshold)
                    ingredient_history['stock_status'] = (
                        'critical' if current_stock < safe_threshold
                        else 'warning' if current_stock < (total_stock * 0.3)
                        else 'good'
                    )
                    
                    all_ingredients_history[ingredient_id] = ingredient_history
                    
                    print(f"✓ Historial procesado: {len(daily_usage)} días de uso registrados")
                    print(f"  Stock actual: {current_stock:.2f} {unit}")
                    print(f"  Límite seguro ({safe_factor}%): {safe_threshold:.2f} {unit}")
                    print(f"  Estado: {ingredient_history['stock_status'].upper()}")
                else:
                    print("✗ No se encontraron datos de uso")
                    
            except Exception as e:
                print(f"Error procesando ingrediente {item.get('ingredient_name', 'desconocido')}: {e}")
                continue
        
        # Guardar el historial en un archivo JSON
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "lib", "backend", "inventory_data",
            datetime.now().strftime('%Y-%m-%d')
        )
        os.makedirs(report_path, exist_ok=True)
        report_file = os.path.join(report_path, f"ingredients_history_{timestamp}.json")
        
        print(f"\nGuardando historial en: {report_file}")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(all_ingredients_history, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Historial guardado exitosamente")
        
        return all_ingredients_history
        
    except Exception as e:
        print(f"Error generando historial: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return None

async def get_detailed_ingredient_data(ingredient_id: int) -> dict:
    """Obtiene datos detallados de un ingrediente específico"""
    try:
        # Consulta para obtener el historial completo del ingrediente
        history = await supabase.table('ingredient_history')\
            .select('*')\
            .eq('ingredient_id', ingredient_id)\
            .order('created_at.desc')\
            .execute()

        # Consulta para obtener datos de uso en recetas
        recipe_usage = await supabase.table('recipe_ingredients')\
            .select('*,recipes(*)')\
            .eq('ingredient_id', ingredient_id)\
            .execute()

        # Consulta para obtener datos de proveedores
        suppliers = await supabase.table('ingredient_suppliers')\
            .select('*')\
            .eq('ingredient_id', ingredient_id)\
            .execute()

        return {
            "history": history.data,
            "recipe_usage": recipe_usage.data,
            "suppliers": suppliers.data
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos detallados: {str(e)}")
        return {}

def main():
    print("=== Iniciando programa principal ===")
    print("Ejecutando consultas a Supabase...")
    
    try:
        # Obtener datos del inventario
        inventory_items, ingredient_usage = get_inventory_data()
        
        if inventory_items:
            # Generar historial detallado de uso
            generate_ingredient_history_report(inventory_items, ingredient_usage)
        else:
            print("No se encontraron items en el inventario")
            
    except Exception as e:
        print(f"Error en main(): {e}")
        print(f"Tipo de error: {type(e).__name__}")

if __name__ == "__main__":
    main() 