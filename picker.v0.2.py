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

st.set_page_config(page_title="Amanda's Shoe Picker", layout="wide")

# Tighten the overall layout box padding
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
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
st.subheader("👑 Amanda's Shoe Picker", divider="orange")

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
    st.markdown(f"<p style='text-align: center; margin-bottom: 10px;'>Remaining Shoes: <b>{active_count}</b> / {len(all_images)}</p>", unsafe_allow_html=True)

    # Convert the 4 chosen images into base64 data for the isolated component view
    encoded_images = []
    for img_name in st.session_state.current_round:
        path = os.path.join(IMAGE_DIR, img_name)
        with open(path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        encoded_images.append({"name": img_name, "b64": b64_str})

    # BUILD A NATIVE EMBEDDED PHONE TOUCH WRAPPER
    # This runs a tiny isolated layout engine that detects pure taps on images
    # and communicates instantly with Python without breaking the page state.
    html_code = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; font-family: sans-serif; }}
            .grid {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; box-sizing: border-box; }}
            .card {{ width: calc(50% - 5px); box-sizing: border-box; display: flex; justify-content: center; align-items: center; height: 160px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: #fff; cursor: pointer; }}
            .card img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        </style>
    </head>
    <body>
        <div class="grid">
            {"".join([f'<div class="card" onclick="parent.postMessage({{type: \'vote\', value: \'{item["name"]}\'}}, \'*\')"><img src="data:image/png;base64,{item["b64"]}"></div>' for item in encoded_images])}
        </div>
    </body>
    </html>
    """
    
    # Render the layout block window container
    # streamlit.components.v1.html allows us to catch the click without reloading
    import streamlit.components.v1 as components
    response = components.html(html_code, height=340)
    
    # Use a hidden temporary input workaround to process the selection smoothly
    # without breaking layout margins or triggering screen flash loops
    vote_receiver = st.text_input("Internal Token", key="hidden_receiver", label_visibility="collapsed")
    
    st.markdown("""
        <script>
            window.parent.addEventListener('message', function(e) {
                if (e.data.type === 'vote') {
                    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if(inputs.length > 0) {
                        inputs[0].value = e.data.value;
                        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            });
        </script>
    """, unsafe_allow_html=True)
    
    if vote_receiver and vote_receiver in st.session_state.current_round:
        st.session_state.hidden_receiver = ""
        handle_vote(vote_receiver)
        st.rerun()

    # Footer elements
    st.divider()
    footer_left, footer_right = st.columns(2, wrap=False)
    with footer_left:
        with st.expander("💬 Miss a shoe?"):
            missing_input = st.text_input("Brand/Name:", key="missing_shoe_input", label_visibility="collapsed")
            if st.button("Submit"):
                if missing_input: st.success("Logged!")
    with footer_right:
        st.info("📺 Nike Kits Ad")
