#!/usr/bin/env python3
"""
Script to insert Arabic Job Basket FAQ into Oracle database.
Checks if data already exists before inserting.
"""

from db.oracle_repo import OracleRepo
import re
import sys

sys.path.insert(0, "src")


def extract_arabic_job_basket_html():
    """Extract the complete Arabic Job Basket section from HTML file."""
    html_file = r"output_ar\faq_fragments.html"

    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the Arabic Job Basket section - "سلة المهام"
    pattern = (
        r'<section class="faq-item" data-level="4" id="sec-سلة-المهام">.*?</section>'
    )
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(0)
    else:
        raise ValueError("Arabic Job Basket section not found in HTML file!")


def check_answer_exists(repo, answer_id):
    """Check if an answer with the given ID already exists."""
    with repo.conn.cursor() as c:
        c.execute(
            "SELECT COUNT(*) FROM UNI_REPOS.CHATBOT_ANSWERS WHERE ID = :id",
            {"id": answer_id},
        )
        count = c.fetchone()[0]
        return count > 0


def check_questions_exist(repo, question_ids):
    """Check if questions with the given IDs already exist."""
    with repo.conn.cursor() as c:
        placeholders = ",".join([f":id{i}" for i in range(len(question_ids))])
        params = {f"id{i}": qid for i, qid in enumerate(question_ids)}
        c.execute(
            f"SELECT COUNT(*) FROM UNI_REPOS.USER_MANUAL_FAQ WHERE ID IN ({placeholders})",
            params,
        )
        count = c.fetchone()[0]
        return count > 0


def main():
    print("Connecting to Oracle database...")
    repo = OracleRepo(
        dsn="192.168.30.43:1521/OPENBI2", user="UNI_REPOS", password="UNI_REPOS"
    )

    try:
        answer_id = 66666
        question_ids = [66601, 66602, 66603, 66604]

        # Check if data already exists
        print(f"Checking if answer {answer_id} already exists...")
        if check_answer_exists(repo, answer_id):
            print(f"  Answer with ID {answer_id} already exists in the database!")
            print("   Skipping insertion to avoid duplicate key error.")

            if check_questions_exist(repo, question_ids):
                print(
                    f"  Questions with IDs {question_ids[0]}-{question_ids[-1]} already exist!"
                )
                print("\n Data already in database - no action needed.")
            else:
                print(
                    "   But questions are missing. You may need to delete the answer and re-run."
                )

            return

        print("Extracting Arabic Job Basket HTML content...")
        html_content = extract_arabic_job_basket_html()
        print(f"Extracted {len(html_content)} characters of Arabic HTML content")

        # Metadata for the answer
        meta = {
            "console": None,
            "sub_console": None,
            "country": None,
            "inst": None,
            "bank_map": None,
        }

        print("Inserting Arabic answer into CHATBOT_ANSWERS...")

        with repo.conn.cursor() as c:
            sql = """
            INSERT INTO UNI_REPOS.CHATBOT_ANSWERS
              (ID, CONSOLE_CODE, SUB_CONSOLE_CODE, COUNTRY_CODE,
                INST_CODE, BANK_MAP_CODE,
               ANSWER_TEXT_AR, ANSWER_TEXT_OTH, CREATED_AT)
            VALUES (:id, :console, :sub_console, :country, :inst, :bank_map,
                    :ans_ar, :ans_oth, SYSDATE)
            """
            c.execute(
                sql,
                {
                    "id": answer_id,
                    "console": meta["console"],
                    "sub_console": meta["sub_console"],
                    "country": meta["country"],
                    "inst": meta["inst"],
                    "bank_map": meta["bank_map"],
                    "ans_ar": html_content,
                    "ans_oth": None,
                },
            )

        print(f"Answer inserted with ID: {answer_id}")

        # Arabic questions to insert
        questions = [
            {"id": 66601, "text": "ما هي مهام سلة المهام؟"},
            {"id": 66602, "text": "كيف أستعرض مهامي في سلة المهام؟"},
            {"id": 66603, "text": "ما الذي يظهر في تبويب سلة المهام؟"},
            {"id": 66604, "text": "أين أجد سلة المهام؟"},
        ]

        print(f"Inserting {len(questions)} Arabic questions into USER_MANUAL_FAQ...")

        with repo.conn.cursor() as c:
            sql = """
            INSERT INTO UNI_REPOS.USER_MANUAL_FAQ
              (ID, COUNTRY_CODE, INST_CODE, LANG_ID, CONSOLE_CODE,
              SUB_CONSOLE_CODE,
               BANK_MAP_CODE, QUESTION_TEXT, VECTOR_CSV, HIT_COUNT, ANSWER_ID)
            VALUES (:id, :country, :inst, :lang, :console, :sub_console,
                    :bank_map, :q, NULL, 0, :answer_id)
            """

            for q in questions:
                c.execute(
                    sql,
                    {
                        "id": q["id"],
                        "country": None,
                        "inst": None,
                        "lang": 1,  # 1 = Arabic, 2 = English
                        "console": None,
                        "sub_console": None,
                        "bank_map": None,
                        "q": q["text"],
                        "answer_id": answer_id,
                    },
                )
                print(f"  - Question {q['id']}: {q['text']}")

        print("\nCommitting transaction...")
        repo.commit()

        print("\n Successfully inserted Arabic Job Basket FAQ!")
        print(f"   Answer ID: {answer_id}")
        print(f"   Question IDs: {question_ids[0]}-{question_ids[-1]}")
        print(f"   HTML Content Length: {len(html_content)} characters")
        print("   Language: Arabic (LANG_ID = 1)")

    except Exception as e:
        print(f"\n Error occurred: {e}")
        print("Rolling back transaction...")
        repo.rollback()
        raise

    finally:
        print("\nClosing database connection...")
        repo.close()


if __name__ == "__main__":
    main()
