import streamlit as st
import requests
import base64
from datetime import datetime

# ============================================================
# PROJECTOR CINEMA - Streamlit App
# Optimized for big-screen / projector viewing
# ============================================================

# --- Page Config ---
st.set_page_config(
    page_title="🎬 Projector Cinema",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TMDB API Config (Free tier - get yours at https://www.themoviedb.org/settings/api) ---
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "YOUR_TMDB_API_KEY_HERE")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_URL = "https://image.tmdb.org/t/p/original"
YOUTUBE_EMBED = "https://www.youtube.com/embed/"

# --- Custom CSS for Projector / Big Screen ---
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dark cinematic background */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0f0f23 100%);
    }

    /* Big projector-friendly text */
    h1 { font-size: 3.5rem !important; font-weight: 800 !important; letter-spacing: 2px !important; }
    h2 { font-size: 2.5rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.8rem !important; font-weight: 600 !important; }
    p, div { font-size: 1.2rem !important; }

    /* Neon glow effects */
    .neon-text {
        color: #00d4ff;
        text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff, 0 0 40px #0099cc;
    }

    .neon-purple {
        color: #e040fb;
        text-shadow: 0 0 10px #e040fb, 0 0 20px #aa00ff;
    }

    /* Movie cards */
    .movie-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #2d2d44 100%);
        border-radius: 16px;
        padding: 12px;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.05);
        cursor: pointer;
    }

    .movie-card:hover {
        transform: scale(1.05);
        border-color: #00d4ff;
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
    }

    /* Search bar styling */
    .stTextInput > div > div > input {
        font-size: 1.5rem !important;
        padding: 20px !important;
        border-radius: 50px !important;
        background: rgba(255,255,255,0.05) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        color: white !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
    }

    /* Buttons */
    .stButton > button {
        font-size: 1.3rem !important;
        padding: 15px 40px !important;
        border-radius: 50px !important;
        background: linear-gradient(90deg, #00d4ff, #0099cc) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.5) !important;
    }

    /* Category pills */
    .category-pill {
        display: inline-block;
        padding: 10px 25px;
        margin: 5px;
        border-radius: 50px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .category-pill:hover, .category-pill.active {
        background: linear-gradient(90deg, #e040fb, #aa00ff);
        border-color: #e040fb;
        box-shadow: 0 0 20px rgba(224, 64, 251, 0.4);
    }

    /* Video player container */
    .video-container {
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        border-radius: 20px;
        box-shadow: 0 0 50px rgba(0,0,0,0.8);
        border: 2px solid rgba(0, 212, 255, 0.2);
    }

    .video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 20px;
    }

    /* Rating badge */
    .rating-badge {
        background: linear-gradient(135deg, #ffd700, #ff8c00);
        color: black;
        font-weight: 800;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 1.1rem;
        display: inline-block;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0a0a0a; }
    ::-webkit-scrollbar-thumb { background: #00d4ff; border-radius: 4px; }

    /* Hide streamlit default containers on mobile */
    @media (max-width: 768px) {
        h1 { font-size: 2rem !important; }
        h2 { font-size: 1.5rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "category" not in st.session_state:
    st.session_state.category = "trending"
if "custom_video_url" not in st.session_state:
    st.session_state.custom_video_url = ""

def go_home():
    st.session_state.page = "home"
    st.session_state.selected_movie = None
    st.rerun()

def show_movie_detail(movie):
    st.session_state.selected_movie = movie
    st.session_state.page = "detail"
    st.rerun()

def show_player():
    st.session_state.page = "player"
    st.rerun()

# --- API Functions ---
def fetch_tmdb(endpoint, params=None):
    """Generic TMDB API fetcher"""
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    try:
        response = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def get_trending():
    data = fetch_tmdb("/trending/all/week")
    return data.get("results", []) if data else []

def get_popular_movies():
    data = fetch_tmdb("/movie/popular")
    return data.get("results", []) if data else []

def get_popular_series():
    data = fetch_tmdb("/tv/popular")
    return data.get("results", []) if data else []

def get_top_rated():
    data = fetch_tmdb("/movie/top_rated")
    return data.get("results", []) if data else []

def search_content(query):
    data = fetch_tmdb("/search/multi", {"query": query})
    return data.get("results", []) if data else []

def get_movie_videos(movie_id, media_type="movie"):
    endpoint = f"/{media_type}/{movie_id}/videos"
    data = fetch_tmdb(endpoint)
    if data and data.get("results"):
        # Prefer YouTube trailers
        for video in data["results"]:
            if video.get("site") == "YouTube" and "trailer" in video.get("type", "").lower():
                return video["key"]
        # Fallback to any YouTube video
        for video in data["results"]:
            if video.get("site") == "YouTube":
                return video["key"]
    return None

def get_movie_details(movie_id, media_type="movie"):
    endpoint = f"/{media_type}/{movie_id}"
    return fetch_tmdb(endpoint)

# --- UI Components ---
def render_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("## 🎬")
    with col2:
        st.markdown("<h1 style='text-align: center;' class='neon-text'>PROJECTOR CINEMA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888; font-size: 1.1rem;'>Your Personal Big-Screen Experience</p>", unsafe_allow_html=True)
    with col3:
        if st.session_state.page != "home":
            if st.button("🏠 Home", key="home_btn"):
                go_home()
    st.markdown("<hr style='border: 1px solid rgba(0,212,255,0.2); margin: 20px 0;'>", unsafe_allow_html=True)

def render_search_bar():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input("", placeholder="🔍 Search movies, series, actors...", 
                              value=st.session_state.search_query, key="search_input")
    with col2:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.search_query = query
            st.session_state.category = "search"
            st.rerun()
    with col3:
        if st.button("📺 My Player", use_container_width=True):
            show_player()
    return query

def render_categories():
    cols = st.columns(5)
    categories = [
        ("🔥 Trending", "trending"),
        ("🎬 Movies", "movies"),
        ("📺 Series", "series"),
        ("⭐ Top Rated", "toprated"),
        ("🎞️ My Videos", "player")
    ]
    for i, (label, cat) in enumerate(categories):
        with cols[i]:
            active = "active" if st.session_state.category == cat else ""
            if st.button(label, use_container_width=True, key=f"cat_{cat}"):
                if cat == "player":
                    show_player()
                else:
                    st.session_state.category = cat
                    st.session_state.search_query = ""
                    st.rerun()

def render_movie_card(item, idx):
    """Render a single movie/series card"""
    title = item.get("title") or item.get("name") or "Unknown"
    poster = item.get("poster_path")
    rating = item.get("vote_average", 0)
    year = (item.get("release_date") or item.get("first_air_date") or "N/A")[:4]
    media_type = item.get("media_type", "movie")

    poster_url = f"{TMDB_IMG_URL}{poster}" if poster else "https://via.placeholder.com/300x450/1a1a2e/00d4ff?text=No+Poster"

    card_html = f"""
    <div class="movie-card" style="text-align: center;">
        <img src="{poster_url}" style="width: 100%; border-radius: 12px; margin-bottom: 10px; aspect-ratio: 2/3; object-fit: cover;">
        <div style="font-weight: 700; font-size: 1.1rem; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{title}</div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 8px;">
            <span class="rating-badge">⭐ {rating:.1f}</span>
            <span style="color: #888; font-size: 0.9rem;">{year}</span>
        </div>
    </div>
    """

    # Use columns for layout
    return card_html, item

def render_movie_grid(items, title=""):
    if title:
        st.markdown(f"<h2 class='neon-purple'>{title}</h2>", unsafe_allow_html=True)

    if not items:
        st.info("🎬 No content found. Try a different search!")
        return

    # Display in rows of 5 (projector-friendly large cards)
    cols_per_row = 5
    for i in range(0, len(items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(items):
                with col:
                    item = items[idx]
                    card_html, item_data = render_movie_card(item, idx)
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button("▶ Watch", key=f"btn_{idx}_{item.get('id')}", use_container_width=True):
                        show_movie_detail(item_data)

# --- Page: Home ---
def home_page():
    render_header()

    # Search Bar
    query = render_search_bar()
    st.markdown("<br>", unsafe_allow_html=True)

    # Categories
    render_categories()
    st.markdown("<br>", unsafe_allow_html=True)

    # Content based on category
    if st.session_state.category == "search" and st.session_state.search_query:
        with st.spinner("🔍 Searching the galaxy..."):
            results = search_content(st.session_state.search_query)
        render_movie_grid(results, f"🔍 Results for '{st.session_state.search_query}'")

    elif st.session_state.category == "trending":
        with st.spinner("🔥 Loading trending..."):
            trending = get_trending()
        render_movie_grid(trending[:15], "🔥 Trending This Week")

        with st.spinner("🎬 Loading popular movies..."):
            popular = get_popular_movies()
        render_movie_grid(popular[:10], "🎬 Popular Movies")

    elif st.session_state.category == "movies":
        with st.spinner("🎬 Loading movies..."):
            movies = get_popular_movies()
        render_movie_grid(movies[:20], "🎬 Popular Movies")

        with st.spinner("⭐ Loading top rated..."):
            top = get_top_rated()
        render_movie_grid(top[:10], "⭐ Top Rated Movies")

    elif st.session_state.category == "series":
        with st.spinner("📺 Loading series..."):
            series = get_popular_series()
        render_movie_grid(series[:20], "📺 Popular Series")

    elif st.session_state.category == "toprated":
        with st.spinner("⭐ Loading top rated..."):
            top = get_top_rated()
        render_movie_grid(top[:20], "⭐ Top Rated of All Time")

# --- Page: Movie Detail ---
def detail_page():
    movie = st.session_state.selected_movie
    if not movie:
        go_home()
        return

    movie_id = movie.get("id")
    media_type = movie.get("media_type", "movie")
    if media_type not in ["movie", "tv"]:
        media_type = "movie"

    # Fetch detailed info
    with st.spinner("🎬 Loading details..."):
        details = get_movie_details(movie_id, media_type)
        trailer_key = get_movie_videos(movie_id, media_type)

    title = details.get("title") or details.get("name") or movie.get("title") or movie.get("name") or "Unknown"
    overview = details.get("overview", "No description available.")
    rating = details.get("vote_average", movie.get("vote_average", 0))
    backdrop = details.get("backdrop_path") or movie.get("backdrop_path")
    poster = details.get("poster_path") or movie.get("poster_path")
    genres = [g["name"] for g in details.get("genres", [])]
    runtime = details.get("runtime") or details.get("episode_run_time", ["N/A"])[0]
    year = (details.get("release_date") or details.get("first_air_date") or "N/A")[:4]

    # Backdrop header
    if backdrop:
        backdrop_url = f"{TMDB_BACKDROP_URL}{backdrop}"
        st.markdown(f"""
        <div style="position: relative; width: 100%; height: 400px; border-radius: 20px; overflow: hidden; margin-bottom: 30px;">
            <img src="{backdrop_url}" style="width: 100%; height: 100%; object-fit: cover; opacity: 0.4;">
            <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 40px; background: linear-gradient(transparent, #0a0a0a);">
                <h1 style="color: white; text-shadow: 0 0 20px black;">{title}</h1>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span class="rating-badge">⭐ {rating:.1f}</span>
                    <span style="color: #ccc; font-size: 1.2rem;">{year}</span>
                    <span style="color: #ccc; font-size: 1.2rem;">⏱ {runtime} min</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<h1 class='neon-text'>{title}</h1>", unsafe_allow_html=True)

    # Back button
    if st.button("⬅ Back to Browse", key="back_btn"):
        go_home()

    st.markdown("<br>", unsafe_allow_html=True)

    # Two column layout
    col1, col2 = st.columns([1, 2])

    with col1:
        if poster:
            st.image(f"{TMDB_IMG_URL}{poster}", use_container_width=True)

        # Genres
        if genres:
            st.markdown("<br>", unsafe_allow_html=True)
            genre_html = " ".join([f'<span style="background: rgba(0,212,255,0.2); color: #00d4ff; padding: 5px 15px; border-radius: 20px; margin: 3px; display: inline-block;">{g}</span>' for g in genres])
            st.markdown(genre_html, unsafe_allow_html=True)

    with col2:
        st.markdown(f"<h3 class='neon-purple'>📖 Storyline</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #ccc; line-height: 1.8;'>{overview}</p>", unsafe_allow_html=True)

        # Trailer
        if trailer_key:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<h3 class='neon-purple'>🎬 Trailer</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="video-container">
                <iframe src="{YOUTUBE_EMBED}{trailer_key}?autoplay=0&rel=0" 
                        frameborder="0" allowfullscreen 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                </iframe>
            </div>
            """, unsafe_allow_html=True)

        # Custom Video Player Section
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3 class='neon-purple'>▶ Play Your Video</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #888;'>Paste a direct video URL (.mp4, .m3u8, YouTube, etc.) to watch:</p>", unsafe_allow_html=True)

        video_url = st.text_input("Video URL", placeholder="https://example.com/movie.mp4", key="detail_video_url")
        if video_url:
            st.video(video_url)

# --- Page: Custom Player ---
def player_page():
    render_header()

    st.markdown("<h1 class='neon-text' style='text-align: center;'>📺 Personal Video Player</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Paste any video URL to watch on your projector</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Main player
    video_url = st.text_input("🎬 Enter Video URL", 
                               placeholder="https://example.com/video.mp4 or https://youtube.com/watch?v=...",
                               key="player_url")

    if video_url:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="video-container" style="box-shadow: 0 0 60px rgba(0,212,255,0.2);">
        </div>
        """, unsafe_allow_html=True)
        st.video(video_url)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px; background: rgba(255,255,255,0.02); border-radius: 20px; border: 2px dashed rgba(0,212,255,0.3);">
            <h2 style="color: #00d4ff;">📥 Paste a Video URL</h2>
            <p style="color: #888;">Supports: Direct MP4 links, YouTube URLs, HLS streams (.m3u8), and more</p>
            <p style="color: #666; font-size: 0.9rem;">💡 Tip: Use this with your personal media server (Plex, Jellyfin, Emby) or any legal video source</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick bookmarks section
    st.markdown("<h3 class='neon-purple'>📌 Quick Bookmarks</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>Save your frequently watched URLs (session only):</p>", unsafe_allow_html=True)

    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = []

    new_bookmark = st.text_input("Add Bookmark URL", placeholder="Paste URL here...", key="bookmark_input")
    bookmark_name = st.text_input("Bookmark Name (optional)", placeholder="My Movie", key="bookmark_name")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Add", use_container_width=True) and new_bookmark:
            st.session_state.bookmarks.append({"url": new_bookmark, "name": bookmark_name or f"Bookmark {len(st.session_state.bookmarks)+1}"})
            st.rerun()

    if st.session_state.bookmarks:
        st.markdown("<br>", unsafe_allow_html=True)
        for i, bm in enumerate(st.session_state.bookmarks):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"<p style='color: #00d4ff;'>▶ {bm['name']}</p>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("▶ Play", key=f"play_bm_{i}"):
                    st.session_state.custom_video_url = bm["url"]
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_bm_{i}"):
                    st.session_state.bookmarks.pop(i)
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Back to Home", use_container_width=True):
        go_home()

# --- Main Router ---
def main():
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "detail":
        detail_page()
    elif st.session_state.page == "player":
        player_page()

if __name__ == "__main__":
    main()
