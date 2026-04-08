import streamlit as st
import pandas as pd
import os
import barcode
import base64
import time
import extra_streamlit_components as stx
from barcode.writer import ImageWriter
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- CONFIGURACIÓN Y CARGA ---
load_dotenv()
USUARIO_REAL = os.getenv("USER_CUGAT")
CLAVE_REAL = os.getenv("PASS_CUGAT")

st.set_page_config(page_title="Cugat App", layout="centered")

# --- GESTOR DE COOKIES ---
def iniciar_cookie_manager():
    return stx.CookieManager()

cookie_manager = iniciar_cookie_manager()

def cargar_recursos():
    if os.path.exists("BRUSHSCI.ttf"):
        with open("BRUSHSCI.ttf", "rb") as f:
            font_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            @font-face {{
                font-family: 'BrushScript';
                src: url(data:font/ttf;base64,{font_data}) format('truetype');
            }}

            /* FONDO COMBINADO: Naranja a Negro */
            .stApp {{
                background: radial-gradient(circle, #FD8204 0%, #1a0d00 70%, #000000 100%) !important;
                background-attachment: fixed !important;
            }}

            /* LOGO BLANCO (Solo para el login) */
            .logo-blanco img {{
                filter: brightness(0) invert(1) !important;
            }}
            
            /* Títulos */
            h1, h2, h3 {{
                color: #FFFFFF !important;
                font-family: 'BrushScript', cursive !important;
                text-align: center;
            }}
            
            /* Tarjetas de productos */
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background-color: rgba(0, 0, 0, 0.4) !important;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(253, 130, 4, 0.3) !important;
                border-radius: 15px;
            }}
            </style>
            """, unsafe_allow_html=True)
    
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_recursos()

# --- FUNCIONES DE DATOS ---
@st.cache_data(show_spinner=False, ttl=10)
def cargar_datos():
    if os.path.exists('productos.xlsx'):
        df = pd.read_excel('productos.xlsx')
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df.sort_values(by='NOMBRE PRODUCTO')
    return pd.DataFrame(columns=['CODIGO', 'NOMBRE PRODUCTO', 'PRECIO'])

def generar_barcode(numero_codigo):
    try:
        COD = barcode.get_barcode_class('code128')
        codigo = COD(str(numero_codigo), writer=ImageWriter())
        buffer = BytesIO()
        codigo.write(buffer)
        return buffer
    except:
        return None

# --- LÓGICA DE LOGIN CON PERSISTENCIA (CORREGIDA PARA F5) ---
sesion_activa = cookie_manager.get('usuario_cugat')

# Si no está marcado como ingresado en esta ejecución, revisamos la cookie
if not st.session_state.get('ingresado'):
    if sesion_activa:
        st.session_state['ingresado'] = True
    else:
        # Espera estratégica de 0.5s para que el manager lea la cookie tras un F5
        time.sleep(0.5)
        sesion_activa = cookie_manager.get('usuario_cugat')
        if sesion_activa:
            st.session_state['ingresado'] = True
            st.rerun()

# --- INTERFAZ DE LOGIN ---
if not st.session_state.get('ingresado'):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("Logo-cugat-web.png"):
            st.markdown('<div class="logo-blanco">', unsafe_allow_html=True)
            st.image("Logo-cugat-web.png", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<h1>Acceso Cajas</h1>", unsafe_allow_html=True)
        user = st.text_input("Usuario", key="user_login")
        passw = st.text_input("Contraseña", type="password", key="pass_login")
        
        if st.button("Ingresar", use_container_width=True):
            if user == USUARIO_REAL and passw == CLAVE_REAL:
                st.session_state['ingresado'] = True
                # Guardamos sesión por 1 hora
                expira = datetime.now() + timedelta(hours=1)
                cookie_manager.set('usuario_cugat', 'sesion_valida', expires_at=expira)
                st.success("Acceso concedido")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# --- APP PRINCIPAL (Solo accesible tras Login) ---
st.markdown("<h1>Buscador de Productos</h1>", unsafe_allow_html=True)

# Botón para cerrar sesión manual
if st.sidebar.button("Cerrar Sesión"):
    cookie_manager.delete('usuario_cugat')
    st.session_state['ingresado'] = False
    st.rerun()

df = cargar_datos()
busqueda = st.text_input("Buscar...", placeholder="Escribe nombre o código...")

df_f = df[df['NOMBRE PRODUCTO'].str.contains(busqueda, case=False, na=False) | 
          df['CODIGO'].astype(str).str.contains(busqueda, na=False)] if busqueda else df

for index, row in df_f.iterrows():
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.8, 2.2, 2.0])
        with c1:
            ruta = f"fotos/{row['CODIGO']}.png"
            st.image(ruta if os.path.exists(ruta) else "https://via.placeholder.com/60", width=70)
        with c2:
            st.markdown(f"**{row['NOMBRE PRODUCTO']}**")
            if 'PRECIO' in row and pd.notna(row['PRECIO']):
                try:
                    p_val = int(float(row['PRECIO']))
                    st.markdown(f"<span style='color: #FD8204; font-size: 1.6rem; font-weight: bold;'>${p_val:,}</span>".replace(",", "."), unsafe_allow_html=True)
                except: pass
            st.caption(f"ID: {row['CODIGO']}")
        with c3:
            img_buffer = generar_barcode(row['CODIGO'])
            if img_buffer:
                st.markdown('<div style="background-color: white; padding: 10px; border-radius: 8px; display: flex; justify-content: center;">', unsafe_allow_html=True)
                st.image(img_buffer, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: rgba(255,255,255,0.6); padding-bottom: 20px;'>
        <h3 style='font-family: "BrushScript", cursive; font-size: 1.6rem; margin-bottom: 0px;'>
            Desarrollado por Informática Cugat Osorno
        </h3>
        <p style='font-size: 0.85rem;'>Año 2026 - Osorno, Chile</p>
    </div>
    """, 
    unsafe_allow_html=True
)