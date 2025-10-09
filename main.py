# main.py
import argparse
import json
import logging
import sys
from pathlib import Path

from src.faq.splitter import split_into_faq_items
from src.io.docx_to_html import convert_docx_to_html
from src.utils.files import ensure_dir, write_text


def build_parser():
    """Build command-line argument parser.
    Example usage:
        python main.py --in EN_doc.docx --out output --mode concat
    Arguments:
        --in: Input DOCX file (default: EN_doc.docx)
        --out: Output directory (default: out)
        --mode: Output mode: concat (single file) or files (one per section)
        --log: Logging level (default: INFO)
        --gen-questions: Generate questions using LLM
        --lm-base: Base URL for LLM API (default: http://localhost:1234/v1)
        --lm-model: Model name for LLM (default: "")
        --qmin: Minimum number of questions per section (default: 3)
        --qmax: Maximum number of questions per section (default: 8)
        --q-max-words: Maximum words per question (default: 12)
        --q-out: Output file for questions (default: output/questions.jsonl)
        --limit: Limit number of sections to process (default: None)
    """
    p = argparse.ArgumentParser("docx → FAQ HTML fragments")
    p.add_argument("--in", dest="docx", default="EN_doc.docx", help="Input DOCX")
    p.add_argument("--out", dest="outdir", default="out", help="Output folder")
    p.add_argument(
        "--mode",
        choices=["concat", "files"],
        default="concat",
        help="concat=single fragments file, files=one file per section",
    )
    p.add_argument("--log", default="INFO")

    p.add_argument("--gen-questions", action="store_true")
    p.add_argument("--lm-base", default="http://localhost:1234/v1")
    p.add_argument("--lm-model", default="")
    p.add_argument("--qmin", type=int, default=3)
    p.add_argument("--qmax", type=int, default=8)
    p.add_argument("--q-max-words", type=int, default=12)
    p.add_argument("--q-out", default="output/questions.jsonl")
    p.add_argument("--limit", type=int, default=None)

    p.add_argument("--db-insert", action="store_true")
    p.add_argument("--db-dsn", default="192.168.30.43:1521/OPENBI2")
    p.add_argument("--db-user", default="UNI_REPOS")
    p.add_argument("--db-pass", default="UNI_REPOS")
    p.add_argument("--country", type=int, default=0)
    p.add_argument("--inst", type=int, default=0)
    p.add_argument("--lang", type=int, default=1)  # 1 = English now
    p.add_argument("--console", type=int, default=0)
    p.add_argument("--sub-console", type=int, default=0)
    p.add_argument("--bank-map", default="")
    p.add_argument("--fragments", default="output/faq_fragments.html")
    p.add_argument("--questions-jsonl", default="output/questions.jsonl")
    p.add_argument("--answers-to", choices=["AR", "OTH"], default="OTH")  # English→OTH
    p.add_argument("--seq-ans", default="")  # optional: CHATBOT_ANSWERS seq name
    p.add_argument("--seq-faq", default="")  # optional: USER_MANUAL_FAQ seq name

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    # Configure logging to both console and file
    log_level = getattr(logging, args.log.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Generate daily log filename
    from datetime import datetime

    log_filename = f"faq_processing_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Configure root logger with both file and console handlers
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / log_filename, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger(__name__)

    docx_path = Path(args.docx)
    outdir = Path(args.outdir)

    logger.info("Starting FAQ processing pipeline")
    logger.info("Input file: %s", docx_path)
    logger.info("Output directory: %s", outdir)
    logger.info("Mode: %s", args.mode)

    try:
        ensure_dir(outdir)
        logger.debug("Created output directory: %s", outdir)
    except Exception as e:
        logger.error("Failed to create output directory %s: %s", outdir, e)
        raise

    logger.info("Converting DOCX → HTML: %s", docx_path)
    try:
        html = convert_docx_to_html(docx_path)
        logger.info("Successfully converted DOCX to HTML (%d characters)", len(html))
    except Exception as e:
        logger.error("Failed to convert DOCX to HTML: %s", e)
        raise

    logger.info("Splitting into FAQ items…")
    try:
        items = split_into_faq_items(html)
        logger.info("Successfully split into %d FAQ items", len(items))
        for i, item in enumerate(items):
            logger.debug("Item %d: %s (level %d)", i + 1, item["slug"], item["level"])
    except Exception as e:
        logger.error("Failed to split into FAQ items: %s", e)
        raise
    # [{slug, level, heading, fragment_html}]

    if args.mode == "concat":
        logger.info("Writing concatenated output file")
        out = outdir / "faq_fragments.html"
        content = "\n\n".join(item["fragment_html"] for item in items)
        try:
            write_text(out, content)
            logger.info("Wrote %s (concat of %d fragments)", out, len(items))
        except Exception as e:
            logger.error("Failed to write concatenated file %s: %s", out, e)
            raise
    else:
        logger.info("Writing individual fragment files")
        for i, item in enumerate(items):
            fp = outdir / f"{item['slug']}.html"
            try:
                write_text(fp, item["fragment_html"])
                logger.debug("Wrote fragment %d/%d: %s", i + 1, len(items), fp)
            except Exception as e:
                logger.error("Failed to write fragment file %s: %s", fp, e)
                raise
        logger.info("Wrote %d fragment files to %s", len(items), outdir)

    if args.gen_questions:
        logger.info("Starting question generation with LLM")
        logger.info("LLM base URL: %s", args.lm_base)
        logger.info("LLM model: %s", args.lm_model or "(default)")
        logger.info("Questions per section: %d-%d", args.qmin, args.qmax)
        logger.info("Max words per question: %d", args.q_max_words)
        if args.limit:
            logger.info("Processing limited to first %d sections", args.limit)

        from src.faq.questions import generate_questions_for_items
        from src.llm.client import LMClient

        try:
            ensure_dir(Path(args.q_out))
            logger.debug("Ensured questions output directory exists")
        except Exception as e:
            logger.error("Failed to create questions output directory: %s", e)
            raise

        try:
            client = LMClient(base_url=args.lm_base, model=args.lm_model)
            logger.info("Initialized LLM client successfully")
        except Exception as e:
            logger.error("Failed to initialize LLM client: %s", e)
            raise

        try:
            qrows = generate_questions_for_items(
                items,
                client,
                qmin=args.qmin,
                qmax=args.qmax,
                max_words=args.q_max_words,
                limit=args.limit,
            )
            logger.info("Generated questions for %d sections", len(qrows))
        except Exception as e:
            logger.error("Failed to generate questions: %s", e)
            raise

        # save JSONL: one record per section
        try:
            lines = []
            for r in qrows:
                lines.append(json.dumps(r, ensure_ascii=False))
            write_text(Path(args.q_out), "\n".join(lines))
            logger.info("Wrote questions to %s", args.q_out)
        except Exception as e:
            logger.error("Failed to write questions file %s: %s", args.q_out, e)
            raise

    logger.info("FAQ processing pipeline completed successfully")

    if args.db_insert:
        from src.db.oracle_repo import OracleRepo
        from src.faq.persist import load_fragments_map, load_questions_jsonl

        try:
            repo = OracleRepo(args.db_dsn, args.db_user, args.db_pass)
            frag = load_fragments_map(args.fragments)
            qrows = load_questions_jsonl(args.questions_jsonl)

            meta = dict(
                country=args.country,
                inst=args.inst,
                lang=args.lang,
                console=args.console,
                sub_console=args.sub_console,
                bank_map=args.bank_map,
            )

            # Delete existing FAQ for the same console and subconsole
            logger.info("Checking for existing FAQ data to delete...")
            deleted_q, deleted_a = repo.delete_existing_faq(
                args.console, args.sub_console
            )
            if deleted_q > 0 or deleted_a > 0:
                logger.info(
                    "Deleted %d existing questions and %d existing answers",
                    deleted_q,
                    deleted_a,
                )
            else:
                logger.info("No existing FAQ data found for this console/subconsole")

            # Track counts for verification
            total_answers_inserted = 0
            total_questions_inserted = 0

            logger.info("Starting database insertion...")
            logger.info("Processing %d sections from questions file", len(qrows))

            for idx, r in enumerate(qrows, 1):
                slug = r["slug"]
                heading, answer_html = frag[slug]

                # 1) insert ANSWER, get ID
                ans_id = repo.insert_answer(
                    meta,
                    html=answer_html,
                    answers_to=args.answers_to,
                    seq_name=args.seq_ans,
                )
                total_answers_inserted += 1

                # 2) insert QUESTIONS: base heading + variants share the same ANSWER_ID
                qs = [heading] + (r.get("alternatives") or [])
                rows = [{"q": q, "answer_id": ans_id, **meta} for q in qs]
                repo.insert_questions_bulk(rows, seq_name=args.seq_faq)
                total_questions_inserted += len(rows)

                logger.debug(
                    "Section %d/%d: Inserted 1 answer + %d questions for '%s'",
                    idx,
                    len(qrows),
                    len(rows),
                    slug[:50],
                )

            repo.commit()

            # Final verification log
            logger.info("=" * 80)
            logger.info("DATABASE INSERTION SUMMARY")
            logger.info("=" * 80)
            logger.info("Sections processed: %d", len(qrows))
            logger.info("Answers inserted: %d", total_answers_inserted)
            logger.info("Questions inserted: %d", total_questions_inserted)
            logger.info(
                "Verification: Sections=%d, Answers=%d (Should be identical)",
                len(qrows),
                total_answers_inserted,
            )
            logger.info("Database transaction committed successfully")
            logger.info("=" * 80)
        except Exception as e:
            logging.error("Exception during DB insert: %s", e)
            try:
                repo.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                repo.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())


# python main.py --db-insert \
#   --db-dsn "192.168.30.43:1521/OPENBI2" --db-user "BI_DWH" --db-pass "BI_DWH" \
#   --fragments output/faq_fragments.html \
#   --questions-jsonl output/questions.jsonl \
#   --country 400 --inst 1 --lang 1 --console 10 --sub-console 20 --bank-map "XYZ" \
#   --answers-to OTH \
#   --seq-ans "CHATBOT_ANSWERS_SEQ" --seq-faq "USER_MANUAL_FAQ_SEQ"


# python main.py --in EN_doc.docx --out output/first.html --mode concat --gen-questions
# --lm-base http://localhost:1234/v1 --qmin 3 --qmax 8 --q-max-words 20 --q-out output/questions.jsonl --db-dsn "192.168.30.43:1521/OPENBI2" --db-user "UNI_REPOS" --db-pass "****"
