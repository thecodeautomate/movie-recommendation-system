import pickle
import streamlit as st
import requests
import sqlite3
import re
import random
import os

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(page_title="SmartFlix", layout="wide")

# ---------------- SESSION PERSISTENCE ---------------- #

SESSION_FILE = 'session.pkl'

if os.path.exists(SESSION_FILE):
    try:
        with open(SESSION_FILE, 'rb') as f:
            saved_username = pickle.load(f)
            st.session_state.logged_in = True
            st.session_state.username = saved_username
    except Exception:
        pass  # If file corrupted, ignore

# ---------------- UI STYLE ---------------- #

st.markdown("""
<style>
* {
    box-sizing: border-box;
}

.main-title{
    text-align:center;
    font-size: clamp(32px, 8vw, 55px);
    font-weight:bold;
    color:#E50914;
    margin: 20px 0;
}

.stButton>button{
    background-color:#E50914;
    color:white;
    border-radius:8px;
    height:clamp(40px, 5vh, 50px);
    min-width:80px;
    font-size:clamp(12px, 2vw, 16px);
    font-weight:700;
}

.stButton>button:hover {
    opacity: 0.85;
}

/* Detail Panel */
.detail-panel {
    background: linear-gradient(135deg, rgba(20,20,20,0.97) 0%, rgba(40,10,10,0.97) 100%);
    border: 1px solid #E50914;
    border-radius: 16px;
    padding: clamp(16px, 3vw, 36px);
    margin: 16px 0;
    color: white;
    box-shadow: 0 8px 40px rgba(229,9,20,0.25);
}

.detail-title {
    font-size: clamp(24px, 6vw, 36px);
    font-weight: 800;
    color: #E50914;
    margin-bottom: 6px;
}

.detail-meta {
    font-size: clamp(11px, 2vw, 14px);
    color: #aaa;
    margin-bottom: 16px;
    letter-spacing: 1px;
}

.detail-overview {
    font-size: clamp(13px, 2vw, 16px);
    line-height: 1.7;
    color: #ddd;
    margin-bottom: 20px;
}

.detail-badge {
    display: inline-block;
    background: #E50914;
    color: white;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: clamp(10px, 1.5vw, 12px);
    font-weight: 700;
    margin: 3px 4px 3px 0;
}

.section-header {
    font-size: clamp(16px, 4vw, 22px);
    font-weight: 700;
    color: white;
    margin: 20px 0 12px 0;
    border-left: 4px solid #E50914;
    padding-left: 12px;
}

.close-btn>button {
    background-color: #333 !important;
    color: white !important;
    border-radius: 8px !important;
    font-size: clamp(11px, 2vw, 13px) !important;
    height: clamp(34px, 4vh, 42px) !important;
}

.profile-card{
    width:90%;
    max-width:420px;
    margin:auto;
    padding: clamp(20px, 4vw, 40px);
    border-radius:20px;
    background: rgba(0,0,0,0.65);
    text-align:center;
    color:white;
}

.profile-title{
    font-size: clamp(28px, 6vw, 50px);
    font-weight:bold;
    margin-bottom:20px;
}

.profile-text{
    font-size: clamp(14px, 3vw, 20px);
    margin:12px 0;
}

.close-btn>button {
    background-color: #333 !important;
    color: white !important;
    border-radius: 8px !important;
    width: 100px !important;
    font-size: 13px !important;
}

@media (max-width: 640px) {
    .stTabs [data-baseweb="tabs"] {
        flex-direction: column;
    }
    .stTabs [data-baseweb="tab"] {
        width: 100%;
    }
}

</style>
""", unsafe_allow_html=True)


# ---------------- DATABASE ---------------- #

conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
email TEXT,
contact TEXT,
age INTEGER,
password TEXT
)
""")

conn.commit()

# ---------------- DATABASE FUNCTIONS ---------------- #

def add_user(username, email, contact, age, password):
    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (username, email, contact, age, password))
        conn.commit()
        return True
    except Exception:
        return False


def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()


def get_user(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()


def get_user_by_email(email):
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    return c.fetchone()


def update_password(username, new_password):
    c.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
    conn.commit()


# ---------------- VALIDATION HELPERS ---------------- #

def is_valid_email(email):
    pattern = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_mobile(contact):
    return re.fullmatch(r'^\d{10}$', contact) is not None


def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one special character (e.g. @, #, $, !)."
    return True, ""


# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

if "selected_movie_title" not in st.session_state:
    st.session_state.selected_movie_title = None

if "action_movies" not in st.session_state:
    st.session_state.action_movies = None

if "horror_movies" not in st.session_state:
    st.session_state.horror_movies = None

if "thriller_movies" not in st.session_state:
    st.session_state.thriller_movies = None


# ---------------- LOGIN / SIGNUP ---------------- #

if st.session_state.logged_in == False:

    st.markdown("<h1 class='main-title'>SmartFlix</h1>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([3, 1, 0.2, 1, 3])

    with col2:
        if st.button("Login"):
            st.session_state.page = "login"

    with col4:
        if st.button("Signup"):
            st.session_state.page = "signup"

    st.write("")

    # ---------------- LOGIN FORM ---------------- #

    if st.session_state.page == "login":

        col1, col2, col3 = st.columns([2, 2, 2])

        with col2:
            # Sub-tabs: Login | Forgot Password | Forgot Username
            login_tab, forgot_pwd_tab, forgot_user_tab = st.tabs(
                ["🔑 Login", "🔒 Forgot Password", "👤 Forgot Username"]
            )

            # ---- LOGIN TAB ----
            with login_tab:
                st.subheader("Login")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")

                if st.button("Submit Login"):
                    result = login_user(username, password)
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        with open(SESSION_FILE, 'wb') as f:
                            pickle.dump(username, f)
                        st.success("Login Successful")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")

            # ---- FORGOT PASSWORD TAB ----
            with forgot_pwd_tab:
                st.subheader("Reset Password")
                st.caption("Enter your registered email and username to reset your password.")
                fp_username = st.text_input("Username", key="fp_username")
                fp_email    = st.text_input("Registered Email", key="fp_email")
                fp_new_pwd  = st.text_input("New Password", type="password", key="fp_new_pwd")
                st.caption("🔒 Min 8 characters with letters, numbers & a special character")
                fp_confirm  = st.text_input("Confirm New Password", type="password", key="fp_confirm")

                if st.button("Reset Password"):
                    if not fp_username.strip() or not fp_email.strip():
                        st.error("Please fill in all fields.")
                    else:
                        user_row = get_user(fp_username.strip())
                        if user_row and user_row[1] == fp_email.strip():
                            pwd_ok, pwd_msg = is_strong_password(fp_new_pwd)
                            if not pwd_ok:
                                st.error(pwd_msg)
                            elif fp_new_pwd != fp_confirm:
                                st.error("Passwords do not match.")
                            else:
                                update_password(fp_username.strip(), fp_new_pwd)
                                st.success("✅ Password updated successfully! You can now log in.")
                        else:
                            st.error("No account found with that username and email combination.")

            # ---- FORGOT USERNAME TAB ----
            with forgot_user_tab:
                st.subheader("Find Your Username")
                st.caption("Enter your registered email address to retrieve your username.")
                fu_email = st.text_input("Registered Email", key="fu_email")

                if st.button("Find Username"):
                    if not fu_email.strip():
                        st.error("Please enter your email address.")
                    elif not is_valid_email(fu_email.strip()):
                        st.error("Please enter a valid email address.")
                    else:
                        user_row = get_user_by_email(fu_email.strip())
                        if user_row:
                            st.success(f"✅ Your username is: **{user_row[0]}**")
                        else:
                            st.error("No account found with that email address.")

    # ---------------- SIGNUP FORM ---------------- #

    if st.session_state.page == "signup":

        col1, col2, col3 = st.columns([2, 2, 2])

        with col2:
            st.subheader("Create Account")
            new_user = st.text_input("Username",placeholder="username")
            email = st.text_input("Email ID",placeholder="email@example.com")
            contact = st.text_input("Contact Number", placeholder="1234567890", max_chars=10)
            age = st.number_input("Age", min_value=10, max_value=100)
            new_password = st.text_input("Password", type="password")
            st.caption("🔒 Min 8 characters with letters, numbers & a special character (e.g. @#$!)")
            confirm_password = st.text_input("Re-enter Password", type="password")

            if st.button("SignUp"):
                errors = []

                if not new_user.strip():
                    errors.append("Username cannot be empty.")

                if not is_valid_email(email):
                    errors.append("Enter a valid email address (e.g. user@example.com).")

                if not is_valid_mobile(contact):
                    errors.append("Contact number must be exactly 10 digits (numbers only).")

                pwd_ok, pwd_msg = is_strong_password(new_password)
                if not pwd_ok:
                    errors.append(pwd_msg)

                if new_password != confirm_password:
                    errors.append("Passwords do not match.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success = add_user(new_user, email, contact, age, new_password)
                    if success:
                        st.success("Account Created Successfully!")
                        st.info("Now click Login to sign in.")
                    else:
                        st.error("Username already exists. Please choose a different username.")


# ---------------- DASHBOARD ---------------- #

if st.session_state.logged_in:

    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    menu = ["Home", "Profile", "Logout"]
    choice = st.sidebar.selectbox("Navigation", menu)

    # ---------------- PROFILE ---------------- #

    if choice == "Profile":

        user = get_user(st.session_state.username)

        st.markdown("""
        <style>
        .profile-card{
            width:420px;
            margin:auto;
            padding:40px;
            border-radius:20px;
            background: rgba(0,0,0,0.65);
            backdrop-filter: blur(10px);
            text-align:center;
            box-shadow:0px 0px 25px rgba(0,0,0,0.6);
            color:white;
        }
        .profile-img{
            width:120px;
            border-radius:50%;
            margin-bottom:20px;
        }
        .profile-title{
            font-size:50px;
            font-weight:bold;
            text-align:center;
            margin-bottom:40px;
        }
        .profile-text{
            font-size:20px;
            margin:12px 0;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="profile-title">User Profile</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="profile-card">
        <img class="profile-img" src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png">
        <div class="profile-text">👤 <b>Username:</b> {user[0]}</div>
        <div class="profile-text">📧 <b>Email:</b> {user[1]}</div>
        <div class="profile-text">📞 <b>Contact:</b> {user[2]}</div>
        <div class="profile-text">🎂 <b>Age:</b> {user[3]}</div>
        <div class="profile-text">🔒 <b>Password:</b> ********</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- MOVIE DASHBOARD ---------------- #

    if choice == "Home":

        st.markdown("<h1 class='main-title'>SmartFlix</h1>", unsafe_allow_html=True)

        movies = pickle.load(open('artificats/movies_list.pkl', 'rb'))
        similarity = pickle.load(open('artificats/similarity.pkl', 'rb'))

        API_KEY = "a0924b64e00b89e738d0c3bc7b3c317c"

        # -------- FETCH POSTER -------- #

        def fetch_poster(movie_id):
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
            data = requests.get(url).json()
            poster_path = data.get('poster_path', '')
            if poster_path:
                return "http://image.tmdb.org/t/p/w500/" + poster_path
            return "https://via.placeholder.com/500x750?text=No+Image"

        # -------- FETCH FULL MOVIE DETAILS -------- #

        def fetch_movie_details(movie_id):
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
            data = requests.get(url).json()
            return data

        # -------- RECOMMEND -------- #

        def recommend(movie):
            try:
                index = movies[movies['title'] == movie].index[0]
                distances = sorted(
                    list(enumerate(similarity[index])),
                    reverse=True,
                    key=lambda x: x[1]
                )
                names = []
                posters = []
                ids = []
                for i in distances[1:6]:
                    movie_id = movies.iloc[i[0]].id
                    names.append(movies.iloc[i[0]].title)
                    posters.append(fetch_poster(movie_id))
                    ids.append(movie_id)
                return names, posters, ids
            except IndexError:
                # Movie not found in dataset, return empty recommendations
                return [], [], []

        # -------- MOVIE DETAIL PANEL -------- #

        def show_movie_detail(movie_id, movie_title):
            details = fetch_movie_details(movie_id)
            poster = fetch_poster(movie_id)

            genres = [g['name'] for g in details.get('genres', [])]
            overview = details.get('overview', 'No description available.')
            release_date = details.get('release_date', 'N/A')
            rating = details.get('vote_average', 'N/A')
            runtime = details.get('runtime', 'N/A')
            year = release_date[:4] if release_date != 'N/A' else 'N/A'

            st.markdown('<div class="detail-panel">', unsafe_allow_html=True)

            img_col, info_col = st.columns([1, 2.5])

            with img_col:
                st.image(poster, use_container_width=True)

            with info_col:
                st.markdown(f'<div class="detail-title">{movie_title}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="detail-meta">📅 {year} &nbsp;|&nbsp; ⏱ {runtime} min &nbsp;|&nbsp; ⭐ {round(rating, 1)}/10</div>',
                    unsafe_allow_html=True
                )

                genre_html = "".join([f'<span class="detail-badge">{g}</span>' for g in genres])
                st.markdown(genre_html, unsafe_allow_html=True)

                st.markdown(f'<div class="detail-overview" style="margin-top:16px">{overview}</div>', unsafe_allow_html=True)

                close_col, _ = st.columns([1, 4])
                with close_col:
                    st.markdown('<div class="close-btn">', unsafe_allow_html=True)
                    if st.button("✕ Close", key="close_detail"):
                        st.session_state.selected_movie_id = None
                        st.session_state.selected_movie_title = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # --- Suggestions based on clicked movie --- #
            st.markdown('<div class="section-header">🎬 Similar Movies You Might Like</div>', unsafe_allow_html=True)

            rec_names, rec_posters, rec_ids = recommend(movie_title)

            if rec_names:
                rec_cols = st.columns(5)
                for i, col in enumerate(rec_cols):
                    with col:
                        movie_card(rec_names[i], rec_ids[i], key_prefix="sugg")
            else:
                st.write("No similar movies found in our database.")

        # -------- CLICKABLE MOVIE CARD -------- #
        # Streamlit cannot make st.image natively clickable.
        # Best UX: full poster image + a sleek pill button below that looks
        # intentional and modern (not a clunky rectangle).

        def movie_card(title, movie_id, key_prefix=""):
            poster = fetch_poster(movie_id)

            # Poster with hover glow via HTML (purely visual)
            st.markdown(f"""
            <div style="
                border-radius:12px;overflow:hidden;
                box-shadow:0 4px 20px rgba(0,0,0,0.6);
                transition:transform 0.2s;
                margin-bottom:0px;
            ">
                <img src="{poster}" style="width:100%;display:block;border-radius:12px;" />
            </div>
            <div style="
                background:linear-gradient(135deg,#1a0000,#2a0a0a);
                border:1px solid rgba(229,9,20,0.3);
                border-radius:0 0 10px 10px;
                padding:8px 10px 10px;
                margin-top:-6px;
            ">
                <div style="
                    color:#fff;font-size:12px;font-weight:700;
                    font-family:sans-serif;line-height:1.3;
                    margin-bottom:8px;min-height:32px;
                ">{title}</div>
            </div>
            """, unsafe_allow_html=True)

            # Modern pill-style "▶ Play" button
            btn_css = f"""
            <style>
            div[data-key="{key_prefix}_{movie_id}"] button {{
                background: linear-gradient(135deg, #E50914, #b0060f) !important;
                color: white !important;
                border: none !important;
                border-radius: 20px !important;
                width: 100% !important;
                height: 34px !important;
                font-size: 12px !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                cursor: pointer !important;
                transition: opacity 0.2s !important;
                margin-top: -4px !important;
            }}
            div[data-key="{key_prefix}_{movie_id}"] button:hover {{
                opacity: 0.85 !important;
            }}
            </style>
            """
            st.markdown(btn_css, unsafe_allow_html=True)
            if st.button("▶  View Details", key=f"{key_prefix}_{movie_id}"):
                st.session_state.selected_movie_id = movie_id
                st.session_state.selected_movie_title = title
                st.rerun()

        # -------- SHOW CATEGORY -------- #

        def show_category(title, movies_list):
            st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns(5)
            cols = [col1, col2, col3, col4, col5]
            for i in range(5):
                with cols[i]:
                    movie_card(movies_list[i][0], movies_list[i][1], key_prefix=title[:3])

        # -------- SMART SEARCH — pure Streamlit, fully working -------- #

        GENRE_MAP = {
            "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
            "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
            "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
            "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
            "Thriller": 53, "War": 10752, "Western": 37
        }

        def search_by_title(query):
            url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={requests.utils.quote(query)}&language=en-US&page=1"
            data = requests.get(url).json()
            return [(r['title'], r['id']) for r in data.get('results', [])[:10] if r.get('poster_path')]

        def search_by_person(query, role="cast"):
            url = f"https://api.themoviedb.org/3/search/person?api_key={API_KEY}&query={requests.utils.quote(query)}"
            data = requests.get(url).json()
            results = data.get('results', [])
            if not results:
                return []
            person_id = results[0]['id']
            person_name = results[0]['name']
            url2 = f"https://api.themoviedb.org/3/person/{person_id}/movie_credits?api_key={API_KEY}"
            data2 = requests.get(url2).json()
            raw = data2.get('cast', []) if role == "cast" else [m for m in data2.get('crew', []) if m.get('job') == 'Director']
            raw = sorted(raw, key=lambda x: x.get('popularity', 0), reverse=True)[:10]
            return [(m['title'], m['id'], person_name) for m in raw if m.get('poster_path')]

        def discover_movies(genre_ids=None, year=None, min_rating=None, sort_by="popularity.desc"):
            params = {"api_key": API_KEY, "language": "en-US", "sort_by": sort_by, "page": 1, "include_adult": "false"}
            if genre_ids:
                params["with_genres"] = ",".join(str(g) for g in genre_ids)
            if year:
                params["primary_release_year"] = year
            if min_rating and min_rating > 0:
                params["vote_average.gte"] = min_rating
                params["vote_count.gte"] = 100
            url = "https://api.themoviedb.org/3/discover/movie?" + "&".join(f"{k}={v}" for k, v in params.items())
            data = requests.get(url).json()
            return [(r['title'], r['id']) for r in data.get('results', [])[:20] if r.get('poster_path')]

        def get_random_genre_movies(genre_id, num=5):
            movies = discover_movies(genre_ids=[genre_id], sort_by="popularity.desc")
            random.shuffle(movies)
            return movies[:num]

        # ---- Search panel styles ----
        st.markdown("""
        <style>
        /* Hide default radio buttons, show as styled tabs */
        div[data-testid="stRadio"] > div {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            background: transparent !important;
        }
        div[data-testid="stRadio"] label {
            background: rgba(255,255,255,0.06) !important;
            border: 1.5px solid rgba(255,255,255,0.15) !important;
            border-radius: 24px !important;
            padding: 7px 18px !important;
            color: #aaa !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.15s !important;
        }
        div[data-testid="stRadio"] label:hover {
            border-color: #E50914 !important;
            color: #fff !important;
            background: rgba(229,9,20,0.1) !important;
        }
        div[data-testid="stRadio"] label[data-checked="true"],
        div[data-testid="stRadio"] input:checked + div {
            background: linear-gradient(135deg, #E50914, #b0060f) !important;
            border-color: #E50914 !important;
            color: #fff !important;
            box-shadow: 0 2px 8px rgba(229,9,20,0.4) !important;
            transform: translateY(-1px) !important;
        }
        /* Style the search container */
        .smartsearch-wrap {
            background: rgba(12,12,12,0.95);
            border: 1.5px solid rgba(229,9,20,0.45);
            border-radius: 20px;
            padding: 22px 28px 26px;
            margin-bottom: 24px;
        }
        .smartsearch-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            color: #555;
            margin-bottom: 14px;
        }
        /* Style text inputs inside search */
        .smartsearch-wrap div[data-testid="stTextInput"] input {
            background: rgba(255,255,255,0.05) !important;
            border: 1.5px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
            color: #fff !important;
            font-size: 15px !important;
            padding: 10px 16px !important;
        }
        .smartsearch-wrap div[data-testid="stTextInput"] input:focus {
            border-color: #E50914 !important;
            box-shadow: 0 0 0 2px rgba(229,9,20,0.2) !important;
        }
        .smartsearch-wrap div[data-testid="stTextInput"] input::placeholder {
            color: #444 !important;
        }
        /* Selectbox */
        .smartsearch-wrap div[data-testid="stSelectbox"] > div > div {
            background: rgba(255,255,255,0.05) !important;
            border: 1.5px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
            color: #fff !important;
        }
        /* Multiselect */
        .smartsearch-wrap div[data-testid="stMultiSelect"] > div {
            background: rgba(255,255,255,0.05) !important;
            border: 1.5px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
        }
        /* Number input */
        .smartsearch-wrap div[data-testid="stNumberInput"] input {
            background: rgba(255,255,255,0.05) !important;
            border: 1.5px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
            color: #fff !important;
        }
        /* Slider */
        .smartsearch-wrap div[data-testid="stSlider"] div[data-testid="stSliderTrack"] {
            background: rgba(229,9,20,0.3) !important;
        }
        /* Search execute button */
        div[data-key="search_execute"] button {
            background: linear-gradient(135deg, #E50914, #b0060f) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            width: 100% !important;
            height: 42px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            margin-top: 4px !important;
        }
        div[data-key="search_execute"] button:hover { opacity: 0.88 !important; }
        </style>
        """, unsafe_allow_html=True)

        # ---- Search UI ----
        st.markdown('<div class="smartsearch-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="smartsearch-label">Smart Search</div>', unsafe_allow_html=True)

        # Tab selector — shows as pill buttons
        search_mode = st.radio(
            "search_mode",
            ["🎬 Title", "🎭 Genre", "⭐ Actor", "🎬 Director", "📅 Year & Rating", "✨ Recommend"],
            horizontal=True,
            label_visibility="collapsed",
            key="search_mode_radio"
        )

        search_results = []
        result_label   = ""

        # ---- TITLE ----
        if search_mode == "🎬 Title":
            col_inp, col_btn = st.columns([5, 1])
            with col_inp:
                title_q = st.text_input("title_q", placeholder="Search any movie title...",
                                        label_visibility="collapsed", key="title_input")
            with col_btn:
                go = st.button("Search", key="search_execute")
            if go and title_q.strip():
                with st.spinner("Searching TMDB..."):
                    search_results = search_by_title(title_q.strip())
                    result_label = f'Title: "{title_q.strip()}"'
            elif not go and title_q.strip():
                search_results = search_by_title(title_q.strip())
                result_label = f'Title: "{title_q.strip()}"'

        # ---- GENRE ----
        elif search_mode == "🎭 Genre":
            col_g, col_s, col_btn = st.columns([3, 2, 1])
            with col_g:
                sel_genres = st.multiselect("Genres", list(GENRE_MAP.keys()),
                                             default=["Action"], label_visibility="visible", key="genre_ms")
            with col_s:
                sort_opt = st.selectbox("Sort", ["Most Popular", "Top Rated", "Newest"], key="genre_sort")
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                go = st.button("Search", key="search_execute")
            if go and sel_genres:
                sort_map = {"Most Popular": "popularity.desc", "Top Rated": "vote_average.desc", "Newest": "release_date.desc"}
                gids = [GENRE_MAP[g] for g in sel_genres if g in GENRE_MAP]
                with st.spinner("Fetching movies..."):
                    search_results = discover_movies(genre_ids=gids, sort_by=sort_map[sort_opt])
                    result_label = f"{' + '.join(sel_genres)}  ·  {sort_opt}"

        # ---- ACTOR ----
        elif search_mode == "⭐ Actor":
            col_inp, col_btn = st.columns([5, 1])
            with col_inp:
                cast_q = st.text_input("cast_q", placeholder="e.g. Tom Hanks, Zendaya, Leonardo DiCaprio...",
                                       label_visibility="collapsed", key="cast_input")
            with col_btn:
                go = st.button("Search", key="search_execute")
            if go and cast_q.strip():
                with st.spinner(f"Finding movies with {cast_q.strip()}..."):
                    raw = search_by_person(cast_q.strip(), role="cast")
                    if raw:
                        search_results = [(t, i) for t, i, _ in raw]
                        result_label = f"Starring: {raw[0][2]}"
                    else:
                        st.warning("No actor found with that name.")

        # ---- DIRECTOR ----
        elif search_mode == "🎬 Director":
            col_inp, col_btn = st.columns([5, 1])
            with col_inp:
                dir_q = st.text_input("dir_q", placeholder="e.g. Christopher Nolan, Quentin Tarantino...",
                                      label_visibility="collapsed", key="dir_input")
            with col_btn:
                go = st.button("Search", key="search_execute")
            if go and dir_q.strip():
                with st.spinner(f"Finding films by {dir_q.strip()}..."):
                    raw = search_by_person(dir_q.strip(), role="director")
                    if raw:
                        search_results = [(t, i) for t, i, _ in raw]
                        result_label = f"Directed by: {raw[0][2]}"
                    else:
                        st.warning("No director found with that name.")

        # ---- YEAR & RATING ----
        elif search_mode == "📅 Year & Rating":
            col_y, col_r, col_g, col_btn = st.columns([2, 2, 2, 1])
            with col_y:
                year_val = st.number_input("Year", min_value=1950, max_value=2025, value=2023, step=1, key="year_inp")
            with col_r:
                rating_val = st.slider("Min Rating ⭐", 0.0, 10.0, 7.0, 0.5, key="rating_sl")
            with col_g:
                genre_single = st.selectbox("Genre", ["Any"] + list(GENRE_MAP.keys()), key="yr_genre")
            with col_btn:
                st.markdown("<br><br>", unsafe_allow_html=True)
                go = st.button("Search", key="search_execute")
            if go:
                gids = [GENRE_MAP[genre_single]] if genre_single != "Any" else None
                with st.spinner("Fetching movies..."):
                    search_results = discover_movies(genre_ids=gids, year=int(year_val),
                                                     min_rating=rating_val if rating_val > 0 else None)
                    result_label = f"{int(year_val)}  ·  ⭐ {rating_val}+  ·  {genre_single}"

        # ---- RECOMMEND ----
        elif search_mode == "✨ Recommend":
            col_inp, col_btn = st.columns([5, 1])
            with col_inp:
                rec_movie = st.selectbox("Pick a movie", movies['title'].values,
                                         label_visibility="collapsed", key="rec_sel")
            with col_btn:
                go = st.button("Go", key="search_execute")
            if go and rec_movie:
                with st.spinner("Finding similar movies..."):
                    names, _, ids = recommend(rec_movie)
                    search_results = list(zip(names, ids))
                    result_label = f"Because you watched: {rec_movie}"

        st.markdown('</div>', unsafe_allow_html=True)

        # ---- RENDER RESULTS ----
        if search_results:
            st.markdown(f'<div class="section-header">🔍 {result_label}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div style="color:#777;font-size:13px;margin:-10px 0 20px;font-style:italic;">'
                f'{len(search_results)} movie(s) found</div>', unsafe_allow_html=True
            )
            for row_start in range(0, len(search_results), 5):
                row = search_results[row_start:row_start + 5]
                cols = st.columns(5)
                for i, (t, mid) in enumerate(row):
                    with cols[i]:
                        movie_card(t, mid, key_prefix=f"sr{row_start}")

        # -------- SHOW DETAIL PANEL IF A MOVIE IS CLICKED -------- #

        if st.session_state.selected_movie_id is not None:
            st.markdown("---")
            show_movie_detail(st.session_state.selected_movie_id, st.session_state.selected_movie_title)
            st.markdown("---")

        # -------- MOVIE CATEGORIES -------- #

        if st.session_state.action_movies is None:
            st.session_state.action_movies = get_random_genre_movies(28)

        if st.session_state.horror_movies is None:
            st.session_state.horror_movies = get_random_genre_movies(27)

        if st.session_state.thriller_movies is None:
            st.session_state.thriller_movies = get_random_genre_movies(53)

        show_category("🔥 Top 5 Action Movies", st.session_state.action_movies)
        show_category("👻 Top 5 Horror Movies", st.session_state.horror_movies)
        show_category("🕵️ Top 5 Thriller Movies", st.session_state.thriller_movies)

    # ---------------- LOGOUT ---------------- #

    if choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.selected_movie_id = None
        st.session_state.selected_movie_title = None
        st.session_state.action_movies = None
        st.session_state.horror_movies = None
        st.session_state.thriller_movies = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()