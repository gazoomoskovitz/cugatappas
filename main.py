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

# --- 2. FUNCIONES DE UTILIDAD ---
def img_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def generar_barcode_base64(codigo_texto):
    if not codigo_texto or pd.isna(codigo_texto): return ""
    try:
        cod_clean = str(codigo_texto).split('.')[0].strip()
        COD = barcode.get_barcode_class('code128')
        codigo = COD(cod_clean, writer=ImageWriter())
        buffer = BytesIO()
        codigo.write(buffer)
        return base64.b64encode(buffer.getvalue()).decode()
    except: return ""

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
def cargar_csv():
    archivo = "productos bd web.csv"
    if os.path.exists(archivo):
        try:
            df = pd.read_csv(archivo, sep=None, dtype=str, engine='python', on_bad_lines='skip')
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 4. INTERFAZ ---
st.markdown("<h1>Buscador</h1>", unsafe_allow_html=True)
modo = st.pills("Base:", ["Autoservicio (Nube)", "Cugat Osorno (Local)"], default="Autoservicio (Nube)")

df = cargar_csv() if "Local" in modo else cargar_online()
busqueda = st.text_input("🔍 Buscar...", placeholder="Escribe nombre o código...")

if not df.empty:
    col_codigo = 'CODIGO' if 'CODIGO' in df.columns else df.columns[0]
    col_nombre = 'NOMBRE PRODUCTO' if 'NOMBRE PRODUCTO' in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])

    if busqueda:
        mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_f = df[mask].head(15)
    else:
        df_f = df.head(15)

    # --- 5. RENDERIZADO ---
    IMAGEN_CONEJO_64 = img_to_base64("conejo-cugat-ico.png")

    for _, row in df_f.iterrows():
        cod = str(row[col_codigo]).split('.')[0]
        nom = str(row[col_nombre])
        
        # Imagen
        img_prod = img_to_base64(f"fotos/{cod}.png")
        final_img = img_prod if img_prod else IMAGEN_CONEJO_64
        
        # Precio
        try:
            p_val = int(float(str(row['PRECIO']).replace('.','').replace(',','')))
            precio_html = f"<div class='precio-producto'>${p_val:,}</div>".replace(',', '.')
        except:
            precio_html = f"<div class='precio-producto'>${row.get('PRECIO', '---')}</div>"

        # Barcode
        b64_bar = generar_barcode_base64(cod)
        
        # HTML SIN ESPACIOS AL INICIO DE LÍNEA
        card = f'<div class="tarjeta-producto"><div class="fila-datos"><img class="img-fija" src="data:image/png;base64,{final_img}"><div class="contenedor-texto"><div class="nombre-producto">{nom}</div>{precio_html}<div style="color: #aaa; font-size: 0.7rem;">ID: {cod}</div></div></div><img class="barcode-fijo" src="data:image/png;base64,{b64_bar}"></div>'
        
        st.markdown(card, unsafe_allow_html=True)

st.markdown("<center><p style='color:white; opacity: 0.3; font-size: 0.7rem;'>Sistema Cugat 2026</p></center>", unsafe_allow_html=True)