import streamlit as st
import pandas as pd
import os
import barcode
import base64
from barcode.writer import ImageWriter
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cugat App", page_icon="👑", layout="centered")

def cargar_estilos():
    if os.path.exists("styles.css"):
        with open("styles.css", "r", encoding="utf-8", errors="ignore") as f:
            css = f.read()
        if os.path.exists("BRUSHSCI.ttf"):
            with open("BRUSHSCI.ttf", "rb") as f:
                font_64 = base64.b64encode(f.read()).decode()
            css = css.replace("BASE64_DATA", font_64)
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

cargar_estilos()

# --- 2. UTILIDADES ---
def img_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def generar_barcode_base64(codigo_texto, zoom=False):
    if not codigo_texto or pd.isna(codigo_texto): return ""
    try:
        cod_clean = str(codigo_texto).split('.')[0].strip()
        COD = barcode.get_barcode_class('code128')
        options = {
            "write_text": True,
            "font_size": 12 if zoom else 10,
            "text_distance": 5 if zoom else 4, 
            "quiet_zone": 5.0 if zoom else 2.0,
            "module_height": 20.0 if zoom else 15.0
        }
        codigo = COD(cod_clean, writer=ImageWriter())
        buffer = BytesIO()
        codigo.write(buffer, options=options)
        return base64.b64encode(buffer.getvalue()).decode()
    except: return ""

@st.dialog("CÓDIGO DE BARRAS", width="large")
def mostrar_zoom(nombre, codigo):
    st.markdown(f"### {nombre}")
    b64 = generar_barcode_base64(codigo, zoom=True)
    if b64:
        html_zoom = f"""
        <div style="display:flex; justify-content:center; width:100%; background-color:white; padding:10px 10px 30px 10px; border-radius:8px;">
            <img class="img-zoom-barcode" src="data:image/png;base64,{b64}">
        </div>
        """
        st.markdown(html_zoom, unsafe_allow_html=True)
        st.markdown(f"**ID:** `{codigo}`")

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=10)
def cargar_online():
    SHEET_ID = "1Wf2WxlVh0UdQJG3vhE-EUDr15E3cPE3n8iqHd0b7If4"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=productos"
    try:
        df = pd.read_csv(url, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

@st.cache_data
def cargar_local(archivo):
    if os.path.exists(archivo):
        try:
            if archivo.endswith('.xlsx'):
                df = pd.read_excel(archivo, dtype=str)
            else:
                df = pd.read_csv(archivo, sep=None, dtype=str, engine='python', on_bad_lines='skip')
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 4. INTERFAZ ---
logo_b64 = img_to_base64("Logo-cugat-web.png")
if logo_b64:
    st.markdown(f'<div style="display:flex; justify-content:center; filter:brightness(0) invert(1); padding-bottom:10px;"><img src="data:image/png;base64,{logo_b64}" width="110"></div>', unsafe_allow_html=True)

st.markdown("<h1>Buscador de Productos</h1>", unsafe_allow_html=True)

opciones = {
    "☁️ Autoservicio (Nube)": "NUBE",
    "🏠 Cugat Osorno (Local)": "LOCAL",
    "🍎 Frutas y Verduras": "PERECIBLES",
    "🥩 Carnicería": "PERECIBLES_CARNE",
    "🥖 Panadería": "PERECIBLES_PAN",
    "🍗 Rotisería": "PERECIBLES_ROTI",
    "🍱 Platos Preparados": "PERECIBLES_PLATOS"
}

seleccion = st.selectbox("📍 Seleccione un Área:", list(opciones.keys()))
modo = opciones[seleccion]

archivos = {
    "LOCAL": "productos-bd-web.csv",
    "PERECIBLES": "MaestraPLU_FFVV.xlsx",
    "PERECIBLES_CARNE": "MaestraPLU_Carniceria.xlsx",
    "PERECIBLES_PAN": "MaestraPLU_Panaderia.xlsx",
    "PERECIBLES_ROTI": "MaestraPLU_Rotiseria.xlsx",
    "PERECIBLES_PLATOS": "MaestraPLU_PPreparados.xlsx"
}

if modo == "NUBE":
    df = cargar_online()
else:
    df = cargar_local(archivos.get(modo, "productos-bd-web.csv"))

busqueda = st.text_input("🔍 Buscar...", placeholder="Escribe nombre o código...")

# --- 5. RENDERIZADO ---
if not df.empty:
    cols = df.columns.tolist()
    col_codigo = next((c for c in cols if any(x in c for x in ["NRO_PLU", "COD"])), cols[0])
    col_nombre = next((c for c in cols if any(x in c for x in ["DESCRIPCION L1", "NOM", "PRODUCTO", "DETALLE"])), cols[1] if len(cols)>1 else cols[0])
    col_precio = next((c for c in cols if "PRE" in c), None)

    if busqueda:
        mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_f = df[mask].head(15)
    else:
        df_f = df.head(15)

    IMAGEN_CONEJO_64 = img_to_base64("conejo-cugat-ico.png")

    for idx, row in df_f.iterrows():
        cod = str(row[col_codigo]).split('.')[0]
        nom = str(row[col_nombre])
        img_prod = img_to_base64(f"fotos/{cod}.png")
        final_img = img_prod if img_prod else IMAGEN_CONEJO_64
        
        # Formateo de Precio
        p_txt = "---"
        if col_precio:
            try:
                p_val = int(float(str(row[col_precio]).replace('.','').replace(',','')))
                p_txt = f"${p_val:,}".replace(',', '.')
            except: p_txt = f"${row[col_precio]}"

        # --- LÓGICA DE VISUALIZACIÓN ---
        # Verificamos si la pestaña actual es de perecederos
        es_perecible = modo.startswith("PERECIBLES")

        if not es_perecible:
            # DISEÑO NORMAL PARA NUBE Y LOCAL (Con Barcode abajo)
            b64_bar = generar_barcode_base64(cod)
            st.markdown(f"""
            <div class="tarjeta-producto">
                <div class="fila-datos">
                    <img class="img-fija" src="data:image/png;base64,{final_img}">
                    <div class="contenedor-texto">
                        <div class="nombre-producto">{nom}</div>
                        <div class="precio-producto">{p_txt}</div>
                        <div style="color: #aaa; font-size: 0.7rem;">ID: {cod}</div>
                    </div>
                </div>
                <div class="barcode-container">
                    <img class="barcode-fijo" src="data:image/png;base64,{b64_bar}">
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔍 AMPLIAR CÓDIGO", key=f"btn_{modo}_{cod}_{idx}"):
                mostrar_zoom(nom, cod)
        
        else:
            # DISEÑO PARA PERECIBLES (PLU Grande a la derecha)
            st.markdown(f"""
            <div class="tarjeta-producto">
                <div class="fila-perecedero">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <img class="img-fija" src="data:image/png;base64,{final_img}">
                        <div class="contenedor-texto">
                            <div class="nombre-producto">{nom}</div>
                            <div class="precio-producto">{p_txt}</div>
                        </div>
                    </div>
                    <div class="plu-resaltado">
                        <span class="plu-etiqueta">ID/PLU</span>
                        {cod}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.info(f"Seleccione una opción o verifique el archivo.")

st.markdown("<center><p style='color:white; opacity: 0.2; font-size: 0.7rem; margin-top:30px;'>Informatica Cugat Osorno - 2026</p></center>", unsafe_allow_html=True)