import streamlit as st
import os
import random

# -------------------------------------------------------------
# 1. SETUP STATE & DATA CONFIGURATION
# -------------------------------------------------------------
IMAGE_DIR = "inputs/shoes"
STRIKES_ALLOWED = 3
CHOICES_PER_ROUND = 4

st.set_page_config(page_title="Amanda's Shoe Picker V0.2", layout="wide")

# This specialized CSS styles standard Streamlit buttons into large,
# borderless cards that expand your shoe images to fill the 2x2 grid.
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
        }
        /* Style Streamlit columns to look like container blocks */
        div[data-testid="stColumn"] {
            border: 1px solid #ddd !important;
            border-radius: 8px !important;
            padding: 4px !important;
            background-color: transparent !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        /* Style the native button container to become the flat clickable card body */
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
        /* Force the button image to fill the card bounds cleanly */
        div[data-testid="stButton"] button img {
            max-height: 130px !important;
            max-width: 100% !important;
            object-fit: contain !important;
        }
        /* Scale feedback animation on click */
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

if "photo_pool" not in st.session_state:
    st.session_state.photo_pool = {
        img: {"strikes": 0, "wins": 0, "active": True} for img in all_images
    }
    st.session_state.current_round = []
    st.session_state.winner = None

pool = st.session_state.photo_pool


# -------------------------------------------------------------
# 2. THE ALGORITHMIC GAME MECHANICS
# -------------------------------------------------------------
def get_active_photos():
    return [img for img, data in pool.items() if data["active"]]


def generate_new_round():
    active_list = get_active_photos()

    if len(active_list) == 1:
        st.session_state.winner = active_list[0]
        st.session_state.current_round = []
    elif len(active_list) == 0:
        st.session_state.winner = max(pool, key=lambda k: pool[k]["wins"])
        st.session_state.current_round = []
    else:
        count_to_draw = min(CHOICES_PER_ROUND, len(active_list))
        st.session_state.current_round = random.sample(active_list, count_to_draw)


def handle_vote(chosen_img):
    pool[chosen_img]["wins"] += 1

    for img in st.session_state.current_round:
        if img != chosen_img:
            pool[img]["strikes"] += 1
            if pool[img]["strikes"] >= STRIKES_ALLOWED:
                pool[img]["active"] = False

    generate_new_round()


if not st.session_state.current_round and not st.session_state.winner:
    generate_new_round()

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
        del st.session_state.winner
        st.rerun()

else:
    active_count = len(get_active_photos())
    st.markdown(f"<p style='text-align: center; margin-bottom: 5px;'>Remaining Shoes: <b>{active_count}</b> / {len(all_images)}</p>", unsafe_allow_html=True)

    current_selection = st.session_state.current_round

    # Render an explicit responsive 2x2 grid layout
    row1_col1, row1_col2 = st.columns(2, wrap=False)
    row2_col1, row2_col2 = st.columns(2, wrap=False)
    
    grid_cols = [row1_col1, row1_col2, row2_col1, row2_col2]

    for idx, img_name in enumerate(current_selection):
        if idx < len(grid_cols):
            with grid_cols[idx]:
                img_path = os.path.join(IMAGE_DIR, img_name)
                
                # Convert image to raw inline base64 data to bypass cloud image scaling rules
                import base64
                with open(img_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("utf-8")
                
                # Render the image label string directly inside a native button.
                # Our top CSS block catches this and strips out all button styling,
                # leaving a clean, large, 100% clickable full-size card tile.
                st.button(
                    label=f"![shoe](data:image/png;base64,{data})",
                    key=f"tile_btn_{img_name}_{idx}",
                    on_click=handle_vote,
                    args=(img_name,),
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
