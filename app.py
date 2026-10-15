import os
import json
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq

# --- 1. Page Configuration & Futuristic UI Styling ---
st.set_page_config(
    page_title="Smart Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Top Hero Banner */
    .hero-container {
        text-align: center;
        padding: 2.5rem 1rem 1.2rem 1rem;
        background: radial-gradient(circle at 50% 10%, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        border-radius: 20px;
        margin-bottom: 20px;
    }
    
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 20%, #A5B4FC 60%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.15;
        margin-bottom: 0.6rem;
    }
    
    .hero-subtitle {
        font-size: 1.12rem;
        color: #94A3B8;
        max-width: 720px;
        margin: 0 auto 1.2rem auto;
        line-height: 1.6;
    }
    
    /* Stats Bar */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 24px;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    .stat-chip {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 8px 18px;
        text-align: center;
    }
    .stat-number {
        font-size: 1.25rem;
        font-weight: 800;
        color: #38BDF8;
    }
    .stat-text {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 600;
    }

    /* Glass Cards */
    .glass-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 22px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        border-color: #818CF8;
        transform: translateY(-4px);
        box-shadow: 0 14px 28px -8px rgba(99, 102, 241, 0.25);
    }
    
    .card-icon-box {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-bottom: 14px;
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 8px;
    }
    
    .card-desc {
        font-size: 0.9rem;
        color: #94A3B8;
        line-height: 1.55;
    }
    
    /* Interactive Preview Box */
    .preview-box {
        background: #0B0F19;
        border: 1px solid #1E293B;
        border-radius: 14px;
        padding: 18px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. Setup Client & Dynamic Fallback ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

@st.cache_resource(show_spinner=False)
def get_live_groq_models():
    try:
        model_list = client.models.list()
        active_ids = [m.id for m in model_list.data if m.active]
        priority = ["llama", "mixtral", "qwen"]
        def model_rank(m_id):
            m_lower = m_id.lower()
            for idx, p in enumerate(priority):
                if p in m_lower and "vision" not in m_lower:
                    return idx
            return 99
        active_ids.sort(key=model_rank)
        return active_ids
    except Exception:
        return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

ACTIVE_MODELS = get_live_groq_models()

# State Management
if "doc_text" not in st.session_state:
    st.session_state["doc_text"] = ""
if "file_name" not in st.session_state:
    st.session_state["file_name"] = ""
if "summary_output" not in st.session_state:
    st.session_state["summary_output"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "quiz_data" not in st.session_state:
    st.session_state["quiz_data"] = []
if "quiz_submitted" not in st.session_state:
    st.session_state["quiz_submitted"] = False

# Helper Functions
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    extracted = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            extracted.append(t)
    return "\n".join(extracted)

def call_llm(prompt: str) -> str:
    last_error = ""
    for model_name in ACTIVE_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = str(e)
            continue
    st.error(f"Execution Error: {last_error}")
    return ""

def clean_json(raw_text: str) -> str:
    raw = raw_text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.markdown("### 🗂️ Document Control")
    side_pdf = st.file_uploader("Upload Study PDF", type=["pdf"], key="side_uploader")

    if side_pdf is not None and st.session_state.get("file_name") != side_pdf.name:
        with st.spinner("Analyzing document structure..."):
            extracted = extract_text_from_pdf(side_pdf)
            if extracted.strip():
                st.session_state["doc_text"] = extracted
                st.session_state["file_name"] = side_pdf.name
                st.session_state["summary_output"] = ""
                st.session_state["chat_history"] = []
                st.session_state["quiz_data"] = []
                st.session_state["quiz_submitted"] = False
                st.success("Document loaded successfully!")
            else:
                st.warning("No readable text found in PDF.")

    if st.session_state["doc_text"]:
        st.markdown("---")
        st.markdown("### 📊 Document Insights")
        w_count = len(st.session_state["doc_text"].split())
        c_count = len(st.session_state["doc_text"])
        st.metric("Total Words", f"{w_count:,}")
        st.metric("Total Characters", f"{c_count:,}")
        
        if st.button("🔄 Reset Workspace", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- 4. Main View ---

# ========================================================
# FRONT PAGE: INTERACTIVE LANDING SCREEN (NO PDF LOADED)
# ========================================================
if not st.session_state["doc_text"]:
    # Hero Header (Badge removed, Title updated)
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Smart Study Assistant</div>
        <div class="hero-subtitle">
            Turn long syllabus PDFs, lecture notes, and engineering slides into instant structured summaries, grounded live Q&A, and interactive test simulators.
        </div>
        <div class="stats-row">
            <div class="stat-chip">
                <div class="stat-number">10x</div>
                <div class="stat-text">Faster Revision</div>
            </div>
            <div class="stat-chip">
                <div class="stat-number">100%</div>
                <div class="stat-text">Notes-Grounded</div>
            </div>
            <div class="stat-chip">
                <div class="stat-number">&lt; 1s</div>
                <div class="stat-text">Inference Latency</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Row: Center Uploader + Demo Button
    col_u, col_d = st.columns([2.2, 1])
    with col_u:
        main_upload = st.file_uploader("📂 Drop your study material here to launch workspace:", type=["pdf"], key="main_upload_hero")
        if main_upload:
            extracted = extract_text_from_pdf(main_upload)
            if extracted.strip():
                st.session_state["doc_text"] = extracted
                st.session_state["file_name"] = main_upload.name
                st.rerun()

    with col_d:
        st.write("")
        st.write("")
        st.markdown("**Want to test right now?**")
        if st.button("🚀 Load Sample Notes (Demo)", type="primary", use_container_width=True):
            sample_text = """
Artificial Intelligence & Machine Learning Overview:
1. Supervised Learning: Algorithms learn on labeled datasets to make predictions (e.g. Linear Regression, Logistic Regression, Support Vector Machines).
2. Unsupervised Learning: Discovering inherent groupings or representations in unlabelled datasets (e.g. K-Means, Principal Component Analysis).
3. Neural Networks & Deep Learning: Multi-layered computational graphs. Essential components include Weights, Biases, Activation Functions (ReLU, Sigmoid, Softmax), and Backpropagation via Gradient Descent.
4. Model Regularization: Techniques like L1 (Lasso), L2 (Ridge), and Dropout are used to mitigate overfitting and ensure generalization on unseen test data.
5. Transformer Architectures: Utilize Self-Attention mechanisms to process entire sequences in parallel, serving as the foundational backbone for modern Large Language Models (LLMs).
"""
            st.session_state["doc_text"] = sample_text
            st.session_state["file_name"] = "Sample_ML_Notes.txt"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3 Feature Showcase Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="glass-card">
            <div class="card-icon-box">📝</div>
            <div class="card-title">Adaptive Summaries</div>
            <div class="card-desc">Condense multi-page documents into structured bullet takeaways, comprehensive exam guides, or formula cheat sheets in seconds.</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div class="card-icon-box">💬</div>
            <div class="card-title">Contextual Q&A Chat</div>
            <div class="card-desc">Ask specific conceptual questions and get crisp explanations strictly derived from your uploaded notes without hallucinations.</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="glass-card">
            <div class="card-icon-box">🎯</div>
            <div class="card-title">Interactive MCQ Quiz</div>
            <div class="card-desc">Automatically generate multiple-choice assessments with immediate scoring, detailed rationales, and performance metrics.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Live Previews on Front Page
    st.markdown("#### ✨ Live Workspace Preview (Click to explore capabilities)")
    p_tab1, p_tab2, p_tab3 = st.tabs(["📑 Summary Output Preview", "💬 Q&A Chat Preview", "🎯 MCQ Quiz Preview"])

    with p_tab1:
        st.markdown("""
        <div class="preview-box">
            <span style="color: #38BDF8; font-weight: 700;">Sample Generated Summary:</span>
            <ul>
                <li><b>Supervised vs Unsupervised:</b> Supervised uses labeled input-output pairs; Unsupervised finds intrinsic structures without target labels.</li>
                <li><b>Overfitting Mitigation:</b> L1/L2 regularization and Dropout penalize complex weight vectors to improve generalization.</li>
                <li><b>Self-Attention Backbone:</b> Allows models to weigh the significance of words across the entire sequence concurrently.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with p_tab2:
        st.markdown("""
        <div class="preview-box">
            <p><b>Student:</b> <i>"How does Dropout prevent overfitting in Deep Learning?"</i></p>
            <p style="color: #A5B4FC;"><b>StudyMate:</b> During training, Dropout randomly deactivates a fraction of neurons, forcing the network to learn redundant representations rather than relying on specific paths.</p>
        </div>
        """, unsafe_allow_html=True)

    with p_tab3:
        st.markdown("""
        <div class="preview-box">
            <p><b>Q1: Which activation function outputs values strictly in the range (0, 1)?</b></p>
            <span style="color: #10B981; font-weight: 600;">✅ Sigmoid</span> | <span>❌ ReLU</span> | <span>❌ Tanh</span> | <span>❌ Softplus</span>
            <p style="font-size: 0.85rem; color: #94A3B8; margin-top: 6px;"><i>Rationale: Sigmoid maps all real values into probabilities between 0 and 1.</i></p>
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# ========================================================
# WORKSPACE: ONCE PDF / DEMO IS ACTIVE
# ========================================================
st.markdown(f'<div class="hero-title" style="font-size: 2.2rem;">🎓 Smart Study Assistant</div>', unsafe_allow_html=True)
st.caption(f"Active Material: **{st.session_state['file_name']}** | Status: Ready for Synthesis")

tab_sum, tab_chat, tab_quiz = st.tabs(["📝 Summarize", "💬 Interactive Chat", "🎯 Practice Quiz"])

# TAB 1: SUMMARY
with tab_sum:
    st.subheader("Smart Notes Synthesis")
    c_fmt, c_btn = st.columns([3, 1])
    with c_fmt:
        summary_format = st.selectbox(
            "Select Summary Format:",
            [
                "Key Concept Bullets & Takeaways",
                "Detailed Study & Revision Guide",
                "Quick Review Formula & Definition Cheat Sheet"
            ]
        )
    with c_btn:
        st.write("")
        st.write("")
        btn_sum = st.button("⚡ Generate Summary", type="primary", use_container_width=True)

    if btn_sum:
        with st.spinner("Synthesizing study notes..."):
            prompt = f"""
You are an expert academic tutor. Summarize these study notes using the style: '{summary_format}'.
Use clean Markdown with bold terminology, bullet lists, and clear subheadings.

Study Material:
{st.session_state['doc_text'][:12000]}
"""
            res = call_llm(prompt)
            if res:
                st.session_state["summary_output"] = res

    if st.session_state["summary_output"]:
        st.markdown("---")
        st.markdown(st.session_state["summary_output"])

# TAB 2: CHAT
with tab_chat:
    st.subheader("Document Q&A")
    st.caption("Ask specific doubts strictly answered from your notes context.")

    for msg in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.write(msg["user"])
        with st.chat_message("assistant"):
            st.write(msg["bot"])

    user_q = st.chat_input("Ask a question about your uploaded notes...")
    if user_q:
        with st.chat_message("user"):
            st.write(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document notes..."):
                prompt = f"""
Answer the following student question accurately and concisely, using ONLY the provided study notes context.
If the answer is not present in the notes, state clearly that it is not covered.

Question: {user_q}

Study Material:
{st.session_state['doc_text'][:12000]}
"""
                ans = call_llm(prompt)
                if ans:
                    st.write(ans)
                    st.session_state["chat_history"].append({"user": user_q, "bot": ans})

# TAB 3: QUIZ
with tab_quiz:
    st.subheader("Interactive Practice Quiz")
    cq1, cq2 = st.columns([3, 1])
    with cq1:
        num_q = st.slider("Number of Questions", min_value=3, max_value=10, value=5)
    with cq2:
        st.write("")
        btn_quiz = st.button("🎲 Generate Quiz", type="primary", use_container_width=True)

    if btn_quiz:
        with st.spinner(f"Generating {num_q} multiple choice questions..."):
            prompt = f"""
Generate exactly {num_q} multiple-choice questions based on the provided notes.
Output MUST be raw, valid JSON only without markdown or code formatting around it.
JSON structure:
[
  {{
    "id": 1,
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "explanation": "Brief explanation"
  }}
]

Study Material:
{st.session_state['doc_text'][:12000]}
"""
            raw = call_llm(prompt)
            try:
                st.session_state["quiz_data"] = json.loads(clean_json(raw))
                st.session_state["quiz_submitted"] = False
            except Exception:
                st.error("JSON parse issue. Please click Generate Quiz again.")

    if st.session_state["quiz_data"]:
        with st.form("exam_form"):
            user_choices = {}
            for item in st.session_state["quiz_data"]:
                q_id = item.get("id", 1)
                st.markdown(f"**Q{q_id}: {item['question']}**")
                user_choices[q_id] = st.radio(
                    f"Opt_{q_id}",
                    options=item["options"],
                    key=f"mcq_{q_id}",
                    index=None,
                    label_visibility="collapsed"
                )
                st.write("")

            submit_btn = st.form_submit_button("🏁 Submit Test for Scoring", type="primary")

        if submit_btn:
            st.session_state["quiz_submitted"] = True
            st.session_state["user_choices"] = user_choices

        if st.session_state.get("quiz_submitted"):
            score = 0
            total = len(st.session_state["quiz_data"])
            choices = st.session_state.get("user_choices", {})
            st.markdown("---")
            st.subheader("📋 Evaluation & Results")

            for item in st.session_state["quiz_data"]:
                q_id = item.get("id", 1)
                selected = choices.get(q_id)
                actual = item["answer"]

                with st.expander(f"Question {q_id}: {item['question']}", expanded=True):
                    if selected == actual:
                        score += 1
                        st.success(f"✅ **Correct!** Selected: {selected}")
                    else:
                        st.error(f"❌ **Incorrect.** Selected: {selected if selected else 'Not Answered'} | Correct: {actual}")
                    st.info(f"💡 **Explanation:** {item.get('explanation', 'No explanation provided.')}")

            pct = (score / total) * 100
            st.metric("Final Score", f"{score} / {total}", delta=f"{pct:.1f}% Accuracy")
            if pct >= 70:
                st.balloons()