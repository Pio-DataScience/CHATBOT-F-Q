# CHATBOT FAQ Processing System

## Overview

The CHATBOT FAQ Processing System is a comprehensive pipeline that converts DOCX documents into structured FAQ data for chatbot integration. The system processes documents in multiple languages (English and Arabic) and stores the results in an Oracle database.

## System Architecture

### Core Components

1. **Document Conversion** (`src/io/docx_to_html.py`)
   - Converts DOCX files to HTML using Mammoth library
   - Preserves document structure and formatting

2. **FAQ Splitting** (`src/faq/splitter.py`)
   - Splits HTML content into individual FAQ items based on headings
   - Supports both English and Arabic content with proper RTL handling
   - Generates unique slugs for each section

3. **Question Generation** (`src/llm/questions.py`)
   - Uses LLM to generate alternative question variants
   - Supports language-appropriate punctuation (? for English, ؟ for Arabic)

4. **Database Integration** (`src/db/oracle_repo.py`)
   - Stores FAQ data in Oracle database
   - Supports multiple languages with appropriate column mapping

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure Oracle database sequences exist:
   ```sql
   CREATE SEQUENCE CHATBOT_ANSWERS_SEQ START WITH 1 INCREMENT BY 1;
   CREATE SEQUENCE USER_MANUAL_FAQ_SEQ START WITH 1 INCREMENT BY 1;
   ```

## Usage

### Basic Command Structure

```bash
python main.py [OPTIONS] [INPUT_FILE]
```

### Command Line Arguments

#### Required Arguments
- `INPUT_FILE`: Path to the DOCX file to process (default: `EN_doc.docx`)

#### Processing Options
- `--output-dir, -o`: Output directory (default: `out`)
- `--mode`: Processing mode - `concat` (default) or `separate`
- `--fragments`: Path to write HTML fragments file
- `--questions-jsonl`: Path to write questions JSONL file

#### Database Options
- `--db-insert`: Enable database insertion
- `--country`: Country code (numeric)
- `--inst`: Institution code (numeric)  
- `--lang`: Language ID (numeric)
- `--console`: Console ID (numeric)
- `--sub-console`: Sub-console ID (numeric)
- `--bank-map`: Bank mapping identifier
- `--answers-to`: Target answer column (`OTH` for English, `AR` for Arabic)
- `--seq-ans`: Answer sequence name (e.g., `CHATBOT_ANSWERS_SEQ`)
- `--seq-faq`: FAQ sequence name (e.g., `USER_MANUAL_FAQ_SEQ`)

## Usage Examples

### 1. Basic Processing (No Database Insert)

Process an English document and generate output files:

```bash
python main.py EN_doc.docx --output-dir output --fragments output/faq_fragments.html --questions-jsonl output/questions.jsonl
```

### 2. English Document with Database Insert

Process English document and insert into database:

```bash
python main.py EN_doc.docx \
  --db-insert \
  --fragments output/faq_fragments.html \
  --questions-jsonl output/questions.jsonl \
  --country 700 \
  --inst 1 \
  --lang 1 \
  --console 10 \
  --sub-console 20 \
  --bank-map "XYZ" \
  --answers-to OTH \
  --seq-ans "CHATBOT_ANSWERS_SEQ" \
  --seq-faq "USER_MANUAL_FAQ_SEQ"
```

### 3. Arabic Document with Database Insert

Process Arabic document and insert into Arabic columns:

```bash
python main.py AR_doc.docx \
  --db-insert \
  --fragments output/faq_fragments_ar.html \
  --questions-jsonl output/questions_ar.jsonl \
  --country 700 \
  --inst 1 \
  --lang 2 \
  --console 10 \
  --sub-console 20 \
  --bank-map "XYZ" \
  --answers-to AR \
  --seq-ans "CHATBOT_ANSWERS_SEQ" \
  --seq-faq "USER_MANUAL_FAQ_SEQ"
```

### 4. Processing with Virtual Environment

When using a virtual environment, use the full path to Python:

```bash
C:/Users/anas.aburaya/.vscode/WorkSpace/CHATBOT-F-Q/.venv/Scripts/python.exe main.py \
  --db-insert \
  --fragments output/faq_fragments.html \
  --questions-jsonl output/questions.jsonl \
  --country 700 --inst 1 --lang 1 --console 10 --sub-console 20 \
  --bank-map "XYZ" --answers-to OTH \
  --seq-ans "CHATBOT_ANSWERS_SEQ" --seq-faq "USER_MANUAL_FAQ_SEQ"
```

## Language Support

### English Documents
- Use `--lang 1` for English language ID
- Use `--answers-to OTH` to store in English answer columns
- Questions will end with `?`
- Text direction: `dir="auto"`

### Arabic Documents  
- Use `--lang 2` (or appropriate Arabic language ID)
- Use `--answers-to AR` to store in Arabic answer columns
- Questions will end with `؟` (Arabic question mark)
- Text direction: `dir="rtl"` for Arabic content
- Supports Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩)

## Output Files

### HTML Fragments (`faq_fragments.html`)
Contains concatenated HTML fragments for all FAQ items with:
- Proper text direction attributes
- Unique section IDs
- Structured heading and content divs

### Questions JSONL (`questions.jsonl`)
Line-delimited JSON file with:
- Original heading text
- Generated question alternatives
- Language-appropriate punctuation
- Section metadata

## Database Schema

The system expects Oracle database tables with:
- `ANSWER_TEXT_OTH`: English answer content
- `ANSWER_TEXT_AR`: Arabic answer content  
- Language ID columns for proper categorization
- Sequence-generated primary keys

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'mammoth'
   ```
   **Solution**: Install requirements with `pip install -r requirements.txt`

2. **Database Sequence Error**
   ```
   ORA-02289: sequence does not exist
   ```
   **Solution**: Create the required sequences in your Oracle database

3. **File Not Found**
   ```
   FileNotFoundError: [Errno 2] No such file or directory: 'EN_doc.docx'
   ```
   **Solution**: Ensure the input DOCX file exists in the correct path

### Debug Mode

Add logging to see detailed processing steps:

```bash
python main.py --verbose EN_doc.docx
```

## Development Notes

- The system maintains backward compatibility for existing English workflows
- Arabic support is additive and doesn't break existing functionality
- All changes preserve the original pipeline architecture
- Database insertion respects the specified language and target columns

## File Structure

```
CHATBOT-F-Q/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── EN_doc.docx            # Sample English document
├── src/
│   ├── io/
│   │   └── docx_to_html.py    # DOCX conversion
│   ├── faq/
│   │   ├── splitter.py        # HTML splitting logic
│   │   ├── questions.py       # Question generation
│   │   └── persist.py         # File persistence
│   ├── db/
│   │   └── oracle_repo.py     # Database operations
│   ├── llm/
│   │   ├── client.py          # LLM integration
│   │   └── prompts.py         # LLM prompts
│   └── utils/
│       └── files.py           # File utilities
└── output/                    # Generated output files
    ├── faq_fragments.html
    └── questions.jsonl
```
