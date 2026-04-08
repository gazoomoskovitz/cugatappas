import streamlit as st
import pandas as pd
import os
import barcode
import base64
import time
from barcode.writer import ImageWriter
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cugat App", page_icon="👑", layout="centered")

# --- ESTILOS PERSONALIZADOS (Diseño original de GitHub) ---
def cargar_estilos():
    if os.path.exists("BRUSHSCI.ttf"):
        with open("BRUSHSCI.ttf", "rb") as f:
            font_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            @font-face {{
                font-family: 'BrushScript';
                src: url(data:font/ttf;base64,{font_data}) format('truetype');
            }}
            .stApp {{
                background: radial-gradient(circle, #FD8204 0%, #1a0d00 70%, #000000 100%) !important;
                background-attachment: fixed !important;
            }}
            .logo-blanco img {{
                filter: brightness(0) invert(1) !important;
            }}
            h1, h2, h3 {{
                color: #FFFFFF !important;
                font-family: 'BrushScript', cursive !important;
                text-align: center;
            }}
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background-color: rgba(0, 0, 0, 0.4) !important;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(253, 130, 4, 0.3) !important;
                border-radius: 15px;
            }}
            </style>
            """, unsafe_allow_html=True)

cargar_estilos()

# --- CARGA DE DATOS (Google Sheets con Precio Opcional) ---
@st.cache_data(ttl=5, show_spinner=False)
def cargar_datos():
    SHEET_ID = "1Wf2WxlVh0UdQJG3vhE-EUDr15E3cPE3n8iqHd0b7If4" 
    SHEET_NAME = "productos" 
    url_gsheets = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    df = None
    try:
        df = pd.read_csv(url_gsheets)
        df.columns = [str(c).strip().upper() for c in df.columns]
    except Exception:
        if os.path.exists('productos.xlsx'):
            try:
                df = pd.read_excel('productos.xlsx')
                df.columns = [str(c).strip().upper() for c in df.columns]
            except: pass
    
    if df is not None:
        # Renombrar columnas si vienen con nombres distintos
        if 'NOMBRE PRODUCTO' not in df.columns and 'NOMBRE' in df.columns:
            df.rename(columns={'NOMBRE': 'NOMBRE PRODUCTO'}, inplace=True)
        if 'CODIGO' not in df.columns and 'COD' in df.columns:
            df.rename(columns={'COD': 'CODIGO'}, inplace=True)
            
        return df.sort_values(by='NOMBRE PRODUCTO')
    
    return pd.DataFrame(columns=['CODIGO', 'NOMBRE PRODUCTO'])

def generar_barcode(numero_codigo):
    try:
        COD = barcode.get_barcode_class('code128')
        codigo = COD(str(numero_codigo), writer=ImageWriter())
        buffer = BytesIO()
        codigo.write(buffer)
        return buffer
    except:
        return None

# --- CUERPO DE LA APP (SIN LOGIN) ---

# Mostrar Logo original
if os.path.exists("Logo-cugat-web.png"):
    st.markdown('<div class="logo-blanco" style="display: flex; justify-content: center; margin-bottom: 20px;">', unsafe_allow_html=True)
    st.image("Logo-cugat-web.png", width=180)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Buscador de Productos</h1>", unsafe_allow_html=True)

df = cargar_datos()
busqueda = st.text_input("Buscar...", placeholder="Escribe nombre o código...")

if busqueda:
    df_filtrado = df[df['NOMBRE PRODUCTO'].astype(str).str.contains(busqueda, case=False, na=False) | 
                     df['CODIGO'].astype(str).str.contains(busqueda, na=False)]
else:
    df_filtrado = df 

# --- RENDERIZADO ---
for index, row in df_filtrado.iterrows():
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.8, 2.2, 2.0])
        
        with c1:
            ruta_foto = f"fotos/{row['CODIGO']}.png"
            if os.path.exists(ruta_foto):
                st.image(ruta_foto, width=70)
            else:
                st.image("https://via.placeholder.com/60", width=70)
        
        with c2:
            st.markdown(f"**{row['NOMBRE PRODUCTO']}**")
            
            # Solo mostrar precio si la columna existe en la planilla
            if 'PRECIO' in row and pd.notna(row['PRECIO']):
                try:
                    p_val = int(float(row['PRECIO']))
                    st.markdown(f"<span style='color: #FD8204; font-size: 1.6rem; font-weight: bold;'>${p_val:,}</span>".replace(",", "."), unsafe_allow_html=True)
                except:
                    pass
            
            st.caption(f"ID: {row['CODIGO']}")
            
        with c3:
            buffer_bar = generar_barcode(row['CODIGO'])
            if buffer_bar:
                st.markdown('<div style="background-color: white; padding: 10px; border-radius: 8px; display: flex; justify-content: center;">', unsafe_allow_html=True)
                st.image(buffer_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: rgba(255,255,255,0.6); padding-bottom: 20px;'>
        <h3 style='font-family: "BrushScript", cursive; font-size: 1.6rem; margin-bottom: 0px;'>
            Desarrollado para Cugat
        </h3>
        <p style='font-size: 0.85rem;'>Sistema de Consulta 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
