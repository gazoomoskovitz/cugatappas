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
        df = pd.read_csv(url, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

@st.cache_data
def cargar_csv():
    archivo = "productos bd web.csv"
    if os.path.exists(archivo):
        try:
            # Intento inteligente de lectura
            df = pd.read_csv(archivo, sep=None, dtype=str, engine='python', on_bad_lines='skip')
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Si el CSV se lee mal (una sola columna), forzamos división
            if len(df.columns) == 1:
                col = df.columns[0]
                df = df[col].str.split(',', n=2, expand=True) if ',' in str(df.iloc[0]) else df[col].str.split(';', n=2, expand=True)
                df.columns = ['CODIGO', 'NOMBRE PRODUCTO', 'PRECIO']
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
    st.markdown('<div style="display: flex; justify-content: center; filter: brightness(0) invert(1);">', unsafe_allow_html=True)
    st.image("Logo-cugat-web.png", width=90)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Buscador</h1>", unsafe_allow_html=True)

modo = st.pills("Base:", ["Autoservicio (Nube)", "Cugat Osorno (Local)"], default="Autoservicio (Nube)")

df = cargar_csv() if "Local" in modo else cargar_online()
busqueda = st.text_input("🔍 Buscar...", placeholder="Escribe nombre o código...")

# --- 4. FILTRADO UNIVERSAL (REPARADO) ---
df_f = pd.DataFrame()

if not df.empty:
    # Identificamos columnas por posición si los nombres fallan
    # Col 0 suele ser Código, Col 1 suele ser Nombre
    col_codigo = 'CODIGO' if 'CODIGO' in df.columns else df.columns[0]
    col_nombre = 'NOMBRE PRODUCTO' if 'NOMBRE PRODUCTO' in df.columns else ('DETALLE' if 'DETALLE' in df.columns else df.columns[min(1, len(df.columns)-1)])

    if busqueda:
        # Buscamos en todas las columnas para no fallar
        mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_f = df[mask].head(20)
    else:
        # Mostramos los primeros 20 por defecto si no hay búsqueda
        df_f = df.head(20)

# --- 5. RENDERIZADO COMPACTO ---
IMAGEN_CONEJO = "conejo-cugat-ico.png"

for index, row in df_f.iterrows():
    st.markdown('<div class="tarjeta-producto">', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([0.7, 2.3, 1.2])
    
    # Extraer datos de forma segura
    curr_cod = str(row[col_codigo]).split('.')[0] if col_codigo in row else str(row.iloc[0]).split('.')[0]
    curr_nom = str(row[col_nombre]) if col_nombre in row else "Producto sin nombre"
    
    with c1:
        ruta_foto = f"fotos/{curr_cod}.png"
        if os.path.exists(ruta_foto): st.image(ruta_foto)
        elif os.path.exists(IMAGEN_CONEJO): st.image(IMAGEN_CONEJO)
        else: st.image("https://via.placeholder.com/50")

    with c2:
        st.markdown(f"<span class='nombre-producto'>{curr_nom}</span>", unsafe_allow_html=True)
        if 'PRECIO' in df.columns:
            try:
                p = int(float(str(row['PRECIO']).replace('.','').replace(',','')))
                st.markdown(f"<span class='precio-producto'>${p:,}</span>".replace(',','.'), unsafe_allow_html=True)
            except: pass
        st.caption(f"ID: {curr_cod}")

    with c3:
        img_bar = generar_barcode(curr_cod)
        if img_bar:
            st.markdown('<div class="barcode-contenedor">', unsafe_allow_html=True)
            st.image(img_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<center><p style='color:white; opacity: 0.3; font-size: 0.7rem;'>Sistema Cugat 2026</p></center>", unsafe_allow_html=True)
