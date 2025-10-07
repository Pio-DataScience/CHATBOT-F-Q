"""
Streamlit GUI for FAQ document processing system.
Provides user interface for document upload and compilation.
"""

import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def load_console_options():
    """
    L        params = {
            "console_id": console_id,
            "sub_console_id": sub_console_id,
            "country": country,
            "inst": inst,
            "lang": lang,
            "answers_to": answers_to_code,
            "bank_map": bank_map,
            "gen_questions": True,
            "lm_base": lm_base,
            "lm_model": lm_model,
            "qmin": qmin,
            "qmax": qmax,
            "q_max_words": q_max_words,
            "seq_ans": seq_ans,
            "seq_faq": seq_faq
        }ns from the API.

    Returns:
        List of console dictionaries or empty list on error
    """
    try:
        response = requests.get(f"{API_BASE_URL}/options/console", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("consoles", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load console options: {str(e)}")
        return []


def load_subconsole_options(console_id):
    """
    Load subconsole options for a given console from the API.

    Args:
        console_id: The ID of the parent console

    Returns:
        List of subconsole dictionaries or empty list on error
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/options/subconsole/{console_id}", timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("subconsoles", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load subconsole options: {str(e)}")
        return []


def compile_document(file, params):
    """
    Send document and parameters to the API for compilation.

    Args:
        file: The uploaded file object
        params: Dictionary of compilation parameters

    Returns:
        API response JSON or None on error
    """
    try:
        files = {
            "file": (
                file.name,
                file.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }

        form_data = {
            "console_id": params["console_id"],
            "sub_console_id": params["sub_console_id"],
            "country": params["country"],
            "inst": params["inst"],
            "lang": params["lang"],
            "answers_to": params["answers_to"],
            "bank_map": params.get("bank_map", ""),
            "gen_questions": params.get("gen_questions", False),
            "lm_base": params.get("lm_base", "http://localhost:1234/v1"),
            "lm_model": params.get("lm_model", ""),
            "qmin": params.get("qmin", 3),
            "qmax": params.get("qmax", 8),
            "q_max_words": params.get("q_max_words", 12),
            "seq_ans": params.get("seq_ans", ""),
            "seq_faq": params.get("seq_faq", ""),
        }

        response = requests.post(
            f"{API_BASE_URL}/compile", files=files, data=form_data, timeout=600
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        st.error("Request timeout - the compilation took too long")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Compilation failed: {str(e)}")
        if hasattr(e.response, "text"):
            st.error(f"Details: {e.response.text}")
        return None


def main():
    """
    Main Streamlit application function.
    """
    st.set_page_config(
        page_title="FAQ Document Compiler", page_icon="📚", layout="wide"
    )

    st.title("📚 FAQ Document Compilation System")
    st.markdown("---")

    health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if health_response.status_code == 200:
        st.success("API is connected and healthy")
    else:
        st.error("API is not responding properly")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Console Configuration")

        consoles = load_console_options()
        if not consoles:
            st.error(
                "No console options available. Please check the database connection."
            )
            return

        console_options = {
            f"{c['id']} - {c.get('desc_eng', 'N/A')}": c["id"] for c in consoles
        }

        selected_console_label = st.selectbox(
            "Select Console",
            options=list(console_options.keys()),
            help="Choose the console for this FAQ document",
        )
        console_id = console_options[selected_console_label]

        subconsoles = load_subconsole_options(console_id)

        if subconsoles:
            subconsole_options = {
                f"{sc['id']} - {sc.get('desc_eng', 'N/A')}": sc["id"]
                for sc in subconsoles
            }

            selected_subconsole_label = st.selectbox(
                "Select Sub-Console",
                options=list(subconsole_options.keys()),
                help="Choose the sub-console for this FAQ document",
            )
            sub_console_id = subconsole_options[selected_subconsole_label]
        else:
            st.warning("No sub-console options available for the selected console")
            sub_console_id = 0

        st.markdown("---")

        country = st.number_input(
            "Country Code",
            min_value=0,
            value=400,
            step=1,
            help="Enter the country code",
        )

        inst = st.number_input(
            "Institution Code",
            min_value=0,
            value=1,
            step=1,
            help="Enter the institution code",
        )

        answers_to = st.selectbox(
            "Document Language",
            options=["English", "Arabic"],
            index=0,
            help="Select the language of the FAQ document",
        )

        if answers_to == "Arabic":
            lang = 1
            answers_to_code = "AR"
        else:
            lang = 2
            answers_to_code = "OTH"

        bank_map = st.text_input(
            "Bank Map Code", value="", help="Optional: Enter the bank mapping code"
        )

    with col2:
        st.subheader("📝 Question Generation Settings")

        st.info("Questions will be automatically generated using AI")

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            qmin = st.number_input(
                "Min Questions per Section",
                min_value=1,
                value=3,
                step=1,
                help="Minimum questions to generate per section",
            )

        with col_q2:
            qmax = st.number_input(
                "Max Questions per Section",
                min_value=1,
                value=8,
                step=1,
                help="Maximum questions to generate per section",
            )

        q_max_words = st.number_input(
            "Max Words per Question",
            min_value=1,
            value=12,
            step=1,
            help="Maximum words allowed per question",
        )

        lm_base = "http://localhost:1234/v1"
        lm_model = ""
        seq_ans = ""
        seq_faq = ""

    st.markdown("---")
    st.subheader("📁 Document Upload")

    uploaded_file = st.file_uploader(
        "Choose a DOCX file",
        type=["docx"],
        help="Upload the FAQ document in DOCX format",
    )

    if uploaded_file is not None:
        st.info(f"File selected: {uploaded_file.name}")
        st.write(f"File size: {uploaded_file.size / 1024:.2f} KB")

    st.markdown("---")

    if st.button("🚀 Compile Document", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a DOCX file first")
            return

        if not sub_console_id:
            st.error("Please select a valid sub-console")
            return

        params = {
            "console_id": console_id,
            "sub_console_id": sub_console_id,
            "country": country,
            "inst": inst,
            "lang": lang,
            "answers_to": answers_to_code,
            "bank_map": bank_map,
            "gen_questions": True,
            "lm_base": lm_base,
            "lm_model": lm_model,
            "qmin": qmin,
            "qmax": qmax,
            "q_max_words": q_max_words,
            "seq_ans": seq_ans,
            "seq_faq": seq_faq,
        }

        with st.spinner("Processing document... This may take several minutes."):
            result = compile_document(uploaded_file, params)

        if result:
            st.success("Document compiled successfully")

            with st.expander("View Compilation Details", expanded=True):
                st.json(result)

            if "output" in result:
                with st.expander("View System Output"):
                    st.code(result["output"], language="text")


if __name__ == "__main__":
    main()
