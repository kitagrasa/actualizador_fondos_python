"""
Utilidades comunes para todos los scripts
"""
import json
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, SOURCE_PRIORITY, KEEP_DAYS

def read_json(filepath):
    """Lee archivo JSON de forma segura"""
    try:
        filepath = Path(filepath)
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
    return {}

def write_json(filepath, data):
    """Escribe archivo JSON con encoding UTF-8"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def upsert_day(isin, date, value):
    """
    Inserta o actualiza datos de un día
    Respeta prioridades: FT (20) > Fundsquare (10)
    """
    day_file = DATA_DIR / isin / f"{date}.json"
    prev = read_json(day_file)
    
    new_close = float(value.get('close', 0))
    if not (new_close > 0):
        return {'changed': False, 'inserted_new_date': False}
    
    # Verificar prioridad de fuente
    if prev.get('date'):
        prev_close = float(prev.get('close', 0))
        prev_priority = SOURCE_PRIORITY.get(prev.get('src'), 0)
        new_priority = SOURCE_PRIORITY.get(value.get('src'), 0)
        
        # No sobrescribir si la nueva fuente tiene menor prioridad
        if new_priority < prev_priority:
            return {'changed': False, 'inserted_new_date': False}
        
        # No cambiar si es el mismo precio y misma prioridad
        if prev_close == new_close and prev_priority == new_priority:
            return {'changed': False, 'inserted_new_date': False}
    
    # Guardar datos
    now_ms = int(datetime.now().timestamp() * 1000)
    data = {
        'date': date,
        'close': new_close,
        'src': value.get('src', 'unknown'),
        'ms': value.get('ms'),
        'saved_at': prev.get('saved_at', now_ms),
        'updated_at': now_ms,
        'prev_src': prev.get('src'),
        'prev_close': prev.get('close')
    }
    
    write_json(day_file, data)
    return {'changed': True, 'inserted_new_date': not bool(prev.get('date'))}

def update_index(isin, date):
    """Actualiza índice de fechas para un ISIN (mantiene últimos KEEP_DAYS)"""
    idx_file = DATA_DIR / f"idx_{isin}.json"
    idx = read_json(idx_file)
    
    dates = idx.get('dates', [])
    if date not in dates:
        dates.append(date)
        dates.sort()
        
        # Mantener solo los últimos KEEP_DAYS
        if len(dates) > KEEP_DAYS:
            dates = dates[-KEEP_DAYS:]
        
        write_json(idx_file, {'dates': dates})

def get_madrid_date(timestamp_ms):
    """
    Convierte timestamp en milisegundos a fecha en zona horaria Madrid
    Incluye fallback a UTC si pytz falla
    """
    try:
        import pytz
        from datetime import timezone
        
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        madrid_tz = pytz.timezone('Europe/Madrid')
        madrid_dt = dt.astimezone(madrid_tz)
        return madrid_dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error convirtiendo fecha: {e}")
        # Fallback a UTC
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime('%Y-%m-%d')

def save_health_status(source, success_count, total_funds):
    """Actualiza el archivo de estado de salud con información de la fuente"""
    health_file = DATA_DIR / 'health.json'
    health = read_json(health_file)
    
    now_ms = int(datetime.now().timestamp() * 1000)
    now_iso = datetime.now().isoformat()
    
    # Actualizar última ejecución de la fuente específica
    health[f'last_{source}'] = {
        'timestamp': now_ms,
        'iso': now_iso,
        'success_count': success_count,
        'total_funds': total_funds
    }
    
    # Actualizar last_ok solo si hubo éxito
    if success_count > 0:
        health['last_ok'] = {
            'timestamp': now_ms,
            'iso': now_iso,
            'source': source
        }
    
    write_json(health_file, health)
