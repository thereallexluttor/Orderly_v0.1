from supabase import create_client, Client
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
import json

# Cargar variables de entorno
load_dotenv()

# Configurar cliente Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Configuración de datos
FOOD_INGREDIENTS = {
    1: [(1, 150.0), (2, 50.0), (3, 30.0)],  # Food 1 usa ingredientes 1, 2, 3
    2: [(6, 70.0), (7, 30.0), (8, 10.0)],   # Food 2 usa ingredientes 6, 7, 8
    3: [(4, 200.0), (5, 50.0)],             # Food 3 usa ingredientes 4, 5
    4: [(9, 250.0), (12, 70.0)],            # Food 4 usa ingredientes 9, 12
    5: [(10, 120.0), (11, 50.0)],           # Food 5 usa ingredientes 10, 11
    6: [(13, 100.0), (14, 40.0)],           # Food 6 usa ingredientes 13, 14
    7: [(19, 120.0), (20, 50.0)],           # Food 7 usa ingredientes 19, 20
    8: [(15, 200.0), (16, 60.0)],           # Food 8 usa ingredientes 15, 16
    9: [(17, 100.0), (18, 40.0)],           # Food 9 usa ingredientes 17, 18
    10: [(15, 200.0), (16, 60.0)]           # Food 10 usa ingredientes 15, 16
}

# Definir patrones de uso por día de la semana (multiplicadores)
WEEKDAY_PATTERNS = {
    0: 0.7,  # Lunes
    1: 0.8,  # Martes
    2: 0.9,  # Miércoles
    3: 1.0,  # Jueves
    4: 1.3,  # Viernes
    5: 1.5,  # Sábado
    6: 1.2   # Domingo
}

FOOD_PRICES = {
    1: 25.00, 2: 18.50, 3: 20.50, 4: 28.75, 5: 12.00,
    6: 20.00, 7: 29.50, 8: 36.60, 9: 12.20, 10: 30.00
}

PAYMENT_METHODS = ['Tarjeta', 'Efectivo']
ORDER_STATUS = ['Completada', 'Pendiente', 'Cancelada']
STATUS_WEIGHTS = [0.7, 0.2, 0.1]  # 70% Completada, 20% Pendiente, 10% Cancelada

NOTES = [
    'Sin cebolla', 'Con extra aguacate', 'Sin salsa picante', 'Con doble carne',
    'Sin pimiento', 'Sin tomate', 'Sin pepinillos', 'Con mayonesa extra',
    'Para llevar', None, None, None  # Más probabilidad de que no haya notas
]

def get_daily_order_count(date):
    """Determina el número de órdenes basado en el día de la semana y patrones"""
    weekday = date.weekday()
    base_orders = random.randint(8, 15)
    return int(base_orders * WEEKDAY_PATTERNS[weekday])

def get_max_ids():
    """Obtiene los IDs máximos actuales de las tablas"""
    try:
        # Obtener máximo order_id
        order_response = supabase.from_('order_table').select('order_id').order('order_id', desc=True).limit(1).execute()
        max_order_id = order_response.data[0]['order_id'] if order_response.data else 0
        
        # Obtener máximo order_item_id
        item_response = supabase.from_('order_items_table').select('order_item_id').order('order_item_id', desc=True).limit(1).execute()
        max_order_item_id = item_response.data[0]['order_item_id'] if item_response.data else 0
        
        # Obtener máximo customer_id
        customer_response = supabase.from_('order_table').select('customer_id').order('customer_id', desc=True).limit(1).execute()
        max_customer_id = customer_response.data[0]['customer_id'] if customer_response.data else 0
        
        return max_order_id + 1, max_order_item_id + 1, max_customer_id + 1
    except Exception as e:
        print(f"Error obteniendo IDs máximos: {e}")
        # Usar valores por defecto altos si hay error
        return 50000, 50000, 50000

def generate_orders(start_date, end_date):
    current_date = start_date
    # Obtener IDs iniciales seguros
    order_id, order_item_id, customer_id = get_max_ids()
    print(f"\nComenzando con IDs:")
    print(f"Order ID inicial: {order_id}")
    print(f"Order Item ID inicial: {order_item_id}")
    print(f"Customer ID inicial: {customer_id}\n")
    
    orders = []
    order_items = []
    ingredient_usage = []
    
    while current_date <= end_date:
        # Generar órdenes basadas en el día de la semana
        num_orders = get_daily_order_count(current_date)
        
        for _ in range(num_orders):
            # Generar hora aleatoria para la orden
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            order_datetime = current_date.replace(hour=hour, minute=minute)
            
            # Generar orden
            status = random.choices(ORDER_STATUS, weights=STATUS_WEIGHTS)[0]
            order = {
                'order_id': order_id,
                'customer_id': customer_id,
                'order_date': order_datetime.isoformat(),
                'order_status': status,
                'payment_method': random.choice(PAYMENT_METHODS),
                'notes': random.choice(NOTES),
                'total_amount': 0
            }
            
            # Generar items de la orden (1-4 items por orden)
            num_items = random.randint(1, 4)
            order_total = 0
            
            for item_num in range(num_items):
                # Añadir variación en la popularidad de los platillos
                food_weights = [random.uniform(0.8, 1.2) for _ in range(10)]
                food_id = random.choices(range(1, 11), weights=food_weights)[0]
                quantity = random.randint(1, 3)
                price = FOOD_PRICES[food_id]
                total_price = price * quantity
                order_total += total_price
                
                order_item = {
                    'order_item_id': order_item_id,
                    'order_id': order_id,
                    'food_id': food_id,
                    'quantity': quantity,
                    'price_per_unit': price,
                    'total_price': total_price
                }
                order_items.append(order_item)
                
                # Generar uso de ingredientes si la orden no está cancelada
                if status != 'Cancelada':
                    # Añadir variación aleatoria en el uso de ingredientes (±10%)
                    variation = random.uniform(0.9, 1.1)
                    for ingredient_id, base_quantity in FOOD_INGREDIENTS[food_id]:
                        ingredient_usage.append({
                            'order_id': order_id,
                            'order_item_id': order_item_id,
                            'food_id': food_id,
                            'ingredient_id': ingredient_id,
                            'quantity_used': base_quantity * quantity * variation,
                            'usage_date': order_datetime.date().isoformat()
                        })
                
                order_item_id += 1
            
            order['total_amount'] = order_total
            orders.append(order)
            
            order_id += 1
            customer_id += 1
        
        # Generar uso adicional de ingredientes para mermas y preparaciones
        if random.random() < 0.3:  # 30% de probabilidad de mermas por día
            for food_id, ingredients in FOOD_INGREDIENTS.items():
                if random.random() < 0.5:  # 50% de probabilidad por platillo
                    for ingredient_id, base_quantity in ingredients:
                        waste_amount = base_quantity * random.uniform(0.05, 0.15)  # 5-15% de merma
                        ingredient_usage.append({
                            'order_id': None,
                            'order_item_id': None,
                            'food_id': food_id,
                            'ingredient_id': ingredient_id,
                            'quantity_used': waste_amount,
                            'usage_date': current_date.date().isoformat()
                        })
        
        current_date += timedelta(days=1)
    
    return orders, order_items, ingredient_usage

def insert_data_to_supabase(orders, order_items, ingredient_usage):
    try:
        print("Insertando órdenes...")
        for order in orders:
            try:
                response = supabase.table('order_table').insert(order).execute()
                print(f"Orden {order['order_id']} insertada")
            except Exception as e:
                if '23505' in str(e):  # Código de error para duplicados
                    print(f"Orden {order['order_id']} ya existe, continuando...")
                    continue
                else:
                    raise e
        
        print("\nInsertando items de órdenes...")
        for item in order_items:
            try:
                response = supabase.table('order_items_table').insert(item).execute()
                print(f"Item de orden {item['order_id']} (Item ID: {item['order_item_id']}) insertado")
            except Exception as e:
                if '23505' in str(e):
                    print(f"Item {item['order_item_id']} ya existe, continuando...")
                    continue
                else:
                    raise e
        
        print("\nInsertando uso de ingredientes...")
        for usage in ingredient_usage:
            try:
                response = supabase.table('ingredient_usage_table').insert(usage).execute()
                print(f"Uso de ingrediente para orden {usage.get('order_id', 'N/A')} (Item ID: {usage.get('order_item_id', 'N/A')}) insertado")
            except Exception as e:
                if '23505' in str(e):
                    print(f"Uso de ingrediente para orden {usage.get('order_id', 'N/A')} ya existe, continuando...")
                    continue
                elif '23503' in str(e):  # Error de clave foránea
                    print(f"Error de referencia para orden {usage.get('order_id', 'N/A')}, continuando...")
                    continue
                else:
                    raise e
        
        print("\nDatos insertados exitosamente")
        
    except Exception as e:
        print(f"Error general insertando datos: {e}")
        raise e

def clear_tables():
    """Borra todos los registros de las tablas en el orden correcto"""
    try:
        print("Borrando datos existentes...")
        
        # Borrar en orden debido a las restricciones de clave foránea
        print("Borrando ingredient_usage_table...")
        supabase.table('ingredient_usage_table').delete().neq('ingredient_id', 0).execute()
        
        print("Borrando order_items_table...")
        supabase.table('order_items_table').delete().neq('order_item_id', 0).execute()
        
        print("Borrando order_table...")
        supabase.table('order_table').delete().neq('order_id', 0).execute()
        
        print("Tablas limpiadas exitosamente")
    except Exception as e:
        print(f"Error borrando datos: {e}")
        raise e

def main():
    # Limpiar tablas primero
    clear_tables()
    
    # Generar datos desde noviembre 2024 hasta enero 2025
    start_date = datetime(2024, 11, 1)
    end_date = datetime(2025, 1, 4)
    
    print(f"Generando datos desde {start_date.date()} hasta {end_date.date()}")
    
    orders, order_items, ingredient_usage = generate_orders(start_date, end_date)
    
    print(f"\nDatos generados:")
    print(f"Órdenes: {len(orders)}")
    print(f"Items de órdenes: {len(order_items)}")
    print(f"Registros de uso de ingredientes: {len(ingredient_usage)}")
    
    # Guardar datos en archivos JSON para referencia
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('generated_data', exist_ok=True)
    
    with open(f'generated_data/orders_{timestamp}.json', 'w') as f:
        json.dump(orders, f, indent=2)
    with open(f'generated_data/order_items_{timestamp}.json', 'w') as f:
        json.dump(order_items, f, indent=2)
    with open(f'generated_data/ingredient_usage_{timestamp}.json', 'w') as f:
        json.dump(ingredient_usage, f, indent=2)
    
    print("\nArchivos JSON generados en el directorio 'generated_data'")
    
    # Insertar datos en Supabase
    insert_data_to_supabase(orders, order_items, ingredient_usage)

if __name__ == "__main__":
    main() 