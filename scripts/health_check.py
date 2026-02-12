"""
Verificación de salud del sistema
Alertas granulares: >1h sin updates, >20h por fuente
"""
import sys
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, STALE_HOURS, STALE_WEBSITE_HOURS
from utils import read_json, write_json

def check_overall_health(health):
    """Verifica salud general del sistema (cualquier actualización exitosa)"""
    last_ok = health.get('last_ok')
    
    if not last_ok or not last_ok.get('timestamp'):
        print("⚠️ No successful updates recorded yet (normal on first run)")
        return None
    
    now_ms = int(datetime.now().timestamp() * 1000)
    last_ok_ms = int(last_ok['timestamp'])
    age_ms = now_ms - last_ok_ms
    age_hours = age_ms / (60 * 60 * 1000)
    
    print(f"\n📊 Overall System Health:")
    print(f"   Last successful update: {last_ok.get('iso', 'Unknown')}")
    print(f"   Age: {age_hours:.2f} hours")
    print(f"   Threshold: {STALE_HOURS} hour(s)")
    
    if age_hours >= STALE_HOURS:
        print(f"   Status: ❌ STALE")
        return {
            'type': 'overall',
            'age_hours': age_hours,
            'threshold': STALE_HOURS,
            'last_ok': last_ok
        }
    else:
        print(f"   Status: ✅ FRESH")
        return None

def check_source_health(health, source_name, threshold_hours):
    """Verifica salud de una fuente específica (FT o Fundsquare)"""
    source_key = f'last_{source_name}'
    source_data = health.get(source_key)
    
    if not source_data or not source_data.get('timestamp'):
        print(f"   No data for {source_name}")
        return None
    
    now_ms = int(datetime.now().timestamp() * 1000)
    source_ms = int(source_data['timestamp'])
    age_ms = now_ms - source_ms
    age_hours = age_ms / (60 * 60 * 1000)
    
    success_count = source_data.get('success_count', 0)
    total_funds = source_data.get('total_funds', 0)
    
    print(f"\n📡 {source_name.upper()} Health:")
    print(f"   Last attempt: {source_data.get('iso', 'Unknown')}")
    print(f"   Age: {age_hours:.2f} hours")
    print(f"   Success rate: {success_count}/{total_funds}")
    print(f"   Threshold: {threshold_hours} hour(s)")
    
    # Alertar si la fuente lleva mucho tiempo fallando completamente
    if age_hours >= threshold_hours and success_count == 0:
        print(f"   Status: ❌ FAILING (no successful updates)")
        return {
            'type': 'source',
            'source': source_name,
            'age_hours': age_hours,
            'threshold': threshold_hours,
            'last_attempt': source_data
        }
    elif success_count < total_funds:
        print(f"   Status: ⚠️ PARTIAL (some funds failing)")
    else:
        print(f"   Status: ✅ HEALTHY")
    
    return None

def main():
    """Función principal de verificación de salud"""
    print("=== Health Check Started ===")
    print(f"Time: {datetime.now().isoformat()}")
    
    health_file = DATA_DIR / 'health.json'
    health = read_json(health_file)
    
    alerts = []
    
    # 1. Verificar salud general (>1h sin ninguna actualización)
    overall_alert = check_overall_health(health)
    if overall_alert:
        alerts.append(overall_alert)
    
    # 2. Verificar cada fuente específica (>20h fallando)
    ft_alert = check_source_health(health, 'ft', STALE_WEBSITE_HOURS)
    if ft_alert:
        alerts.append(ft_alert)
    
    fundsquare_alert = check_source_health(health, 'fundsquare', STALE_WEBSITE_HOURS)
    if fundsquare_alert:
        alerts.append(fundsquare_alert)
    
    # 3. Crear o eliminar flag según alertas
    flag_file = DATA_DIR / 'health_alert_needed.flag'
    
    if alerts:
        print(f"\n❌ ALERTS DETECTED: {len(alerts)} issue(s)")
        
        alert_data = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'iso': datetime.now().isoformat(),
            'alerts': alerts
        }
        
        write_json(flag_file, alert_data)
        print(f"Created alert flag: {flag_file}")
        
        # Mostrar resumen
        for alert in alerts:
            if alert['type'] == 'overall':
                print(f"\n🚨 System has not updated in {alert['age_hours']:.2f} hours")
            elif alert['type'] == 'source':
                print(f"\n🚨 {alert['source'].upper()} has been failing for {alert['age_hours']:.2f} hours")
    else:
        print(f"\n✅ ALL SYSTEMS HEALTHY")
        
        if flag_file.exists():
            flag_file.unlink()
            print("Removed alert flag (all systems recovered)")
    
    print("\n=== Health Check Completed ===\n")

if __name__ == '__main__':
    main()
