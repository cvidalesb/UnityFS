import streamlit as st
from utils.api_functions import update_static_transfer_fee
from utils.pdf_generator import generate_wire_transfer_pdf
import pandas as pd
from datetime import datetime
from utils.api_functions import create_transfer
from utils.logging_functions import save_transfer_log, get_transfer_logs


def create_transfer_payload(transfer_type, form_data):
    """Create the API payload based on transfer type"""
    payload = {
        "client_reference_id": form_data["client_id"],
        "amount": form_data["amount"],
        "on_behalf_of": form_data["on_behalf_of"],
        "developer_fee": form_data["developer_fee"]
    }
    
    if transfer_type == "crypto_to_crypto":
        payload["source"] = {
            "payment_rail": form_data["from_rail"],
            "currency": form_data["from_currency"],
            "from_address": form_data["from_address"]
        }
        payload["destination"] = {
            "payment_rail": form_data["to_rail"],
            "currency": form_data["to_currency"],
            "to_address": form_data["to_address"]
        }
    
    elif transfer_type == "crypto_to_fiat":
        payload["source"] = {
            "payment_rail": form_data["from_rail_crypto"],
            "currency": form_data["from_currency_crypto"],
            "from_address": form_data["from_address_crypto"]
        }
        payload["destination"] = {
            "payment_rail": form_data["to_rail_fiat"],
            "currency": form_data["to_currency_fiat"],
            "to_address": form_data["bank_account"]
        }
        if form_data.get("routing_number"):
            payload["destination"]["routing_number"] = form_data["routing_number"]
    
    elif transfer_type == "fiat_to_crypto":
        payload["source"] = {
            "payment_rail": form_data["from_rail_fiat_in"],
            "currency": form_data["from_currency_fiat_in"],
            "from_address": form_data["bank_account_in"]
        }
        payload["destination"] = {
            "payment_rail": form_data["to_rail_crypto_in"],
            "currency": form_data["to_currency_crypto_in"],
            "to_address": form_data["to_address_crypto_in"]
        }
    
    return payload

def validate_form(transfer_type, form_data):
    """Validate form fields based on transfer type"""
    errors = []
    
    # Common validations
    if not form_data.get("api_key"):
        errors.append("API Key es requerida")
    if not form_data.get("amount"):
        errors.append("Cantidad es requerida")
    if not form_data.get("transfer_type"):
        errors.append("Tipo de transferencia es requerido")
    
    # Transfer type specific validations
    if transfer_type == "crypto_to_crypto":
        required_fields = ["from_rail", "from_currency", "from_address", "to_rail", "to_currency", "to_address"]
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Campo {field} es requerido para Crypto a Crypto")
    
    elif transfer_type == "crypto_to_fiat":
        required_fields = ["from_rail_crypto", "from_currency_crypto", "from_address_crypto", 
                          "to_rail_fiat", "to_currency_fiat", "bank_account"]
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Campo {field} es requerido para Crypto a Fiat")
    
    elif transfer_type == "fiat_to_crypto":
        required_fields = ["from_rail_fiat_in", "from_currency_fiat_in", "bank_account_in",
                          "to_rail_crypto_in", "to_currency_crypto_in", "to_address_crypto_in"]
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Campo {field} es requerido para Fiat a Crypto")
    
    elif transfer_type == "bridge_wallet":
        required_fields = ["bridge_wallet_id", "bridge_wallet_rail", "bridge_wallet_currency", "bridge_wallet_address"]
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Campo {field} es requerido para Bridge Wallet")
    
    elif transfer_type == "wire_transfer":
        required_fields = ["wire_currency", "wire_account", "wire_routing"]
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Campo {field} es requerido para Wire Transfer")
    
    return errors


def show_transfer_fee_screen():
    """Pantalla de modificación de developer fee para transfers"""
    tab1, tab2, tab3 = st.tabs(["Actualizar Developer Fee", "Generar PDF de Transfer", "Static Transfer Template"])
    
    with tab1:
        st.markdown("### Actualizar Developer Fee de Transfer")
        
        # Información adicional
        st.info("Esta herramienta te permite actualizar el developer fee para transfers específicos.")
        
        # Formulario para actualizar developer fee de transfer
        with st.form("transfer_fee_update_form"):
            st.markdown("#### Formulario de actualización de developer fee para transfer")
            
            transfer_id = st.text_input("Transfer ID*", help="Ingresa el ID de la transferencia")
            developer_fee = st.text_input("Developer Fee*", help="Ingresa el fee como porcentaje (ej: 2.5)")
            api_key = st.text_input("API Key*", type="password", help="Ingresa tu clave de API")
            
            submitted_transfer = st.form_submit_button("Actualizar Developer Fee")
        
        # Procesar formulario de transfer
        if submitted_transfer:
            if not all([transfer_id, developer_fee, api_key]):
                st.error("❌ Hay campos vacíos. Por favor completa todos los campos.")
            else:
                with st.spinner("Procesando solicitud de actualización de developer fee..."):
                    try:
                        # Usar la función existente de utils/api_functions
                        status_code, response_text, success = update_static_transfer_fee(
                            transfer_id, developer_fee, api_key
                        )
                        
                        st.subheader("Respuesta de la API")
                        st.code(response_text)
                        
                        if success and status_code == 200:
                            st.success("✅ Developer fee actualizado exitosamente.")
                        elif success:
                            st.warning(f"⚠️ La operación se completó pero con código de estado: {status_code}")
                        else:
                            st.error(f"❌ Error en la actualización: {response_text}")
                            
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
        
    with tab2:
        # Formulario para generar PDF de transfer
        with st.form("pdf_transfer_form"):
            st.markdown("#### Generar PDF de Transfer")
            
            transfer_id = st.text_input("Transfer ID*", help="Ingresa el ID de la transferencia")
            api_key = st.text_input("API Key*", type="password", help="Ingresa tu clave de API")
            
            generate_pdf = st.form_submit_button("Generar PDF")
        
        # Procesar formulario de transfer
        if generate_pdf:
            if not all([transfer_id, api_key]):
                st.error("❌ Hay campos vacíos. Por favor completa todos los campos.")
            else:
                with st.spinner("Generando PDF de transfer..."):
                    try:
                        # Usar la función existente de utils/api_functions
                        output_path = f"TransferenciasPDF/{transfer_id}.pdf"
                        generate_wire_transfer_pdf(transfer_id, api_key, output_path, "Logo.png")
                        
                        st.success("✅ PDF generado exitosamente.")
                        st.info(f"El archivo se ha guardado como: {output_path}")
                            
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
                        

# The make_transfer_request function is now replaced by create_transfer from utils.api_functions

    with tab3:
        """Pantalla de transferencias Bridge"""
        st.markdown("### Bridge Transfer Tool")
        
        # Información adicional
        st.info("Esta herramienta te permite crear transferencias entre diferentes blockchains y payment rails usando la API de Bridge.xyz")
        
        # Crear layout de dos columnas
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Configuración de Transferencia")
            
            # API Key input
            api_key = st.text_input("API Key*", type="password", help="Ingresa tu clave de API de Bridge.xyz")
            
            # Sandbox mode
            #sandbox_mode = st.checkbox("Modo Sandbox", help="Activar para usar el entorno de pruebas")
            
            # Transfer type selection
            transfer_type = st.selectbox(
                "Tipo de Transferencia *",
                ["crypto_to_fiat", "fiat_to_crypto", "crypto_to_crypto"],
                index=0,
                format_func=lambda x: {
                    "fiat_to_crypto": "On Ramp",
                    "crypto_to_crypto": "Crypto a Crypto", 
                    "crypto_to_fiat": "Off Ramp"
                }[x],
                help="Selecciona el tipo de transferencia para mostrar los campos relevantes"
            )
            
            # General information section
            st.markdown("#### Información General")
            
            client_id = st.text_input("Client ID", value="", help="Identificador del cliente")
            amount = st.text_input("Cantidad *", value="", help="Cantidad a transferir (ej: 10.00)")
            on_behalf_of = st.text_input("On Behalf Of", value="", 
                                    help="ID del cliente en cuyo nombre se realiza la transferencia")
            developer_fee = st.text_input("Developer Fee", value="", 
                                        help="Porcentaje de fee del desarrollador")
            
            # Conditional fields based on transfer type
            with col2:
                if transfer_type == "crypto_to_crypto":
                    st.markdown("#### Crypto a Crypto")
                    
                    st.markdown("**📤 Origen (Crypto)**")
                    from_rail = st.selectbox("Payment Rail (Blockchain) *", [
                        "ethereum", "polygon", "arbitrum", "optimism", "base", 
                        "avalanche_c_chain", "solana", "tron"
                    ], format_func=lambda x: x.replace("_", " ").title())
                    from_currency = st.selectbox("Moneda (Origen) *", ["dai","eurc","pyusd","usdb","usdc","usdt"],
                                                help="Moneda de origen (ej: usdt, usdc, dai)")
                    from_address = st.text_input("From Address *", value="", 
                                            help="Dirección de wallet de origen")
                    
                    st.markdown("**📥 Destino (Crypto)**")
                    to_rail = st.selectbox("Payment Rail (Blockchain) *", [
                        "ethereum", "polygon", "arbitrum", "optimism", "base", 
                        "avalanche_c_chain", "solana", "tron"
                    ], format_func=lambda x: x.replace("_", " ").title())
                    to_currency = st.selectbox("Moneda (Origen) *", ["dai","eurc","pyusd","usdb","usdc","usdt"],
                                            help="Moneda de destino (ej: usdc, usdt, dai)")
                    to_address = st.text_input("To Address *", value="", 
                                            help="Dirección de wallet de destino")
                
                elif transfer_type == "crypto_to_fiat":
                    st.markdown("#### Crypto a Fiat")
                    
                    st.markdown("**📤 Origen (Crypto)**")
                    from_rail_crypto = st.selectbox("Payment Rail (Blockchain) *", [
                        "ethereum", "polygon", "arbitrum", "optimism", "base", 
                        "avalanche_c_chain", "solana", "tron"
                    ], format_func=lambda x: x.replace("_", " ").title())
                    from_currency_crypto = st.selectbox("Moneda (Origen) *", ["dai","eurc","pyusd","usdb","usdc","usdt"],
                                                    help="Moneda de origen (ej: usdt, usdc, dai)")
                    from_address_crypto = st.text_input("From Address *", value="", 
                                                    help="Dirección de wallet de origen")
                    
                    st.markdown("**📥 Destino (Fiat)**")
                    to_rail_fiat = st.selectbox("Payment Rail (Destino) *", ["wire", "ach", "sepa", "spei", "swift"], 
                                            format_func=lambda x: x.upper())
                    to_currency_fiat = st.selectbox("Moneda (Destino) *",["usd","eur","mxn"], 
                                                help="Moneda fiat de destino (ej: usd, eur, mxn)")
                    bank_account = st.text_input("Cuenta Bancaria *", help="Número de cuenta bancaria de destino")
                    routing_number = st.text_input("Routing Number", help="Número de routing bancario")
                
                elif transfer_type == "fiat_to_crypto":
                    st.markdown("#### Fiat a Crypto")
                    
                    st.markdown("**📤 Origen (Fiat)**")
                    from_rail_fiat_in = st.selectbox("Payment Rail (Origen) *", ["wire", "ach", "sepa", "spei", "swift"], 
                                                format_func=lambda x: x.upper())
                    from_currency_fiat_in = st.selectbox("Moneda (Origen) *", [
                    "eur", "mxn", "usd"])
                    bank_account_in = st.text_input("Cuenta Bancaria *", help="Número de cuenta bancaria de origen")
                    
                    st.markdown("**📥 Destino (Crypto)**")
                    to_rail_crypto_in = st.selectbox("Payment Rail (Blockchain) *", [
                        "ethereum", "polygon", "arbitrum", "optimism", "base", 
                        "avalanche_c_chain", "solana", "tron"
                    ], format_func=lambda x: x.replace("_", " ").title())
                    to_currency_crypto_in = st.selectbox("Moneda (Destino) *", ["dai","eurc","pyusd","usdb","usdc","usdt"], 
                                                        help="Moneda de destino (ej: usdc, usdt, dai)")
                    to_address_crypto_in = st.text_input("To Address *", value="", 
                                                    help="Dirección de wallet de destino")
                
            # Submit button
            if st.button("🚀 Enviar Transferencia", type="primary"):
                if not api_key:
                    st.error("❌ API Key es requerida")
                    return
                
                # Collect form data
                form_data = {
                    "transfer_type": transfer_type,
                    "client_id": client_id,
                    "on_behalf_of": on_behalf_of,
                    "amount": amount,
                    "developer_fee": developer_fee,
                    "api_key": api_key
                }
                
                # Add conditional fields
                if transfer_type == "crypto_to_crypto":
                    form_data.update({
                        "from_rail": from_rail,
                        "from_currency": from_currency,
                        "from_address": from_address,
                        "to_rail": to_rail,
                        "to_currency": to_currency,
                        "to_address": to_address
                    })
                elif transfer_type == "crypto_to_fiat":
                    form_data.update({
                        "from_rail_crypto": from_rail_crypto,
                        "from_currency_crypto": from_currency_crypto,
                        "from_address_crypto": from_address_crypto,
                        "to_rail_fiat": to_rail_fiat,
                        "to_currency_fiat": to_currency_fiat,
                        "bank_account": bank_account,
                        "routing_number": routing_number
                    })
                elif transfer_type == "fiat_to_crypto":
                    form_data.update({
                        "from_rail_fiat_in": from_rail_fiat_in,
                        "from_currency_fiat_in": from_currency_fiat_in,
                        "bank_account_in": bank_account_in,
                        "to_rail_crypto_in": to_rail_crypto_in,
                        "to_currency_crypto_in": to_currency_crypto_in,
                        "to_address_crypto_in": to_address_crypto_in
                    })
                
                # Validate form
                errors = validate_form(transfer_type, form_data)
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                    return
                
                # Show loading
                with st.spinner("🔄 Procesando transferencia..."):
                    # Create payload
                    payload = create_transfer_payload(transfer_type, form_data)
                    
                    # Make API request
                    response = create_transfer(api_key, payload)
                    
                    # Store response in session state
                    st.session_state.transfer_response = response
                    
                    # Save log
                    source_info = payload.get("source", {})
                    destination_info = payload.get("destination", {})
                    log_saved = save_transfer_log(
                        transfer_type, amount, source_info, destination_info, 
                        response["status_code"], response
                    )
                    
                    # Show result
                    if response["success"]:
                        st.success("✅ Transferencia creada correctamente!")
                        if log_saved:
                            st.info("📝 Registro guardado en el archivo de logs.")
                    else:
                        st.error(f"❌ Error en la transferencia: {response['status_code']}")
        
        
            # API Response section
        if hasattr(st.session_state, 'transfer_response') and st.session_state.transfer_response:
            st.markdown("#### Respuesta de la API")
            
            response = st.session_state.transfer_response
            
            # Response details
            st.metric("Status Code", response["status_code"])
            st.metric("Success", "✅ Sí" if response["success"] else "❌ No")
            st.metric("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            st.metric("Environment", "Production")
            
            # Response data
            st.markdown("**📄 Datos de Respuesta**")
            st.json(response["data"])
            
            # Headers (if available)
            if response.get("headers"):
                with st.expander("📋 Headers de Respuesta"):
                    st.json(response["headers"])
        else:
            st.info("👈 Completa el formulario y envía para ver la respuesta de la API.")
        
        # Mostrar historial de transferencias
        st.markdown("---")
        st.markdown("### Historial de transferencias recientes")
        
        try:
            logs_df = get_transfer_logs(limit=10)
            
            if not logs_df.empty:
                # Formatear la tabla para mejor visualización
                display_df = logs_df.copy()
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                display_df = display_df[['timestamp', 'transfer_type', 'amount', 'source_rail', 'destination_rail', 'status_code']]
                display_df.columns = ['Fecha', 'Tipo', 'Cantidad', 'Origen', 'Destino', 'Estado']
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No hay registros de transferencias previas.")
        except Exception as e:
            st.warning(f"No se pudieron cargar los registros: {e}")
        
        # Mostrar información adicional
        st.markdown("---")
        st.markdown("### Información sobre Transferencias")
        st.markdown("""
        **Tipos de transferencia disponibles:**
        - **Fiat a Crypto**: Transferir desde cuentas bancarias a wallets de criptomonedas
        - **Crypto a Crypto**: Transferir entre diferentes blockchains y criptomonedas
        - **Crypto a Fiat**: Transferir desde wallets de criptomonedas a cuentas bancarias
        
        **Payment Rails soportados:**
        - **Crypto**: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche C-Chain, Solana, Tron
        - **Fiat**: Wire, ACH, SEPA
        """) 
                        
