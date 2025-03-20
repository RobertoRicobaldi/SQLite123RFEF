import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
from io import BytesIO
from PIL import Image

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect("jugadoras.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS valoraciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        captador TEXT,
                        nombre TEXT,
                        posicion TEXT,
                        club TEXT,
                        valoracion INTEGER,
                        comentario TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()

def agregar_valoracion(captador, nombre, posicion, club, valoracion, comentario):
    conn = sqlite3.connect("jugadoras.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO valoraciones (captador, nombre, posicion, club, valoracion, comentario) VALUES (?, ?, ?, ?, ?, ?)",
                   (captador, nombre, posicion, club, valoracion, comentario))
    conn.commit()
    conn.close()

def obtener_valoraciones():
    conn = sqlite3.connect("jugadoras.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM valoraciones")
    datos = cursor.fetchall()
    conn.close()
    return datos

# Configuración de la aplicación Streamlit
st.title("Scouting de Jugadoras")

# Cargar datos desde Excel
@st.cache_data
def load_data():
    file_path = r"C:\Users\rricobaldi\Desktop\OPTA - Provision\Informes Power BI\Ligas\1 RFEF\Futboleras\Jugadoras_123Total13marzo2025.xlsx"
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {e}")
        return pd.DataFrame()

df = load_data()

# Verificar que el DataFrame no esté vacío
if df.empty:
    st.error("No se pudo cargar el archivo de datos o está vacío.")
else:
    st.write("Columnas disponibles en el DataFrame:", df.columns.tolist())

    # Verificar si la columna 'NOMBRE' existe antes de usarla
    if "NOMBRE" in df.columns:
        jugadora_seleccionada = st.selectbox("Selecciona una jugadora", df["NOMBRE"].dropna().unique())
    else:
        st.error("La columna 'NOMBRE' no se encuentra en el archivo Excel.")

# Formulario para agregar valoración
st.header("Agregar valoración")
captador = st.text_input("Nombre del captador")
nombre = st.text_input("Nombre de la jugadora")
posicion = st.selectbox("Posición", ["Delantera", "Centrocampista", "Defensa", "Portera"])
club = st.text_input("Club")
valoracion = st.selectbox("Valoración", [3, 5, 7, 9])
comentario = st.text_area("Comentario")

if st.button("Guardar valoración"):
    if captador and nombre and club and comentario:
        agregar_valoracion(captador, nombre, posicion, club, valoracion, comentario)
        st.success("Valoración guardada correctamente.")
    else:
        st.error("Por favor, completa todos los campos.")

# Mostrar valoraciones existentes
st.header("Valoraciones guardadas")
datos = obtener_valoraciones()

if datos:
    for fila in datos:
        st.write(f"📋 **Captador:** {fila[1]}")
        st.write(f"**{fila[2]}** - {fila[3]} en {fila[4]}")
        st.write(f"⭐ Valoración: {fila[5]}")
        st.write(f"📝 Comentario: {fila[6]}")
        st.write("---")
else:
    st.write("No hay valoraciones registradas aún.")

# Botón para mostrar la base de datos SQLite
if st.button("Mostrar todas las valoraciones en la base de datos"):
    st.write("📊 Valoraciones guardadas en SQLite:")
    df_valoraciones = pd.DataFrame(obtener_valoraciones(), columns=["ID", "Captador", "Nombre", "Posición", "Club", "Valoración", "Comentario"])
    st.dataframe(df_valoraciones)
