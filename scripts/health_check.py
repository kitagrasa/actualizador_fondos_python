"""
Verificación de salud del sistema
"""
import sys
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, STALE_HOURS
from utils import read_json, write_json

def main():
    """Función principal de verificación de salud"""
    print("=== Health Check Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    
    health_file = DATA_DIR / 'health.json'
    health = read_json(health_file)
    
    last_ok = health.get('last_ok')
    
    if not last_ok or not last_ok.get('timestamp'):
        print("⚠️ No successful updates recorded yet (normal on first run)")
        return
    
    try:
        now_ms = int(datetime.now().timestamp() * 1000)
        last_ok_ms = int(last_ok['timestamp'])
        age_ms = now_ms - last_ok_ms
        age_hours = age_ms / (60 * 60 * 1000)
        
        print(f"Last OK: {last_ok.get('iso', 'Unknown')}")
        print(f"Age: {age_hours:.2f} hours")
        print(f"Threshold: {STALE_HOURS} hours")
        
        flag_file = DATA_DIR / 'health_alert_needed.flag'
        
        if age_hours >= STALE_HOURS:
            print(f"❌ Data is STALE ({age_hours:.2f} hours old, threshold: {STALE_HOURS}h)")
            
            alert_data = {
                'timestamp': now_ms,
                'iso': datetime.now().isoformat(),
                'last_ok': last_ok,
                'age_hours': age_hours,
                'threshold_hours': STALE_HOURS
            }
            
            write_json(flag_file, alert_data)
            print(f"Created alert flag: {flag_file}")
            
        else:
            print(f"✅ Data is FRESH ({age_hours:.2f} hours old, threshold: {STALE_HOURS}h)")
            
            if flag_file.exists():
                flag_file.unlink()
                print("Removed alert flag (data is now fresh)")
        
    except Exception as e:
        print(f"Error during health check: {e}")
    
    print("=== Health Check Completed ===\n")

if __name__ == '__main__':
    main()
