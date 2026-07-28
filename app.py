import base64

import streamlit as st

from study_buddy.flashcards import generate_flashcards, load_flashcards, save_flashcards
from study_buddy.materials import MATERIALS_DIR, ensure_materials_dir, list_pdfs, pdf_document_block
from study_buddy.quiz import generate_quiz, grade_answer
from study_buddy.summarize import summarize

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="centered")


def uploaded_pdf_block(uploaded_file):
    data = base64.standard_b64encode(uploaded_file.getvalue()).decode("utf-8")
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": data},
        "title": uploaded_file.name,
    }


def material_input(key_prefix):
    source = st.radio(
        "Study material source",
        ["Paste text", "Upload PDF", "Use a PDF from materials/"],
        key=f"{key_prefix}_source",
    )
    if source == "Paste text":
        text = st.text_area("Paste your study material", height=200, key=f"{key_prefix}_text")
        return text if text.strip() else None
    if source == "Upload PDF":
        uploaded = st.file_uploader("Upload a PDF", type="pdf", key=f"{key_prefix}_upload")
        if uploaded is None:
            return None
        return [uploaded_pdf_block(uploaded), {"type": "text", "text": "This is the study material."}]
    ensure_materials_dir()
    pdfs = list_pdfs()
    if not pdfs:
        st.info(f"No PDFs found in `{MATERIALS_DIR}`. Drop one there or upload instead.")
        return None
    filename = st.selectbox("Pick a PDF", pdfs, key=f"{key_prefix}_pdf_select")
    return [pdf_document_block(filename), {"type": "text", "text": "This is the study material."}]


def reset_quiz_state():
    for k in ("quiz_questions", "quiz_index", "quiz_score", "quiz_feedback"):
        st.session_state.pop(k, None)


st.title("📚 AI Study Buddy")

tab_summarize, tab_quiz, tab_flashcards, tab_review = st.tabs(
    ["Summarize", "Quiz", "Flashcards", "Review Flashcards"]
)

with tab_summarize:
    content = material_input("summarize")
    if st.button("Summarize", key="summarize_btn", disabled=content is None):
        with st.spinner("Summarizing..."):
            result = summarize(content)
        st.markdown(result)

with tab_quiz:
    content = material_input("quiz")
    num_questions = st.number_input(
        "How many questions?", min_value=1, max_value=20, value=5, key="quiz_num"
    )
    if st.button("Generate quiz", key="quiz_btn", disabled=content is None):
        with st.spinner("Generating quiz..."):
            st.session_state.quiz_questions = generate_quiz(content, int(num_questions))
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_feedback = None
        st.experimental_rerun()

    questions = st.session_state.get("quiz_questions")
    if questions:
        idx = st.session_state.quiz_index
        if idx < len(questions):
            q = questions[idx]
            st.subheader(f"Question {idx + 1} of {len(questions)}")
            st.write(q["question"])
            if q["type"] == "mcq" and q["options"]:
                answer = st.radio("Your answer", q["options"], key=f"quiz_answer_{idx}")
            else:
                answer = st.text_input("Your answer", key=f"quiz_answer_{idx}")

            if st.session_state.quiz_feedback is None:
                if st.button("Submit answer", key=f"quiz_submit_{idx}"):
                    with st.spinner("Grading..."):
                        result = grade_answer(q["question"], q["answer"], answer)
                    st.session_state.quiz_feedback = result
                    if result["correct"]:
                        st.session_state.quiz_score += 1
                    st.experimental_rerun()
            else:
                fb = st.session_state.quiz_feedback
                if fb["correct"]:
                    st.success(f"Correct! {fb['feedback']}")
                else:
                    st.error(f"Not quite. Correct answer: {q['answer']}. {fb['feedback']}")
                if st.button("Next question", key=f"quiz_next_{idx}"):
                    st.session_state.quiz_index += 1
                    st.session_state.quiz_feedback = None
                    st.experimental_rerun()
        else:
            st.success(f"Quiz complete! Score: {st.session_state.quiz_score}/{len(questions)}")
            if st.button("Restart", key="quiz_restart"):
                reset_quiz_state()
                st.experimental_rerun()

with tab_flashcards:
    content = material_input("flashcards")
    num_cards = st.number_input(
        "How many flashcards?", min_value=1, max_value=50, value=10, key="fc_num"
    )
    if st.button("Generate flashcards", key="fc_btn", disabled=content is None):
        with st.spinner("Generating flashcards..."):
            cards = generate_flashcards(content, int(num_cards))
        all_cards = save_flashcards(cards)
        st.success(f"Saved {len(cards)} flashcards to flashcards.json ({len(all_cards)} total).")
        st.session_state.new_flashcards = cards

    if st.session_state.get("new_flashcards"):
        for i, c in enumerate(st.session_state.new_flashcards, 1):
            with st.expander(f"Card {i}: {c['front']}"):
                st.write(c["back"])

with tab_review:
    cards = load_flashcards()
    if not cards:
        st.info("No flashcards saved yet. Generate some in the Flashcards tab.")
    else:
        for i, c in enumerate(cards, 1):
            with st.expander(f"Card {i}: {c['front']}"):
                st.write(c["back"])
