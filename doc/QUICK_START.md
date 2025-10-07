# Quick Start Guide

## How to Run the System

### Option 1: Network Access (Recommended)
Run this **single command** in PowerShell:

```powershell
.\start_network.ps1
```

This will:
1. Activate the virtual environment
2. Start the API server in a separate window
3. Start the GUI in the current window
4. Display the URLs for network access

**Do NOT run `python interface_api.py` manually** - the script handles everything!

### Option 2: Local Only
If you only need local access:

```powershell
.\start_simple.ps1
```

## Where to Find Logs

### Real-Time Logs
When processing documents, logs are now saved to:
- **`logs/faq_processing.log`** - Detailed processing logs from main.py

You can monitor this file in real-time:
```powershell
Get-Content logs\faq_processing.log -Wait -Tail 50
```

### API Logs
The API server logs appear in the **separate PowerShell window** that opens when you run `start_network.ps1`.

### GUI Logs
The Streamlit GUI logs appear in the **terminal where you ran the start script**.

## Understanding the Windows

After running `start_network.ps1`, you'll see:
1. **Window 1** (new): API Server - shows API requests and responses
2. **Window 2** (current): Streamlit GUI - shows GUI logs and status

## Troubleshooting

### Not seeing processing logs?
Check the file: `logs/faq_processing.log`

This file contains ALL the detailed logs from document processing, including:
- DOCX to HTML conversion
- FAQ splitting
- Question generation (if enabled)
- Database insertion
- **Deletion of existing records** (new feature)
- Number of records inserted

### How to view logs while processing?
Open a new PowerShell window and run:
```powershell
Get-Content logs\faq_processing.log -Wait -Tail 50
```

This shows the last 50 lines and updates in real-time as new logs are written.

## Network Access URLs

When running with `start_network.ps1`, share these URLs with your team:

- **GUI:** `http://<YOUR-IP>:8501`
- **API:** `http://<YOUR-IP>:8000`
- **API Docs:** `http://<YOUR-IP>:8000/docs`

Your IP address will be displayed when the script starts.

## What's New

### Delete Existing Q&A
When you upload a document with the same Console and Sub-Console combination:
- Old questions and answers are **automatically deleted**
- New data is inserted fresh
- No more duplicate records!

Check `logs/faq_processing.log` to see how many records were deleted.

### Smaller HTML Headers
HTML output now has smaller, more readable headers with inline styling.
