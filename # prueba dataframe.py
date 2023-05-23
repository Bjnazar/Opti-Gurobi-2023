# prueba dataframe
import pandas as pd

def crear_lista_desde_csv(archivo_csv, columna):
    df = pd.read_csv(archivo_csv)
    print(df)
    print(df[columna])
    # lista = df[columna].tolist()
    # return lista

# Ejemplo de uso
archivo_csv = 'rutas.csv'  # Reemplaza con el nombre de tu archivo CSV
columna = 'distancia'  # Reemplaza con el nombre de la columna que deseas extraer

crear_lista_desde_csv(archivo_csv, columna)
# lista_valores = crear_lista_desde_csv(archivo_csv, columna)
# print(lista_valores)