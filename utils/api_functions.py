import requests
import uuid

def get_liquidation_address_id(customer_id, address_to_find, api_key):
    """
    Obtiene el ID de la dirección de liquidación para un cliente específico.
    
    Args:
        customer_id (str): ID del cliente
        address_to_find (str): Dirección de wallet a buscar
        api_key (str): Clave de API para autenticación
    
    Returns:
        str or None: ID de la dirección de liquidación si se encuentra, None en caso contrario
    """
    url = f"https://api.bridge.xyz/v0/customers/{customer_id}/liquidation_addresses?limit=100"
    headers = {
        "accept": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error al hacer la petición: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        for item in data.get("data", []):
            if item["address"].lower() == address_to_find.lower():
                return item
        
        print(f"No se encontró ningún ID para la address {address_to_find}")
        return None
        
    except Exception as e:
        print(f"Error en la petición: {e}")
        return None
    

def update_static_transfer_fee(transfer_id, fee_value, api_key):
    """
    Returns:
        tuple: (status_code, response_text, success)
    """
    url = f"https://api.bridge.xyz/v0/transfers/{transfer_id}"
    payload = {"developer_fee_percent": fee_value}
    headers = {
    "Api-Key": api_key,
    "Content-Type": "application/json"
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        return response.status_code, response.text, True
    except Exception as e:
        return None, str(e), False 
    

def update_developer_fee(customer_id, liquidation_address_id, fee_value, api_key):
    """
    Actualiza el developer fee para una dirección de liquidación específica.
    
    Args:
        customer_id (str): ID del cliente 
        liquidation_address_id (str): ID de la dirección de liquidación
        fee_value (str): Valor del fee como porcentaje
        api_key (str): Clave de API para autenticación
    
    Returns:
        tuple: (status_code, response_text, success)
    """
    url = f"https://api.bridge.xyz/v0/customers/{customer_id}/liquidation_addresses/{liquidation_address_id}"
    payload = {"custom_developer_fee_percent": fee_value}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        return response.status_code, response.text, True
    except Exception as e:
        return None, str(e), False 
    
def create_virtual_accounts(customer_id, source_currency, destination_currency, payment_rail, address, blockchain_memo, bridge_wallet_id, developer_fee_percent, api_key):

    url = f"https://api.bridge.xyz/v0/customers/{customer_id}/virtual_accounts"

    payload = {
        "source": { "currency": source_currency },
        "destination": {
            "currency": destination_currency,
            "payment_rail": payment_rail,
            "address": address,
            "blockchain_memo": blockchain_memo,
            "bridge_wallet_id": bridge_wallet_id
        },
        "developer_fee_percent": developer_fee_percent
    }
    headers = {
        "accept": "application/json",
        "Idempotency-Key": customer_id+address+source_currency+destination_currency+payment_rail,
        "content-type": "application/json",
        "Api-Key": api_key
    }

    response = requests.post(url, json=payload, headers=headers)
    
    return response.status_code, response.text, True

def get_virtual_accounts(customer_id, api_key):

    url = f"https://api.bridge.xyz/v0/customers/{customer_id}/virtual_accounts"

    headers = {
        "accept": "application/json",
        "Api-Key": api_key
    }

    response = requests.get(url, headers=headers)
    
    return response.status_code, response.text, True


def create_transfer(api_key, payload):
    """
    Crea una transferencia usando la API de Bridge.xyz
    
    Args:
        api_key (str): Clave de API para autenticación
        payload (dict): Payload de la transferencia
    
    Returns:
        dict: Respuesta de la API con status_code, success, data y headers
    """
    url = "https://api.bridge.xyz/v0/transfers"
    
    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4())
    }

    try:
        print("--------------------------------")
        print(headers)
        print(payload)
        print("--------------------------------")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return {
            "status_code": response.status_code,
            "success": response.ok,
            "data": response.json() if response.ok else {"error": response.text},
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "data": {"error": f"Error de conexión: {str(e)}"},
            "headers": {}
        }
    
def fetch_client_data(customer_id, api_key):
    """
    Fetch client data from the API.
    
    Args:
        customer_id: Customer ID to fetch
        api_key: API authentication key
    
    Returns:
        Client data as dictionary
    
    Raises:
        requests.RequestException: If API request fails
    """
    url = f"https://api.bridge.xyz/v0/customers/{customer_id}"
    headers = {"Api-Key": api_key}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_transfer_data(transfer_id, api_key):
    """
    Fetch transfer data from the API.
    
    Args:
        transfer_id: Transfer ID to fetch
        api_key: API authentication key
    
    Returns:
        Transfer data as dictionary
    
    Raises:
        requests.RequestException: If API request fails
    """
    url = f"https://api.bridge.xyz/v0/transfers/{transfer_id}"
    headers = {"Api-Key": api_key}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

