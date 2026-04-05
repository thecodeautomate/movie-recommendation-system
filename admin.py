import streamlit as st
import pandas as pd
import pickle
import os
from datetime import datetime
import json
import sqlite3

st.set_page_config(page_title="SmartFlix Admin", layout="wide")


# ---------------- ADMIN LOGIN ---------------- #

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------- DATABASE CONNECTION ---------------- #

def get_connection():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    return conn


# ---------------- MOVIE DATA ---------------- #

def load_data():
    try:
        movies_dict = pickle.load(open('artificats/movies_list.pkl','rb'))
        movies = pd.DataFrame(movies_dict)
        return movies
    except:
        return pd.DataFrame()

def save_data(movies_df):
    movies_dict = movies_df.to_dict()
    with open('artificats/movies_list.pkl', 'wb') as f:
        pickle.dump(movies_dict, f)


# ---------------- LOAD USERS FROM SQLITE ---------------- #

def load_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username,email,contact,age FROM users")

    data = cursor.fetchall()

    df = pd.DataFrame(data,columns=["Username","Email","Contact","Age"])

    conn.close()

    return df


def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    add_log("User Deleted", f"Deleted user: {username}")


def update_user(username, email, contact, age):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET email = ?, contact = ?, age = ? WHERE username = ?",
        (email, contact, age, username),
    )
    conn.commit()
    conn.close()
    add_log("User Updated", f"Updated user: {username}")


# ---------------- SYSTEM LOGS ---------------- #

def load_system_logs():
    try:
        with open('system_logs.json', 'r') as f:
            return json.load(f)
    except Exception:
        return []

def add_log(action, details):

    logs = load_system_logs()

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    }

    logs.append(log_entry)

    with open('system_logs.json', 'w') as f:
        json.dump(logs[-100:], f)


# ---------------- LOGIN PAGE ---------------- #

def login():

    st.title("Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            st.session_state.logged_in = True
            st.rerun()

        else:
            st.error("Invalid credentials")


# ---------------- ADMIN DASHBOARD ---------------- #

def admin_dashboard():

    st.title("SmartFlixs - Admin Panel")

    st.write(f"**Current Date & Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard","Movie Dataset","User Management","System Reports"]
    )

    if menu == "Dashboard":
        dashboard_page()

    elif menu == "Movie Dataset":
        dataset_page()

    elif menu == "User Management":
        user_management_page()

    elif menu == "System Reports":
        reports_page()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


# ---------------- DASHBOARD ---------------- #

def dashboard_page():

    st.header("Dashboard")

    movies = load_data()
    users = load_users()
    logs = load_system_logs()

    col1,col2,col3 = st.columns(3)

    with col1:
        st.metric("Total Movies", len(movies))

    with col2:
        st.metric("Total Users", len(users))

    with col3:
        st.metric("System Logs", len(logs))


    st.subheader("Recent Activity")

    if logs:

        for log in logs[-5:]:

            st.write(
                f"**{log['timestamp']}** - {log['action']}: {log['details']}"
            )


# ---------------- DATASET PAGE ---------------- #

def dataset_page():

    st.header("Movie Dataset Management")

    movies = load_data()

    tab1,tab2,tab3 = st.tabs(["View Dataset","Add Movie","Update Dataset"])


    # VIEW DATASET

    with tab1:

        st.subheader("Current Dataset")

        if not movies.empty:

            st.write(f"Total movies: {len(movies)}")

            for i,row in movies.head(10).iterrows():

                st.write(
                    f"• {row.get('title','N/A')} (ID: {row.get('movie_id','N/A')})"
                )

        else:
            st.warning("No dataset loaded")


    # ADD MOVIE

    with tab2:

        st.subheader("Add New Movie")

        with st.form("add_movie"):

            title = st.text_input("Movie Title")
            movie_id = st.number_input("Movie ID",min_value=1)
            genres = st.text_input("Genres")

            if st.form_submit_button("Add Movie"):

                if title and movie_id:

                    new_movie = pd.DataFrame({

                        'title':[title],
                        'movie_id':[movie_id],
                        'genres':[genres]

                    })

                    movies = pd.concat([movies,new_movie],ignore_index=True)

                    save_data(movies)

                    add_log("Movie Added",f"Added movie: {title}")

                    st.success("Movie added successfully!")

                    st.rerun()


    # UPDATE DATASET

    with tab3:

        st.subheader("Upload New Dataset")

        uploaded_file = st.file_uploader("Upload CSV",type="csv")

        if uploaded_file:

            new_data = pd.read_csv(uploaded_file)

            st.write(f"Preview: {len(new_data)} rows loaded")

            if st.button("Update Dataset"):

                save_data(new_data)

                add_log(
                    "Dataset Updated",
                    f"Updated with {len(new_data)} movies"
                )

                st.success("Dataset updated successfully!")


# ---------------- USER MANAGEMENT ---------------- #

def user_management_page():

    st.header("User Management")

    users = load_users()

    st.subheader("Registered Users")

    if users.empty:
        st.info("No users registered")
        return

    header_cols = st.columns([2, 3, 2, 1, 1, 1])
    header_cols[0].markdown("**Username**")
    header_cols[1].markdown("**Email**")
    header_cols[2].markdown("**Contact**")
    header_cols[3].markdown("**Age**")
    header_cols[4].markdown("**Edit**")
    header_cols[5].markdown("**Delete**")

    for idx, row in users.reset_index(drop=True).iterrows():
        cols = st.columns([2, 3, 2, 1, 1, 1])
        cols[0].write(row.Username)
        cols[1].write(row.Email)
        cols[2].write(row.Contact)
        cols[3].write(row.Age)

        if cols[4].button("Edit", key=f"edit_{idx}_{row.Username}"):
            st.session_state.edit_user = row.Username
            st.session_state.edit_email = row.Email
            st.session_state.edit_contact = row.Contact
            st.session_state.edit_age = int(row.Age)
            st.experimental_rerun()

        if cols[5].button("Delete", key=f"delete_{idx}_{row.Username}"):
            delete_user(row.Username)
            st.success(f"Deleted user: {row.Username}")
            st.experimental_rerun()

    st.write(f"Total Users: **{len(users)}**")

    if "edit_user" in st.session_state and st.session_state.edit_user:
        st.markdown("---")
        st.subheader(f"Edit User: {st.session_state.edit_user}")

        edit_email = st.text_input(
            "Email",
            value=st.session_state.get("edit_email", ""),
            key="manage_edit_email",
        )
        edit_contact = st.text_input(
            "Contact Number (+91)",
            value=st.session_state.get("edit_contact", ""),
            placeholder="+911234567890",
            max_chars=13,
            key="manage_edit_contact",
        )
        edit_age = st.number_input(
            "Age",
            min_value=10,
            max_value=100,
            value=st.session_state.get("edit_age", 18),
            key="manage_edit_age",
        )

        if st.button("Save Changes", key="save_user_changes"):
            update_user(
                st.session_state.edit_user,
                edit_email,
                edit_contact,
                edit_age,
            )
            st.success(f"User {st.session_state.edit_user} updated successfully.")
            st.session_state.edit_user = ""
            st.session_state.edit_email = ""
            st.session_state.edit_contact = ""
            st.session_state.edit_age = 18
            st.experimental_rerun()

        if st.button("Cancel", key="cancel_edit"):
            st.session_state.edit_user = ""
            st.session_state.edit_email = ""
            st.session_state.edit_contact = ""
            st.session_state.edit_age = 18
            st.experimental_rerun()


# ---------------- REPORTS ---------------- #

def reports_page():

    st.header("System Reports")

    logs = load_system_logs()

    if logs:

        st.subheader("System Activity Logs")

        for log in logs[-10:]:

            st.write(
                f"**{log['timestamp']}** - {log['action']}: {log['details']}"
            )


        st.subheader("Activity Summary")

        actions = [log['action'] for log in logs]

        action_counts = {}

        for action in actions:

            action_counts[action] = action_counts.get(action,0)+1

        for action,count in action_counts.items():

            st.write(f"• {action}: {count}")

    else:
        st.info("No logs available")


# ---------------- MAIN ---------------- #

def main():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
    else:
        admin_dashboard()


if __name__ == "__main__":
    main()