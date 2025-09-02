# -*- coding: utf-8 -*-
"""
Wire Transfer PDF Generator
Generates professional PDF documents for wire transfer information.
"""

import os
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# API Configuration
API_BASE_URL = "https://api.bridge.xyz/v0"
API_ENDPOINTS = {
    "transfers": "/transfers",
    "customers": "/customers"
}

# PDF Layout Configuration
PDF_CONFIG = {
    "page_size": landscape(A4),
    "margins": {
        "left": 18 * mm,
        "right": 18 * mm,
        "top": 28 * mm,
        "bottom": 15 * mm
    },
    "logo": {
        "width": 28 * mm,
        "height": 12 * mm
    },
    "table_proportions": {
        "label": 0.32,  # 32% for labels
        "value": 0.68   # 68% for values
    }
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_money(amount_str: str, currency: str = "USD") -> str:
    """
    Format monetary amounts with proper currency formatting.
    
    Args:
        amount_str: Amount as string
        currency: Currency code (default: USD)
    
    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    try:
        amount = float(amount_str)
        if currency.upper() == "USD":
            return f"${amount:,.2f}"
        return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return str(amount_str)

def format_date(iso_str: str) -> str:
    """
    Convert ISO date string to readable format.
    
    Args:
        iso_str: ISO format date string
    
    Returns:
        Formatted date string (e.g., "Feb 14, 2025")
    """
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return str(iso_str)

def format_address(address_dict: dict) -> str:
    """
    Combine address components into a single formatted string.
    
    Args:
        address_dict: Dictionary containing address fields
    
    Returns:
        Formatted address string
    """
    if not address_dict:
        return ""
    
    address_parts = [
        address_dict.get("street_line_1", ""),
        address_dict.get("street_line_2", ""),
        address_dict.get("city", ""),
        address_dict.get("state", ""),
        address_dict.get("postal_code", ""),
        address_dict.get("country", "")
    ]
    
    # Filter out empty parts and join with commas
    return ", ".join([part for part in address_parts if part and str(part).strip()])

# =============================================================================
# PDF STYLE DEFINITIONS
# =============================================================================

def create_pdf_styles():
    """
    Create and return all PDF styles used in the document.
    
    Returns:
        Dictionary containing all paragraph styles
    """
    styles = getSampleStyleSheet()
    
    # Section header style
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading4"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
    )
    
    # Label style for table headers
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        wordWrap="CJK",
    )
    
    # Value style for table data
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        wordWrap="CJK",
    )
    
    return {
        "section": section_style,
        "label": label_style,
        "value": value_style
    }

# =============================================================================
# TABLE CREATION HELPERS
# =============================================================================

def create_paragraph_rows(data_rows: list, styles: dict) -> list:
    """
    Convert raw data rows to Paragraph objects for better text handling.
    
    Args:
        data_rows: List of [label, value] pairs
        styles: Dictionary containing label and value styles
    
    Returns:
        List of [Paragraph(label), Paragraph(value)] pairs
    """
    formatted_rows = []
    for label, value in data_rows:
        label_para = Paragraph(str(label or ""), styles["label"])
        value_para = Paragraph(str(value or ""), styles["value"])
        formatted_rows.append([label_para, value_para])
    return formatted_rows

def create_data_table(rows: list, column_widths: list) -> Table:
    """
    Create a styled table with proper alignment and padding.
    
    Args:
        rows: Formatted rows with Paragraph objects
        column_widths: List of column widths
    
    Returns:
        Styled Table object
    """
    table = Table(rows, colWidths=column_widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table

def create_section_header(title: str, styles: dict) -> list:
    """
    Create a section header with title and horizontal line.
    
    Args:
        title: Section title
        styles: Dictionary containing styles
    
    Returns:
        List containing title paragraph and horizontal line
    """
    return [
        Paragraph(title, styles["section"]),
        HRFlowable(
            width="40%", 
            thickness=0.2, 
            lineCap='round',
            color="black", 
            spaceBefore=0, 
            spaceAfter=2, 
            hAlign='LEFT'
        )
    ]

# =============================================================================
# DATA EXTRACTION HELPERS
# =============================================================================

def extract_transfer_data(transfer_json: dict) -> dict:
    """
    Extract and format key transfer data from API response.
    
    Args:
        transfer_json: Raw transfer data from API
    
    Returns:
        Dictionary containing formatted transfer data
    """
    amount = format_money(
        transfer_json.get("amount", ""), 
        transfer_json.get("currency", "USD")
    )
    created_at = format_date(transfer_json.get("created_at", ""))
    status = transfer_json.get("state", "").capitalize()
    
    source_data = transfer_json.get("source", {})
    imad = source_data.get("imad", "")
    omad = source_data.get("omad", "")
    from_account = transfer_json.get("on_behalf_of", "")
    account_type = source_data.get("payment_rail", "")
    
    return {
        "amount": amount,
        "created_at": created_at,
        "status": status,
        "imad": imad,
        "omad": omad,
        "from_account": from_account,
        "account_type": account_type.upper(),
        "transfer_id": transfer_json.get("id", ""),
        "reference_id": transfer_json.get("client_reference_id", ""),
        "deposit_instructions": transfer_json.get("source_deposit_instructions", {})
    }

def extract_client_data(client_json: dict) -> dict:
    """
    Extract and format client data from API response.
    
    Args:
        client_json: Raw client data from API
    
    Returns:
        Dictionary containing formatted client data
    """
    first_name = client_json.get("first_name", "")
    last_name = client_json.get("last_name", "")
    address = format_address(client_json.get("address", {}))
    
    return {
        "full_name": f"{first_name} {last_name}".strip(),
        "address": address
    }

# =============================================================================
# PDF GENERATION
# =============================================================================

def create_header_footer_function(logo_path: str = None):
    """
    Create header/footer drawing function for the PDF.
    
    Args:
        logo_path: Path to logo image file
    
    Returns:
        Function that draws header and footer
    """
    def draw_header_footer(canvas, doc_obj):
        canvas.saveState()
        
        # Draw logo in top-left corner
        if logo_path and os.path.exists(logo_path):
            canvas.drawImage(
                logo_path,
                doc_obj.leftMargin,
                doc_obj.height + doc_obj.topMargin - PDF_CONFIG["logo"]["height"],
                width=PDF_CONFIG["logo"]["width"],
                height=PDF_CONFIG["logo"]["height"],
                preserveAspectRatio=True,
                mask='auto'
            )
        
        # Draw page number in bottom-right corner
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            doc_obj.pagesize[0] - doc_obj.rightMargin,
            doc_obj.bottomMargin - 5 * mm,
            f"Page {doc_obj.page} of 1"
        )
        canvas.restoreState()
    
    return draw_header_footer

def build_wire_transfer_pdf(transfer_data: dict, client_data: dict, 
                          output_path: str, logo_path: str = None) -> None:
    """
    Build and generate the complete wire transfer PDF document.
    
    Args:
        transfer_data: Formatted transfer data
        client_data: Formatted client data
        output_path: Output PDF file path
        logo_path: Path to logo image file
    """
    # Create document template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=PDF_CONFIG["page_size"],
        leftMargin=PDF_CONFIG["margins"]["left"],
        rightMargin=PDF_CONFIG["margins"]["right"],
        topMargin=PDF_CONFIG["margins"]["top"],
        bottomMargin=PDF_CONFIG["margins"]["bottom"]
    )
    
    # Get styles and calculate table dimensions
    styles = create_pdf_styles()
    table_total_width = doc.width
    half_width = table_total_width / 2.0
    
    # Create header/footer function
    header_footer_func = create_header_footer_function(logo_path)
    
    # Initialize story (content list)
    story = []
    
    # Add main title
    story.append(Paragraph("Domestic Wire Transfer", styles["section"]))
    story.append(HRFlowable(
        width="40%", 
        thickness=0.2, 
        lineCap='round',
        color="black", 
        spaceBefore=0, 
        spaceAfter=2, 
        hAlign='LEFT'
    ))
    
    # Create main data tables
    left_data = [
        ["Wire Number:", transfer_data["transfer_id"]],
        ["Reference Number:", transfer_data["reference_id"]],
        ["FED Acceptance Date:", transfer_data["created_at"]],
        ["FED Acceptance Time:", ""],
        ["Effective Date:", transfer_data["created_at"]],
        ["Amount:", transfer_data["amount"]]
    ]
    
    right_data = [
        ["IMAD:", transfer_data["imad"]],
        ["OMAD:", transfer_data["omad"]],
        ["Upload Date:", transfer_data["created_at"]],
        ["From Account:", transfer_data["from_account"]],
        ["Account Type:", transfer_data["account_type"]],
        ["Status:", transfer_data["status"]]
    ]
    
    # Convert to paragraph rows and create tables
    left_rows = create_paragraph_rows(left_data, styles)
    right_rows = create_paragraph_rows(right_data, styles)
    
    left_col_widths = [
        PDF_CONFIG["table_proportions"]["label"] * half_width,
        PDF_CONFIG["table_proportions"]["value"] * half_width
    ]
    right_col_widths = [
        0.30 * half_width,  # Slightly different proportions for right side
        0.70 * half_width
    ]
    
    table_left = create_data_table(left_rows, left_col_widths)
    table_right = create_data_table(right_rows, right_col_widths)
    
    # Create outer container table
    outer_table = Table(
        [[table_left, table_right]],
        colWidths=[half_width, half_width],
        hAlign="LEFT"
    )
    outer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    story.append(outer_table)
    story.append(Spacer(1, 6))
    
    # Add beneficiary section
    story.extend(create_section_header("Beneficiary", styles))
    
    beneficiary_data = [
        ["Identification Type:", "Account Number"],
        ["Identification Number:", transfer_data["deposit_instructions"].get("bank_account_number", "")],
        ["Name:", client_data["full_name"]],
        ["Address:", client_data["address"] or "-"]
    ]
    
    beneficiary_rows = create_paragraph_rows(beneficiary_data, styles)
    story.append(create_data_table(
        beneficiary_rows, 
        [0.27 * table_total_width, 0.73 * table_total_width]
    ))
    
    # Add beneficiary institution section
    story.extend(create_section_header("Beneficiary Institution", styles))
    
    institution_data = [
        ["Identification Type:", "Fed Routing Number"],
        ["Identification Number:", transfer_data["deposit_instructions"].get("bank_routing_number", "")],
        ["Name:", transfer_data["deposit_instructions"].get("bank_name", "")],
        ["Address:", transfer_data["deposit_instructions"].get("bank_address", "")]
    ]
    
    institution_rows = create_paragraph_rows(institution_data, styles)
    story.append(create_data_table(
        institution_rows, 
        [0.27 * table_total_width, 0.73 * table_total_width]
    ))
    
    # Add receiving institution section
    story.extend(create_section_header("Receiving Institution", styles))
    
    receiving_data = [
        ["Routing/Transit Number:", transfer_data["deposit_instructions"].get("bank_routing_number", "")],
        ["Institution Name:", transfer_data["deposit_instructions"].get("bank_name", "")]
    ]
    
    receiving_rows = create_paragraph_rows(receiving_data, styles)
    story.append(create_data_table(
        receiving_rows, 
        [0.27 * table_total_width, 0.73 * table_total_width]
    ))
    
    # Build the PDF
    doc.build(story, onFirstPage=header_footer_func, onLaterPages=header_footer_func)

# =============================================================================
# API FUNCTIONS
# =============================================================================

def fetch_transfer_data(transfer_id: str, api_key: str) -> dict:
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
    url = f"{API_BASE_URL}{API_ENDPOINTS['transfers']}/{transfer_id}"
    headers = {"Api-Key": api_key}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_client_data(customer_id: str, api_key: str) -> dict:
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
    url = f"{API_BASE_URL}{API_ENDPOINTS['customers']}/{customer_id}"
    headers = {"Api-Key": api_key}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def generate_wire_transfer_pdf(transfer_id: str, api_key: str, 
                             output_path: str = "wire_transfer_report.pdf",
                             logo_path: str = None) -> str:
    """
    Main function to generate wire transfer PDF.
    
    Args:
        transfer_id: Transfer ID to process
        api_key: API authentication key
        output_path: Output PDF file path
        logo_path: Path to logo image file
    
    Returns:
        Path to generated PDF file
    
    Raises:
        ValueError: If required data is missing
        requests.RequestException: If API requests fail
    """
    # Fetch data from API
    transfer_json = fetch_transfer_data(transfer_id, api_key)
    
    # Extract customer ID
    customer_id = transfer_json.get("on_behalf_of")
    if not customer_id:
        raise ValueError("No se encontró el campo on_behalf_of en la transferencia")
    
    # Fetch client data
    client_json = fetch_client_data(customer_id, api_key)
    
    # Extract and format data
    transfer_data = extract_transfer_data(transfer_json)
    client_data = extract_client_data(client_json)
    
    # Generate PDF
    build_wire_transfer_pdf(transfer_data, client_data, output_path, logo_path)
    
    return output_path

if __name__ == "__main__":
    # Configuration
    API_KEY = ""
    TRANSFER_ID = ""
    LOGO_PATH = "../Logo.png"
    
    try:
        # Generate PDF
        output_file = generate_wire_transfer_pdf(
            transfer_id=TRANSFER_ID,
            api_key=API_KEY,
            logo_path=LOGO_PATH
        )
        print(f"PDF generado exitosamente: {output_file}")
        
    except ValueError as e:
        print(f"Error de validación: {e}")
    except requests.RequestException as e:
        print(f"Error de API: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
