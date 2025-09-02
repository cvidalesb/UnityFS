import streamlit as st

def show_home_screen():
    """Pantalla de inicio"""
    st.markdown("## Bienvenido a Unity Financial Services")
    st.markdown("Selecciona una opción del menú lateral para comenzar.")
    
    # Información adicional de la página de inicio
    st.markdown("### Servicios disponibles:")
    st.markdown("- **Modificación de Developer Fee**: Actualiza las tarifas de desarrollador")
    st.markdown("- **Transfer Fee**: Actualiza el developer fee de transfers específicos")
    st.markdown("- **Crear virtual account**: Crea una virtual account para un cliente")
    st.markdown("- **Transfer**: Crea transferencias entre diferentes blockchains y payment rails")
    st.markdown("- **Contacto**: Información de contacto y soporte")
    
    st.markdown("---")
    st.markdown("*Sistema de gestión de tarifas financieras*") 