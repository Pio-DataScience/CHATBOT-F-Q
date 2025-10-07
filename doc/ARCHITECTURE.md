# FAQ Interface System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │  Streamlit Web GUI (http://localhost:8501)            │    │
│  │  - Console Selection Dropdowns                         │    │
│  │  - Parameter Input Forms                               │    │
│  │  - DOCX File Upload                                    │    │
│  │  - Compile Button                                      │    │
│  │  - Results Display                                     │    │
│  └───────────────────┬───────────────────────────────────┘    │
│                      │                                         │
└──────────────────────┼─────────────────────────────────────────┘
                       │ HTTP REST API
                       │ (GET/POST requests)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API BACKEND LAYER                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │  FastAPI Server (http://localhost:8000)               │    │
│  │                                                        │    │
│  │  Endpoints:                                            │    │
│  │  ├─ GET  /options/console                             │    │
│  │  ├─ GET  /options/subconsole/{id}                     │    │
│  │  ├─ POST /compile                                      │    │
│  │  └─ GET  /health                                       │    │
│  │                                                        │    │
│  │  Features:                                             │    │
│  │  - Request validation                                  │    │
│  │  - File handling                                       │    │
│  │  - Subprocess management                               │    │
│  │  - Error handling                                      │    │
│  └────────┬──────────────────┬──────────────────┬────────┘    │
│           │                  │                  │             │
└───────────┼──────────────────┼──────────────────┼─────────────┘
            │                  │                  │
            │                  │                  │
            ▼                  ▼                  ▼
    ┌───────────┐     ┌────────────┐    ┌──────────────┐
    │  Oracle   │     │  main.py   │    │ Temp File    │
    │ Database  │     │ Processing │    │ Management   │
    │           │     │            │    │              │
    │ Tables:   │     │ Steps:     │    │ - Upload     │
    │ ├─Console │     │ 1.Convert  │    │ - Storage    │
    │ ├─SubCons │     │ 2.Extract  │    │ - Cleanup    │
    │ ├─Answers │     │ 3.Generate │    │              │
    │ └─FAQ     │     │ 4.Insert   │    │              │
    └───────────┘     └─────┬──────┘    └──────────────┘
                            │
                            │
                            ▼
              ┌──────────────────────────┐
              │   Processing Modules     │
              │                          │
              │  src/io/docx_to_html.py │
              │  src/faq/splitter.py    │
              │  src/faq/questions.py   │
              │  src/llm/client.py      │
              │  src/db/oracle_repo.py  │
              └──────────────────────────┘
```

## Request Flow Diagram

```
User Action                API Processing                  Database
─────────────             ──────────────────              ─────────

1. Opens GUI
   │
   ├──► Request consoles ──► Query PIO_CONSOLE ──────────► [QUERY]
   │                                                         │
   │    ◄── Console list ◄── Return results ◄──────────────┘
   │
   │
2. Selects console
   │
   ├──► Request subconsoles ──► Query PIO_SUB_CONSOLE ────► [QUERY]
   │                             WHERE console_id = X        │
   │    ◄── Subconsole list ◄── Return results ◄────────────┘
   │
   │
3. Fills parameters
   & uploads DOCX
   │
   │
4. Clicks "Compile"
   │
   ├──► POST /compile ──────┐
   │    (file + params)     │
   │                        ▼
   │                   Save temp file
   │                        │
   │                        ▼
   │                   Run subprocess:
   │                   python main.py
   │                   --in temp.docx
   │                   --country X
   │                   --inst Y
   │                   ...
   │                        │
   │                        ▼
   │                   main.py processes:
   │                   ├─ Convert DOCX→HTML
   │                   ├─ Split into sections
   │                   ├─ Generate questions (opt)
   │                   └─ Insert to database ────────────────► [INSERT]
   │                        │                                   │
   │                        │                              CHATBOT_ANSWERS
   │                        │                              USER_MANUAL_FAQ
   │                        │                                   │
   │                        ▼                                   │
   │                   Clean temp files                         │
   │                        │                                   │
   │    ◄── Success response ◄──────────────────────────────────┘
   │
   │
5. Views results
   │
   └──► Display success
        & details
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                      INTERFACE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  interface_gui.py          ◄──HTTP──►      interface_api.py│
│  (Streamlit)                                  (FastAPI)     │
│                                                             │
│  • User input              Requests:         • Validation   │
│  • File upload             - GET /options    • DB queries   │
│  • Display results         - POST /compile   • Subprocess   │
│  • Error handling          - GET /health     • Response     │
│                                                             │
└──────────────┬──────────────────────────────────┬───────────┘
               │                                  │
               │                                  │
               ▼                                  ▼
┌──────────────────────┐              ┌──────────────────────┐
│   HTTP Client        │              │  Database Client     │
│   (requests)         │              │  (oracledb)          │
│                      │              │                      │
│  • GET requests      │              │  • Connection pool   │
│  • POST multipart    │              │  • Query execution   │
│  • Timeout handling  │              │  • Result mapping    │
└──────────────────────┘              └──────────────────────┘
                                                 │
                                                 │
                                                 ▼
               ┌──────────────────────────────────────────┐
               │            CORE SYSTEM                   │
               ├──────────────────────────────────────────┤
               │                                          │
               │  main.py                                 │
               │  ├─ Argument parsing                     │
               │  ├─ Pipeline orchestration               │
               │  └─ Error handling                       │
               │                                          │
               │  src/io/docx_to_html.py                 │
               │  └─ DOCX → HTML conversion              │
               │                                          │
               │  src/faq/splitter.py                    │
               │  └─ HTML → FAQ sections                 │
               │                                          │
               │  src/faq/questions.py                   │
               │  └─ Question generation                  │
               │                                          │
               │  src/llm/client.py                      │
               │  └─ LLM API integration                 │
               │                                          │
               │  src/db/oracle_repo.py                  │
               │  └─ Database operations                  │
               │                                          │
               └──────────────────────────────────────────┘
```

## Data Flow

```
Input: DOCX Document
   │
   ├─► [1] Convert to HTML
   │       (mammoth library)
   │       │
   │       └─► Raw HTML with sections
   │
   ├─► [2] Split into FAQ items
   │       (BeautifulSoup parsing)
   │       │
   │       └─► List of FAQ sections
   │            {slug, level, heading, html}
   │
   ├─► [3] Generate questions (optional)
   │       (LLM API calls)
   │       │
   │       └─► Questions for each section
   │            {slug, alternatives[]}
   │
   └─► [4] Insert to database
           (Oracle transactions)
           │
           ├─► Insert answers
           │    CHATBOT_ANSWERS table
           │    Returns: answer_id
           │
           └─► Insert questions
                USER_MANUAL_FAQ table
                Links to: answer_id

Output: Database records + HTML/JSONL files
```

## File System Structure

```
CHATBOT-F-Q/
│
├── Interface Layer (New)
│   ├── interface_api.py         # FastAPI backend
│   ├── interface_gui.py         # Streamlit frontend
│   ├── start_interface.bat      # Windows launcher
│   ├── start_interface.ps1      # PowerShell launcher
│   └── test_installation.py     # Installation test
│
├── Documentation (New)
│   ├── README_INTERFACE.md      # Usage guide
│   ├── DEPLOYMENT_GUIDE.md      # Deployment instructions
│   ├── PROJECT_SUMMARY.md       # Project overview
│   └── ARCHITECTURE.md          # This file
│
├── Configuration
│   ├── requirements.txt         # Updated dependencies
│   ├── .env.template           # Config template
│   └── pyproject.toml          # Project metadata
│
├── Core System (Existing)
│   ├── main.py                 # Main processing script
│   ├── src/
│   │   ├── db/
│   │   │   └── oracle_repo.py  # Database operations
│   │   ├── faq/
│   │   │   ├── splitter.py     # FAQ extraction
│   │   │   ├── questions.py    # Question generation
│   │   │   └── persist.py      # Data persistence
│   │   ├── io/
│   │   │   └── docx_to_html.py # Document conversion
│   │   ├── llm/
│   │   │   ├── client.py       # LLM client
│   │   │   └── prompts.py      # Prompt templates
│   │   └── utils/
│   │       └── files.py        # File utilities
│   │
│   └── output/                 # Generated files
│       ├── faq_fragments.html  # HTML output
│       └── questions.jsonl     # Questions output
│
└── Data Files
    ├── EN_doc.docx            # English input
    └── AR_doc.docx            # Arabic input
```

## Technology Stack

```
┌─────────────────────────────────────────────┐
│           PRESENTATION LAYER                │
├─────────────────────────────────────────────┤
│  Streamlit 1.39.0                          │
│  - Web UI framework                        │
│  - Reactive components                     │
│  - File upload handling                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│              API LAYER                      │
├─────────────────────────────────────────────┤
│  FastAPI 0.115.0                           │
│  - REST API framework                      │
│  - Async request handling                  │
│  - Auto documentation                      │
│                                            │
│  Uvicorn 0.32.0                           │
│  - ASGI server                            │
│  - Hot reload support                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           PROCESSING LAYER                  │
├─────────────────────────────────────────────┤
│  Mammoth 1.11.0                            │
│  - DOCX to HTML conversion                │
│                                            │
│  BeautifulSoup 4.14.2                     │
│  - HTML parsing                           │
│  - Content extraction                     │
│                                            │
│  Requests 2.32.5                          │
│  - HTTP client                            │
│  - LLM API calls                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│            DATABASE LAYER                   │
├─────────────────────────────────────────────┤
│  oracledb 3.3.0                            │
│  - Oracle database driver                  │
│  - Connection pooling                      │
│  - Transaction management                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│          INFRASTRUCTURE                     │
├─────────────────────────────────────────────┤
│  Python 3.8+                               │
│  - Core runtime                            │
│                                            │
│  Windows Server                            │
│  - Deployment environment                  │
│                                            │
│  Oracle Database                           │
│  - Data storage                            │
└─────────────────────────────────────────────┘
```

## Security Model

```
┌─────────────────────────────────────────────┐
│              INPUT VALIDATION               │
├─────────────────────────────────────────────┤
│  • File type check (.docx only)            │
│  • Parameter validation                    │
│  • Size limits                             │
│  • SQL injection prevention                │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│            AUTHENTICATION                   │
├─────────────────────────────────────────────┤
│  • Database credentials                     │
│  • Environment variables                    │
│  • No hardcoded passwords                   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              DATA HANDLING                  │
├─────────────────────────────────────────────┤
│  • Temporary file cleanup                   │
│  • Transaction rollback on error            │
│  • Error message sanitization               │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│               LOGGING                       │
├─────────────────────────────────────────────┤
│  • Application logs                         │
│  • Error tracking                           │
│  • Audit trail                              │
└─────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌────────────────────────────────────────────────────┐
│              Windows Server                        │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Terminal 1: API Server                  │    │
│  │  Port 8000                               │    │
│  │  $ python interface_api.py               │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Terminal 2: GUI Server                  │    │
│  │  Port 8501                               │    │
│  │  $ streamlit run interface_gui.py        │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  File System                             │    │
│  │  - Temp uploads                          │    │
│  │  - Output directory                      │    │
│  │  - Application logs                      │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
└────────┬───────────────────────────────────┬──────┘
         │                                   │
         │ Database                          │ Users
         │ Connection                        │ Browser
         ▼                                   ▼
┌─────────────────┐              ┌──────────────────┐
│  Oracle Server  │              │   Web Browser    │
│  Port 1521      │              │   localhost:8501 │
│  OPENBI2 DB     │              │                  │
└─────────────────┘              └──────────────────┘
```

This architecture provides:
- ✓ Separation of concerns
- ✓ Easy maintenance
- ✓ Scalability
- ✓ Error isolation
- ✓ Clear data flow
- ✓ Security layers
