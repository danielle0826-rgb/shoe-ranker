import streamlit as st
import os
import random

# -------------------------------------------------------------
# 1. SETUP STATE & DATA CONFIGURATION
# -------------------------------------------------------------
IMAGE_DIR = "images"
STRIKES_ALLOWED = 3  # You can change this to 2, 3, 4, etc.
CHOICES_PER_ROUND = 4

st.set_page_config(page_title="The Ultimate Shoe Ranker", layout="centered")

# Read files from your local folder
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
    st.warning(f"Created a folder named '{IMAGE_DIR}'. Please drop your shoe images inside it and refresh!")
    st.stop()

all_images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if len(all_images) < CHOICES_PER_ROUND:
    st.error(f"Please place at least {CHOICES_PER_ROUND} images inside the '{IMAGE_DIR}' folder to start the game.")
    st.stop()

# Initialize the master tracker database in session memory
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

    # Check for Win/Loss states immediately
    if len(active_list) == 1:
        st.session_state.winner = active_list[0]
        st.session_state.current_round = []
    elif len(active_list) == 0:
        # Fallback safeguard: find the item with the most wins if all died at once
        st.session_state.winner = max(pool, key=lambda k: pool[k]["wins"])
        st.session_state.current_round = []
    else:
        # Pull a random group based on your layout constraints
        count_to_draw = min(CHOICES_PER_ROUND, len(active_list))
        st.session_state.current_round = random.sample(active_list, count_to_draw)


def handle_vote(chosen_img):
    # Winner gets +1 win
    pool[chosen_img]["wins"] += 1

    # Everyone else displayed in this round gets +1 strike
    for img in st.session_state.current_round:
        if img != chosen_img:
            pool[img]["strikes"] += 1
            if pool[img]["strikes"] >= STRIKES_ALLOWED:
                pool[img]["active"] = False

    # Refresh the loop deck
    generate_new_round()


# Setup the first round on fresh launch
if not st.session_state.current_round and not st.session_state.winner:
    generate_new_round()

# -------------------------------------------------------------
# 3. INTERACTIVE USER INTERFACE DESIGN (THE WIREFRAME)
# -------------------------------------------------------------
st.title("👟 The Ultimate Shoe Ranker")

# Check if a winner has emerged
if st.session_state.winner:
    st.balloons()
    st.success(f"🏆 We Have a Winner!")

    # Display the definitive winner
    winner_path = os.path.join(IMAGE_DIR, st.session_state.winner)
    st.image(winner_path, use_container_width=True, caption=st.session_state.winner)

    # Sticky Affiliate / Merch Zone
    st.markdown("### 🛍️ Ready to Buy?")
    st.button("👉 Click Here to Buy This Winning Pair! (Affiliate Link)")

    # Reset Application Button
    if st.button("Play Again 🔄"):
        del st.session_state.photo_pool
        del st.session_state.current_round
        del st.session_state.winner
        st.rerun()

# Otherwise, render the active game board
else:
    active_count = len(get_active_photos())
    st.write(f"Remaining Shoes Surviving: **{active_count}** / {len(all_images)}")

    # Build your 2x2 grid layout using Streamlit columns
    current_selection = st.session_state.current_round

    # Top Row
    col1, col2 = st.columns(2)
    # Bottom Row
    col3, col4 = st.columns(2)
    grid_cols = [col1, col2, col3, col4]

    for idx, img_name in enumerate(current_selection):
        if idx < len(grid_cols):
            with grid_cols[idx]:
                img_path = os.path.join(IMAGE_DIR, img_name)
                # Render the image inside the grid element
                st.image(img_path, use_container_width=True)

                # Render the selection target button directly underneath
                # Streamlit keys require unique identifiers
                st.button(
                    "Pick Me! 🎯",
                    key=f"btn_{img_name}_{idx}",
                    on_click=handle_vote,
                    args=(img_name,),
                    use_container_width=True
                )

    # The User Feedback Feature Loop
    st.divider()
    with st.expander("💬 Did we miss an outfit or shoe?"):
        missing_input = st.text_input("Type the missing name or brand here:")
        if st.button("Submit Suggestion"):
            if missing_input:
                st.success(f"Thanks! '{missing_input}' has been logged into our data backend suggestions list.")

    # The Non-Intrusive Contextual Banner Zone
    st.markdown("---")
    st.info("📺 **ADVERTISEMENT:** *Sponsored shoe cleaning kits available now at Nike.com (Contextual Ad Space)*")
