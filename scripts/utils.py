#!/usr/bin/env python3
"""
UTILIDADES UNIFICADAS v2.0 - 1 ARCHIVO POR ISIN
Datos frescos Febrero 2026 - Arquitectura optimizada
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path("data")
JSON_DIR = Path("json")
KEEP_DAYS = 2920  # 8 años trading
SOURCE_PRIORITY = {"ft": 20, "fundsquare": 10}

# Tus 7 fondos (actualiza nombres si cambian)
FUNDS = [
    {"isin": "LU0223332320", "name": "KONWAVE Gold Equity Fund B EUR Hedged Cap"},
    {"isin": "LU0524465548", "name": "KONWAVE Gold Equity Fund A USD Cap"},
    {"isin": "LU1234567890", "name": "Tu otro fondo..."},
    # Agrega los otros 4 ISINs aquí
]

def read_json(filepath: Path) -> Dict[str, Any]:
    """Lectura robusta JSON"""
    filepath = Path(filepath)
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error leyendo {filepath}: {e}")
    return {}

def write_json(filepath: Path, data: Dict[str, Any]):
    """Escritura con backup automático"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if filepath.exists():
        backup = filepath.with_suffix('.json.bak')
        shutil.copy2(filepath, backup)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    days = len(data.get('prices', {}))
    print(f"💾 {filepath.name}: {days} días")

def upsert_price(isin: str, date: str, value: Dict[str, Any]) -> Dict[str, bool]:
    """Upsert inteligente con prioridades FT > Fundsquare"""
    isin_file = DATA_DIR / f"{isin}.json"
    data = read_json(isin_file)
    
    new_close = float(value.get('close', 0))
    if new_close <= 0:
        return {'changed': False, 'inserted_new_date': False}
    
    # Verificar prioridad y duplicados
    existing = data.get('prices', {}).get(date)
    if existing:
        existing_close = float(existing.get('close', 0))
        existing_priority = SOURCE_PRIORITY.get(existing.get('src'), 0)
        new_priority = SOURCE_PRIORITY.get(value.get('src'), 0)
        
        if new_priority < existing_priority:
            return {'changed': False, 'inserted_new_date': False}
        if existing_close == new_close and new_priority == existing_priority:
            return {'changed': False, 'inserted_new_date': False}
    
    # Insertar/actualizar
    if 'prices' not in data:
        data['prices'] = {}
    
    now_ms = int(datetime.now().timestamp() * 1000)
    data['prices'][date] = {
        'close': new_close,
        'src': value.get('src', 'unknown'),
        'ms': value.get('ms', now_ms),
        'updated_at': now_ms
    }
    
    # Metadatos
    data['isin'] = isin
    data['name'] = next((f['name'] for f in FUNDS if f['isin'] == isin), f"ISIN_{isin}")
    data['dates'] = sorted(data['prices'].keys())
    data['total_days'] = len(data['dates'])
    data['last_updated'] = now_ms
    
    # Rotación automática 8 años
    if len(data['dates']) > KEEP_DAYS:
        old_dates = data['dates'][:-KEEP_DAYS]
        for old_date in old_dates:
            del data['prices'][old_date]
        data['dates'] = data['dates'][-KEEP_DAYS:]
        print(f"♻️ {isin}: Rotación {len(old_dates)} días antiguos")
    
    write_json(isin_file, data)
    return {'changed': True, 'inserted_new_date': existing is None}

def update_global_index():
    """Dashboard global todos los fondos"""
    index = {}
    for isin_file in DATA_DIR.glob("*.json"):
        if isin_file.stem in ['health', 'all-index']:
            continue
        data = read_json(isin_file)
        if data.get('dates'):
            index[isin_file.stem] = {
                'total_days': len(data['dates']),
                'last_date': data['dates'][-1],
                'name': data.get('name', 'Unknown'),
                'last_close': data['prices'][data['dates'][-1]]['close']
            }
    
    index['summary'] = {
        'total_funds': len(index),
        'total_days_across_all': sum(f['total_days'] for f in index.values()),
        'last_updated': int(datetime.now().timestamp() * 1000)
    }
    write_json(DATA_DIR / 'all-index.json', index)
    print(f"📊 Índice: {len(index)} fondos")

def save_health_status(source: str, success_count: int, total_funds: int):
    """Monitoreo health"""
    health_file = DATA_DIR / 'health.json'
    health = read_json(health_file)
    now_ms = int(datetime.now().timestamp() * 1000)
    
    health[f'last_{source}'] = {
        'timestamp': now_ms,
        'success_count': success_count,
        'total_funds': total_funds
    }
    health['last_ok'] = {
        'timestamp': now_ms,
        'source': source,
        'success_rate': round(success_count / total_funds * 100, 1)
    }
    write_json(health_file, health)
