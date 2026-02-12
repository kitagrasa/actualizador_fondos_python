#!/usr/bin/env python3
"""
Genera JSON Portfolio Performance desde estructura unificada v2.0
"""
import json
from pathlib import Path
from utils import read_json, DATA_DIR, JSON_DIR, write_json

def main():
    """Genera todos los JSON Portfolio Performance"""
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0
    
    for isin_file in DATA_DIR.glob("*.json"):
        if isin_file.stem in ['health', 'all-index']:
            continue
        
        data = read_json(isin_file)
        if data.get('prices'):
            # Formato EXACTO Portfolio Performance
            pp_data = [
                {'date': date, 'close': info['close']}
                for date, info in data['prices'].items()
            ]
            pp_data.sort(key=lambda x: x['date'])
            
            output_file = JSON_DIR / f"{isin_file.stem}.json"
            write_json(output_file, pp_data)
            print(f"✅ {isin_file.stem}: {len(pp_data)} días")
            generated += 1
    
    print(f"🎉 Portfolio Performance: {generated} fondos generados")

if __name__ == "__main__":
    main()
