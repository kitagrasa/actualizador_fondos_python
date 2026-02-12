"""
Actualización desde Financial Times - Extrae tabla HTML
"""
import sys
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

from config import FUNDS, DATA_DIR
from utils import upsert_day, update_index, save_health_status

def parse_ft_date(text):
    """Convierte fecha de FT 'Tuesday, February 10, 2026' a YYYY-MM-DD"""
    try:
        # Limpiar texto
        clean_text = text.strip()
        
        # Extraer fecha con regex: "Tuesday, February 10, 2026"
        match = re.search(r'([A-Za-z]{3,}day),?\s+([A-Za-z]{3,})\s+(\d{1,2}),?\s+(\d{4})', clean_text)
        if match:
            month_str = match.group(2)
            day_str = match.group(3)
            year_str = match.group(4)
            
            # Convertir mes abreviado
            date_str = f"{month_str} {day_str}, {year_str}"
            
            # Intentar con mes completo
            try:
                dt = datetime.strptime(date_str, "%B %d, %Y")
                return dt.strftime('%Y-%m-%d')
            except:
                # Intentar con mes abreviado
                dt = datetime.strptime(date_str, "%b %d, %Y")
                return dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"[FT] Error parsing date '{text}': {e}")
    return None

def parse_ft_price(text):
    """Extrae precio decimal de texto como '780.94'"""
    try:
        clean = text.strip().replace(',', '').replace(' ', '')
        value = float(clean)
        return value if value > 0 else None
    except:
        return None

def extract_ft_data(html):
    """Extrae TODOS los precios de la tabla HTML de FT"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Buscar tabla con class 'mod-tearsheet-historical-prices__results'
        table = soup.find('table', class_='mod-tearsheet-historical-prices__results')
        
        if not table:
            print("[FT] No historical prices table found")
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            print("[FT] No tbody found in table")
            return []
        
        rows = []
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            
            if len(tds) < 5:
                continue
            
            # Columna 0: Fecha (formato largo o corto)
            # Columna 4: Close price
            date_cell = tds[0]
            close_cell = tds[4]
            
            # La fecha puede estar en <span> para mostrar diferente en mobile/desktop
            date_text = date_cell.get_text(strip=True)
            close_text = close_cell.get_text(strip=True)
            
            date = parse_ft_date(date_text)
            close = parse_ft_price(close_text)
            
            if date and close:
                rows.append({'date': date, 'close': close})
        
        print(f"[FT] Extracted {len(rows)} historical prices from table")
        return rows
        
    except Exception as e:
        print(f"[FT] Error extracting data: {e}")
        import traceback
        traceback.print_exc()
        return []

def update_from_ft(fund):
    """Actualiza TODOS los precios históricos desde FT"""
    isin = fund['isin']
    ft_code = fund['ft']
    url = f"https://markets.ft.com/data/funds/tearsheet/historical?s={ft_code}"
    
    try:
        print(f"[FT] Fetching ALL historical data for {isin}...")
        
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'cache-control': 'no-cache',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extraer TODOS los precios de la tabla
        rows = extract_ft_data(response.text)
        
        if not rows:
            print(f"[FT] No data extracted for {isin}")
            return {'success': False, 'error': 'No data extracted'}
        
        # Procesar TODOS los precios
        rows.sort(key=lambda x: x['date'], reverse=True)
        
        updated = 0
        new_dates = 0
        
        for row in rows:
            result = upsert_day(isin, row['date'], {
                'date': row['date'],
                'close': row['close'],
                'src': 'ft'
            })
            
            if result['changed']:
                updated += 1
                if result['inserted_new_date']:
                    new_dates += 1
                    update_index(isin, row['date'])
        
        if updated > 0:
            print(f"[FT] ✓ Updated {updated} prices for {isin} ({new_dates} new dates)")
        else:
            print(f"[FT] = No changes for {isin} (all {len(rows)} prices already stored)")
        
        return {
            'success': True, 
            'updated': updated, 
            'new_dates': new_dates,
            'total': len(rows)
        }
        
    except requests.exceptions.Timeout:
        print(f"[FT] Timeout for {isin}")
        return {'success': False, 'error': 'Timeout'}
    except requests.exceptions.RequestException as e:
        print(f"[FT] Request error for {isin}: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f"[FT] Error fetching {isin}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def main():
    """Función principal"""
    print("=== Financial Times Update Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    print("Mode: Downloading ALL available historical data from HTML table")
    
    success_count = 0
    total_updated = 0
    total_new_dates = 0
    
    for fund in FUNDS:
        result = update_from_ft(fund)
        if result['success']:
            success_count += 1
            total_updated += result.get('updated', 0)
            total_new_dates += result.get('new_dates', 0)
        time.sleep(2)  # Pausa entre requests
    
    save_health_status('ft', success_count, len(FUNDS))
    
    print(f"=== Financial Times Update Completed ===")
    print(f"Success: {success_count}/{len(FUNDS)} funds")
    print(f"Total prices updated: {total_updated}")
    print(f"New dates added: {total_new_dates}\n")
    
    if success_count == 0:
        print("❌ CRITICAL: No funds were updated from Financial Times")
        sys.exit(1)

if __name__ == '__main__':
    main()
