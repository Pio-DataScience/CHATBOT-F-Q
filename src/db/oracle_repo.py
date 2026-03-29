import datetime
import os
import logging

import oracledb

logger = logging.getLogger(__name__)


class OracleRepo:
    def __init__(
        self,
        dsn,
        user,
        password,
        schema="UNI_REPOS",
        table_answers="CHATBOT_ANSWERS",
        table_questions="USER_MANUAL_FAQ",
    ):
        # Enable Thick mode if Instant Client path is provided or found
        client_path = os.getenv("ORACLE_CLIENT_PATH", r"C:\Program Files\instantclient_23_9")
        if client_path and os.path.exists(client_path):
            try:
                oracledb.init_oracle_client(lib_dir=client_path)
            except oracledb.ProgrammingError:
                # Already initialized
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to initialize Oracle Client from {client_path}: {e}")

        self.conn = oracledb.connect(user=user, password=password, dsn=dsn)
        self.conn.autocommit = False
        self.schema = schema.strip(' "') if schema else ""
        self.table_answers = table_answers.strip(' "') if table_answers else ""
        self.table_questions = table_questions.strip(' "') if table_questions else ""
        
        # Check if CREATED_AT column exists in the answers table
        self.has_created_at = self._check_column_exists(self.table_answers, "CREATED_AT")
        
        logger.info(f"OracleRepo connected to: [{dsn}] as user: [{user}]")
        logger.info(f"OracleRepo initialized with schema: [{self.schema}] (len={len(self.schema)})")
        logger.info(f"Answers table: [{self.table_answers}] (len={len(self.table_answers)}), has_created_at: {self.has_created_at}")
        logger.info(f"Questions table: [{self.table_questions}] (len={len(self.table_questions)})")

    def _check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table in the current schema."""
        try:
            with self.conn.cursor() as c:
                # Use a lightweight query to check the schema
                c.execute(f"SELECT * FROM {self.schema}.{table_name} WHERE 1=0")
                columns = [col[0].upper() for col in c.description]
                return column_name.upper() in columns
        except Exception as e:
            logger.warning(f"Failed to check column existence for {table_name}.{column_name}: {e}")
            return False # Safe fallback: assume it doesn't exist

    def close(self):
        self.conn.close()

    def nextval(self, seq_name: str | None):
        if not seq_name:
            return None
        with self.conn.cursor() as c:
            c.execute(f"SELECT {seq_name}.NEXTVAL FROM dual")
            return c.fetchone()[0]

    def get_sequence_info(self, seq_name: str):
        """Get current value and next value of a sequence."""
        with self.conn.cursor() as c:
            # Get last number
            c.execute(
                """
                SELECT LAST_NUMBER 
                FROM USER_SEQUENCES 
                WHERE SEQUENCE_NAME = :seq_name
            """,
                {"seq_name": seq_name},
            )
            result = c.fetchone()
            last_number = result[0] if result else None

            return {"sequence_name": seq_name, "last_number": last_number}

    def get_table_id_stats(self, table_name: str):
        """Get min, max, and count of IDs in a table."""
        with self.conn.cursor() as c:
            c.execute(f"""
                SELECT 
                    MIN(ID) as min_id,
                    MAX(ID) as max_id,
                    COUNT(*) as row_count
                FROM {self.schema}.{table_name}
            """)
            result = c.fetchone()
            return {
                "table": table_name,
                "min_id": result[0] if result else None,
                "max_id": result[1] if result else None,
                "row_count": result[2] if result else 0,
            }

    def check_id_exists(self, table_name: str, id_value: int):
        """Check if an ID already exists in a table."""
        with self.conn.cursor() as c:
            c.execute(
                f"""
                SELECT COUNT(*) 
                FROM {self.schema}.{table_name} 
                WHERE ID = :id_val
            """,
                {"id_val": id_value},
            )
            count = c.fetchone()[0]
            return count > 0

    def delete_existing_faq(self, console, sub_console, lang):
        """
        Delete existing FAQ questions and answers for the same console, subconsole, and language.
        This allows re-importing updated documents while preserving other language versions.

        Args:
            console: Console code
            sub_console: Sub-console code
            lang: Language ID
        """
        with self.conn.cursor() as c:
            logger.info(f"Targeting questions table for delete: {self.schema}.{self.table_questions}")
            c.execute(
                f"""
                DELETE FROM {self.schema}.{self.table_questions}
                WHERE CONSOLE_CODE = :console
                AND SUB_CONSOLE_CODE = :sub_console
                AND LANG_ID = :lang
            """,
                {"console": console, "sub_console": sub_console, "lang": lang},
            )

            deleted_questions = c.rowcount

            logger.info(f"Targeting answers table for delete: {self.schema}.{self.table_answers}")
            c.execute(
                f"""
                DELETE FROM {self.schema}.{self.table_answers}
                WHERE CONSOLE_CODE = :console
                AND SUB_CONSOLE_CODE = :sub_console
                AND LANG_ID = :lang
            """,
                {"console": console, "sub_console": sub_console, "lang": lang},
            )

            deleted_answers = c.rowcount

        return deleted_questions, deleted_answers

    def insert_answer(self, meta, html, answers_to="OTH", seq_name=""):
        """
        Insert answer into CHATBOT_ANSWERS table.

        The ID is automatically generated by database trigger using sequence.
        The seq_name parameter is kept for backward compatibility but not used.

        Args:
            meta: Dictionary with console, sub_console, country, inst, lang, bank_map
            html: HTML content for the answer
            answers_to: 'OTH' or 'AR' to specify which language column to use
            seq_name: (deprecated) Sequence name - not used, triggers handle IDs

        Returns:
            answer_id: The generated answer ID from the database
        """
        import logging

        logger = logging.getLogger(__name__)

        # SQL now includes LANG_ID to match USER_MANUAL_FAQ table logic
        cols = [
            "CONSOLE_CODE",
            "SUB_CONSOLE_CODE",
            "COUNTRY_CODE",
            "INST_CODE",
            "LANG_ID",
            "BANK_MAP_CODE",
            "ANSWER_TEXT_AR",
            "ANSWER_TEXT_OTH",
        ]
        placeholders = [
            ":console",
            ":sub_console",
            ":country",
            ":inst",
            ":lang",
            ":bank_map",
            ":ans_ar",
            ":ans_oth",
        ]

        if self.has_created_at:
            cols.append("CREATED_AT")
            placeholders.append(":created_at")

        sql = f"""
        INSERT INTO {self.schema}.{self.table_answers}
          ({', '.join(cols)})
        VALUES ({', '.join(placeholders)})
        RETURNING ID INTO :new_id
        """

        ans = {
            "ans_ar": html if answers_to == "AR" else None,
            "ans_oth": html if answers_to == "OTH" else None,
        }

        logger.debug("Inserting answer (ID will be auto-generated by trigger)")
        logger.debug(
            "Console: %s, Sub-console: %s, Country: %s, Inst: %s, Lang: %s",
            meta.get("console"),
            meta.get("sub_console"),
            meta.get("country"),
            meta.get("inst"),
            meta.get("lang"),
        )

        try:
            with self.conn.cursor() as c:
                # Create output variable to capture generated ID
                id_var = c.var(int)

                binds = dict(
                    console=meta["console"],
                    sub_console=meta["sub_console"],
                    country=meta["country"],
                    inst=meta["inst"],
                    lang=meta["lang"],
                    bank_map=meta["bank_map"],
                    **ans,
                    new_id=id_var,
                )
                if self.has_created_at:
                    binds["created_at"] = datetime.datetime.now()

                c.execute(sql, binds)

                # Get the generated ID from the output variable
                new_id = id_var.getvalue()[0]

                logger.info("✓ Answer inserted with auto-generated ID: %s", new_id)
                return new_id

        except Exception as e:
            logger.error("✗ Failed to insert answer")
            logger.error(
                "Insert values - Console: %s, Sub-console: %s, "
                "Country: %s, Inst: %s, Lang: %s, Bank_map: %s, Answers_to: %s",
                meta.get("console"),
                meta.get("sub_console"),
                meta.get("country"),
                meta.get("inst"),
                meta.get("lang"),
                meta.get("bank_map"),
                answers_to,
            )
            logger.error("Error details: %s", str(e))
            raise

    def insert_questions_bulk(self, rows, seq_name=""):
        """
        Insert multiple questions into USER_MANUAL_FAQ table.

        The IDs are automatically generated by database trigger using sequence.
        The seq_name parameter is kept for backward compatibility but not used.

        Args:
            rows: List of dicts with question_text, answer_id, country,
                  inst, lang, console, sub_console, bank_map
            seq_name: (deprecated) Sequence name - not used, triggers handle IDs
        """
        import logging

        logger = logging.getLogger(__name__)

        # SQL now omits ID - database trigger will assign it automatically
        sql = f"""
        INSERT INTO {self.schema}.{self.table_questions}
          (COUNTRY_CODE, INST_CODE, LANG_ID, CONSOLE_CODE,
           SUB_CONSOLE_CODE,
           BANK_MAP_CODE, QUESTION_TEXT, VECTOR_CSV, HIT_COUNT, ANSWER_ID)
        VALUES (:country, :inst, :lang, :console, :sub_console,
                :bank_map, :q, NULL, 0, :answer_id)
        """

        logger.debug(
            "Inserting %d questions (IDs will be auto-generated by trigger)", len(rows)
        )

        try:
            with self.conn.cursor() as c:
                data = []
                for r in rows:
                    data.append(
                        dict(
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
                logger.info(
                    "✓ Inserted %d questions with auto-generated IDs", len(data)
                )

        except Exception as e:
            logger.error("✗ Failed to insert questions bulk")
            logger.error("Number of rows: %d", len(rows))
            logger.error("First row data: %s", data[0] if data else "N/A")
            logger.error("Error details: %s", str(e))
            raise

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
