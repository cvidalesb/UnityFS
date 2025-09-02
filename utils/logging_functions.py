import pandas as pd
import os
from datetime import datetime
import json
import csv
import io
from collections.abc import MutableMapping

def save_fee_log(customer_id, liq_address, fee_val, status_code, response_text, csv_file="registro_fees.csv"):
    """
    Guarda un registro de la operación de modificación de fee en un archivo CSV.
    
    Args:
        customer_id (str): ID del cliente
        liq_address (str): Dirección de liquidación
        fee_val (str): Valor del fee
        status_code (int): Código de estado de la respuesta
        response_text (str): Texto de respuesta de la API
        csv_file (str): Nombre del archivo CSV (por defecto: registro_fees.csv)
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "customer_id": customer_id,
        "liq_address": liq_address,
        "fee_val": fee_val,
        "status_code": status_code,
        "response": response_text
    }

    df_log = pd.DataFrame([log_entry])
    
    try:
        if os.path.isfile(csv_file):
            df_log.to_csv(csv_file, mode='a', header=False, index=False)
        else:
            df_log.to_csv(csv_file, index=False)
        return True
    except Exception as e:
        print(f"Error al guardar el log: {e}")
        return False

def get_fee_logs(csv_file="registro_fees.csv", limit=50):
    """
    Obtiene los registros de fees desde el archivo CSV.
    
    Args:
        csv_file (str): Nombre del archivo CSV
        limit (int): Número máximo de registros a retornar
    
    Returns:
        pandas.DataFrame: DataFrame con los registros
    """
    try:
        if os.path.isfile(csv_file):
            df = pd.read_csv(csv_file)
            return df.tail(limit)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error al leer el archivo de logs: {e}")
        return pd.DataFrame() 
    
def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ','.join(map(str, v))))
        else:
            items.append((new_key, v))
    return dict(items)

def json_response_to_flat_csv_bytes(json_string):
    data = json.loads(json_string)
    rows = [flatten_dict(item) for item in data['data']]
    headers = sorted({k for row in rows for k in row.keys()})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def save_transfer_log(transfer_type, amount, source_info, destination_info, status_code, response_data, csv_file="registro_transfers.csv"):
    """
    Guarda un registro de la operación de transferencia en un archivo CSV.
    
    Args:
        transfer_type (str): Tipo de transferencia
        amount (str): Cantidad transferida
        source_info (dict): Información del origen
        destination_info (dict): Información del destino
        status_code (int): Código de estado de la respuesta
        response_data (dict): Datos de respuesta de la API
        csv_file (str): Nombre del archivo CSV (por defecto: registro_transfers.csv)
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "transfer_type": transfer_type,
        "amount": amount,
        "source_rail": source_info.get("payment_rail", ""),
        "source_currency": source_info.get("currency", ""),
        "destination_rail": destination_info.get("payment_rail", ""),
        "destination_currency": destination_info.get("currency", ""),
        "status_code": status_code,
        "success": response_data.get("success", False),
        "response_id": response_data.get("data", {}).get("id", ""),
        "error_message": response_data.get("data", {}).get("error", "")
    }

    df_log = pd.DataFrame([log_entry])
    
    try:
        if os.path.isfile(csv_file):
            df_log.to_csv(csv_file, mode='a', header=False, index=False)
        else:
            df_log.to_csv(csv_file, index=False)
        return True
    except Exception as e:
        print(f"Error al guardar el log de transferencia: {e}")
        return False


def get_transfer_logs(csv_file="registro_transfers.csv", limit=50):
    """
    Obtiene los registros de transferencias desde el archivo CSV.
    
    Args:
        csv_file (str): Nombre del archivo CSV
        limit (int): Número máximo de registros a retornar
    
    Returns:
        pandas.DataFrame: DataFrame con los registros
    """
    try:
        if os.path.isfile(csv_file):
            df = pd.read_csv(csv_file)
            return df.tail(limit)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error al leer el archivo de logs de transferencias: {e}")
        return pd.DataFrame()