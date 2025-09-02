import streamlit as st

def show_header(logo_width=150):
    """
    Muestra el header con logo y título
    
    Args:
        logo_width (int): Ancho del logo en píxeles (por defecto 150)
        title_size (str): Tamaño del título ('h1', 'h2', 'h3', etc.) (por defecto 'h2')
    """
    col1, col2 = st.columns([3, 1])
    with col1:
       
        st.header("UNITY FINANCIAL SERVICES")

    
    with col2:
        try:
            st.image("Logo.png", width=logo_width)
        except:
            st.warning("No se encontró la imagen 'Logo.png'")
    
    st.markdown("---")