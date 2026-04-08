import streamlit as st
import pandas as pd
import os
import barcode
import base64
from barcode.writer import ImageWriter
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cugat App Autoservicio", page_icon="👑", layout="centered")

def cargar_estilos():
    if os.path.exists("styles.css"):
        with open("styles.css", "r") as f:
            css = f.read()
        if os.path.exists("BRUSHSCI.ttf"):
            with open("BRUSHSCI.ttf", "rb") as f:
                font_64 = base64.b64encode(f.read()).decode()
            css = css.replace("BASE64_DATA", font_64)
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

cargar_estilos()

# --- 2. FUNCIONES DE CARGA ---
@st.cache_data(ttl=10)
def cargar_online():
    SHEET_ID = "1Wf2WxlVh0UdQJG3vhE-EUDr15E3cPE3n8iqHd0b7If4"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=productos"
    try:
        df = pd.read_csv(url, dtype={'CODIGO': str})
        df.columns = [str(c).strip().upper() for c in df.columns]
        if 'DETALLE' in df.columns: df.rename(columns={'DETALLE': 'NOMBRE PRODUCTO'}, inplace=True)
        return df
    except: return pd.DataFrame(columns=['CODIGO', 'NOMBRE PRODUCTO', 'PRECIO'])

@st.cache_data
def cargar_csv():
    archivo = "productos bd web.csv"
    if os.path.exists(archivo):
        try:
            df = pd.read_csv(archivo, sep=',', dtype=str, engine='python', on_bad_lines='skip')
            df.columns = [str(c).strip().upper() for c in df.columns]
            if len(df.columns) == 1:
                col = df.columns[0]
                nuevo_df = df[col].str.split(',', n=2, expand=True)
                nuevo_df.columns = ['CODIGO', 'NOMBRE PRODUCTO', 'PRECIO']
                df = nuevo_df
            if 'DETALLE' in df.columns: df.rename(columns={'DETALLE': 'NOMBRE PRODUCTO'}, inplace=True)
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

def generar_barcode(numero_codigo):
    if not numero_codigo or pd.isna(numero_codigo): return None
    try:
        cod_clean = str(numero_codigo).split('.')[0].strip()
        COD = barcode.get_barcode_class('code128')
        codigo = COD(cod_clean, writer=ImageWriter())
        buffer = BytesIO()
        codigo.write(buffer)
        return buffer
    except: return None

# --- 3. INTERFAZ ---
if os.path.exists("Logo-cugat-web.png"):
    st.markdown('<div class="logo-contenedor" style="display: flex; justify-content: center; filter: brightness(0) invert(1);">', unsafe_allow_html=True)
    st.image("Logo-cugat-web.png", width=110)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Buscador de Productos</h1>", unsafe_allow_html=True)

modo = st.pills("Base de Datos:", ["Autoservicio (Nube)", "Buscador General (Cugat Osorno)"], default="Autoservicio (Nube)")

df = cargar_csv() if modo == "Buscador General (Cugat Osorno)" else cargar_online()
busqueda = st.text_input("🔍 Buscar...", placeholder="Nombre o código...")

if busqueda and not df.empty:
    mask = (df['NOMBRE PRODUCTO'].astype(str).str.contains(busqueda, case=False, na=False) | 
            df['CODIGO'].astype(str).str.contains(busqueda, na=False))
    df_f = df[mask].head(25)
else:
    df_f = df.head(25) if (modo == "Autoservicio (Nube)" and not df.empty) else pd.DataFrame()

# --- 4. RENDERIZADO HORIZONTAL ---
IMAGEN_PREDETERMINADA = "conejo-cugat-ico.png"

for index, row in df_f.iterrows():
    st.markdown('<div class="tarjeta-producto">', unsafe_allow_html=True)
    
    # Tres columnas: [Imagen, Info Centro, Código Barras]
    col_img, col_info, col_bar = st.columns([0.6, 2.4, 1.5])
    raw_code = str(row.get('CODIGO', '000')).split('.')[0]
    
    with col_img:
        st.markdown('<div class="img-producto">', unsafe_allow_html=True)
        ruta_foto = f"fotos/{raw_code}.png"
        if os.path.exists(ruta_foto): st.image(ruta_foto)
        elif os.path.exists(IMAGEN_PREDETERMINADA): st.image(IMAGEN_PREDETERMINADA)
        else: st.image("https://via.placeholder.com/60")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_info:
        st.markdown(f"<span class='nombre-producto'>{row.get('NOMBRE PRODUCTO', 'Sin nombre')}</span>", unsafe_allow_html=True)
        if 'PRECIO' in row:
            try:
                p = int(float(str(row['PRECIO']).replace('.','').replace(',','')))
                st.markdown(f"<span class='precio-producto'>${p:,}</span>".replace(',','.'), unsafe_allow_html=True)
            except: pass
        st.caption(f"ID: {raw_code}")
    
    with col_bar:
        img_bar = generar_barcode(row.get('CODIGO'))
        if img_bar:
            st.markdown('<div class="barcode-contenedor">', unsafe_allow_html=True)
            st.image(img_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><center><p style='color:white; opacity: 0.3; font-size: 0.7rem;'>Sistema Cugat 2026</p></center>", unsafe_allow_html=True)
