import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO
from PIL import Image

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect("jugadoras.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS valoraciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        posicion TEXT,
                        club TEXT,
                        valoracion INTEGER,
                        comentario TEXT
                    )''')

    cursor.execute("PRAGMA table_info(valoraciones)")
    columnas = [col[1] for col in cursor.fetchall()]
    if "captador" not in columnas:
        cursor.execute("ALTER TABLE valoraciones ADD COLUMN captador TEXT")

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

st.title("Análisis y Scouting de Jugadoras de 1-2 RFEF")

pagina = st.sidebar.radio("Selecciona una página", ["Scouting", "Filtros y Datos", "Búsqueda de Jugadoras", "Comparativa de Jugadoras"], key="pagina_principal")

def get_file_path():
    github_url = "https://github.com/RobertoRicobaldi/SQLite123RFEF/raw/main/Jugadoras_123Total13marzo2025.xlsx"
    response = requests.get(github_url)
    if response.status_code == 200:
        return github_url
    else:
        st.error("Error: No se encontró el archivo Excel en GitHub.")
        return None

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
            st.error("Error al descargar el archivo desde GitHub.")
            return pd.DataFrame()

        return data
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("No se pudo cargar el archivo de datos o está vacío.")

def cargar_escudos():
    try:
        url_escudos = "https://github.com/RobertoRicobaldi/123RFEF/raw/main/00_Modelo%20de%20datos%20-%20Primera%20RFEF%2024-25.xlsx"
        response = requests.get(url_escudos)
        if response.status_code == 200:
            excel_data = BytesIO(response.content)
            df_escudos = pd.read_excel(excel_data, engine='openpyxl')
            return dict(zip(df_escudos["EQUIPO"], df_escudos["URL_ESCUDO"]))
        else:
            st.error("No se pudo cargar el archivo de escudos.")
            return {}
    except Exception as e:
        st.error(f"Error al cargar escudos: {e}")
        return {}

escudos_dict = cargar_escudos()

def mostrar_tabla_con_escudos(df):
    df = df.copy()
    df["ESCUDO"] = df["EQUIPO"].apply(lambda eq: f'<img src="{escudos_dict.get(eq, "")}" width="30">' if eq in escudos_dict else "")
    columnas = ["ESCUDO", "EQUIPO", "NOMBRE", "EDAD"] + [col for col in df.columns if col not in ["ESCUDO", "EQUIPO", "NOMBRE", "EDAD"]]
    df = df[columnas]
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# SCOUTING
if pagina == "Scouting":
    st.header("Scouting de Jugadoras")

    jugadoras = df["NOMBRE"].dropna().unique()
    seleccionada = st.selectbox("Selecciona una jugadora", ["Selecciona una jugadora"] + list(jugadoras), key="scouting_jugadora")

    if seleccionada and seleccionada != "Selecciona una jugadora":
        datos_jugadora = df[df["NOMBRE"] == seleccionada]
        st.write(f"### Datos de {seleccionada}")
        mostrar_tabla_con_escudos(datos_jugadora)

st.write("### Agregar valoración")
captador = st.text_input("Nombre del captador")
valoracion = st.selectbox("Valoración", [3, 5, 7, 9], key="valoracion")
comentario = st.text_area("Comentario")

if st.button("Guardar valoración"):
    if captador and comentario:
        with st.spinner("Guardando valoración..."):
            if not datos_jugadora.empty:
                if "POS" in datos_jugadora.columns and pd.notna(datos_jugadora.iloc[0]["POS"]):
                    posicion = datos_jugadora.iloc[0]["POS"]
                else:
                    posicion = "Sin posición"

                if "EQUIPO" in datos_jugadora.columns and pd.notna(datos_jugadora.iloc[0]["EQUIPO"]):
                    club = datos_jugadora.iloc[0]["EQUIPO"]
                else:
                    club = "Sin club"

                agregar_valoracion(captador, seleccionada, posicion, club, valoracion, comentario)
                st.success("Valoración guardada correctamente.")
            else:
                st.error("No se encontraron datos de la jugadora seleccionada.")
                st.stop()
    else:
        st.error("Por favor, completa todos los campos.")

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

# Página: Filtros y Datos
elif pagina == "Filtros y Datos":
    st.subheader("Filtros y Datos Generales")
    equipos = df["EQUIPO"].dropna().unique()
    equipo_seleccionado = st.sidebar.selectbox("Selecciona un equipo", ["Todos"] + list(equipos))

    df_filtrado = df if equipo_seleccionado == "Todos" else df[df["EQUIPO"] == equipo_seleccionado]
    st.write("### Vista previa de jugadoras")
    mostrar_tabla_con_escudos(df_filtrado.head(10))

    st.write("### Ranking por Goles")
    if "Goles" in df_filtrado.columns:
        ranking = df_filtrado.sort_values(by="Goles", ascending=False).head(10)
        mostrar_tabla_con_escudos(ranking)

st.write("### 🏆 Ranking de Jugadoras Más Valoradas")

valoraciones_df = pd.DataFrame(obtener_valoraciones(), columns=["ID", "Captador", "Nombre", "Posición", "Club", "Valoración", "Comentario"])
ranking = valoraciones_df.groupby("Nombre").agg(
    Media_Valoracion=("Valoración", "mean"),
    Num_Valoraciones=("Valoración", "count")
).sort_values(by="Media_Valoracion", ascending=False).head(10)

st.table(ranking.reset_index())

# Página: Búsqueda de Jugadoras
if pagina == "Búsqueda de Jugadoras":
    st.subheader("Búsqueda de Jugadoras")

    # Filtros adicionales
    st.sidebar.markdown("### Filtros de búsqueda")
    edad_min = int(df["EDAD"].min()) if "EDAD" in df.columns else 15
    edad_max = int(df["EDAD"].max()) if "EDAD" in df.columns else 45
    edad_range = st.sidebar.slider("Rango de Edad", edad_min, edad_max, (edad_min, edad_max))

    pj_min = int(df["PJ"].min()) if "PJ" in df.columns else 0
    pj_max = int(df["PJ"].max()) if "PJ" in df.columns else 30
    pj_range = st.sidebar.slider("Rango de Partidos Jugados", pj_min, pj_max, (pj_min, pj_max))

    # Aplicar filtros
    df_filtrado = df.copy()
    if "EDAD" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["EDAD"] >= edad_range[0]) & (df_filtrado["EDAD"] <= edad_range[1])]
    if "PJ" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["PJ"] >= pj_range[0]) & (df_filtrado["PJ"] <= pj_range[1])]

    jugadoras = df_filtrado["NOMBRE"].dropna().unique()
    seleccionada = st.selectbox("Selecciona una jugadora", jugadoras, key="busqueda_jugadora")

    if seleccionada:
        datos = df_filtrado[df_filtrado["NOMBRE"] == seleccionada]
        st.write(f"### Datos de {seleccionada}")
        mostrar_tabla_con_escudos(datos)

        st.write("### Valoraciones de captadores")

        @st.cache_data
        def get_valoraciones():
            return pd.DataFrame(obtener_valoraciones(), columns=["ID", "Captador", "Nombre", "Posición", "Club", "Valoración", "Comentario"])

        valoraciones_df = get_valoraciones()
        valoraciones_filtradas = valoraciones_df[valoraciones_df["Nombre"] == seleccionada]

        if not valoraciones_filtradas.empty:
            for _, fila in valoraciones_filtradas.iterrows():
                with st.expander(f"📋 {fila['Captador']} - ⭐ {'⭐' * int(fila['Valoración'])} ({fila['Valoración']})"):
                    nuevo_comentario = st.text_area(f"Editar comentario ({fila['ID']})", value=fila['Comentario'], key=f"comentario_{fila['ID']}")
                    if st.button(f"Actualizar comentario ({fila['ID']})"):
                        conn = sqlite3.connect("jugadoras.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE valoraciones SET comentario = ? WHERE id = ?", (nuevo_comentario, fila['ID']))
                        conn.commit()
                        conn.close()
                        st.success("Comentario actualizado.")

            # Mostrar media de valoraciones
            media = valoraciones_filtradas["Valoración"].mean()
            st.write(f"📊 **Media de valoraciones:** {media:.2f}")
        else:
            st.write("Sin valoraciones registradas.")

# Página: Comparativa de Jugadoras
    elif pagina == "Comparativa de Jugadoras":
        st.write("### Comparativa de Jugadoras")
        st.write("Selecciona dos jugadoras para comparar sus estadísticas.")

    if "EQUIPO" in df.columns:
        equipos = df["EQUIPO"].unique()
        equipo_seleccionado = st.sidebar.selectbox("Selecciona un equipo", ["Todos"] + list(equipos), key="comparativa_equipo")
    else:
        st.error("La columna 'EQUIPO' no se encuentra en el archivo Excel.")
        st.stop()

    if "PJ" in df.columns:
        min_pj = int(df["PJ"].min())
        max_pj = int(df["PJ"].max())
        rango_pj = st.sidebar.slider("Selecciona un rango de partidos jugados", min_pj, max_pj, (min_pj, max_pj), key="comparativa_pj")
    else:
        st.error("La columna 'PJ' no se encuentra en el archivo Excel.")
        st.stop()

    df_filtrado = df[df["EQUIPO"] == equipo_seleccionado] if equipo_seleccionado != "Todos" else df.copy()
    df_filtrado = df_filtrado[(df_filtrado["PJ"] >= rango_pj[0]) & (df_filtrado["PJ"] <= rango_pj[1])]

    jugadoras = df_filtrado["NOMBRE"].dropna().unique()
    jugadora_1 = st.selectbox("Selecciona la primera jugadora", jugadoras, key="jugadora_1")
    jugadora_2 = st.selectbox("Selecciona la segunda jugadora", jugadoras, key="jugadora_2")

    if jugadora_1 and jugadora_2:
        st.write("### Valoraciones registradas")

# Mostrar media de valoraciones
    if not valoraciones_filtradas.empty:
        media = valoraciones_filtradas["Valoración"].mean()
        st.write(f"📊 **Media de valoraciones:** {media:.2f}")

    # ✅ Añadir esta línea para evitar el NameError
    valoraciones_df = pd.DataFrame(obtener_valoraciones(), columns=["ID", "Captador", "Nombre", "Posición", "Club", "Valoración", "Comentario"])

    for jugadora in [jugadora_1, jugadora_2]:
        st.write(f"#### {jugadora}")
        valoraciones_jugadora = valoraciones_df[valoraciones_df["Nombre"] == jugadora]
        if not valoraciones_jugadora.empty:
            for _, fila in valoraciones_jugadora.iterrows():
                st.write(f"📋 **Captador:** {fila['Captador']}")
                st.write(f"⭐ Valoración: {'⭐' * int(fila['Valoración'])} ({fila['Valoración']})")
                st.write(f"📝 Comentario: {fila['Comentario']}")
                st.write("---")
        else:
            st.write("Sin valoraciones registradas.")

    # Después de mostrar valoraciones, el radar y barras
    jugadora_1_data = df[df["NOMBRE"] == jugadora_1]
    jugadora_2_data = df[df["NOMBRE"] == jugadora_2]

    st.write(f"#### Estadísticas de {jugadora_1} y {jugadora_2}")
    st.write(jugadora_1_data)
    st.write(jugadora_2_data)

    st.write("#### Radar Chart Comparativo")
    metricas = ["Goles", "Asist.", "TA", "TR", "PJ"]
    valores_1 = jugadora_1_data[metricas].sum().tolist()
    valores_2 = jugadora_2_data[metricas].sum().tolist()

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=valores_1, theta=metricas, fill='toself', name=jugadora_1))
    fig_radar.add_trace(go.Scatterpolar(r=valores_2, theta=metricas, fill='toself', name=jugadora_2))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    st.plotly_chart(fig_radar)

    st.write("#### Gráfico de Barras Comparativo")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=metricas, y=valores_1, name=jugadora_1))
    fig_bar.add_trace(go.Bar(x=metricas, y=valores_2, name=jugadora_2))
    fig_bar.update_layout(barmode='group', title="Comparativa de Métricas", xaxis_title="Métricas", yaxis_title="Valor")
    st.plotly_chart(fig_bar)

