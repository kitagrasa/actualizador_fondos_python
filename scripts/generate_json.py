"""
Genera archivos JSON para Portfolio Performance
"""
from datetime import datetime
from pathlib import Path

from config import FUNDS, DATA_DIR, JSON_DIR, KEEP_DAYS
from utils import read_json, write_json

def generate_json_for_fund(fund):
    """Genera JSON de precios para un fondo específico"""
    isin = fund['isin']
    idx_file = DATA_DIR / f"idx_{isin}.json"
    idx = read_json(idx_file)
    
    dates = idx.get('dates', [])[-KEEP_DAYS:]
    
    out = []
    for date in dates:
        day_file = DATA_DIR / isin / f"{date}.json"
        day_data = read_json(day_file)
        
        close = day_data.get('close')
        if day_data.get('date') and close is not None:
            try:
                close_float = float(close)
                if close_float > 0:
                    out.append({
                        'date': day_data['date'],
                        'close': close_float
                    })
            except (ValueError, TypeError):
                pass
    
    out.sort(key=lambda x: x['date'])
    return out

def main():
    """Función principal"""
    print("=== JSON Generation Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    for fund in FUNDS:
        data = generate_json_for_fund(fund)
        output_file = JSON_DIR / f"{fund['isin']}.json"
        write_json(output_file, data)
        print(f"✓ Generated {fund['isin']}.json ({len(data)} entries)")
    
    consolidated = {}
    for fund in FUNDS:
        consolidated[fund['isin']] = generate_json_for_fund(fund)
    
    consolidated_file = JSON_DIR / 'all-funds.json'
    write_json(consolidated_file, consolidated)
    print(f"✓ Generated all-funds.json ({len(FUNDS)} funds)")
    
    print("=== JSON Generation Completed ===\n")

if __name__ == '__main__':
    main()
