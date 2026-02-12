"""
Actualización desde Financial Times
Descarga TODO el histórico disponible de la tabla HTML
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
    """Convierte fecha de Financial Times a formato YYYY-MM-DD"""
    try:
        # Formato típico: "Tue, Jan 28, 2026" o "Tuesday, January 28, 2026"
        match = re.search(r'([A-Za-z]{3,}),?\s+([A-Za-z]{3,})\s+(\d{1,2}),?\s+(\d{4})', text)
        if match:
            date_str = f"{match.group(2)} {match.group(3)}, {match.group(4)}"
            dt = datetime.strptime(date_str, "%b %d, %Y")
            return dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error parsing date '{text}': {e}")
    return None

def parse_ft_number(text):
    """Convierte texto a número decimal"""
    try:
        clean = text.strip().replace(' ', '').replace(',', '')
        value = float(clean)
        return value if value > 0 else None
    except:
        return None

def extract_ft_data(html):
    """Extrae TODOS los datos de precios de la tabla HTML de Financial Times"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Buscar la tabla de precios históricos
        table = soup.find('table', class_=lambda x: x and 'mod-tearsheet-historical-prices__results' in x)
        
        if not table:
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            return []
        
        rows = []
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 5:
                continue
            
            # Columna 0: Fecha, Columna 4: Precio de cierre
            date_text = tds[0].get_text(strip=True)
            close_text = tds[4].get_text(strip=True)
            
            date = parse_ft_date(date_text)
            close = parse_ft_number(close_text)
            
            if date and close:
                rows.append({'date': date, 'close': close})
        
        # Eliminar duplicados (mantener el último precio por fecha)
        seen = {}
        for row in rows:
            seen[row['date']] = row['close']
        
        result = [{'date': k, 'close': v} for k, v in seen.items()]
        print(f"[FT] Extracted {len(result)} historical prices from HTML")
        return result
        
    except Exception as e:
        print(f"Error extracting FT data: {e}")
        return []

def update_from_ft(fund):
    """Actualiza TODOS los precios históricos desde Financial Times"""
    isin = fund['isin']
    ft_code = fund['ft']
    url = f"https://markets.ft.com/data/funds/tearsheet/historical?s={ft_code}"
    
    try:
        print(f"[FT] Fetching ALL historical data for {isin}...")
        
        headers = {
            'accept': 'text/html,application/xhtml+xml',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extraer TODOS los precios de la tabla
        rows = extract_ft_data(response.text)
        
        if not rows:
            print(f"[FT] No data extracted for {isin}")
            return {'success': False, 'error': 'No data extracted'}
        
        # Procesar TODOS los precios (no solo el último)
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
        return {'success': False, 'error': str(e)}

def main():
    """Función principal"""
    print("=== Financial Times Update Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    print("Mode: Downloading ALL available historical data")
    
    success_count = 0
    total_updated = 0
    total_new_dates = 0
    
    for fund in FUNDS:
        result = update_from_ft(fund)
        if result['success']:
            success_count += 1
            total_updated += result.get('updated', 0)
            total_new_dates += result.get('new_dates', 0)
        time.sleep(2)  # Pausa entre requests para no sobrecargar el servidor
    
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
