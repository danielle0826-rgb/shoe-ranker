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
    st.markdown(f"<p style='text-align: center; margin-bottom: 5px; margin-top: 0px;'>Remaining Shoes: <b>{active_count}</b> / {len(all_images)}</p>", unsafe_allow_html=True)

    current_selection = st.session_state.current_round

    # 1. ENFORCE A TIGHT 2x2 MOBILE GRID USING FLEXBOX HTML
    # This builds a flex layout container that fits exactly 2 images per row on phone screens
    import base64
    grid_html = '<div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; width: 100%;">'
    
    for idx, img_name in enumerate(current_selection):
        img_path = os.path.join(IMAGE_DIR, img_name)
        with open(img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        
        # Each card takes up exactly 47% width so 2 fit side-by-side perfectly on mobile
        grid_html += f'''
        <div style="width: 47%; display: flex; flex-direction: column; align-items: center; background: #1E1E1E; border-radius: 8px; padding: 4px; box-sizing: border-box;">
            <div style="height: 120px; display: flex; justify-content: center; align-items: center; overflow: hidden;">
                <img src="data:image/png;base64,{data}" style="max-height: 100%; max-width: 100%; object-fit: contain;">
            </div>
            <div style="width: 100%; margin-top: 4px;">
                <a href="?vote={img_name}&idx={idx}" target="_self" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #FF4B4B; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px; cursor: pointer;">
                        Pick Me! 🎯
                    </button>
                </a>
            </div>
        </div>
        '''
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # 2. CAPTURE THE MOBILE CLICK MECHANIC VIA URL QUERY
    query_params = st.query_params
    if "vote" in query_params:
        chosen_img = query_params["vote"]
        # Immediately clear the URL so it doesn't loop votes on reload
        st.query_params.clear()
        handle_vote(chosen_img)
        st.rerun()

    # 3. TIGHTEN FOOTER MODULES SIDE-BY-SIDE FOR PHONES
    st.divider()
    footer_left, footer_right = st.columns(2)
    
    with footer_left:
        with st.expander("💬 Miss a shoe?"):
            missing_input = st.text_input("Name:", key="missing_shoe_input", label_visibility="collapsed")
            if st.button("Submit"):
                if missing_input:
                    st.success("Logged!")

    with footer_right:
        st.info("📺 Nike Kits Ad")


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
