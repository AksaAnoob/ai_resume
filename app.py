import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from modules.resume_parser import extract_text_from_pdf
from modules.skill_extractor import SkillExtractor
from modules.matcher import ResumeMatcher
from modules.skill_gap import analyze_skill_gap
from modules.recommender import ResourceRecommender

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Blue/Navy Glassmorphism Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Navy Background */
    .stApp {
        background: radial-gradient(circle at top right, #1E1B4B 0%, #0F172A 40%, #020617 100%);
        color: #F8FAFC;
    }

    /* Main Container Glassmorphism Card */
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60A5FA 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 24px;
    }

    /* Metric Cards */
    .metric-container {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.5);
    }

    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #38BDF8;
    }

    .metric-lbl {
        font-size: 0.9rem;
        color: #94A3B8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Skill Chips */
    .chip {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .chip-match {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .chip-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    .chip-extra {
        background: rgba(59, 130, 246, 0.15);
        color: #93C5FD;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }

    /* Learning Resource Card */
    .rec-card {
        background: rgba(30, 41, 59, 0.4);
        border-left: 4px solid #818CF8;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .rec-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    .rec-platform {
        font-size: 0.8rem;
        background: #312E81;
        color: #C7D2FE;
        padding: 2px 8px;
        border-radius: 6px;
        margin-left: 8px;
    }

    .rec-desc {
        color: #CBD5E1;
        font-size: 0.9rem;
        margin-top: 6px;
    }

    .rec-link {
        display: inline-block;
        margin-top: 8px;
        color: #38BDF8;
        font-weight: 600;
        text-decoration: none;
        font-size: 0.88rem;
    }
    .rec-link:hover {
        text-decoration: underline;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Singleton Resource Loaders with Streamlit Cache
@st.cache_resource
def get_skill_extractor():
    return SkillExtractor()

@st.cache_resource
def get_matcher():
    return ResumeMatcher()

@st.cache_resource
def get_recommender():
    return ResourceRecommender()

# Sample Job Description for Instant Testing
SAMPLE_JD = """
We are seeking a Senior Full-Stack AI Engineer to join our team. 

Key Responsibilities:
- Design, build, and deploy high-performance web applications using Python, React, and Next.js.
- Develop backend REST APIs with FastAPI and Node.js.
- Implement Machine Learning and NLP models using PyTorch, Hugging Face, and LangChain.
- Containerize services using Docker and manage deployments on AWS cloud infrastructure with Kubernetes.
- Utilize PostgreSQL and Redis for data persistence and high-speed caching.
- Maintain CI/CD pipelines with GitHub Actions.

Requirements:
- 4+ years experience with Python, JavaScript, TypeScript, and SQL.
- Strong expertise in Docker, Kubernetes, Microservices, and System Design.
- Experience with Deep Learning, LLMs, and Scikit-Learn is a major plus.
- Excellent Problem Solving and Teamwork skills.
"""

def build_gauge_chart(overall_score, semantic_score, skill_score):
    """Generates an interactive Plotly radial gauge chart."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = overall_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Compatibility", 'font': {'size': 18, 'color': '#F8FAFC'}},
        number = {'suffix': "%", 'font': {'size': 42, 'color': '#38BDF8', 'family': 'Inter'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': "#6366F1"},
            'bgcolor': "rgba(15, 23, 42, 0.5)",
            'borderwidth': 2,
            'bordercolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [50, 75], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "#34D399", 'width': 4},
                'thickness': 0.75,
                'value': overall_score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#F8FAFC", 'family': "Inter"},
        height=260,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def main():
    # Header Section
    st.markdown('<div class="hero-title">🎯 AI Resume Matcher</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Intelligent PDF resume analysis, semantic embedding similarity, skill gap detection & personalized learning roadmaps.</div>', unsafe_allow_html=True)

    # Initialize Modules
    skill_extractor = get_skill_extractor()
    matcher = get_matcher()
    recommender = get_recommender()

    # Sidebar Options
    with st.sidebar:
        st.header("⚙️ Settings & Info")
        st.markdown("""
        **Scoring Algorithm:**
        - **60%** Semantic Text Embedding Similarity (`all-MiniLM-L6-v2`)
        - **40%** Technical Skill Set Match Ratio
        """)
        st.divider()
        st.markdown("### 🧪 Quick Demo")
        if st.button("Load Sample Job Description"):
            st.session_state["sample_jd"] = SAMPLE_JD
            st.rerun()

    # Input Layout - Dual Column
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### 📄 1. Upload Resume (PDF)")
        uploaded_file = st.file_uploader(
            "Choose a PDF resume file",
            type=["pdf"],
            help="Upload candidate resume in PDF format"
        )

    with col_right:
        st.markdown("### 📋 2. Job Description")
        default_jd_val = st.session_state.get("sample_jd", "")
        job_description = st.text_area(
            "Paste the target job description text",
            value=default_jd_val,
            height=200,
            placeholder="Paste target job requirements, qualifications, and responsibilities here..."
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analyze Button
    analyze_btn = st.button("⚡ Analyze Compatibility", type="primary", use_container_width=True)

    if analyze_btn:
        if not uploaded_file:
            st.error("⚠️ Please upload a PDF resume file before running the analysis.")
            return

        if not job_description.strip():
            st.error("⚠️ Please enter or paste a job description.")
            return

        with st.spinner("🔍 Extracting PDF text, computing AI embeddings & analyzing skill gaps..."):
            try:
                # 1. PDF Text Extraction
                resume_text = extract_text_from_pdf(uploaded_file)
                if not resume_text.strip():
                    st.error("❌ Failed to extract readable text from PDF. The document may be scanned images or password protected.")
                    return

                # 2. Skill Extraction
                resume_skills = skill_extractor.extract_skills(resume_text)
                job_skills = skill_extractor.extract_skills(job_description)

                # 3. Skill Gap Analysis
                gap_analysis = analyze_skill_gap(resume_skills, job_skills)
                skill_match_score = gap_analysis["skill_match_percentage"]

                # 4. Semantic Embeddings & Similarity
                semantic_similarity_score = matcher.calculate_semantic_similarity(resume_text, job_description)

                # 5. Overall Weighted Match Score
                overall_score = matcher.compute_overall_score(
                    semantic_similarity_pct=semantic_similarity_score,
                    skill_match_pct=skill_match_score
                )

                # 6. Recommendations
                missing_skills = gap_analysis["missing_skills"]
                recommendations = recommender.get_recommendations(missing_skills)

                # Render Results Dashboard
                st.markdown("---")
                st.markdown("## 📊 Compatibility Analysis Dashboard")

                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-val">{overall_score}%</div>
                        <div class="metric-lbl">Overall Compatibility</div>
                    </div>
                    """, unsafe_allow_html=True)

                with m2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-val" style="color:#A78BFA">{semantic_similarity_score}%</div>
                        <div class="metric-lbl">Semantic Match (60%)</div>
                    </div>
                    """, unsafe_allow_html=True)

                with m3:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-val" style="color:#34D399">{skill_match_score}%</div>
                        <div class="metric-lbl">Skill Match (40%)</div>
                    </div>
                    """, unsafe_allow_html=True)

                with m4:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-val" style="color:#F472B6">{len(gap_analysis['matching_skills'])} / {len(job_skills)}</div>
                        <div class="metric-lbl">Matched Skills</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Score Breakdown Chart & Skill Distribution
                c_chart, c_skills = st.columns([1, 1], gap="large")

                with c_chart:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown("### 📈 Score Gauge")
                    gauge_fig = build_gauge_chart(overall_score, semantic_similarity_score, skill_match_score)
                    st.plotly_chart(gauge_fig, use_container_width=True)
                    
                    st.markdown(f"""
                    **Compatibility Breakdown:**
                    - **Semantic Alignment:** {semantic_similarity_score}% similarity in domain concepts, experience descriptions, and context.
                    - **Skill Coverage:** {skill_match_score}% of key required skills were explicitly found on your resume.
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_skills:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown("### 🧩 Skill Alignment Matrix")

                    # Matching Skills
                    st.markdown("#### ✅ Matched Skills")
                    if gap_analysis["matching_skills"]:
                        chips_html = "".join([f'<span class="chip chip-match">✓ {s}</span>' for s in gap_analysis["matching_skills"]])
                        st.markdown(chips_html, unsafe_allow_html=True)
                    else:
                        st.info("No direct skill matches detected.")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Missing Skills
                    st.markdown("#### ⚠️ Missing Skills (Required by Job)")
                    if gap_analysis["missing_skills"]:
                        chips_html = "".join([f'<span class="chip chip-missing">✕ {s}</span>' for s in gap_analysis["missing_skills"]])
                        st.markdown(chips_html, unsafe_allow_html=True)
                    else:
                        st.success("🎉 Perfect match! No key skills missing.")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Extra Resume Skills
                    if gap_analysis["extra_skills"]:
                        with st.expander(f"💡 Additional Resume Skills Detected ({len(gap_analysis['extra_skills'])})"):
                            chips_html = "".join([f'<span class="chip chip-extra">• {s}</span>' for s in gap_analysis["extra_skills"]])
                            st.markdown(chips_html, unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                # Learning Recommendations Section
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("## 🚀 Recommended Upskilling Plan")

                if recommendations:
                    st.caption("Targeted courses and tutorials to bridge your identified skill gaps:")
                    rec_cols = st.columns(2)
                    for idx, rec in enumerate(recommendations):
                        col_target = rec_cols[idx % 2]
                        with col_target:
                            st.markdown(f"""
                            <div class="rec-card">
                                <div>
                                    <span class="rec-title">Learn {rec['skill']}</span>
                                    <span class="rec-platform">{rec['platform']}</span>
                                </div>
                                <div style="color:#A78BFA; font-weight:600; font-size:0.85rem; margin-top:4px;">
                                    📘 {rec['title']} ({rec['level']})
                                </div>
                                <div class="rec-desc">{rec['description']}</div>
                                <a class="rec-link" href="{rec['url']}" target="_blank">🔗 Start Learning &rarr;</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.success("Great job! Your resume covers all required skills detected in the job description.")

                # Raw Text Inspection Accordion
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🔍 Inspect Extracted Resume Text"):
                    st.text_area("Extracted Resume Text", value=resume_text, height=250, disabled=True)

            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")

if __name__ == "__main__":
    main()
