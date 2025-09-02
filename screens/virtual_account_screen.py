
import streamlit as st
import pandas as pd
import json
from utils.api_functions import get_liquidation_address_id, update_developer_fee, create_virtual_accounts    
from utils.logging_functions import save_fee_log
from utils.api_functions import get_virtual_accounts
from utils.logging_functions import json_response_to_flat_csv_bytes

def show_virtual_account_screen():
    """Pantalla de creación de virtual account"""
    st.markdown("### Virtual Account")
    
    # Información adicional
    #st.info("Esta herramienta te permite actualizar el developer fee para direcciones de liquidación específicas.")


    
    # Variable para almacenar la información de la dirección
    liq_address_info = None
    
    
    # --- Entradas del formulario ---
    with st.form("fee_modification_form"):
        
        customer_id = st.text_input("Customer ID* ", help="Ingresa el UUID del cliente")
        # Cambiar currency a un selectbox
        source_currency = st.selectbox("Source Currency*", options=["usd", "eur", "mxn"], help="Selecciona la moneda")
        destination_currency = st.selectbox("Destination Currency*", options=["usdb", "usdc", "usdt", "dai", "pyusd", "eurc"], help="Selecciona la moneda")
        payment_rail = st.selectbox("Payment Rail*", options=[ "arbitrum",  "avalanche_c_chain",  "base",  "ethereum",  "optimism", "polygon", "solana", "stellar", "tron" ], help="Selecciona la red")
        address = st.text_input("Address", help="The crypto wallet address that the customer wishes to ultimately receive funds at")
        blockchain_memo = st.text_input("Blockchain Memo", help="The memo to include when sending funds on chain. Only allowed for blockchains that support memos such as Stellar")
        bridge_wallet_id = st.text_input("Bridge Wallet ID", help="The Bridge Wallet to which Bridge will send the funds. The chain associated with the Bridge Wallet must match the payment rail.")
        developer_fee_percent = st.text_input("Developer Fee", help="Developer fee percentage")
        api_key = st.text_input("API Key* ", type="password", help="Ingresa tu clave de API")
        
        submitted = st.form_submit_button("Crear virtual account")
    
    # --- Procesar formulario ---
    if submitted:
        if not all([customer_id, source_currency, destination_currency, payment_rail, api_key]):
            st.error("❌ Hay campos vacíos. Por favor completa todos los campos.")
        else:
            with st.spinner("Procesando solicitud..."):


                status_code, response_text, success = create_virtual_accounts(customer_id, source_currency, destination_currency, payment_rail, address, blockchain_memo, bridge_wallet_id, developer_fee_percent, api_key)
                
                
                if success:
                    st.subheader("Respuesta de la API")
                    st.code(response_text)
                    
                    if status_code == 201:
                        st.success("✅ Virtual account creada exitosamente.")
                        # --- NUEVO: Botón para descargar la información de la cuenta creada ---
                        
                        try:
                            response_dict = json.loads(response_text)
                        except Exception:
                            response_dict = {"error": "No se pudo parsear la respuesta como JSON"}
                        st.download_button(
                            label="Descargar información de la cuenta",
                            data=json.dumps(response_dict, indent=2, ensure_ascii=False),
                            file_name="virtual_account_info.json",
                            mime="application/json"
                        )
                    else:
                        st.warning(f"⚠️ La operación se completó pero con código de estado: {status_code}")
                else:
                    st.error(f"❌ Error inesperado: {response_text}")
                    
    st.markdown("### Client accounts")

    
    with st.form("Download client accounts"):
        
        customer_id = st.text_input("Customer ID* ", help="Ingresa el UUID del cliente")
        api_key = st.text_input("API Key* ", type="password", help="Ingresa tu clave de API")
        
        clientaccount_csv = st.form_submit_button("Download client accounts")
    
    if clientaccount_csv:
        print(customer_id)
        print(api_key)
        if  all([customer_id, api_key]):

            status_code, response_text, success = get_virtual_accounts(customer_id, api_key)
            print(response_text)
            
            if success:

                try:
                    csv_bytes = json_response_to_flat_csv_bytes(response_text)
                    st.download_button(
                        label="Descargar CSV",
                        data=csv_bytes,
                        file_name="client_accounts.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error procesando el JSON: {e}")
                    