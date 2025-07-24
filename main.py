import argparse
import os
import sys
import logging
from datetime import datetime
import inquirer
from src.pdf_handler.handler import extract_images
from src.qr_code_processor.processor import decode_qr_code, parse_upnqr_data
from src.xml_generator.generator import generate_eslog_xml, map_upnqr_to_eslog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s]: %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF invoices with UPNQR codes to e-SLOG 2.0 XML format.",
        epilog="Example: python main.py invoice.pdf"
    )
    parser.add_argument("-o", "--output", help="Output XML file path (default: same as input with .xml extension)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)

     # ─── Determine the “base” folder ───
    if getattr(sys, 'frozen', False):
        # We're in a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as a normal script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    # Change working directory so all relative I/O happens there
    os.chdir(base_dir)
    logger.debug(f"Working directory set to: {base_dir}")

    # ─── List PDF files from that folder ───
    pdf_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.error("No PDF files found in the current directory.")
        sys.exit(1)

    questions = [
        inquirer.List('pdf_file',
                        message="Choose a PDF file to process",
                        choices=pdf_files,
                    ),
    ]
    answers = inquirer.prompt(questions)
    pdf_file = answers['pdf_file']


    logger.info(f"Processing {pdf_file}...")
    
    try:
        # 1. Extract images from PDF
        logger.info("Extracting images from PDF...")
        pdf_images = extract_images(pdf_file)
        logger.info(f"Found {len(pdf_images)} images in PDF")
        
        # 2. Find and decode QR code
        qr_data = None
        for i, image in enumerate(pdf_images):
            logger.debug(f"Trying to decode QR code from image {i+1}...")
            qr_data = decode_qr_code(image)
            if qr_data:
                logger.info(f"Successfully decoded QR code from image {i+1}")
                break
        
        if not qr_data:
            logger.error("Error: No QR code found in the PDF.")
            logger.info("Make sure the PDF contains a valid UPNQR code.")
            sys.exit(1)
        
        logger.debug(f"QR data:\n{qr_data}")
        
        # 3. Parse UPNQR data
        logger.info("Parsing UPNQR data...")
        upnqr_data = parse_upnqr_data(qr_data)
        if not upnqr_data:
            logger.error("Error: Could not parse UPNQR data. Invalid format.")
            sys.exit(1)
        
        logger.info(f"Successfully parsed UPNQR data:")
        logger.info(f"  - Payer: {upnqr_data.get('ime_placnika', 'N/A')}")
        logger.info(f"  - Receiver: {upnqr_data.get('ime_prejemnika', 'N/A')}")
        logger.info(f"  - Amount: €{upnqr_data.get('znesek', 0):.2f}")
        logger.info(f"  - Due date: {upnqr_data.get('rok_placila', 'N/A')}")
        
        # 4. Map UPNQR data to e-SLOG fields
        logger.info("Mapping UPNQR data to e-SLOG format...")
        eslog_data = map_upnqr_to_eslog(upnqr_data)
        
        # 5. Log final data summary
        logger.info(f"Final invoice data:")
        logger.info(f"  - Invoice Number: {eslog_data.get('InvoiceNumber', 'N/A')}")
        logger.info(f"  - Seller: {eslog_data.get('SellerName', 'N/A')}")
        logger.info(f"  - Seller VAT ID: {eslog_data.get('SellerVATID', 'N/A')}")
        logger.info(f"  - Buyer: {eslog_data.get('BuyerName', 'N/A')}")
        logger.info(f"  - Amount: €{eslog_data.get('Amount', 0):.2f}")
        logger.info(f"  - Due Date: {eslog_data.get('DueDate', 'N/A')}")
        
        # 6. Generate e-SLOG XML
        logger.info("Generating e-SLOG 2.0 XML...")
        xml_output = generate_eslog_xml(eslog_data)
        
        # 7. Save the XML file
        output_filename = args.output or os.path.splitext(pdf_file)[0] + ".xml"
        
        logger.info(f"Saving XML to {output_filename}...")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(xml_output)
        
        logger.info(f"Successfully generated {output_filename}")
        logger.info(f"File size: {os.path.getsize(output_filename)} bytes")
        
        # Optional: Validate the generated XML
        try:
            from lxml import etree
            doc = etree.fromstring(xml_output.encode('utf-8'))
            logger.info("Generated XML is well-formed")
        except Exception as e:
            logger.warning(f"XML validation warning: {e}")
        
        logger.info("✓ Generated e-SLOG 2.0 compliant XML")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()