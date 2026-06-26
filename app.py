import streamlit as st
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Finance Document AI Review",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: #e5e7eb;
}
.block-container {
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(135deg, #0f172a, #1e3a8a);
    padding: 35px;
    border-radius: 22px;
    text-align: center;
    border: 1px solid #334155;
    box-shadow: 0px 8px 25px rgba(0,0,0,0.35);
}
.hero h1 {
    color: white;
    font-size: 42px;
}
.hero p {
    color: #cbd5e1;
    font-size: 18px;
}
.card {
    background: #0f172a;
    border: 1px solid #334155;
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 18px;
}
.metric-card {
    background: #111827;
    border: 1px solid #2563eb;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
}
.safe {
    color: #22c55e;
    font-weight: bold;
}
.medium {
    color: #facc15;
    font-weight: bold;
}
.high {
    color: #ef4444;
    font-weight: bold;
}
.stButton button {
    background: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 24px;
}
.stButton button:hover {
    background: #1d4ed8;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📄 Finance Document Extraction & AI Review System</h1>
    <p>Extract financial information, generate AI summaries, detect risks, and approve with human review.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    if file_name.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception:
            return "PDF text extraction failed. Please paste document text manually."

    if file_name.endswith((".png", ".jpg", ".jpeg")):
        return "Image uploaded. OCR is not enabled in this simple version. Please paste text manually."

    return ""

def find_value(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "Not Found"

def mask_sensitive(text):
    text = re.sub(r'\b\d{9,18}\b', lambda x: "XXXXXX" + x.group(0)[-4:], text)
    text = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', "XXXXX0000X", text)
    return text

def detect_prompt_injection(text):
    danger_words = [
        "ignore previous instructions",
        "reveal password",
        "system prompt",
        "bypass",
        "delete data",
        "act as admin",
        "jailbreak"
    ]
    found = [word for word in danger_words if word in text.lower()]
    return found

def calculate_risk(text, fields, injection):
    score = 0

    missing = list(fields.values()).count("Not Found")
    score += missing * 10

    if injection:
        score += 35

    if re.search(r'\b\d{9,18}\b', text):
        score += 15

    if "overdue" in text.lower() or "penalty" in text.lower():
        score += 20

    if score < 30:
        level = "Low"
    elif score < 60:
        level = "Medium"
    else:
        level = "High"

    return score, level

left, right = st.columns([1.2, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📤 Upload Finance Document")
    uploaded_file = st.file_uploader(
        "Upload PDF, TXT, PNG, JPG",
        type=["pdf", "txt", "png", "jpg", "jpeg"]
    )

    manual_text = st.text_area(
        "Or paste finance document text here",
        height=260,
        placeholder="""Example:
Customer Name: Ravi Kumar
Account Number: 123456789012
Loan Amount: 850000
Interest Rate: 8.5%
EMI: 12500
Due Date: 20-07-2026
PAN: ABCDE1234F"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🛡️ System Guardrails")
    st.write("✅ Sensitive data masking")
    st.write("✅ Prompt injection detection")
    st.write("✅ Human approval workflow")
    st.write("✅ Risk score dashboard")
    st.write("✅ No API key required")
    st.markdown("</div>", unsafe_allow_html=True)

if st.button("🚀 Analyze Document"):
    file_text = extract_text_from_file(uploaded_file)
    text = manual_text.strip() if manual_text.strip() else file_text.strip()

    if not text:
        st.warning("Please upload a document or paste text.")
        st.stop()

    fields = {
        "Customer Name": find_value(r"Customer Name\s*[:\-]\s*(.+)", text),
        "Account Number": find_value(r"Account Number\s*[:\-]\s*([A-Za-z0-9]+)", text),
        "Loan Amount": find_value(r"Loan Amount\s*[:\-]\s*₹?\s*([0-9,]+)", text),
        "Interest Rate": find_value(r"Interest Rate\s*[:\-]\s*([0-9.]+%?)", text),
        "EMI": find_value(r"EMI\s*[:\-]\s*₹?\s*([0-9,]+)", text),
        "Due Date": find_value(r"Due Date\s*[:\-]\s*(.+)", text),
        "PAN": find_value(r"PAN\s*[:\-]\s*([A-Z]{5}[0-9]{4}[A-Z])", text),
        "Invoice Number": find_value(r"Invoice Number\s*[:\-]\s*(.+)", text),
        "GST": find_value(r"GST\s*[:\-]\s*([A-Za-z0-9]+)", text),
        "Total Amount": find_value(r"Total Amount\s*[:\-]\s*₹?\s*([0-9,]+)", text),
    }

    injection = detect_prompt_injection(text)
    risk_score, risk_level = calculate_risk(text, fields, injection)

    masked_text = mask_sensitive(text)

    st.write("")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Documents Processed", "1")
    c2.metric("Fields Extracted", len([v for v in fields.values() if v != "Not Found"]))
    c3.metric("Risk Score", f"{risk_score}/100")
    c4.metric("Review Status", "Pending")

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📌 Extracted Data",
        "🧠 AI Summary",
        "📊 Risk Dashboard",
        "👨‍💼 Human Review"
    ])

    with tab1:
        st.subheader("Extracted Financial Fields")

        df = pd.DataFrame({
            "Field": list(fields.keys()),
            "Value": list(fields.values())
        })

        st.dataframe(df, use_container_width=True)

        st.subheader("Masked Document Text")
        st.text_area("Safe text view", masked_text, height=220)

    with tab2:
        st.subheader("Generated AI Narrative")

        customer = fields["Customer Name"]
        loan = fields["Loan Amount"]
        rate = fields["Interest Rate"]
        emi = fields["EMI"]
        due = fields["Due Date"]
        total = fields["Total Amount"]

        summary = f"""
This finance document appears to belong to **{customer}**.

The extracted loan amount is **₹{loan}**, with an interest rate of **{rate}**.
The monthly EMI is **₹{emi}**, and the due date mentioned is **{due}**.

The total amount found in the document is **₹{total}**.

Risk level is classified as **{risk_level}** based on missing fields, sensitive data, overdue terms, and prompt-injection checks.
"""

        st.info(summary)

        if injection:
            st.error("⚠️ Prompt injection detected: " + ", ".join(injection))
        else:
            st.success("No prompt injection detected.")

    with tab3:
        st.subheader("Risk Level Graph")

        risk_df = pd.DataFrame({
            "Category": ["Missing Fields", "Sensitive Data", "Prompt Injection", "Penalty/Overdue"],
            "Score": [
                list(fields.values()).count("Not Found") * 10,
                15 if re.search(r'\b\d{9,18}\b', text) else 0,
                35 if injection else 0,
                20 if "overdue" in text.lower() or "penalty" in text.lower() else 0
            ]
        })

        fig = px.bar(
            risk_df,
            x="Category",
            y="Score",
            title="Risk Contribution Analysis",
            text="Score"
        )
        fig.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

        pie_df = pd.DataFrame({
            "Status": ["Extracted", "Missing"],
            "Count": [
                len([v for v in fields.values() if v != "Not Found"]),
                list(fields.values()).count("Not Found")
            ]
        })

        fig2 = px.pie(
            pie_df,
            names="Status",
            values="Count",
            title="Field Extraction Completeness"
        )
        fig2.update_layout(
            paper_bgcolor="#0f172a",
            font_color="white"
        )
        st.plotly_chart(fig2, use_container_width=True)

        if risk_level == "Low":
            st.markdown('<p class="safe">Risk Level: LOW ✅</p>', unsafe_allow_html=True)
        elif risk_level == "Medium":
            st.markdown('<p class="medium">Risk Level: MEDIUM ⚠️</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="high">Risk Level: HIGH 🚨</p>', unsafe_allow_html=True)

    with tab4:
        st.subheader("Human Review Panel")

        edited_summary = st.text_area(
            "Edit AI Summary Before Approval",
            summary,
            height=250
        )

        r1, r2, r3 = st.columns(3)

        with r1:
            if st.button("✅ Approve"):
                st.success("Document approved successfully.")

        with r2:
            if st.button("✏️ Save Edited Summary"):
                st.info("Edited summary saved.")

        with r3:
            if st.button("❌ Reject"):
                st.error("Document rejected for manual verification.")

        st.download_button(
            "⬇️ Download Final Report",
            data=edited_summary,
            file_name=f"finance_ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

else:
    st.info("Upload or paste a finance document, then click **Analyze Document**.")
