"""
Actualización desde Fundsquare
Descarga todos los precios disponibles y los almacena
"""
import sys
from datetime import datetime
import requests

from config import FUNDS, DATA_DIR
from utils import upsert_day, update_index, save_health_status, get_madrid_date

def update_from_fundsquare(fund):
    """Actualiza precios desde Fundsquare para un fondo"""
    isin = fund['isin']
    id_instr = fund['idInstr']
    url = f"https://www.fundsquare.net/Fundsquare/application/vni/{id_instr}"
    
    try:
        print(f"[Fundsquare] Fetching {isin}...")
        
        headers = {
            'accept': 'application/json,text/plain,*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.fundsquare.net/',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        eur = data.get('EUR', [])
        
        if not eur:
            print(f"[Fundsquare] No EUR data for {isin}")
            return {'success': False, 'error': 'No EUR data'}
        
        # Procesar TODOS los precios disponibles (no solo el último)
        updated = 0
        new_dates = 0
        
        for item in eur:
            ms = float(item.get('dtHrCalcVni', 0))
            close = float(item.get('pxVniPart', 0))
            
            if not (ms > 0 and close > 0):
                continue
            
            date = get_madrid_date(ms)
            
            result = upsert_day(isin, date, {
                'date': date,
                'close': close,
                'src': 'fundsquare',
                'ms': int(ms)
            })
            
            if result['changed']:
                updated += 1
                if result['inserted_new_date']:
                    new_dates += 1
                    update_index(isin, date)
        
        if updated > 0:
            print(f"[Fundsquare] ✓ Updated {updated} prices for {isin} ({new_dates} new dates)")
        else:
            print(f"[Fundsquare] = No changes for {isin} (all {len(eur)} prices already stored)")
        
        return {
            'success': True, 
            'updated': updated, 
            'new_dates': new_dates,
            'total': len(eur)
        }
        
    except requests.exceptions.Timeout:
        print(f"[Fundsquare] Timeout for {isin}")
        return {'success': False, 'error': 'Timeout'}
    except requests.exceptions.RequestException as e:
        print(f"[Fundsquare] Request error for {isin}: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f"[Fundsquare] Error fetching {isin}: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Función principal"""
    print("=== Fundsquare Update Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    print("Mode: Downloading ALL available historical data")
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_updated = 0
    total_new_dates = 0
    
    for fund in FUNDS:
        result = update_from_fundsquare(fund)
        if result['success']:
            success_count += 1
            total_updated += result.get('updated', 0)
            total_new_dates += result.get('new_dates', 0)
    
    save_health_status('fundsquare', success_count, len(FUNDS))
    
    print(f"=== Fundsquare Update Completed ===")
    print(f"Success: {success_count}/{len(FUNDS)} funds")
    print(f"Total prices updated: {total_updated}")
    print(f"New dates added: {total_new_dates}\n")
    
    if success_count == 0:
        print("❌ CRITICAL: No funds were updated from Fundsquare")
        sys.exit(1)

if __name__ == '__main__':
    main()
