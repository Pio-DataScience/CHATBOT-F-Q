# FAQ Document Compilation Interface

This package provides a user-friendly GUI and API interface for the FAQ document processing system.

## Components

### 1. API Backend (`interface_api.py`)
FastAPI-based REST API that provides:
- Console and sub-console options from the database
- Document compilation endpoint
- Health check endpoint

### 2. GUI Frontend (`interface_gui.py`)
Streamlit-based web interface that provides:
- Dropdown menus for console/sub-console selection
- Parameter input fields
- Document upload functionality
- Real-time compilation progress
- Results display

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Access to Oracle database (UNI_REPOS schema)
- VS Code or terminal access

### Installation

1. Install required dependencies:
```powershell
pip install -r requirements.txt
```

2. Configure database connection (optional):
Set environment variables for database access:
```powershell
$env:DB_DSN = "192.168.30.43:1521/OPENBI2"
$env:DB_USER = "UNI_REPOS"
$env:DB_PASS = "your_password"
```

Or modify the default values in `interface_api.py`:
```python
DB_DSN = "192.168.30.43:1521/OPENBI2"
DB_USER = "UNI_REPOS"
DB_PASS = "your_password"
```

## Running the Application

### Option 1: Run Both Components Separately

#### Start the API Backend
Open a terminal and run:
```powershell
python interface_api.py
```
Or using uvicorn directly:
```powershell
uvicorn interface_api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### Start the GUI Frontend
Open another terminal and run:
```powershell
streamlit run interface_gui.py
```

The GUI will open automatically in your browser at: `http://localhost:8501`

### Option 2: Run with Different Ports
If you need to use different ports:

API:
```powershell
uvicorn interface_api:app --reload --host 0.0.0.0 --port 8080
```

GUI (set API_BASE_URL environment variable):
```powershell
$env:API_BASE_URL = "http://localhost:8080"
streamlit run interface_gui.py --server.port 8501
```

## Usage Guide

### Using the GUI

1. **API Connection**: When you open the GUI, it will automatically check the API connection status.

2. **Select Console**: Choose the appropriate console from the dropdown menu.

3. **Select Sub-Console**: Based on your console selection, choose the relevant sub-console.

4. **Enter Parameters**:
   - Country Code (e.g., 400)
   - Institution Code (e.g., 1)
   - Language ID (1=English, 2=Arabic, etc.)
   - Answers Language Target (OTH or AR)
   - Bank Map Code (optional)

5. **LLM Configuration** (Optional):
   - Check "Generate Questions with LLM" if you want automatic question generation
   - Configure LLM settings (URL, model, question parameters)

6. **Database Sequences** (Optional):
   - Enter sequence names if you want to use specific Oracle sequences

7. **Upload Document**:
   - Click "Choose a DOCX file" and select your FAQ document

8. **Compile**:
   - Click "Compile Document" button
   - Wait for processing (may take several minutes)
   - View results and system output

### Using the API Directly

#### Get Console Options
```bash
curl http://localhost:8000/options/console
```

#### Get Sub-Console Options
```bash
curl http://localhost:8000/options/subconsole/10
```

#### Compile Document
```bash
curl -X POST http://localhost:8000/compile \
  -F "file=@EN_doc.docx" \
  -F "console_id=10" \
  -F "sub_console_id=20" \
  -F "country=400" \
  -F "inst=1" \
  -F "lang=1" \
  -F "answers_to=OTH" \
  -F "bank_map=XYZ" \
  -F "gen_questions=false"
```

## API Endpoints

### GET `/`
Root endpoint with API information.

### GET `/options/console`
Returns list of all console options from PIO_CONSOLE table.

**Response:**
```json
{
  "consoles": [
    {
      "id": 10,
      "desc_eng": "Console Name",
      "desc_nat": "Native Name"
    }
  ]
}
```

### GET `/options/subconsole/{console_id}`
Returns sub-console options filtered by console_id.

**Response:**
```json
{
  "subconsoles": [
    {
      "id": 20,
      "desc_eng": "Sub-Console Name",
      "desc_nat": "Native Name"
    }
  ]
}
```

### POST `/compile`
Compiles a DOCX document and inserts into database.

**Parameters:**
- `file`: DOCX file (required)
- `console_id`: Console code (required)
- `sub_console_id`: Sub-console code (required)
- `country`: Country code (required)
- `inst`: Institution code (required)
- `lang`: Language ID (required)
- `answers_to`: AR or OTH (required)
- `bank_map`: Bank mapping code (optional)
- `gen_questions`: Boolean (optional, default: false)
- `lm_base`: LLM API URL (optional)
- `lm_model`: LLM model name (optional)
- `qmin`: Minimum questions (optional, default: 3)
- `qmax`: Maximum questions (optional, default: 8)
- `q_max_words`: Max words per question (optional, default: 12)
- `seq_ans`: Answers sequence name (optional)
- `seq_faq`: FAQ sequence name (optional)

**Response:**
```json
{
  "status": "success",
  "message": "Document compiled and inserted into database successfully",
  "details": {
    "file": "EN_doc.docx",
    "console_id": 10,
    "sub_console_id": 20,
    "country": 400,
    "inst": 1,
    "lang": 1,
    "answers_to": "OTH",
    "fragments_output": "output/faq_fragments.html",
    "questions_output": "output/questions.jsonl"
  },
  "output": "System output..."
}
```

### GET `/health`
Health check endpoint to verify API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Database Requirements

The system expects the following Oracle tables:
- `UNI_REPOS.PIO_CONSOLE`: Console options
- `UNI_REPOS.PIO_SUB_CONSOLE`: Sub-console options
- `UNI_REPOS.CHATBOT_ANSWERS`: FAQ answers
- `UNI_REPOS.USER_MANUAL_FAQ`: FAQ questions

## Troubleshooting

### API Won't Start
- Check if port 8000 is already in use
- Verify database connection settings
- Check Python version (3.8+ required)

### GUI Can't Connect to API
- Ensure API is running first
- Check API_BASE_URL setting
- Verify firewall settings

### Database Connection Errors
- Verify database credentials
- Check network connectivity to Oracle server
- Ensure oracledb package is installed correctly

### Compilation Fails
- Check if main.py is in the same directory
- Verify all required Python packages are installed
- Check DOCX file format is valid
- Review system output for specific errors

## File Structure

```
CHATBOT-F-Q/
├── interface_api.py          # FastAPI backend
├── interface_gui.py          # Streamlit frontend
├── main.py                   # Core processing system
├── requirements.txt          # Python dependencies
├── README_INTERFACE.md       # This file
├── output/                   # Output directory
│   ├── faq_fragments.html
│   └── questions.jsonl
└── src/                      # Source modules
    ├── db/
    ├── faq/
    ├── io/
    ├── llm/
    └── utils/
```

## Support

For issues or questions, please contact the development team or refer to the main project documentation.

## Notes

- The system runs locally on your server via VS Code execution
- Processing time depends on document size and LLM configuration
- Ensure sufficient disk space for temporary files
- Database transactions are committed only on successful completion
- Large documents may take several minutes to process
