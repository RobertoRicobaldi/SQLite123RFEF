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
st.title("Análisis y Scouting de Jugadoras de 1-2 RFEF")

# Función para obtener la ruta del archivo Excel
def get_file_path():
    github_url = "https://github.com/RobertoRicobaldi/SQLite123RFEF/raw/main/Jugadoras_123Total13marzo2025.xlsx"
    response = requests.get(github_url)
    if response.status_code == 200:
        return github_url
    else:
        st.error(f"Error: No se encontró el archivo Excel en GitHub.")
        return None

# Cargar el archivo Excel
@st.cache_data
def load_data():
    try:
        file_path = get_file_path()
        if file_path is None:
            return pd.DataFrame()
        
        response = requests.get(file_path)
        if response.status_code == 200:
            excel_data = BytesIO(response.content)
            data = pd.read_excel(excel_data, engine='openpyxl')
        else:
            st.error(f"Error al descargar el archivo desde GitHub.")
            return pd.DataFrame()
        
        return data
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("No se pudo cargar el archivo de datos o está vacío.")
else:
    if "NOMBRE" in df.columns:
        jugadora_seleccionada = st.selectbox("Selecciona una jugadora", df["NOMBRE"].dropna().unique(), key="busqueda_jugadora")
    else:
        st.error("La columna 'NOMBRE' no se encuentra en el archivo Excel.")

# Formulario para agregar valoración
if st.sidebar.radio("Selecciona una página", ["Scouting", "Filtros y Datos", "Búsqueda de Jugadoras", "Comparativa de Jugadoras"]) != "Comparativa de Jugadoras":
    st.header("Agregar valoración")
    captador = st.text_input("Nombre del captador")
    nombre = st.text_input("Nombre de la jugadora")
    posicion = st.selectbox("Posición", ["Delantera", "Centrocampista", "Defensa", "Portera"], key="posicion")
    club = st.text_input("Club")
    valoracion = st.selectbox("Valoración", [3, 5, 7, 9], key="valoracion")
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

# Página de Comparativa de Jugadoras
def pagina_comparativa():
    st.write("### Comparativa de Jugadoras")
    st.write("Selecciona dos jugadoras para comparar sus estadísticas.")
    if "EQUIPO" in df.columns:
        equipos = df["EQUIPO"].unique()
        equipo_seleccionado = st.sidebar.selectbox("Selecciona un equipo", ["Todos"] + list(equipos), key="comparativa_equipo")
    else:
        st.error("La columna 'EQUIPO' no se encuentra en el archivo Excel.")
        return
    
    if "PJ" in df.columns:
        min_pj = int(df["PJ"].min())
        max_pj = int(df["PJ"].max())
        rango_pj = st.sidebar.slider("Selecciona un rango de partidos jugados", min_pj, max_pj, (min_pj, max_pj), key="comparativa_pj")
    else:
        st.error("La columna 'PJ' no se encuentra en el archivo Excel.")
        return
    
    df_filtrado = df[df["EQUIPO"] == equipo_seleccionado] if equipo_seleccionado != "Todos" else df.copy()
    df_filtrado = df_filtrado[(df_filtrado["PJ"] >= rango_pj[0]) & (df_filtrado["PJ"] <= rango_pj[1])]
    
    jugadoras = df_filtrado["NOMBRE"].unique()
    jugadora_1 = st.selectbox("Selecciona la primera jugadora", jugadoras, key="jugadora_1")
    jugadora_2 = st.selectbox("Selecciona la segunda jugadora", jugadoras, key="jugadora_2")
    
    if jugadora_1 and jugadora_2:
        jugadora_1_data = df[df["NOMBRE"] == jugadora_1]
        jugadora_2_data = df[df["NOMBRE"] == jugadora_2]
        st.write(f"#### Estadísticas de {jugadora_1} y {jugadora_2}")
        st.write(jugadora_1_data)
        st.write(jugadora_2_data)

if st.sidebar.radio("Selecciona una página", ["Filtros y Datos", "Búsqueda de Jugadoras", "Comparativa de Jugadoras"]) == "Comparativa de Jugadoras":
    pagina_comparativa()

