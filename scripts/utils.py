#!/usr/bin/env python3
"""
UTILIDADES v2.0 UNIFICADA - 1 ARCHIVO POR ISIN
Feb 2026 - Arquitectura optimizada
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path("data")
JSON_DIR = Path("json")
KEEP_DAYS = 2920  # 8 años trading
SOURCE_PRIORITY = {"ft": 20, "fundsquare": 10, "unknown": 0}

# Tus 7 fondos (actualiza nombres si necesario)
FUNDS = [
    {"isin": "LU0223332320", "name": "KONWAVE Gold Equity Fund B EUR Hedged Cap"},
    {"isin": "LU0524465548", "name": "Amundi Gold Hedged Cap"},
    {"isin": "LU1598720172", "name": "Lyxor Gold Bullion Securities"},
    {"isin": "IE00B3CNHG25", "name": "WisdomTree Gold"},
    {"isin": "IE00B579F325", "name": "iShares Physical Gold ETC"},
    {"isin": "LU0252633754", "name": "Xetra-Gold"},
    {"isin": "DE000A0S9GB0", "name": "EUWAX Gold II"}
]

def read_json(filepath: Path) -> Dict:
    filepath = Path(filepath)
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error {filepath}: {e}")
    return {}

def write_json(filepath: Path, data: Dict):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if filepath.exists():
        backup = filepath.with_suffix('.json.bak')
        shutil.copy2(filepath, backup)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 {filepath.name}: {len(data.get('prices', {}))} días")

def read_isin_file(isin: str) -> Dict:
    return read_json(DATA_DIR / f"{isin}.json")

def upsert_price(isin: str, date: str, value: Dict) -> Dict:
    """Upsert inteligente con prioridades"""
    isin_file = DATA_DIR / f"{isin}.json"
    data = read_isin_file(isin)
    
    new_close = float(value.get('close', 0))
    if new_close <= 0:
        return {'changed': False, 'inserted_new_date': False}
    
    existing = data.get('prices', {}).get(date)
    if existing:
        existing_close = float(existing.get('close', 0))
        existing_priority = SOURCE_PRIORITY.get(existing.get('src'), 0)
        new_priority = SOURCE_PRIORITY.get(value.get('src'), 0)
        
        if new_priority < existing_priority:
            return {'changed': False, 'inserted_new_date': False}
        if existing_close == new_close and new_priority == existing_priority:
            return {'changed': False, 'inserted_new_date': False}
    
    if 'prices' not in data:
        data['prices'] = {}
    
    now_ms = int(datetime.now().timestamp() * 1000)
    data['prices'][date] = {
        'close': new_close,
        'src': value.get('src', 'unknown'),
        'ms': value.get('ms'),
        'updated_at': now_ms
    }
    
    data.setdefault('isin', isin)
    data['name'] = next((f['name'] for f in FUNDS if f['isin'] == isin), 'Unknown')
    data['dates'] = sorted(data['prices'].keys())
    data['total_days'] = len(data['dates'])
    data['last_updated'] = now_ms
    
    # Rotación 8 años
    if len(data['dates']) > KEEP_DAYS:
        old_dates = data['dates'][:-KEEP_DAYS]
        for old_date in old_dates:
            del data['prices'][old_date]
        data['dates'] = data['dates'][-KEEP_DAYS:]
    
    write_json(isin_file, data)
    return {'changed': True, 'inserted_new_date': existing is None}

def update_global_index():
    """Dashboard global"""
    global_index = {}
    for isin_file in DATA_DIR.glob("*.json"):
        if isin_file.stem in ['health', 'all-index']:
            continue
        data = read_isin_file(isin_file.stem)
        if data.get('dates'):
            global_index[isin_file.stem] = {
                'total_days': len(data['dates']),
                'last_date': data['dates'][-1],
                'name': data.get('name', '?')
            }
    write_json(DATA_DIR / 'all-index.json', global_index)
    print(f"📊 Global: {len(global_index)} fondos")

def 
