# Real-Time Logging Explanation

## The Problem

### Before:
The API was using:
```python
result = subprocess.run(command, capture_output=True, text=True, timeout=600)
```

**What this means:**
- `capture_output=True` captures ALL stdout and stderr
- Nothing is displayed in the terminal during processing
- All output is only available AFTER the process completes
- You see the GUI say "Processing..." but no logs in terminal

**Why it was like this:**
- The captured output was being returned in the API response
- Good for showing results in the GUI
- Bad for monitoring and debugging

### After:
Now using:
```python
result = subprocess.run(command, capture_output=False, text=True, timeout=600)
```

**What this means:**
- `capture_output=False` lets output stream directly to the terminal
- You see logs in REAL-TIME as main.py runs
- Better for monitoring progress
- Better for debugging issues

## What You'll See Now

### API Terminal (python):
```
INFO:interface_api:Executing command: ...
============================================================
INFO:interface_api:Starting document compilation process...
============================================================
INFO:     127.0.0.1:xxxxx - "POST /compile HTTP/1.1" 200 OK

[Then you'll see all the logs from main.py:]
2025-10-07 14:30:00 - __main__ - INFO - Starting FAQ processing pipeline
2025-10-07 14:30:00 - __main__ - INFO - Input file: temp_file.docx
2025-10-07 14:30:01 - __main__ - INFO - Converting DOCX → HTML
2025-10-07 14:30:02 - __main__ - INFO - Successfully converted DOCX to HTML
2025-10-07 14:30:02 - __main__ - INFO - Splitting into FAQ items…
2025-10-07 14:30:03 - __main__ - INFO - Successfully split into 25 FAQ items
2025-10-07 14:30:03 - __main__ - INFO - Starting question generation with LLM
... (all the detailed processing logs)
DB insert OK.

============================================================
INFO:interface_api:Document compiled successfully
============================================================
```

### GUI (Streamlit):
Still shows:
- "Processing document... This may take several minutes."
- Success message when complete
- Compilation details (but not the full logs)

## Benefits

### Real-Time Monitoring
- ✅ See exactly what's happening during processing
- ✅ Monitor LLM question generation progress
- ✅ See database insertion steps
- ✅ Catch errors immediately

### Better Debugging
- ✅ If something goes wrong, you can see WHERE it failed
- ✅ Logs show timing information
- ✅ Can interrupt if needed

### Progress Awareness
- ✅ Know how long each step takes
- ✅ See if it's stuck somewhere
- ✅ Understand the workflow better

## Trade-offs

### Before (capture_output=True):
- ✅ Clean GUI with all output in response
- ❌ No real-time feedback
- ❌ Hard to debug
- ❌ Can't monitor progress

### After (capture_output=False):
- ✅ Real-time logs in terminal
- ✅ Easy to monitor and debug
- ✅ See progress live
- ❌ Output not captured in API response (but you can see it in terminal)

## Best Practice

For background/production systems:
- Use `capture_output=True` + save to log file
- Return structured status updates

For development/monitoring:
- Use `capture_output=False` for live feedback
- Watch terminal for real-time progress

## Current Setup

We're now using the development approach because:
1. You're running it locally on a server
2. You have terminal access
3. You want to monitor what's happening
4. It's easier to debug issues

If you prefer the old behavior (no terminal logs), change it back to:
```python
result = subprocess.run(command, capture_output=True, text=True, timeout=600)
```

## Summary

**Is it normal to not see logs?**
- With `capture_output=True`: YES (by design)
- With `capture_output=False`: NO (you should see everything)

**What did we change?**
- Now you'll see all logs in real-time in the API terminal
- This is BETTER for monitoring and debugging
- The GUI still works the same way

**Next time you compile:**
Watch the API terminal window - you'll see all the processing steps live! 👀
