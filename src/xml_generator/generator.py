from lxml import etree
from datetime import datetime
import re

def generate_eslog_xml(data):
    """Generates a proper e-SLOG 2.0 XML file according to official specification."""
    
    # Define the correct namespace for e-SLOG 2.0
    NS = 'urn:eslog:2.00'
    XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
    
    # Create root element with proper namespace
    root = etree.Element(
        'Invoice',
        nsmap={None: NS, 'xsi': XSI_NS}
    )
    
    # Create main INVOIC message structure
    m_invoic = etree.SubElement(root, 'M_INVOIC')
    m_invoic.set('Id', 'data')  # For digital signature support
    
    # Helper function to add element with text
    def add_element(parent, name, text=None):
        elem = etree.SubElement(parent, name)
        if text is not None:
            elem.text = str(text)
        return elem
    
    # Calculate amounts properly
    total_amount_with_vat = float(data.get('Amount', 0.0))
    tax_rate = float(data.get('TaxRate', 22.0))
    tax_rate_decimal = tax_rate / 100
    
    # Calculate base amount (without VAT) and tax amount
    base_amount = round(total_amount_with_vat / (1 + tax_rate_decimal), 2)
    tax_amount = round(total_amount_with_vat - base_amount, 2)
    
    # 1. UNH - Message Header
    s_unh = add_element(m_invoic, 'S_UNH')
    add_element(s_unh, 'D_0062', data.get('InvoiceNumber', 'INV001'))  # Message reference number
    
    c_s009 = add_element(s_unh, 'C_S009')
    add_element(c_s009, 'D_0065', 'INVOIC')  # Message type
    add_element(c_s009, 'D_0052', 'D')       # Version number
    add_element(c_s009, 'D_0054', '01B')     # Release number
    add_element(c_s009, 'D_0051', 'UN')      # Controlling agency
    
    # 2. BGM - Beginning of Message
    s_bgm = add_element(m_invoic, 'S_BGM')
    
    c_c002 = add_element(s_bgm, 'C_C002')
    add_element(c_c002, 'D_1001', '380')  # Document name code (380 = Commercial Invoice)
    
    c_c106 = add_element(s_bgm, 'C_C106')
    add_element(c_c106, 'D_1004', data.get('InvoiceNumber', 'INV001'))  # Document identifier
    
    # 3. DTM - Date/Time/Period segments
    # Invoice date (137)
    s_dtm_invoice = add_element(m_invoic, 'S_DTM')
    c_c507_invoice = add_element(s_dtm_invoice, 'C_C507')
    add_element(c_c507_invoice, 'D_2005', '137')  # Date qualifier (137 = Document date)
    
    invoice_date = data.get('InvoiceDate', '')
    if not invoice_date:
        invoice_date = datetime.now().strftime('%Y-%m-%d')
    add_element(c_c507_invoice, 'D_2380', invoice_date)
    
    # Service period start date (167)
    s_dtm_service = add_element(m_invoic, 'S_DTM')
    c_c507_service = add_element(s_dtm_service, 'C_C507')
    add_element(c_c507_service, 'D_2005', '167')  # Date qualifier (167 = Service period start)
    add_element(c_c507_service, 'D_2380', invoice_date)
    
    # Service period end date (168)
    s_dtm_service_end = add_element(m_invoic, 'S_DTM')
    c_c507_service_end = add_element(s_dtm_service_end, 'C_C507')
    add_element(c_c507_service_end, 'D_2005', '168')  # Date qualifier (168 = Service period end)
    add_element(c_c507_service_end, 'D_2380', invoice_date)
    
    # Due date (13) if available
    if data.get('DueDate'):
        s_dtm_due = add_element(m_invoic, 'S_DTM')
        c_c507_due = add_element(s_dtm_due, 'C_C507')
        add_element(c_c507_due, 'D_2005', '13')  # Date qualifier (13 = Due date)
        add_element(c_c507_due, 'D_2380', data.get('DueDate'))
    
    # 4. FTX - Free Text segments
    # BT-24: Specification identifier (BR-1 requirement)
    s_ftx_spec = add_element(m_invoic, 'S_FTX')
    add_element(s_ftx_spec, 'D_4451', 'DOC')  # Text subject qualifier (DOC = Document)
    c_c107_spec = add_element(s_ftx_spec, 'C_C107')
    add_element(c_c107_spec, 'D_4441', 'P1')  # Text literal
    c_c108_spec = add_element(s_ftx_spec, 'C_C108')
    add_element(c_c108_spec, 'D_4440', 'urn:cen.eu:en16931:2017')  # Specification identifier
    
    # 5. SG2 - Name and Address segments
    # Buyer (BY)
    if data.get('BuyerName'):
        g_sg2_buyer = add_element(m_invoic, 'G_SG2')
        s_nad_buyer = add_element(g_sg2_buyer, 'S_NAD')
        add_element(s_nad_buyer, 'D_3035', 'BY')  # Party qualifier (BY = Buyer)
        
        # Buyer name
        c_c080_buyer = add_element(s_nad_buyer, 'C_C080')
        add_element(c_c080_buyer, 'D_3036', data.get('BuyerName', ''))
        
        # Buyer address
        buyer_address = data.get('BuyerAddress', '')
        if buyer_address:
            address_parts = buyer_address.split(',')
            c_c059_buyer = add_element(s_nad_buyer, 'C_C059')
            
            if len(address_parts) > 0:
                add_element(c_c059_buyer, 'D_3042', address_parts[0].strip())
            
            # Extract postal code and city
            if len(address_parts) > 1:
                city_part = address_parts[1].strip()
                match = re.match(r'(\d{4})\s+(.+)', city_part)
                if match:
                    add_element(s_nad_buyer, 'D_3164', match.group(2))  # City name
                    add_element(s_nad_buyer, 'D_3251', match.group(1))  # Postal code
        
        add_element(s_nad_buyer, 'D_3207', 'SI')  # Country code
    
    # Seller (SE)
    if data.get('SellerName'):
        g_sg2_seller = add_element(m_invoic, 'G_SG2')
        s_nad_seller = add_element(g_sg2_seller, 'S_NAD')
        add_element(s_nad_seller, 'D_3035', 'SE')  # Party qualifier (SE = Seller)
        
        # Seller name
        c_c080_seller = add_element(s_nad_seller, 'C_C080')
        add_element(c_c080_seller, 'D_3036', data.get('SellerName', ''))
        
        # Seller address
        seller_address = data.get('SellerAddress', '')
        if seller_address:
            address_parts = seller_address.split(',')
            c_c059_seller = add_element(s_nad_seller, 'C_C059')
            
            if len(address_parts) > 0:
                add_element(c_c059_seller, 'D_3042', address_parts[0].strip())
            
            # Extract postal code and city
            if len(address_parts) > 1:
                city_part = address_parts[1].strip()
                match = re.match(r'(\d{4})\s+(.+)', city_part)
                if match:
                    add_element(s_nad_seller, 'D_3164', match.group(2))  # City name
                    add_element(s_nad_seller, 'D_3251', match.group(1))  # Postal code
        
        add_element(s_nad_seller, 'D_3207', 'SI')  # Country code
        
        if data.get('SellerIBAN'):
            s_fii = add_element(g_sg2_seller, 'S_FII')
            add_element(s_fii, 'D_3035', 'RB')  # Party qualifier (RB = Receiving bank)
            c_c078 = add_element(s_fii, 'C_C078')
            add_element(c_c078, 'D_3194', data.get('SellerIBAN'))
        
        seller_vat = data.get('SellerVATID', '')
        if seller_vat:
            g_sg3_vat = add_element(g_sg2_seller, 'G_SG3')
            s_rff_vat = add_element(g_sg3_vat, 'S_RFF')
            c_c506_vat = add_element(s_rff_vat, 'C_C506')
            add_element(c_c506_vat, 'D_1153', 'VA')  # Reference qualifier (VA = VAT registration number)
            add_element(c_c506_vat, 'D_1154', seller_vat)

        # BT-30: Seller Legal Registration Identifier
        seller_legal_id = data.get('SellerLegalID', '')
        if seller_legal_id:
            g_sg3_legal = add_element(g_sg2_seller, 'G_SG3')
            s_rff_legal = add_element(g_sg3_legal, 'S_RFF')
            c_c506_legal = add_element(s_rff_legal, 'C_C506')
            add_element(c_c506_legal, 'D_1153', 'AHP')
            add_element(c_c506_legal, 'D_1154', seller_legal_id)
    
    # 6. SG7 - Currencies
    g_sg7 = add_element(m_invoic, 'G_SG7')
    s_cux = add_element(g_sg7, 'S_CUX')
    c_c504 = add_element(s_cux, 'C_C504')
    add_element(c_c504, 'D_6347', '2')    # Currency details qualifier (2 = Pricing currency)
    add_element(c_c504, 'D_6345', 'EUR')  # ISO currency code
    
    # 7. SG8 - Payment Terms with BT-81 Payment means type code
    g_sg8 = add_element(m_invoic, 'G_SG8')
    s_pat = add_element(g_sg8, 'S_PAT')
    add_element(s_pat, 'D_4279', '1')  # Payment terms type qualifier (1 = Basic)
    
    if data.get('DueDate'):
        s_dtm_payment = add_element(g_sg8, 'S_DTM')
        c_c507_payment = add_element(s_dtm_payment, 'C_C507')
        add_element(c_c507_payment, 'D_2005', '13')  # Date qualifier (13 = Due date)
        add_element(c_c507_payment, 'D_2380', data.get('DueDate'))
    
    # BT-81: Payment means type code (BR-49 requirement)
    s_pai = add_element(g_sg8, 'S_PAI')
    c_c534 = add_element(s_pai, 'C_C534')
    add_element(c_c534, 'D_4461', '30')  # Payment means code (30 = Credit transfer)
    
    # 8. SG26 - Line Details
    g_sg26 = add_element(m_invoic, 'G_SG26')
    s_lin = add_element(g_sg26, 'S_LIN')
    add_element(s_lin, 'D_1082', '1')  # Line item number
    
    # Item description
    s_imd = add_element(g_sg26, 'S_IMD')
    add_element(s_imd, 'D_7077', 'F')  # Item description type (F = Free-form)
    c_c273 = add_element(s_imd, 'C_C273')
    add_element(c_c273, 'D_7008', data.get('ItemDescription', 'Storitev po računu'))
    
    # Quantity
    s_qty = add_element(g_sg26, 'S_QTY')
    c_c186 = add_element(s_qty, 'C_C186')
    add_element(c_c186, 'D_6063', '47')      # Quantity qualifier (47 = Invoiced quantity)
    add_element(c_c186, 'D_6060', '1')       # Quantity
    add_element(c_c186, 'D_6411', 'C62')     # Measure unit qualifier (C62 = One/each)
    
    # BT-131: Invoice line net amount (line amount without VAT)
    g_sg27 = add_element(g_sg26, 'G_SG27')
    s_moa_line = add_element(g_sg27, 'S_MOA')
    c_c516_line = add_element(s_moa_line, 'C_C516')
    add_element(c_c516_line, 'D_5025', '203')  # Monetary amount type (203 = Line item amount)
    add_element(c_c516_line, 'D_5004', f"{base_amount:.2f}")  # Line net amount (without VAT)
    
    # Price details (net price)
    g_sg29 = add_element(g_sg26, 'G_SG29')
    s_pri = add_element(g_sg29, 'S_PRI')
    c_c509 = add_element(s_pri, 'C_C509')
    add_element(c_c509, 'D_5125', 'AAA')     # Price qualifier (AAA = Calculation net)
    add_element(c_c509, 'D_5118', f"{base_amount:.4f}")  # Net price
    add_element(c_c509, 'D_5284', '1')       # Unit price basis
    add_element(c_c509, 'D_6411', 'C62')     # Measure unit qualifier
    
    # Tax information for line item - Only if VAT ID is available
    if data.get('SellerVATID'):
        g_sg34 = add_element(g_sg26, 'G_SG34')
        s_tax_line = add_element(g_sg34, 'S_TAX')
        add_element(s_tax_line, 'D_5283', '7')   # Duty/tax/fee type (7 = Tax)
        
        c_c241_line = add_element(s_tax_line, 'C_C241')
        add_element(c_c241_line, 'D_5153', 'VAT')  # Duty/tax/fee type name
        
        c_c243_line = add_element(s_tax_line, 'C_C243')
        add_element(c_c243_line, 'D_5278', f"{tax_rate:.0f}")  # Duty/tax/fee rate
        
        add_element(s_tax_line, 'D_5305', 'S')   # Duty/tax/fee category code (S = Standard rate)
    
    # 9. UNS - Section Control (separates detail from summary)
    s_uns = add_element(m_invoic, 'S_UNS')
    add_element(s_uns, 'D_0081', 'S')  # Section identification (S = Summary)
    
    # 10. SG50 - Monetary Amounts Summary (Fixed calculations per business rules)
    
    # BT-106: Sum of Invoice line net amount (same as BT-131 for single line)
    g_sg50_line_total = add_element(m_invoic, 'G_SG50')
    s_moa_line_total = add_element(g_sg50_line_total, 'S_MOA')
    c_c516_line_total = add_element(s_moa_line_total, 'C_C516')
    add_element(c_c516_line_total, 'D_5025', '79')  # Monetary amount type (79 = Total line items amount)
    add_element(c_c516_line_total, 'D_5004', f"{base_amount:.2f}")
    
    # BT-109: Invoice total amount without VAT (BR-13 requirement)
    g_sg50_total_no_vat = add_element(m_invoic, 'G_SG50')
    s_moa_total_no_vat = add_element(g_sg50_total_no_vat, 'S_MOA')
    c_c516_total_no_vat = add_element(s_moa_total_no_vat, 'C_C516')
    add_element(c_c516_total_no_vat, 'D_5025', '389')  # Monetary amount type (389 = Total invoice amount excl. VAT)
    add_element(c_c516_total_no_vat, 'D_5004', f"{base_amount:.2f}")
    
    # BT-112: Invoice total amount with VAT (BR-14 requirement)
    g_sg50_total_with_vat = add_element(m_invoic, 'G_SG50')
    s_moa_total_with_vat = add_element(g_sg50_total_with_vat, 'S_MOA')
    c_c516_total_with_vat = add_element(s_moa_total_with_vat, 'C_C516')
    add_element(c_c516_total_with_vat, 'D_5025', '388')  # Monetary amount type (388 = Total invoice amount incl. VAT)
    add_element(c_c516_total_with_vat, 'D_5004', f"{total_amount_with_vat:.2f}")
    
    # BT-110: Invoice total VAT amount - Only if VAT ID is available
    if data.get('SellerVATID'):
        g_sg50_vat_total = add_element(m_invoic, 'G_SG50')
        s_moa_vat_total = add_element(g_sg50_vat_total, 'S_MOA')
        c_c516_vat_total = add_element(s_moa_vat_total, 'C_C516')
        add_element(c_c516_vat_total, 'D_5025', '176')  # Monetary amount type (176 = Total tax amount)
        add_element(c_c516_vat_total, 'D_5004', f"{tax_amount:.2f}")
    
    # BT-115: Amount due for payment (BR-CO-16: BT-112 - BT-113 + BT-114)
    # Assuming no paid amount (BT-113=0) and no rounding (BT-114=0)
    g_sg50_payable = add_element(m_invoic, 'G_SG50')
    s_moa_payable = add_element(g_sg50_payable, 'S_MOA')
    c_c516_payable = add_element(s_moa_payable, 'C_C516')
    add_element(c_c516_payable, 'D_5025', '9')   # Monetary amount type (9 = Amount due/payable)
    add_element(c_c516_payable, 'D_5004', f"{total_amount_with_vat:.2f}")
    
    # BT-113: Paid amount (0.00 for unpaid invoice)
    g_sg50_paid = add_element(m_invoic, 'G_SG50')
    s_moa_paid = add_element(g_sg50_paid, 'S_MOA')
    c_c516_paid = add_element(s_moa_paid, 'C_C516')
    add_element(c_c516_paid, 'D_5025', '113')  # Monetary amount type (113 = Paid amount)
    add_element(c_c516_paid, 'D_5004', '0.00')
    
    # BT-114: Rounding amount (0.00)
    g_sg50_rounding = add_element(m_invoic, 'G_SG50')
    s_moa_rounding = add_element(g_sg50_rounding, 'S_MOA')
    c_c516_rounding = add_element(s_moa_rounding, 'C_C516')
    add_element(c_c516_rounding, 'D_5025', '366')  # Monetary amount type (366 = Rounding amount)
    add_element(c_c516_rounding, 'D_5004', '0.00')
    
    # 11. SG52 - Tax Totals - Only if VAT ID is available
    if data.get('SellerVATID'):
        g_sg52 = add_element(m_invoic, 'G_SG52')
        s_tax_total = add_element(g_sg52, 'S_TAX')
        add_element(s_tax_total, 'D_5283', '7')  # Duty/tax/fee type (7 = Tax)
        
        c_c241_total = add_element(s_tax_total, 'C_C241')
        add_element(c_c241_total, 'D_5153', 'VAT')  # Duty/tax/fee type name
        
        c_c243_total = add_element(s_tax_total, 'C_C243')
        add_element(c_c243_total, 'D_5278', f"{tax_rate:.0f}")  # Duty/tax/fee rate
        
        add_element(s_tax_total, 'D_5305', 'S')  # Duty/tax/fee category code
        
        # BT-116: VAT category taxable amount
        s_moa_tax_base_rate = add_element(g_sg52, 'S_MOA')
        c_c516_tax_base_rate = add_element(s_moa_tax_base_rate, 'C_C516')
        add_element(c_c516_tax_base_rate, 'D_5025', '125')  # Monetary amount type (125 = Taxable amount)
        add_element(c_c516_tax_base_rate, 'D_5004', f"{base_amount:.2f}")
        
        # BT-117: VAT category tax amount
        s_moa_tax_amount_rate = add_element(g_sg52, 'S_MOA')
        c_c516_tax_amount_rate = add_element(s_moa_tax_amount_rate, 'C_C516')
        add_element(c_c516_tax_amount_rate, 'D_5025', '124')  # Monetary amount type (124 = Tax amount)
        add_element(c_c516_tax_amount_rate, 'D_5004', f"{tax_amount:.2f}")
    
    # Generate pretty XML with proper declaration
    return etree.tostring(
        root, 
        pretty_print=True, 
        xml_declaration=True, 
        encoding='UTF-8'
    ).decode('utf-8')


def map_upnqr_to_eslog(upnqr_data):
    """Maps UPNQR data to e-SLOG fields."""
    # Extract seller name and determine VAT ID
    seller_name = upnqr_data.get('ime_prejemnika', '')
    seller_vat_id = ''
    seller_legal_id = ''
    
    # Check if receiver is NGEN and assign their VAT ID
    if 'NGEN' in seller_name.upper():
        seller_vat_id = 'SI24576239'
        seller_legal_id = '8209901000'
    # Otherwise leave empty - UPNQR doesn't contain VAT information
    
    return {
        'InvoiceNumber': upnqr_data.get('stevilka_racuna', upnqr_data.get('referenca_prejemnika', '')),
        'InvoiceDate': '',  # Not in UPNQR, will use current date
        'DueDate': upnqr_data.get('rok_placila', ''),
        'BuyerName': upnqr_data.get('ime_placnika', ''),
        'BuyerAddress': f"{upnqr_data.get('ulica_placnika', '')}, {upnqr_data.get('kraj_placnika', '')}",
        'SellerName': upnqr_data.get('ime_prejemnika', ''),
        'SellerAddress': f"{upnqr_data.get('ulica_prejemnika', '')}, {upnqr_data.get('kraj_prejemnika', '')}",
        'SellerIBAN': upnqr_data.get('iban_prejemnika', ''),
        'SellerVATID': seller_vat_id,  # Will be empty unless it's NGEN
        'SellerLegalID': seller_legal_id,  # Will be empty unless it's NGEN
        'Amount': upnqr_data.get('znesek', 0.0),
        'PaymentReference': upnqr_data.get('referenca_prejemnika', ''),
        'PurposeCode': upnqr_data.get('koda_namena', ''),
        'ItemDescription': upnqr_data.get('namen', ''),
        'TaxRate': 22.0,  # Default Slovenian VAT rate
    }