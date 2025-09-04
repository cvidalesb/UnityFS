from typing import Dict, Any, Iterable, Tuple
from datetime import datetime
from psycopg2.extensions import connection as PgConnection

# --- 1) Flattener (same idea as before) ---
def _flatten(d: Dict[str, Any], parent: str = "", sep: str = "_") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        nk = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            out.update(_flatten(v, nk, sep))
        elif isinstance(v, list):
            # Let psycopg2 adapt Python lists into PG arrays when target col is TEXT[]
            out[nk] = v
        else:
            out[nk] = v
    return out

# --- 2) Column map (JSON key -> DB column) ---
# Keys that arrive nested will be flattened by `_flatten` first.
KEY_TO_COL = {
    # top-level
    "id": "id",
    "client_reference_id": "client_reference_id",
    "state": "state",
    "on_behalf_of": "on_behalf_of",
    "amount": "amount",
    "developer_fee": "developer_fee",
    "currency": "currency",
    "created_at": "created_at",
    "updated_at": "updated_at",

    # source
    "source_payment_rail": "source_payment_rail",
    "source_currency": "source_currency",
    "source_from_address": "source_from_address",
    "source_external_account_id": "source_external_account_id",
    "source_bridge_wallet_id": "source_bridge_wallet_id",
    "source_bank_beneficiary_name": "source_bank_beneficiary_name",
    "source_bank_routing_number": "source_bank_routing_number",
    "source_bank_account_number": "source_bank_account_number",
    "source_bank_name": "source_bank_name",
    "source_imad": "source_imad",
    "source_omad": "source_omad",
    "source_payment_scheme": "source_payment_scheme",

    # destination
    "destination_payment_rail": "destination_payment_rail",
    "destination_currency": "destination_currency",
    "destination_to_address": "destination_to_address",
    "destination_external_account_id": "destination_external_account_id",
    "destination_bridge_wallet_id": "destination_bridge_wallet_id",
    "destination_wire_message": "destination_wire_message",
    "destination_sepa_reference": "destination_sepa_reference",
    "destination_swift_reference": "destination_swift_reference",
    "destination_spei_reference": "destination_spei_reference",
    "destination_swift_charges": "destination_swift_charges",
    "destination_ach_reference": "destination_ach_reference",
    "destination_blockchain_memo": "destination_blockchain_memo",
    "destination_deposit_id": "destination_deposit_id",
    "destination_imad": "destination_imad",

    # source_deposit_instructions (SDI)
    "source_deposit_instructions_payment_rail": "sdi_payment_rail",
    "source_deposit_instructions_payment_rails": "sdi_payment_rails",
    "source_deposit_instructions_amount": "sdi_amount",
    "source_deposit_instructions_currency": "sdi_currency",
    "source_deposit_instructions_deposit_message": "sdi_deposit_message",
    "source_deposit_instructions_from_address": "sdi_from_address",
    "source_deposit_instructions_to_address": "sdi_to_address",
    "source_deposit_instructions_bank_beneficiary_name": "sdi_bank_beneficiary_name",
    "source_deposit_instructions_bank_routing_number": "sdi_bank_routing_number",
    "source_deposit_instructions_bank_account_number": "sdi_bank_account_number",
    "source_deposit_instructions_bank_name": "sdi_bank_name",
    "source_deposit_instructions_iban": "sdi_iban",
    "source_deposit_instructions_bic": "sdi_bic",
    "source_deposit_instructions_account_holder_name": "sdi_account_holder_name",
    "source_deposit_instructions_bank_address": "sdi_bank_address",

    # receipt
    "receipt_initial_amount": "receipt_initial_amount",
    "receipt_developer_fee": "receipt_developer_fee",
    "receipt_exchange_fee": "receipt_exchange_fee",
    "receipt_subtotal_amount": "receipt_subtotal_amount",
    "receipt_gas_fee": "receipt_gas_fee",  # normalized (see below)
    "receipt_final_amount": "receipt_final_amount",
    "receipt_source_tx_hash": "receipt_source_tx_hash",
    "receipt_destination_tx_hash": "receipt_destination_tx_hash",
    "receipt_url": "receipt_url",

    # features
    "features_flexible_amount": "features_flexible_amount",
    "features_static_template": "features_static_template",
    "features_allow_any_from_address": "features_allow_any_from_address",
}

# --- 3) Normalizers for known quirks/variants ---
def _normalize(flat: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(flat)

    # Bridge doc typo: 'receipt_gas_fe' -> 'receipt_gas_fee'
    if "receipt_gas_fe" in out and "receipt_gas_fee" not in out:
        out["receipt_gas_fee"] = out["receipt_gas_fe"]

    # created_at / updated_at may be ISO strings with 'Z'
    for tkey in ("created_at", "updated_at"):
        if tkey in out and isinstance(out[tkey], str):
            s = out[tkey]
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                out[tkey] = datetime.fromisoformat(s)
            except Exception:
                # Let PG cast the string if parsing fails
                pass

    return out

# --- 4) Build parameterized UPSERT ---
def upsert_bridge_transfer(conn: PgConnection, transfer_json: Dict[str, Any]) -> Tuple[int, int]:
    """
    Flattens + normalizes Bridge transfer JSON and upserts into bridge_transfers.
    Returns (rowcount, inserted_columns_count) for debugging/metrics.
    """
    flat = _flatten(transfer_json)
    norm = _normalize(flat)

    # Map known keys to columns; ignore unknown keys
    cols: Iterable[str] = []
    vals: Iterable[Any] = []
    for k, col in KEY_TO_COL.items():
        if k in norm:
            cols = list(cols) + [col]
            vals = list(vals) + [norm[k]]

    if "id" not in transfer_json:
        raise ValueError("transfer_json missing required 'id'")

    # Build SQL safely (placeholders via psycopg2)
    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    set_list = ", ".join([f"{c}=EXCLUDED.{c}" for c in cols if c != "id"])

    sql = f"""
        INSERT INTO bridge_transfers ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE
        SET {set_list}
    """

    with conn.cursor() as cur:
        cur.execute(sql, tuple(vals))
    conn.commit()
    return (1, len(cols))
