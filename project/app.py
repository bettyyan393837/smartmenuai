import streamlit as st
import pandas as pd
import pairing_module
import cart_module
import checkout

# Try import TensorFlow recommender module
try:
    import menu as tf_recommender
    embeddings = None
    embeddings = tf_recommender.load_embeddings(None)
    AI_ON = True
except Exception:
    tf_recommender = None
    embeddings = None
    AI_ON = False


# ---------------------------
# 🌼 Custom Theme (Light Yellow)
# ---------------------------
st.markdown("""
    <style>
    body {
        background-color: #FFFBEA;
    }
    .stApp {
        background-color: #FFFDF3;
    }
    .menu-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #F7EED8;
    }
    .menu-title {
        font-size: 20px;
        font-weight: 700;
        color: #4A4A4A;
    }
    .menu-price {
        color: #D4A017;
        font-size: 18px;
        font-weight: 600;
    }
    .yellow-btn button {
        background-color: #FDEFB2 !important;
        color: #5A4A00 !important;
        border-radius: 10px !important;
        border: 1px solid #E7D48A !important;
    }
    .yellow-btn button:hover {
        background-color: #F9E78A !important;
        border-color: #D8C26D !important;
    }

    /* 主区域收窄，让界面更专业 */
    .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1300px;
        margin: auto;
    }
    </style>
""", unsafe_allow_html=True)



# ---------------------------
# Load Menu
# ---------------------------
menu = pairing_module.load_menu("menu.csv")
CATEGORIES = ["Main", "Soup", "Drink", "Dessert", "Side"]


# ---------------------------
# Streamlit UI Config
# ---------------------------
st.set_page_config(page_title="SmartMenuAI", layout="wide")
st.title("🍽️ SmartMenuAI – Modern Web UI")

# ---------------------------
# CLEAN & FIXED NAVBAR (SELECTIVE WIDTHS)
# ---------------------------

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

def switch_page(p):
    st.session_state["page"] = p
    st.rerun()

# --- CSS ---
st.markdown("""
<style>
/* base style */
.nav-btn > button {
    background-color: white !important;
    border: 1.5px solid #E5D9A6 !important;
    color: #4A4A4A !important;
    padding: 4px 10px !important;
    border-radius: 10px !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    height: 40px !important;
    white-space: nowrap !important;
}

/* default width buttons (Home, Menu, Cart) */
.nav-small > button {
    width: 125px !important;
}

/* wider AI button */
.nav-ai > button {
    width: 160px !important;  }

/* wider Checkout button */
.nav-checkout > button {
    width: 160px !important;
}
.nav-btn > button:hover {
    background-color: #FFF3B0 !important;
    border-color: #D6C67A !important;
}

.nav-active > button {
    background-color: #FFE27A !important;
    border-color: #C4A300 !important;
    color: #4A3500 !important;
}
</style>
""", unsafe_allow_html=True)


# -------- Render Navbar Row -------- #
row = st.columns([1,1,1,1,1])

# Home (small)
with row[0]:
    cls = "nav-btn nav-small nav-active" if st.session_state["page"] == "Home" else "nav-btn nav-small"
    with st.container():
        if st.button("🏠 Home", key="nav_home"):
            switch_page("Home")

# Menu (small)
with row[1]:
    cls = "nav-btn nav-small nav-active" if st.session_state["page"] == "Menu" else "nav-btn nav-small"
    with st.container():
        if st.button("📋 Menu", key="nav_menu"):
            switch_page("Menu")

# AI (wide)
with row[2]:
    cls = "nav-btn nav-ai nav-active" if st.session_state["page"] == "AI" else "nav-btn nav-ai"
    with st.container():
        if st.button("🤖 AI Recommendation", key="nav_ai"):
            switch_page("AI")

# Cart (small)
with row[3]:
    cls = "nav-btn nav-small nav-active" if st.session_state["page"] == "Cart" else "nav-btn nav-small"
    with st.container():
        if st.button("🛒 Cart", key="nav_cart"):
            switch_page("Cart")

# Checkout (wide)
with row[4]:
    cls = "nav-btn nav-checkout nav-active" if st.session_state["page"] == "Checkout" else "nav-btn nav-checkout"
    with st.container():
        if st.button("💰 Checkout", key="nav_checkout"):
            switch_page("Checkout")
# ---------------------------
# PAGE ROUTING
# ---------------------------
page = st.session_state["page"]


# ---------------------------
# CART LOGIC (shared across pages)
# ---------------------------
cart = st.session_state.setdefault("cart", [])

def show_cart_sidebar():
    st.sidebar.header("🛒 Cart")

    if len(cart) == 0:
        st.sidebar.write("Your cart is empty.")
    else:
        for it in cart_module.get_cart_items(cart):
            name = it.get("name")
            qty = it.get("quantity")
            price = it.get("price")
            st.sidebar.write(f"{name} x{qty} — RM {price}")

            if st.sidebar.button(f"Remove {name}", key=f"rm_{name}"):
                cart_module.remove_item(cart, name)
                st.rerun()

        total = cart_module.get_cart_total(cart)
        st.sidebar.success(f"Total: RM {total:.2f}")

        if st.sidebar.button("Clear Cart"):
            cart.clear()
            st.rerun()

show_cart_sidebar()



# ===========================
# PAGE 1 — HOME
# ===========================
if page == "Home":
    st.subheader("✨ Welcome to SmartMenuAI")
    st.write("Use the navigation bar above to explore menu, get AI suggestions, view cart, and checkout.")



# ===========================
# PAGE 2 — MENU
# ===========================
elif page == "Menu":
    
    st.subheader("📂 Menu Categories")

    selected_cat = st.selectbox("Select Category", CATEGORIES)

    items = [
        it for it in menu
        if it.get("category", "").lower() == selected_cat.lower()
    ]

    st.subheader(f"🍱 {selected_cat}")

    cols = st.columns(2)

    for idx, it in enumerate(items):
        with cols[idx % 2]:

            # 卡片
            html = f"""
<div class="menu-card">
    <div class="menu-title">{it['name']}</div>
    <div class="menu-price">RM {it['price']}</div>
    <div style="height: 8px;"></div>
</div>
"""
            st.markdown(html, unsafe_allow_html=True)

            # Add 按钮
            st.markdown('<div class="yellow-btn">', unsafe_allow_html=True)

            if st.button(f"Add: {it['name']}", key=f"add_{it['id']}"):
                cart_module.add_item(cart, it)
                st.success(f"Added {it['name']}")
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



# ===========================
# PAGE 3 — AI RECOMMENDATION
# ===========================
elif page == "AI":

    st.subheader("🤖 AI Recommendation")

    if not AI_ON:
        st.warning("AI model not available. Install TensorFlow and menu.py to enable.")
    else:
        mode = st.selectbox("AI Mode", [
            "Pairing (Cart)",
            "Preference Text",
            "Similar to an Item",
            "Keyword Search"
        ])

        top_k = st.number_input("Top K Results", min_value=1, max_value=10, value=3)

        user_text = st.text_input("Input text (if needed):")

        if st.button("Run AI Recommendation"):
            if mode == "Pairing (Cart)":
                cart_data = [{"id": i.get("id"), "qty": i.get("quantity", 1)} for i in cart_module.get_cart_items(cart)]
                results = pairing_module.recommend_for_cart(cart_data, menu, top_n=top_k)

            elif mode == "Preference Text":
                if not user_text.strip():
                    st.error("Please enter preference text.")
                    st.stop()
                results = tf_recommender.recommend_from_preference(user_text, menu, embeddings, top_k)

            elif mode == "Similar to an Item":
                if len(cart) == 0:
                    st.error("Add an item to cart first.")
                    st.stop()
                first_item = cart[0]
                results = tf_recommender.recommend_similar_item(first_item, menu, embeddings, top_k)

            elif mode == "Keyword Search":
                if not user_text.strip():
                    st.error("Enter keyword for searching.")
                    st.stop()
                results = tf_recommender.semantic_search(user_text, menu, embeddings, top_k)

            else:
                results = []

            st.success("Recommendation Results:")

            for it in results:
                st.write(f"✔ {it.get('name')} — RM {it.get('price')}")
                if st.button(f"Add {it.get('name')}", key=f"ai_add_{it.get('id')}"):
                    cart_module.add_item(cart, it)
                    st.rerun()



# ===========================
# PAGE 4 — CART
# ===========================
elif page == "Cart":
    st.subheader("🛒 Your Cart")

    if len(cart) == 0:
        st.info("Your cart is empty.")
    else:
        for it in cart_module.get_cart_items(cart):
            st.write(f"{it['name']} x{it['quantity']} — RM {it['price']}")

        st.success(f"Total: RM {cart_module.get_cart_total(cart):.2f}")



# ===========================
# PAGE 5 — CHECKOUT
# ===========================
elif page == "Checkout":

    st.subheader("💰 Checkout")

    if st.button("Generate Receipt"):
        receipt = checkout.generate_receipt(cart)
        total = checkout.calculate_total(cart)
        st.code(receipt)
        st.success(f"Total: RM {total:.2f}")

