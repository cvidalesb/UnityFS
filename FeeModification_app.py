import streamlit as st
import pandas as pd

# Importar componentes y pantallas
from components.header import show_header
from screens.home_screen import show_home_screen
from screens.fee_modification_screen import show_fee_modification_screen
from screens.contact_screen import show_contact_screen
from screens.virtual_account_screen import show_virtual_account_screen
from screens.transfer_screen import show_transfer_screen
from screens.transfer_fee_screen import show_transfer_fee_screen
from screens.transfers_analytics_screen import show_transfers_analytics_screen

# --- NUEVO: Función para limpiar los campos de formularios ---
def limpiar_formularios():
    # Campos del formulario de fee_modification
    for key in [
        'customer_id', 'liq_address', 'fee_val', 'api_key',
        # Campos del formulario de virtual_account
        'source_currency', 'destination_currency', 'payment_rail', 'address', 'blockchain_memo', 'bridge_wallet_id',
    ]:
        if key in st.session_state:
            del st.session_state[key]


def main():
    """Función principal de la aplicación"""
    
    # Configuración de la página
    st.set_page_config(
        page_title="Unity Financial Services",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Mostrar header en todas las pantallas
    show_header()
    
    # Sidebar para selección de pantalla
    st.sidebar.markdown("## Navegación")
    # --- NUEVO: selectbox con key y manejo de cambio de pantalla ---
    pantalla_actual = st.session_state.get("pantalla", "Inicio")
    pantalla = st.sidebar.selectbox(
        "Selecciona una pantalla",
        ["Inicio", "Liquidation Address Fee", "Transfers", "Análisis de Transferencias", "Crear virtual account", "Contacto"],
        key="pantalla"
    )
    # Si la pantalla cambió, limpiar formularios
    if pantalla != pantalla_actual:
        limpiar_formularios()
        st.session_state["pantalla"] = pantalla
    
    # Información adicional en el sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Información")
    st.sidebar.markdown("**Versión**: 1.0.0")
    st.sidebar.markdown("**Desarrollado por**: Unity Financial Services")
    
    # Mostrar la pantalla correspondiente
    if pantalla == "Inicio":
        show_home_screen()
    elif pantalla == "Liquidation Address Fee":
        show_fee_modification_screen()
    elif pantalla == "Transfers":
        show_transfer_fee_screen()
    elif pantalla == "Análisis de Transferencias":
        show_transfers_analytics_screen()
    elif pantalla == "Crear virtual account":
        show_virtual_account_screen()
    #elif pantalla == "Transfer":
    #    show_transfer_screen()
    elif pantalla == "Contacto":
        show_contact_screen()

if __name__ == "__main__":
    main()
