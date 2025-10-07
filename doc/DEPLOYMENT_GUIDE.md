# Deployment Guide - FAQ Document Compilation Interface

## Package Contents

This deployment package includes:

1. **Backend API** (`interface_api.py`)
   - FastAPI-based REST API
   - Database integration
   - Document processing endpoints

2. **Frontend GUI** (`interface_gui.py`)
   - Streamlit-based web interface
   - User-friendly form interface
   - Real-time feedback

3. **Launcher Scripts**
   - `start_interface.bat` - Simple batch launcher (Windows)
   - `start_interface.ps1` - PowerShell launcher with checks (Windows)

4. **Documentation**
   - `README_INTERFACE.md` - Complete usage guide
   - This deployment guide

5. **Configuration**
   - `.env.template` - Configuration template
   - Updated `requirements.txt`

## Deployment Steps

### Step 1: Verify Prerequisites

Ensure the following are available on the server:
- Python 3.8 or higher
- Network access to Oracle database (192.168.30.43:1521/OPENBI2)
- Required Python packages (will be installed in Step 3)

### Step 2: Copy Files to Server

Copy the entire `CHATBOT-F-Q` folder to your server location:
```
C:\Users\[username]\.vscode\WorkSpace\CHATBOT-F-Q\
```

Or any preferred location on the server.

### Step 3: Install Dependencies

Open PowerShell or Command Prompt in the project directory and run:
```powershell
pip install -r requirements.txt
```

Wait for all packages to install successfully.

### Step 4: Configure Database Connection (Optional)

If using different database credentials:

Option A: Create `.env` file
```powershell
copy .env.template .env
```
Then edit `.env` with your database credentials.

Option B: Edit `interface_api.py` directly
Update these lines in `interface_api.py`:
```python
DB_DSN = "192.168.30.43:1521/OPENBI2"
DB_USER = "UNI_REPOS"
DB_PASS = "your_password_here"
```

### Step 5: Test Database Connection

Run a quick test:
```powershell
python -c "import oracledb; conn = oracledb.connect(user='UNI_REPOS', password='UNI_REPOS', dsn='192.168.30.43:1521/OPENBI2'); print('Connection successful'); conn.close()"
```

### Step 6: Launch the Application

#### Easy Method (Recommended):
Double-click `start_interface.bat`

Or in PowerShell:
```powershell
.\start_interface.ps1
```

#### Manual Method:
Open two separate terminals:

Terminal 1 - Start API:
```powershell
python interface_api.py
```

Terminal 2 - Start GUI:
```powershell
streamlit run interface_gui.py
```

### Step 7: Access the Application

Open your web browser and navigate to:
- **GUI Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Verification Checklist

After deployment, verify:

- [ ] API is running at http://localhost:8000
- [ ] API health check returns "healthy" status
- [ ] GUI opens at http://localhost:8501
- [ ] GUI shows "API is connected and healthy" message
- [ ] Console dropdown loads with options from database
- [ ] Sub-console dropdown loads based on console selection
- [ ] File upload accepts .docx files
- [ ] Test compilation works end-to-end

## Testing the System

### Quick Test Procedure

1. Open the GUI at http://localhost:8501
2. Verify "API is connected and healthy" message appears
3. Select a console from the dropdown
4. Select a sub-console
5. Enter test parameters:
   - Country: 400
   - Institution: 1
   - Language: 1
   - Answers To: OTH
6. Upload a test DOCX file (use EN_doc.docx or AR_doc.docx)
7. Click "Compile Document"
8. Wait for processing
9. Verify success message and review output

## Troubleshooting

### Issue: "API is not responding properly"

**Solution:**
1. Check if API is running: Visit http://localhost:8000/health
2. Check if port 8000 is available: `netstat -an | findstr "8000"`
3. Check API logs in the terminal
4. Restart the API service

### Issue: "Failed to load console options"

**Solution:**
1. Verify database connection settings
2. Check if PIO_CONSOLE table exists and has data
3. Verify database user has SELECT permissions
4. Check network connectivity to database server

### Issue: Port Already in Use

**Solution:**
Use different ports:

For API (port 8080 instead of 8000):
```powershell
uvicorn interface_api:app --reload --host 0.0.0.0 --port 8080
```

For GUI (set environment variable first):
```powershell
$env:API_BASE_URL = "http://localhost:8080"
streamlit run interface_gui.py --server.port 8502
```

### Issue: "Compilation timeout"

**Solution:**
1. Increase timeout in `interface_gui.py` (line 71):
   ```python
   timeout=1200  # 20 minutes instead of 10
   ```
2. Check main.py execution manually
3. Verify all source files (src/ folder) are present

### Issue: Missing Python Packages

**Solution:**
```powershell
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## Server Deployment Notes

### Running on Startup

To run automatically when server starts:

1. Create a scheduled task in Windows Task Scheduler
2. Trigger: At system startup
3. Action: Start a program
4. Program: `powershell.exe`
5. Arguments: `-File "C:\path\to\CHATBOT-F-Q\start_interface.ps1"`
6. Run with highest privileges

### Running as a Service

For production deployment, consider using:
- NSSM (Non-Sucking Service Manager) for Windows services
- Or Docker containers for isolated deployment

### Security Considerations

1. **Database Credentials**: Use environment variables or secure vault
2. **Network Access**: Restrict to internal network only
3. **File Upload**: Already restricted to .docx files only
4. **API Access**: Consider adding authentication if needed

### Monitoring

Monitor the following:
- API availability (http://localhost:8000/health)
- Disk space in output/ folder
- Database connection pool
- Application logs

### Backup

Regularly backup:
- Configuration files (.env)
- Output directory (output/)
- Database records (CHATBOT_ANSWERS, USER_MANUAL_FAQ)

## Performance Optimization

### For Large Documents

1. Increase subprocess timeout in `interface_api.py` (line 242):
   ```python
   timeout=1200  # Increase from 600 to 1200 seconds
   ```

2. Enable streaming responses for better user feedback

3. Consider batch processing for multiple documents

### For High Load

1. Use multiple uvicorn workers:
   ```powershell
   uvicorn interface_api:app --workers 4 --host 0.0.0.0 --port 8000
   ```

2. Add request queuing if needed

3. Consider load balancer for multiple instances

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Check application logs
   - Verify disk space
   - Test end-to-end flow

2. **Monthly**:
   - Update Python packages
   - Review and clean output/ folder
   - Database maintenance

3. **As Needed**:
   - Update database credentials
   - Adjust parameters
   - Add new features

### Updating the Application

1. Backup current installation
2. Copy new files
3. Update requirements if changed:
   ```powershell
   pip install -r requirements.txt --upgrade
   ```
4. Restart services
5. Test functionality

## Support Contacts

For issues or questions:
- Technical Support: [Your contact]
- Database Issues: [DBA contact]
- Application Development: [Dev team contact]

## Appendix: File Locations

```
CHATBOT-F-Q/
├── interface_api.py              # API backend
├── interface_gui.py              # GUI frontend
├── main.py                       # Core processing
├── requirements.txt              # Dependencies
├── start_interface.bat           # Launcher (batch)
├── start_interface.ps1           # Launcher (PowerShell)
├── .env.template                 # Config template
├── README_INTERFACE.md           # User guide
├── DEPLOYMENT_GUIDE.md           # This file
├── output/                       # Generated files
│   ├── faq_fragments.html
│   └── questions.jsonl
└── src/                          # Source modules
    ├── db/
    ├── faq/
    ├── io/
    ├── llm/
    └── utils/
```

## Quick Reference Commands

```powershell
# Start everything
.\start_interface.bat

# Start API only
python interface_api.py

# Start GUI only
streamlit run interface_gui.py

# Test database connection
python -c "import oracledb; conn = oracledb.connect(user='UNI_REPOS', password='UNI_REPOS', dsn='192.168.30.43:1521/OPENBI2'); print('OK'); conn.close()"

# Check API health
curl http://localhost:8000/health

# View API docs
start http://localhost:8000/docs

# Install/Update packages
pip install -r requirements.txt --upgrade

# Check running processes
netstat -an | findstr "8000 8501"
```

## Success Criteria

Deployment is successful when:
- ✅ API responds to health checks
- ✅ GUI loads without errors
- ✅ Database connections work
- ✅ Console/subconsole dropdowns populate
- ✅ Test document compiles successfully
- ✅ Data appears in database tables
- ✅ All output files are generated

## Conclusion

Your FAQ Document Compilation Interface is now ready for use. The system provides an easy-to-use GUI for processing FAQ documents while maintaining all the power of the underlying command-line system.

For detailed usage instructions, refer to `README_INTERFACE.md`.
