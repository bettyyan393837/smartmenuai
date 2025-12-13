import streamlit as st
import pandas as pd
import pairing_module
import cart_module
import checkout
import os


IMAGE_BASE = "https://raw.githubusercontent.com/bettyyan393837/smartmenuai/main/images/"

def get_image_url(name):
    """自动匹配 PNG 或 JPG 图片，如果都没有则返回 None。"""
    filename = name.replace(" ", "_")

    png_url = IMAGE_BASE + filename + ".png"
    jpg_url = IMAGE_BASE + filename + ".jpg"

    # 不需要实际检查 GitHub 是否存在，Streamlit 会自动处理加载失败图
    # 但最好以 png 优先
    return png_url  # 默认返回 png

# ---------------------------
# Page Routing
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

def go(page_name):
    st.session_state["page"] = page_name
    st.rerun()

# ---------------------------
# Menu Categories
# ---------------------------
CATEGORIES = ["Main", "Soup", "Drink", "Dessert", "Side"]


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

       .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1300px;
        margin: auto;
    }
    </style>
""", unsafe_allow_html=True)


# ---------------------------
# Load Menu (works both locally & Streamlit Cloud)
# ---------------------------

# Try root path first (Streamlit Cloud)
possible_paths = [
    "menu.csv",                # for deployed app
    "project/menu.csv",        # for your local folder structure
    "./menu.csv",
    "./project/menu.csv"
]

csv_path = None

for p in possible_paths:
    if os.path.exists(p):
        csv_path = p
        break

if csv_path is None:
    st.error("❌ menu.csv not found in any known location!")
else:
    menu = pairing_module.load_menu(csv_path)

# 给 menu 每一项加入 image_url
for item in menu:
    item["image_url"] = get_image_url(item["name"])

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


# Cart (small)
with row[2]:
    cls = "nav-btn nav-small nav-active" if st.session_state["page"] == "Cart" else "nav-btn nav-small"
    with st.container():
        if st.button("🛒 Cart", key="nav_cart"):
            switch_page("Cart")

# Explore (small)
with row[3]:  
    cls = "nav-btn nav-small nav-active" if st.session_state["page"] == "Explore" else "nav-btn nav-small"
    with st.container():
        if st.button("🔍 Explore", key="nav_explore"):
            switch_page("Explore")

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
    <img src="{it['image_url']}" style="width:100%; border-radius:12px; margin-bottom:10px;" />
    <div class="menu-title">{it['name']}</div>
    <div class="menu-price">RM {it['price']}</div>
    <div style="height: 8px;"></div>
</div>
"""
            st.markdown(html, unsafe_allow_html=True)

            # Add 按钮
            st.markdown('<div class="yellow-btn">', unsafe_allow_html=True)

            if st.button(f"Add: {it['name']}", key=f"add_{it['id']}"):
                cart_item={
                      "id": it["id"],
                      "name": it["name"],
                      "price": float(it["price"]), 
                      "quantity": 1
                }  
                cart_module.add_item(cart, cart_item)
                st.success(f"Added {it['name']}")
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



# ============================================
#                 🛒 CART PAGE
# ============================================
elif page == "Cart":

    st.title("🛒 Your Cart")

    # 取得购物车内容
    cart_items = cart_module.get_cart_items(cart)

    # ------------------------------------------------
    # 显示购物车内容
    # ------------------------------------------------
    if len(cart_items) == 0:
        st.info("Your cart is empty.")
    else:
        for it in cart_items:
            name = it["name"]
            qty = it["quantity"]
            price = it["price"]
            st.write(f"**{name}** × {qty} — RM {price}")

        total = cart_module.get_cart_total(cart)
        st.success(f"Total: RM {total:.2f}")

    # 清空购物车
    if st.button("Clear Cart", key="clear_cart_btn"):
        cart.clear()
        st.rerun()

    st.write("---")

    # ============================================
    # 🤖 SMART RECOMMENDATION (TOP 3)
    # ============================================
    st.subheader("🤖 Recommended For You")

    # 推荐函数所需格式（无论购物车为空或不空都能运行）
    cart_data = [
        {"id": item["id"], "qty": item["quantity"]}
        for item in cart_items
    ]

    # 使用 pairing_module 生成 top 3 推荐
    recommendations = pairing_module.recommend_for_cart(
        cart_data,
        menu,
        top_n=3
    )

    if recommendations:
        st.write("Here are some items we recommend:")

        for rec in recommendations:
            st.write(f"✔ **{rec['name']}** — RM {rec['price']}")

            # 加入购物车按钮
            if st.button(
                f"Add {rec['name']}",
                key=f"rec_add_{rec['id']}"
            ):
                cart_module.add_item(cart, rec)
                st.success(f"Added {rec['name']} to cart!")
                st.rerun()
    else:
        st.info("No recommendations available.")

# ---------------------------
# EXPLORE PAGE
# ---------------------------
elif page == "Explore":

    st.title("🔍 Explore Menu Tools")

    # -----------------------------
    # 🔎 Search Food
    # -----------------------------
    st.subheader("🔎 Search Food")

    search_query = st.text_input("Enter a food name to search:")

    if st.button("Search", key="explore_search_btn"):
        results = [
            it for it in menu
            if search_query.lower() in it["name"].lower()
        ]

        if results:
            st.success(f"Found {len(results)} items:")
            for it in results:
                st.write(f"✔ {it['name']} — RM {it['price']}")
        else:
            st.warning("No matching food found.")

    st.write("---")

    # -----------------------------
    # 💲 Price Range Filter
    # -----------------------------
    st.subheader("💲 Filter by Price Range")

    col_min, col_max = st.columns(2)
    with col_min:
        min_price = st.number_input("Min price", min_value=0.0, value=0.0)
    with col_max:
        max_price = st.number_input("Max price", min_value=0.0, value=50.0)

    if st.button("Filter", key="explore_filter_btn"):
        results = [
            it for it in menu
            if float(it["price"]) >= min_price and float(it["price"]) <= max_price
        ]

        if results:
            st.success(f"Found {len(results)} items:")
            for it in results:
                st.write(f"✔ {it['name']} — RM {it['price']}")
        else:
            st.warning("No items found in this price range.")

    
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

