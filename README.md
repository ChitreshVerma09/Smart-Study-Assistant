# 🎓 Smart Study Assistant

An AI-powered academic assistant engineered to streamline studying and exam preparation. By leveraging high-throughput **Groq LPU inference** and **Streamlit**, this tool synthesizes dense PDF study materials, provides hallucination-free document Q&A, and auto-evaluates customized mock tests in real-time.

---

## 🚀 Key Features

- **📑 Adaptive Notes Synthesis**: Convert multi-page lecture slides or textbook chapters into:
  - Key Concept Bullets & Takeaways
  - Comprehensive Exam & Revision Guides
  - Quick-Reference Formula & Definition Cheat Sheets
- **💬 Grounded Document Q&A**: Chat directly with uploaded study material. Answers are strictly bounded to the context of the notes to eliminate hallucinations.
- **🎯 Dynamic MCQ Test Simulator**: Automatically generates custom multiple-choice quizzes with real-time scoring, percentage metrics, answer keys, and detailed explanations.
- **⚡ Ultra-Low Latency Inference**: Powered by Groq's high-throughput LPU engine with dynamic model fallback to ensure 100% uptime.
- **🎨 Modern Interactive UI**: Features clean glassmorphism, instant workspace capabilities previews, and a 1-click sample notes demo loader.

---

## 🛠️ Tech Stack & Architecture

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **LLM Engine & Inference**: [Groq API](https://console.groq.com/) (Dynamic fallback prioritizing active Llama/Mistral models)
- **Document Processing**: `pypdf`
- **Environment Management**: `python-dotenv`
- **Language**: Python 3.10+

---

## 📂 Project Structure

```text
Smart-Study-Assistant/
│
├── app.py                # Main Streamlit application with UI & inference logic
├── requirements.txt      # Project dependencies
├── .env                  # Environment variables (Groq API Key)
└── README.md             # Project documentation & setup guide

⚙️ Local Setup & Installation
1. Clone the Repository
git clone [https://github.com/ChitreshVerma09/Smart-Study-Assistant.git](https://github.com/ChitreshVerma09/Smart-Study-Assistant.git)
cd Smart-Study-Assistant

2. Create and Activate Virtual Environment
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Groq API Key
Create a .env file in the root directory:
GROQ_API_KEY=your_actual_groq_api_key_here
(Get your free API key from GroqCloud Console)

5. Run the Application
streamlit run app.py

🎯 How It Works
Upload Notes: Drag and drop any lecture note, syllabus, or chapter in PDF format (or test instantly using the built-in Demo mode).

Synthesize & Explore: Generate structured revision summaries tailored to your study style.

Resolve Doubts: Ask conceptual questions in the live interactive chat.

Self-Assessment: Set the question count, attempt the generated MCQs, and receive instant scorecards with explanations.

🛡️ License
This project is open-source and available under the MIT License.
