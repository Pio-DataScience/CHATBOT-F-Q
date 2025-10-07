"""
FastAPI backend for FAQ document processing system.
Provides endpoints for retrieving console/subconsole options and compiling documents.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import logging

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import oracledb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FAQ Compilation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_DSN = os.getenv("DB_DSN", "192.168.30.43:1521/OPENBI2")
DB_USER = os.getenv("DB_USER", "UNI_REPOS")
DB_PASS = os.getenv("DB_PASS", "UNI_REPOS")


def get_db_connection():
    """
    Create and return a database connection.

    Returns:
        Oracle database connection object
    """
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns:
        JSON with API name and available endpoints
    """
    return {
        "message": "FAQ Compilation API",
        "endpoints": {
            "console_options": "/options/console",
            "subconsole_options": "/options/subconsole/{console_id}",
            "compile_document": "/compile",
        },
    }


@app.get("/options/console")
async def get_console_options():
    """
    Retrieve all console options from the database.

    Returns:
        List of console options with id, desc_eng, and desc_nat
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT ID, DESC_ENG, DESC_NAT 
        FROM UNI_REPOS.PIO_CONSOLE 
        ORDER BY ID
        """
        cursor.execute(query)

        results = []
        for row in cursor:
            results.append({"id": row[0], "desc_eng": row[1], "desc_nat": row[2]})

        cursor.close()
        logger.info(f"Retrieved {len(results)} console options")
        return {"consoles": results}

    except Exception as e:
        logger.error(f"Error fetching console options: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching console options: {str(e)}"
        )

    finally:
        if conn:
            conn.close()


@app.get("/options/subconsole/{console_id}")
async def get_subconsole_options(console_id: int):
    """
    Retrieve subconsole options filtered by console_id.

    Args:
        console_id: The ID of the parent console

    Returns:
        List of subconsole options with id, desc_eng, and desc_nat
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT ID, DESC_ENG, DESC_NAT 
        FROM UNI_REPOS.PIO_SUB_CONSOLE 
        WHERE CONSOLE_ID = :console_id
        ORDER BY ID
        """
        cursor.execute(query, {"console_id": console_id})

        results = []
        for row in cursor:
            results.append({"id": row[0], "desc_eng": row[1], "desc_nat": row[2]})

        cursor.close()
        logger.info(
            f"Retrieved {len(results)} subconsole options for console {console_id}"
        )
        return {"subconsoles": results}

    except Exception as e:
        logger.error(f"Error fetching subconsole options: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching subconsole options: {str(e)}"
        )

    finally:
        if conn:
            conn.close()


@app.post("/compile")
async def compile_document(
    file: UploadFile = File(...),
    console_id: int = Form(...),
    sub_console_id: int = Form(...),
    country: int = Form(...),
    inst: int = Form(...),
    lang: int = Form(...),
    answers_to: str = Form(...),
    bank_map: str = Form(default=""),
    gen_questions: bool = Form(default=False),
    lm_base: str = Form(default="http://localhost:1234/v1"),
    lm_model: str = Form(default=""),
    qmin: int = Form(default=3),
    qmax: int = Form(default=8),
    q_max_words: int = Form(default=12),
    seq_ans: str = Form(default=""),
    seq_faq: str = Form(default=""),
):
    """
    Compile a DOCX document into FAQ format and insert into database.

    Args:
        file: The DOCX file to process
        console_id: Console code
        sub_console_id: Sub-console code
        country: Country code
        inst: Institution code
        lang: Language ID (1=English, 2=Arabic, etc.)
        answers_to: Target language for answers (AR or OTH)
        bank_map: Bank mapping code (optional)
        gen_questions: Whether to generate questions using LLM
        lm_base: LLM API base URL
        lm_model: LLM model name
        qmin: Minimum questions per section
        qmax: Maximum questions per section
        q_max_words: Maximum words per question
        seq_ans: Sequence name for answers table
        seq_faq: Sequence name for FAQ table

    Returns:
        JSON with success status and details
    """
    temp_dir = None
    temp_file_path = None

    try:
        if not file.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Only DOCX files are supported")

        temp_dir = tempfile.mkdtemp()
        temp_file_path = Path(temp_dir) / file.filename

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Saved uploaded file: {temp_file_path}")

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        fragments_path = output_dir / "faq_fragments.html"
        questions_path = output_dir / "questions.jsonl"

        command = [
            sys.executable,
            "main.py",
            "--in",
            str(temp_file_path),
            "--out",
            str(output_dir),
            "--mode",
            "concat",
            "--fragments",
            str(fragments_path),
            "--questions-jsonl",
            str(questions_path),
            "--country",
            str(country),
            "--inst",
            str(inst),
            "--lang",
            str(lang),
            "--console",
            str(console_id),
            "--sub-console",
            str(sub_console_id),
            "--bank-map",
            bank_map,
            "--answers-to",
            answers_to,
            "--db-insert",
        ]

        if gen_questions:
            command.extend(
                [
                    "--gen-questions",
                    "--lm-base",
                    lm_base,
                    "--lm-model",
                    lm_model,
                    "--qmin",
                    str(qmin),
                    "--qmax",
                    str(qmax),
                    "--q-max-words",
                    str(q_max_words),
                ]
            )

        if seq_ans:
            command.extend(["--seq-ans", seq_ans])
        if seq_faq:
            command.extend(["--seq-faq", seq_faq])

        logger.info(f"Executing command: {' '.join(command)}")

        result = subprocess.run(command, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise HTTPException(
                status_code=500, detail=f"Compilation failed: {result.stderr}"
            )

        logger.info("Document compiled successfully")
        logger.info(f"STDOUT: {result.stdout}")

        return {
            "status": "success",
            "message": "Document compiled and inserted into database successfully",
            "details": {
                "file": file.filename,
                "console_id": console_id,
                "sub_console_id": sub_console_id,
                "country": country,
                "inst": inst,
                "lang": lang,
                "answers_to": answers_to,
                "fragments_output": str(fragments_path),
                "questions_output": str(questions_path),
            },
            "output": result.stdout,
        }

    except subprocess.TimeoutExpired:
        logger.error("Command execution timeout")
        raise HTTPException(
            status_code=504, detail="Compilation timeout - operation took too long"
        )

    except Exception as e:
        logger.error(f"Compilation error: {e}")
        raise HTTPException(status_code=500, detail=f"Compilation error: {str(e)}")

    finally:
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

        if temp_dir and Path(temp_dir).exists():
            try:
                Path(temp_dir).rmdir()
            except Exception as e:
                logger.warning(f"Failed to delete temp directory: {e}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.

    Returns:
        JSON with status and database connection state
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.fetchone()
        cursor.close()
        conn.close()

        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("interface_api:app", host="0.0.0.0", port=8000, reload=True)
