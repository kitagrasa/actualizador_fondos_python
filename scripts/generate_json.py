#!/usr/bin/env python3
"""
Genera JSON Portfolio Performance desde data unificada
"""
from pathlib import Path
import json
from utils import DATA_DIR, JSON_DIR, read_isin_file, write_json

def main():
    JSON_DIR.mkdir(exist_ok=True)
    
    for isin_file in DATA_DIR.glob("*.json"):
        if isin_file.stem in ['health', 'all-index']:
            continue
        
        data = read_isin_file(isin_file.stem)
        if data.get('prices'):
            pp_data = [{'date': date, 'close': info['close']} 
                      for date, info in data['prices'].items()]
            pp_data.sort(key=lambda x: x['date'])
            
            output_file = JSON_DIR / f"{isin_file.stem}.json"
            write_json(output_file, pp_data)
            print(f"✅ {isin_file.stem}: {len(pp_data)} días")
    
    print("🎉 Portfolio Performance JSON listos")

if __name__ == "__main__":
    main()
