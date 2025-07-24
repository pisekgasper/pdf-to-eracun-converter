from pyzbar.pyzbar import decode
from datetime import datetime

def decode_qr_code(image):
    """Decodes a QR code from an image and returns the data."""
    decoded_objects = decode(image)
    if not decoded_objects:
        return None
    return decoded_objects[0].data.decode("utf-8")

def parse_upnqr_data(data):
    """Parses UPNQR data into a structured format according to official specification."""
    lines = data.strip().split('\n')
    
    # UPNQR format validation - must have exactly 20 lines
    if len(lines) < 20 or lines[0] != "UPNQR":
        return None
    
    try:
        # Parse amount (field 9, in cents)
        amount_str = lines[8].strip()
        if amount_str:
            amount = int(amount_str) / 100.0
        else:
            amount = 0.0
        
        # Parse payment date (field 10) - convert from DD.MM.YYYY to ISO format
        payment_date_str = lines[9].strip()
        payment_date = None
        if payment_date_str:
            try:
                payment_date = datetime.strptime(payment_date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError:
                payment_date = payment_date_str
        
        # Parse payment deadline (field 14) - convert from DD.MM.YYYY to ISO format
        due_date_str = lines[13].strip()
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError:
                due_date = due_date_str
        
        data_dict = {
            # Header
            "format": lines[0].strip(),                  # Should be "UPNQR"
            
            # Payer (Plačnik) information - fields 2-8
            "iban_placnika": lines[1].strip(),          # Payer IBAN (field 2)
            "polog": lines[2].strip(),                  # Deposit flag (field 3)
            "dvig": lines[3].strip(),                   # Withdrawal flag (field 4)
            "referenca_placnika": lines[4].strip(),     # Payer reference (field 5)
            "ime_placnika": lines[5].strip(),           # Payer name (field 6)
            "ulica_placnika": lines[6].strip(),         # Payer street (field 7)
            "kraj_placnika": lines[7].strip(),          # Payer city (field 8)
            
            # Payment information - fields 9-14
            "znesek": amount,                           # Amount in EUR (field 9)
            "znesek_centi": amount_str,                 # Amount in cents (original)
            "datum_placila": payment_date,              # Payment date formatted (field 10)
            "datum_placila_original": payment_date_str, # Payment date original
            "nujno": lines[10].strip(),                 # Urgent flag (field 11)
            "koda_namena": lines[11].strip(),           # Purpose code (field 12)
            "namen": lines[12].strip(),                 # Payment purpose (field 13)
            "rok_placila": due_date,                    # Due date formatted (field 14)
            "rok_placila_original": due_date_str,       # Due date original
            
            # Receiver (Prejemnik) information - fields 15-19
            "iban_prejemnika": lines[14].strip(),       # Receiver IBAN (field 15)
            "referenca_prejemnika": lines[15].strip(),  # Receiver reference (field 16)
            "ime_prejemnika": lines[16].strip(),        # Receiver name (field 17)
            "ulica_prejemnika": lines[17].strip(),      # Receiver street (field 18)
            "kraj_prejemnika": lines[18].strip().replace('鬚', 'Ž'), # Receiver city (field 19)
            
            # Checksum
            "checksum": lines[19].strip() if len(lines) > 19 else "",  # Sum of lengths (field 20)
        }
        
        # Extract invoice number from payment purpose if present
        namen = data_dict["namen"]
        if "računa št.:" in namen or "računa št:" in namen:
            invoice_num = namen.split("računa št")[-1].strip(":. ")
            data_dict["stevilka_racuna"] = invoice_num
        else:
            # Use receiver reference as fallback
            data_dict["stevilka_racuna"] = data_dict["referenca_prejemnika"]
        
        return data_dict
        
    except (ValueError, IndexError) as e:
        print(f"Error parsing UPNQR data: {e}")
        return None