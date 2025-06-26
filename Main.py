import os
import fitz  # PyMuPDF
import streamlit as st
from datetime import datetime
from io import BytesIO
from PIL import Image
from docx import Document

# -------------------- Setup --------------------
if "case_database" not in st.session_state:
    st.session_state.case_database = {}

if "case_name" not in st.session_state:
    st.session_state.case_name = None

# -------------------- Sidebar --------------------
st.sidebar.title("📁 Case Manager")
case_names = list(st.session_state.case_database.keys())
selected = st.sidebar.selectbox("Open existing case", [""] + case_names)

if selected:
    st.session_state.case_name = selected

new_case = st.sidebar.text_input("Start new case", placeholder="Donald v County")
if st.sidebar.button("➕ Create") and new_case:
    if new_case not in st.session_state.case_database:
        st.session_state.case_database[new_case] = {
            "files": [],
            "violations": [],
            "people": [],
            "timeline": [],
            "checklist": [],
            "evidence": []
        }
        st.session_state.case_name = new_case
        st.success(f"✅ Created case: {new_case}")
    else:
        st.warning("Case already exists.")

if not st.session_state.case_name:
    st.stop()

case = st.session_state.case_database[st.session_state.case_name]
st.title(f"⚖️ Case: {st.session_state.case_name}")

# -------------------- File Upload --------------------
st.markdown("## 📄 Upload Files")
uploaded_files = st.file_uploader("Upload PDFs, DOCX, or Images", type=["pdf", "docx", "png", "jpg", "jpeg"], accept_multiple_files=True)

for file in uploaded_files:
    content = ""
    name = file.name

    if name.endswith(".pdf"):
        pdf_bytes = file.read()
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            content = "\n".join([page.get_text() for page in doc])
    elif name.endswith(".docx"):
        docx = Document(file)
        content = "\n".join([p.text for p in docx.paragraphs])
    elif name.endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(file)
        content = "[Image uploaded — analysis not yet supported.]"

    if content:
        case["files"].append({"name": name, "content": content})
        st.success(f"✅ {name} uploaded.")

# -------------------- Expanders --------------------
with st.expander("🧠 Case Summary"):
    for f in case["files"]:
        st.markdown(f"### {f['name']}")
        st.code(f["content"][:1200] + ("..." if len(f["content"]) > 1200 else ""))

with st.expander("🚨 Violations"):
    v_code = st.text_input("Violation Code", key="vcode")
    v_title = st.text_input("Title", key="vtitle")
    v_desc = st.text_area("Description", key="vdesc")
    if st.button("➕ Add Violation"):
        case["violations"].append({
            "code": v_code,
            "title": v_title,
            "description": v_desc
        })
        st.success("Violation added.")
    for v in case["violations"]:
        st.markdown(f"- **{v['code']}** — {v['title']}")

with st.expander("👤 People"):
    p_name = st.text_input("Name", key="pname")
    p_role = st.selectbox("Role", ["Plaintiff", "Defendant", "Witness", "Other"], key="prole")
    p_notes = st.text_area("Notes", key="pnotes")
    v_link = st.selectbox("Link to Violation", ["None"] + [v["code"] for v in case["violations"]], key="plink")
    if st.button("➕ Add Person"):
        case["people"].append({
            "name": p_name,
            "role": p_role,
            "notes": p_notes,
            "violation": v_link if v_link != "None" else None
        })
        st.success("Person added.")
    for p in case["people"]:
        st.markdown(f"- **{p['role']}**: {p['name']} (Linked: {p['violation']})")

with st.expander("🕓 Timeline"):
    t_date = st.date_input("Event Date")
    t_title = st.text_input("Event Title", key="t_title")
    t_desc = st.text_area("Event Description", key="t_desc")
    if st.button("➕ Add Event"):
        case["timeline"].append({
            "date": str(t_date),
            "title": t_title,
            "description": t_desc
        })
        st.success("Timeline entry added.")
    for t in sorted(case["timeline"], key=lambda x: x["date"]):
        st.markdown(f"- **{t['date']}**: {t['title']} — {t['description']}")

with st.expander("📋 Legal Checklist"):
    c_item = st.text_input("Add checklist item", key="check_add")
    if st.button("➕ Add Item"):
        case["checklist"].append({"text": c_item, "done": False})
    for i, item in enumerate(case["checklist"]):
        item["done"] = st.checkbox(item["text"], value=item["done"], key=f"chk_{i}")

with st.expander("🐇 Rabbit Hole"):
    theory = st.text_area("Pose your theory or legal question:")
    if st.button("🧠 Analyze Theory"):
        if "immunity" in theory.lower():
            st.markdown("Sovereign immunity only applies unless you can show statutory violations.")
        elif "conspiracy" in theory.lower():
            st.markdown("Prove shared intent, agreement, and overt act. Don't guess — prove.")
        else:
            st.markdown("No hallucinations. Stick to the statutes. Play devil’s advocate, but anchor it in law.")

with st.expander("📄 Document Generator"):
    if st.button("📃 Generate"):
        out = f"Case: {st.session_state.case_name}\n"
        out += "\nPeople:\n"
        for p in case["people"]:
            out += f"- {p['role']}: {p['name']} — {p['violation']}\n"
        out += "\nViolations:\n"
        for v in case["violations"]:
            out += f"- {v['code']}: {v['title']}\n"
        out += "\nTimeline:\n"
        for t in case["timeline"]:
            out += f"- {t['date']}: {t['title']}\n"
        st.text_area("📝 Editable Document", value=out, height=400)

with st.expander("📎 Evidence Upload"):
    ev_file = st.file_uploader("Upload file", type=["pdf", "jpg", "jpeg", "png"], key="ev_file")
    ev_desc = st.text_area("Describe evidence", key="ev_desc")
    if st.button("➕ Add Evidence"):
        if ev_file:
            case["evidence"].append({"name": ev_file.name, "description": ev_desc})
            st.success(f"Uploaded: {ev_file.name}")
    for e in case["evidence"]:
        st.markdown(f"- **{e['name']}**: {e['description']}")
