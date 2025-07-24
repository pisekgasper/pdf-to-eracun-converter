# PDF to e-SLOG Converter

This Python application extracts data from a PDF invoice containing a 'slikaj in plačaj' UPNQR code and generates a Slovenian e-račun in e-SLOG 2.0 XML format. The program relies solely on data from the QR code.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.6+**
- **pip** (Python package installer)
- **ZBar** (a software suite for reading bar codes)
- **PyInstaller** (for building standalone executables)

## Installation

Choose the instructions for your operating system:

### macOS

1. Install [Homebrew](https://brew.sh/) if you don't have it already.
2. Install ZBar:
   ```bash
   brew install zbar
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install PyInstaller (if not already installed):
   ```bash
   pip install pyinstaller
   ```

### Debian / Ubuntu

1. Update package lists and install ZBar:
   ```bash
   sudo apt-get update
   sudo apt-get install libzbar0
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install PyInstaller (if not already installed):
   ```bash
   pip install pyinstaller
   ```

### Windows

1. Install Python 3.x from the [official site](https://www.python.org/downloads/windows/) or via [Microsoft Store]. Ensure you check the box to add Python to your PATH.
2. Open PowerShell or CMD as Administrator.
3. Install ZBar:
   - Using [Chocolatey](https://chocolatey.org/):
     ```powershell
     choco install zbar
     ```
   - Or download the ZBar Windows installer from the [ZBar project page](https://github.com/mchehab/zbar/releases) and follow the setup prompts.
4. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```

## Usage

To process a PDF invoice, run the `main.py` script. The program will automatically scan the application directory for PDF files and present you with an interactive menu to choose the file you want to convert.

```bash
python main.py
```

Use the arrow keys to navigate the list of PDF files and press Enter to select one. The application will then generate an XML file with the same name as the selected PDF file, but with an `.xml` extension (e.g., `invoice.xml`).

### Options

- `-o, --output`: Specify a custom output XML file path
- `-v, --verbose`: Enable verbose logging for debugging

### Examples

```bash
# Basic usage
python main.py

# Custom output file
python main.py -o output/invoice_eslog.xml

# Verbose mode
python main.py -v
```

## UPNQR Code Format

The application expects the UPNQR code to be in the standard Slovenian format with exactly 20 lines. The QR code must start with "UPNQR" and contain payment information including payer details, receiver details, amount, and payment references.

## VAT ID Handling

Since UPNQR codes do not contain VAT information, the converter handles VAT IDs as follows:

- If the receiver is "NGEN", the converter automatically uses VAT ID: SI24576239
- For other receivers, the VAT fields are left empty as this information is not available in the UPNQR format

> **Note:** e-SLOG 2.0 requires VAT information for invoices with standard rated VAT. For full compliance, you may need to manually add VAT information to the generated XML if it's not an NGEN invoice.

## Building a Standalone Executable

You can build a standalone executable using PyInstaller:

```bash
pyinstaller --clean --onefile main.spec
```

This will create a `dist` directory containing the standalone executable for your current platform.
