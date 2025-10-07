# src/db/oracle_repo.py
import oracledb
import datetime


class OracleRepo:
    def __init__(self, dsn, user, password):
        self.conn = oracledb.connect(user=user, password=password, dsn=dsn)
        self.conn.autocommit = False

    def close(self):
        self.conn.close()

    def nextval(self, seq_name: str | None):
        if not seq_name:
            return None
        with self.conn.cursor() as c:
            c.execute(f"SELECT {seq_name}.NEXTVAL FROM dual")
            return c.fetchone()[0]

    def delete_existing_faq(self, console, sub_console):
        """
        Delete existing FAQ questions and answers for the same console and subconsole.
        This allows re-importing updated documents.

        Args:
            console: Console code
            sub_console: Sub-console code
        """
        with self.conn.cursor() as c:
            c.execute(
                """
                DELETE FROM UNI_REPOS.USER_MANUAL_FAQ
                WHERE CONSOLE_CODE = :console
                AND SUB_CONSOLE_CODE = :sub_console
            """,
                {"console": console, "sub_console": sub_console},
            )

            deleted_questions = c.rowcount

            c.execute(
                """
                DELETE FROM UNI_REPOS.CHATBOT_ANSWERS
                WHERE CONSOLE_CODE = :console
                AND SUB_CONSOLE_CODE = :sub_console
            """,
                {"console": console, "sub_console": sub_console},
            )

            deleted_answers = c.rowcount

        return deleted_questions, deleted_answers

    def insert_answer(self, meta, html, answers_to="OTH", seq_name=""):
        """
        answers_to: 'OTH' or 'AR'
        returns: answer_id
        """
        sql = f"""
        INSERT INTO UNI_REPOS.CHATBOT_ANSWERS
          (ID, CONSOLE_CODE, SUB_CONSOLE_CODE, COUNTRY_CODE,
            INST_CODE, BANK_MAP_CODE,
           ANSWER_TEXT_AR, ANSWER_TEXT_OTH, CREATED_AT)
        VALUES (:id, :console, :sub_console, :country, :inst, :bank_map,
                :ans_ar, :ans_oth, :created_at)
        """
        ans = {
            "ans_ar": html if answers_to == "AR" else None,
            "ans_oth": html if answers_to == "OTH" else None,
        }
        new_id = self.nextval(seq_name)
        with self.conn.cursor() as c:
            c.execute(
                sql,
                dict(
                    id=new_id,
                    console=meta["console"],
                    sub_console=meta["sub_console"],
                    country=meta["country"],
                    inst=meta["inst"],
                    bank_map=meta["bank_map"],
                    **ans,
                    created_at=datetime.datetime.now(),
                ),
            )
            if new_id is None:
                # Identity column case: fetch just inserted id
                c.execute("SELECT MAX(ID) FROM UNI_REPOS.CHATBOT_ANSWERS")
                new_id = c.fetchone()[0]
        return new_id

    def insert_questions_bulk(self, rows, seq_name=""):
        """
        rows = [ {question_text, answer_id, country,
        inst, lang, console, sub_console, bank_map} ]
        """
        sql = """
        INSERT INTO UNI_REPOS.USER_MANUAL_FAQ
          (ID, COUNTRY_CODE, INST_CODE, LANG_ID, CONSOLE_CODE,
          SUB_CONSOLE_CODE,
           BANK_MAP_CODE, QUESTION_TEXT, VECTOR_CSV, HIT_COUNT, ANSWER_ID)
        VALUES (:id, :country, :inst, :lang, :console, :sub_console,
                :bank_map, :q, NULL, 0, :answer_id)
        """
        with self.conn.cursor() as c:
            data = []
            for r in rows:
                rid = self.nextval(seq_name)
                data.append(
                    dict(
                        id=rid,
                        country=r["country"],
                        inst=r["inst"],
                        lang=r["lang"],
                        console=r["console"],
                        sub_console=r["sub_console"],
                        bank_map=r["bank_map"],
                        q=r["q"][:1000],
                        answer_id=r["answer_id"],
                    )
                )
            c.executemany(sql, data)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
