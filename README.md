# American Hospital Dubai - Smart Data Validator

An AI-powered platform for validating and correcting email addresses and phone numbers in Excel files.

## Features

- Excel file upload support
- AI-driven validation for emails and phone numbers
- Automatic correction suggestions
- Color-coded validation results
- Downloadable processed files
- User-friendly interface

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5001
```

## Usage

1. Click the "Browse Files" button or drag and drop your Excel file
2. The file should contain columns named "email" and/or "phone"
3. Wait for the validation process to complete
4. Download the processed file with validation results

## File Format Requirements

Your Excel file should contain one or both of these columns:
- `email`: Email addresses to validate
- `phone`: Phone numbers to validate

The output file will include additional columns:
- `email_status`: VALID or NOT VALID
- `email_message`: Additional information or error messages
- `phone_status`: VALID or NOT VALID
- `phone_message`: Additional information or error messages

## Security Notes

- Maximum file size: 16MB
- Supported file format: .xlsx only
- Temporary files are automatically cleaned up
