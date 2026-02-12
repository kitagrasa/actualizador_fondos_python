#!/usr/bin/env python3
"""
Fundsquare Updater v2.0 - Arquitectura unificada
Prioridad: FT(20) > Fundsquare(10)
"""
import requests
import json
from datetime import datetime
from utils import upsert_price, FUNDS, save_health_status, update_global_index

def update_from_fundsquare(fund):
    """Extrae datos Fundsquare → upsert_price"""
    isin = fund['isin']
    try:
        # Tu URL/API Fundsquare real aquí
        url = f"https://api.fundsquare.net/fund/{isin}/prices"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        updated = 0
        new_dates = 0
        
        for price_day in data.get('prices', []):
            date = price_day['date']  # '2026-02-10'
            value = {
                'close': price_day['close'],
                'src': 'fundsquare',
                'ms': price_day.get('ms')
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
        print(f"❌ Fundsquare {isin}: {e}")
        return {'success': False}

def main():
    """Ejecuta actualización Fundsquare v2.0"""
    print("🔄 Fundsquare Updater v2.0 iniciando...")
    
    total_updated = 0
    total_new_dates = 0
    successful_funds = 0
    
    for fund in FUNDS:
        result = update_from_fundsquare(fund)
        if result.get('success'):
            successful_funds += 1
            total_updated += result.get('updated', 0)
            total_new_dates += result.get('new_dates', 0)
            print(f"✅ {fund['name'][:30]}: {result.get('updated', 0)} upd")
    
    print(f"\n📊 RESUMEN Fundsquare:")
    print(f"   Fondos OK: {successful_funds}/{len(FUNDS)}")
    print(f"   Total actualizados: {total_updated}")
    print(f"   Nuevas fechas: {total_new_dates}")
    
    # v2.0 Health monitoring
    save_health_status('fundsquare', total_updated, len(FUNDS))
    update_global_index()
    print("✅ Health + índice global actualizados")

if __name__ == "__main__":
    main()
