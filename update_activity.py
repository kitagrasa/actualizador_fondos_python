#Falsear actividad para que Github piense que el repositorio sigue activo

import datetime

def update_readme():
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    contenido = f"""# Repositorio Activo

Última actualización automática: {fecha}

Este repositorio se mantiene activo automáticamente.
"""
    
    with open("README.md", "w", encoding="utf-8") as file:
        file.write(contenido)

if __name__ == "__main__":
    update_readme()
