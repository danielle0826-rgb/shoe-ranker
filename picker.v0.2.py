import streamlit as st
import os
import random
import base64

# -------------------------------------------------------------
# 1. SETUP STATE & DATA CONFIGURATION
# -------------------------------------------------------------
IMAGE_DIR = "inputs/shoes"
STRIKES_ALLOWED = 3
CHOICES_PER_ROUND = 4

st.set_page_config(page_title="Amanda's Shoe Picker V0.2", layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
        }
        div[data-testid="stColumn"] {
            border: 1px solid #ddd !important;
            border-radius: 8px !important;
            padding: 4px !important;
            background-color: transparent !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        div[data-testid="stButton"] button {
            border: none !important;
            background-color: transparent !important;
            padding: 0px !important;
            margin: 0px !important;
            box-shadow: none !important;
            width: 100% !important;
            height: 140px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        div[data-testid="stButton"] button img {
            max-height: 130px !important;
            max-width: 100% !important;
            object-fit: contain !important;
        }
        div[data-testid="stButton"] button:active {
            transform: scale(0.96) !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            padding-bottom: 0.1rem !important;
        }
        hr { margin: 0.4rem 0 !important; }
    </style>
""", unsafe_allow_html=True)

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
    st.warning(f"Created a folder named '{IMAGE_DIR}'. Please drop your shoe images inside it and refresh!")
    st.stop()

all_images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if len(all_images) < CHOICES_PER_ROUND:
    st.error(f"Please place at least {CHOICES_PER_ROUND} images inside the '{IMAGE_DIR}' folder to start the game.")
    st.stop()

# Helper function to convert an image path directly into a base64 string
def get_b64_image(img_name):
    try:
        path = os.path.join(IMAGE_DIR, img_name)
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return ""

if "photo_pool" not in st.session_state:
    st.session_state.photo_pool = {
        img: {"strikes": 0, "wins": 0, "active": True} for img in all_images
    }
    st.session_state.current_round = []  # Holds list of dicts: [{"name": x, "b64": y}, ...]
    st.session_state.next_round = []     # Pre-loaded buffer deck
    st.session_state.winner = None

pool = st.session_state.photo_pool


# -------------------------------------------------------------
# 2. THE BACKGROUND BUFFER ENGINE
# -------------------------------------------------------------
def get_active_photos():
    return [img for img, data in pool.items() if data["active"]]

def build_round_package(selected_names):
    """Packages shoe filenames with their base64 string data at the exact same moment"""
    return [{"name": name, "b64": get_b64_image(name)} for name in selected_names]

def advance_game_deck():
    active_list = get_active_photos()

    # Check for game over states
    if len(active_list) == 1:
        st.session_state.winner = active_list[0]
        st.session_state.current_round = []
        st.session_state.next_round = []
        return
    elif len(active_list) == 0:
        st.session_state.winner = max(pool, key=lambda k: pool[k]["wins"])
        st.session_state.current_round = []
        st.session_state.next_round = []
        return

    # If we have a pre-loaded next round ready, push it to active immediately!
    if st.session_state.next_round:
        st.session_state.current_round = st.session_state.next_round
    else:
        # Fallback for initial fresh game boot
        count_to_draw = min(CHOICES_PER_ROUND, len(active_list))
        chosen_names = random.sample(active_list, count_to_draw)
        st.session_state.current_round = build_round_package(chosen_names)

    # NOW PRE-LOAD THE SUBSEQUENT ROUND IN THE BACKGROUND
    # Recalculate what will remain active after this transition
    post_round_active = get_active_photos()
    if len(post_round_active) > 1:
        count_to_draw = min(CHOICES_PER_ROUND, len(post_round_active))
        next_names = random.sample(post_round_active, count_to_draw)
        st.session_state.next_round = build_round_package(next_names)
    else:
        st.session_state.next_round = []

def handle_vote(chosen_img):
    pool[chosen_img]["wins"] += 1

    # Extract just the filenames from the current packaged round to distribute strikes
    current_names = [item["name"] for item in st.session_state.current_round]
    
    for img in current_names:
        if img != chosen_img:
            pool[img]["strikes"] += 1
            if pool[img]["strikes"] >= STRIKES_ALLOWED:
                pool[img]["active"] = False

    advance_game_deck()


# Initialize decks on fresh launch
if not st.session_state.current_round and not st.session_state.winner:
    advance_game_deck()

# -------------------------------------------------------------
# 3. INTERACTIVE USER INTERFACE DESIGN (THE GAME BOARD)
# -------------------------------------------------------------
st.subheader("👑 Amanda's Shoe Picker V0.2", divider="orange")

if st.session_state.winner:
    st.balloons()
    st.success(f"🏆 We Have a Winner!")

    winner_path = os.path.join(IMAGE_DIR, st.session_state.winner)
    st.image(winner_path, use_container_width=True, caption=st.session_state.winner)

    if st.button("Play Again 🔄"):
        del st.session_state.photo_pool
        del st.session_state.current_round
        del st.session_state.next_round
        del st.session_state.winner
        st.rerun()

else:
    active_count = len(get_active_photos())
    st.markdown(f"<p style='text-align: center; margin-bottom: 5px;'>Remaining Shoes: <b>{active_count}</b> / {len(all_images)}</p>", unsafe_allow_html=True)

    # Render layout columns
    row1_col1, row1_col2 = st.columns(2, wrap=False)
    row2_col1, row2_col2 = st.columns(2, wrap=False)
    grid_cols = [row1_col1, row1_col2, row2_col1, row2_col2]

    # Display the current pre-baked round data packages
    for idx, item in enumerate(st.session_state.current_round):
        if idx < len(grid_cols):
            with grid_cols[idx]:
                st.button(
                    label=f"![shoe](data:image/png;base64,{item['b64']})",
                    key=f"tile_btn_{item['name']}_{idx}",
                    on_click=handle_vote,
                    args=(item['name'],),
                    use_container_width=True
                )

    # Footer elements
    st.divider()
    footer_left, footer_right = st.columns(2, wrap=False)

    with footer_left:
        with st.expander("💬 Miss a shoe?"):
            missing_input = st.text_input("Brand/Name:", key="missing_shoe_input", label_visibility="collapsed")
            if st.button("Submit"):
                if missing_input:
                    st.success("Logged!")

    with footer_right:
        st.info("📺 Nike Kits Ad")
