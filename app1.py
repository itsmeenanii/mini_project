import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from database import get_connection, create_tables

# ---------------- SETUP ----------------
create_tables()
conn = get_connection()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(
    page_title="School Project Management System",
    layout="wide"
)

st.title("🏫 School Project Management System")

# ---------------- SESSION ----------------
if "logged" not in st.session_state:
    st.session_state.logged = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN FUNCTION ----------------
def login(role):
    st.subheader(f"🔐 {role} Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, password, role)
        ).fetchone()

        if user:
            st.session_state.logged = True
            st.session_state.role = role
            st.session_state.user = username
            st.success("Login successful")
            st.experimenal_rerun()
        else:
            st.error("Invalid credentials")

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged:
    login_type = st.sidebar.selectbox(
        "Login As",
        ["Student Login", "Teacher Login", "Admin Login"]
    )

    if login_type == "Student Login":
        login("Student")
    elif login_type == "Teacher Login":
        login("Teacher")
    else:
        login("Admin")

# ================= DASHBOARDS =================
else:
    role = st.session_state.role
    user = st.session_state.user

    if st.sidebar.button("Logout"):
        st.session_state.logged = False
        st.session_state.role = None
        st.session_state.user = None
        st.experimenal_rerun()

    # ================= STUDENT =================
    if role == "Student":
        st.header("🎓 Student Dashboard")

        with st.expander("➕ Submit New Project"):
            title = st.text_input("Project Title")
            desc = st.text_area("Project Description")
            deadline = st.date_input("Project Deadline")
            pdf = st.file_uploader("Upload Project Report (PDF)", type=["pdf"])

            if st.button("Submit Project"):
                if not pdf:
                    st.warning("Please upload a PDF file")
                else:
                    path = os.path.join(UPLOAD_DIR, pdf.name)
                    with open(path, "wb") as f:
                        f.write(pdf.read())

                    conn.execute("""
                        INSERT INTO projects
                        (student,title,description,pdf_path,deadline,status,marks,feedback)
                        VALUES (?,?,?,?,?,'Submitted',NULL,'')
                    """, (user, title, desc, path, str(deadline)))
                    conn.commit()
                    st.success("Project submitted successfully")

        st.subheader("📌 My Projects")
        df = pd.read_sql(
            "SELECT title, deadline, status, marks, feedback FROM projects WHERE student=?",
            conn, params=(user,)
        )
        st.dataframe(df, use_container_width=True)

    # ================= TEACHER =================
    elif role == "Teacher":
        st.header("👩‍🏫 Teacher Dashboard")

        # View all projects
        st.subheader("📋 Submitted Projects")
        df = pd.read_sql("SELECT * FROM projects", conn)
        st.dataframe(df, use_container_width=True)

        # View / Download PDF
        st.subheader("📂 View Project Report")
        view_id = st.number_input("Enter Project ID to View", min_value=1)

        row = conn.execute(
            "SELECT pdf_path FROM projects WHERE id=?",
            (view_id,)
        ).fetchone()

        if row and row[0] and os.path.exists(row[0]):
            with open(row[0], "rb") as f:
                st.download_button(
                    "📄 Download / View PDF",
                    f,
                    file_name=os.path.basename(row[0])
                )
        elif view_id:
            st.info("No PDF available for this project")

        st.divider()

        # Evaluation section
        st.subheader("✏️ Evaluate Project")
        eval_id = st.number_input("Project ID to Evaluate", min_value=1, key="eval")
        status = st.selectbox("Project Status", ["Approved", "In Progress", "Completed"])
        marks = st.slider("Marks", 0, 100)
        feedback = st.text_area("Feedback")

        if st.button("Submit Evaluation"):
            conn.execute("""
                UPDATE projects
                SET status=?, marks=?, feedback=?
                WHERE id=?
            """, (status, marks, feedback, eval_id))
            conn.commit()
            st.success("Evaluation submitted successfully")

    # ================= ADMIN =================
    elif role == "Admin":
        st.header("🛠️ Admin Dashboard")

        # Create users
        st.subheader("➕ Create New User")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_user = st.text_input("Username")
        with col2:
            new_pass = st.text_input("Password")
        with col3:
            new_role = st.selectbox("Role", ["Student", "Teacher"])

        if st.button("Create User"):
            try:
                conn.execute(
                    "INSERT INTO users(username,password,role) VALUES(?,?,?)",
                    (new_user, new_pass, new_role)
                )
                conn.commit()
                st.success("User created successfully")
            except:
                st.error("Username already exists")

        # Analytics
        df = pd.read_sql("SELECT * FROM projects", conn)
        st.subheader("📊 Project Analytics")

        df["marks"] = pd.to_numeric(df["marks"], errors="coerce")

        col1, col2 = st.columns(2)

        with col1:
            if df["status"].notna().any():
                fig1, ax1 = plt.subplots()
                df["status"].value_counts().plot(
                    kind="pie",
                    autopct="%1.1f%%",
                    ax=ax1
                )
                ax1.set_ylabel("")
                ax1.set_title("Project Status Distribution")
                st.pyplot(fig1)
            else:
                st.info("No project status data available")

        with col2:
            marks_data = df["marks"].dropna()
            if not marks_data.empty:
                fig2, ax2 = plt.subplots()
                ax2.hist(marks_data)
                ax2.set_xlabel("Marks")
                ax2.set_ylabel("Number of Projects")
                ax2.set_title("Marks Distribution")
                st.pyplot(fig2)
            else:
                st.info("No marks assigned yet")

        st.subheader("📋 All Projects")
        st.dataframe(df, use_container_width=True)
