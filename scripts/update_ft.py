#!/usr/bin/env python3
"""
Financial Times Updater v2.0 - PRIORIDAD MÁXIMA
FT(20) > Fundsquare(10) - Sobrescribe siempre
"""
import requests
from datetime import datetime
from utils import upsert_price, FUNDS, save_health_status, update_global_index

def update_from_ft(fund):
    """Extrae FT.com → upsert_price (prioridad máxima)"""
    isin = fund['isin']
    try:
        # URL FT real (adapta a tu scraper)
        url = f"https://markets.ft.com/data/funds/tearsheet/historical?s={isin}"
        response = requests.get(url, timeout=15)
        
        # Parsear tabla histórica (adapta selector)
        prices = parse_ft_historical(response.text)
        
        updated = 0
        new_dates = 0
        
        for date, close in prices.items():
            value = {
                'close': float(close),
                'src': 'ft',  # Prioridad 20
                'ms': int(datetime.now().timestamp() * 1000)
            }
            result = upsert_price(isin, date, value)
            if result['changed']:
                updated += 1
                if result['inserted_new_date']:
                    new_dates += 1
        
        return {
            'success': True,
            'updated': updated,
            'new_dates': new_dates
        }
    except Exception as e:
        print(f"❌ FT {isin}: {e}")
        return {'success': False}

def parse_ft_historical(html_content):
    """Parsear tabla FT (BeautifulSoup o regex)"""
    # EJEMPLO placeholder - adapta a tu parser real
    prices = {}
    # lines = html_content.split('\n')
    # for line in lines:
    #     if '2026-02-10' in line:
    #         date = '2026-02-10'
    #         close = extract_close(line)
    #         prices[date] = close
    return prices  # {'2026-02-10': 780.94, ...}

def main():
    """FT Updater v2.0 - Prioridad máxima"""
    print("🔄 FT.com Updater v2.0 (prioridad máxima)")
    
    total_updated = 0
    total_new_dates = 0
    successful_funds = 0
    
    for fund in FUNDS:
        result = update_from_ft(fund)
        if result.get('success'):
            successful_funds += 1
            total_updated += result.get('updated', 0)
            total_new_dates += result.get('new_dates', 0)
            print(f"✅ {fund['name'][:30]}: {result.get('updated', 0)} upd")
    
    print(f"\n📊 RESUMEN FT.com:")
    print(f"   Fondos OK: {successful_funds}/{len(FUNDS)}")
    print(f"   Prioridad aplicada: {total_updated}")
    
    save_health_status('ft', total_updated, len(FUNDS))
    update_global_index()
    print("✅ v2.0: Health + índice completos")

if __name__ == "__main__":
    main()
