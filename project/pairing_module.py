# 功能：根据购物车内容推荐搭配菜品（支持 category + subcategory + 价格百分位映射）
import numpy as np
import csv

# 小工具：根据 id 找菜单项
def find_dish(menu, dish_id):
    return next((d for d in menu if d["id"] == dish_id), None)

# 分析购物车：统计大类和子类
def analyze_cart(cart, menu):
    category_count = {}
    subcategory_count = {}

    for item in cart:
        dish = find_dish(menu, item["id"])
        if not dish:
            continue

        qty = item.get("qty", 1)
        cat = dish.get("category")
        sub = dish.get("subcategory")

        if cat:
            category_count[cat] = category_count.get(cat, 0) + qty
        if sub:
            subcategory_count[sub] = subcategory_count.get(sub, 0) + qty

    return category_count, subcategory_count


# 计算单个菜在“该类别价格分布中的百分位”
def price_percentile_in_subcategory(dish_price, prices_in_subcategory):
    if not prices_in_subcategory:
        return 0.5  # 没数据就给中位数

    sorted_prices = sorted(prices_in_subcategory)
    # 找到 dish_price 在排序列表中的位置（找第一个 >= 的位置）
    idx = 0
    for i, p in enumerate(sorted_prices):
        if dish_price <= p:
            idx = i
            break
    else:
        idx = len(sorted_prices) - 1

    # 百分位：索引 / (总长度 - 1)，防止除 0
    if len(sorted_prices) == 1:
        return 1.0
    percentile = idx / (len(sorted_prices) - 1)
    return float(percentile)


# 计算用户当前“整体价格偏好百分位”（0~1）
def compute_user_price_preference(cart, menu):
    percentiles = []

    # 按 subcategory 分组价格
    subcategory_prices = {}
    for d in menu:
        sub = d.get("subcategory")
        if not sub:
            continue
        subcategory_prices.setdefault(sub, []).append(d["price"])

    for item in cart:
        dish = find_dish(menu, item["id"])
        if not dish:
            continue

        sub = dish.get("subcategory")
        price = dish.get("price")
        if sub is None or price is None:
            continue

        prices_in_sub = subcategory_prices.get(sub, [])
        p = price_percentile_in_subcategory(price, prices_in_sub)
        percentiles.append(p)

    if not percentiles:
        return 0.5

    return float(np.mean(percentiles))

# 根据购物车类别情况，决定要推荐哪些大类
def decide_recommended_categories(category_count):
    recommended_categories = set()

    if category_count.get("Main", 0) > 0:
        # 点了主菜 → 推荐 汤 / 小吃 / 饮品
        recommended_categories.update(["Soup", "Side", "Drink"])

    if category_count.get("Soup", 0) > 0:
        # 点了汤 → 再推荐 主菜 / 小吃
        recommended_categories.update(["Main", "Side"])

    if category_count.get("Drink", 0) > 0:
        # 点了饮品 → 推荐 甜品
        recommended_categories.add("Dessert")

    # 如果啥都没有，给一个默认推荐方向
    if not recommended_categories:
        recommended_categories.update(["Soup", "Side", "Drink"])

    return recommended_categories


# 核心函数：根据用户“价格偏好百分位”在各类中映射价格，并选出最接近的菜
def recommend_for_cart(cart, menu, top_n=3):
    # =========== 情况 0：购物车为空，随便推荐几个基础菜 ===========
    if not cart:
        # 这里可以稍微智能一点：优先主菜 + 汤 + 饮料
        default_categories = ["Main", "Soup", "Drink"]
        rec = []
        for cat in default_categories:
            for d in menu:
                if d.get("category") == cat and d not in rec:
                    rec.append(d)
                    break
        # 如果还不够 top_n，就从剩下菜单里补
        for d in menu:
            if len(rec) >= top_n:
                break
            if d not in rec:
                rec.append(d)
        return rec[:top_n]

    # =========== Step 1：分析购物车类别和子类 ===========
    category_count, subcategory_count = analyze_cart(cart, menu)
    used_subcats = set(subcategory_count.keys())

    # =========== Step 2：计算用户价格偏好百分位（0~1） ===========
    user_pref_p = compute_user_price_preference(cart, menu)
    print("用户价格偏好百分位:", user_pref_p)

    # =========== Step 3：决定要推荐哪些类别 ===========
    target_categories = decide_recommended_categories(category_count)

    # 预先按类别分组所有菜，方便后面按类处理
    category_to_dishes = {}
    for d in menu:
        cat = d.get("category")
        if not cat:
            continue
        category_to_dishes.setdefault(cat, []).append(d)

    recommendations = []

    # =========== Step 4：对每个目标类别，选一到两道菜 ===========
    for cat in target_categories:
        dishes_in_cat = category_to_dishes.get(cat, [])
        if not dishes_in_cat:
            continue

        # 该类别的全部价格列表
        prices_in_cat = sorted([d["price"] for d in dishes_in_cat])

        if not prices_in_cat:
            continue

        # 把“用户百分位”映射到这个类别的价格分布上
        # 例如 p=0.8，而该类有5个价格 → index = round(0.8 * 4) ≈ 3 → 选择第3个价格
        idx = int(round(user_pref_p * (len(prices_in_cat) - 1)))
        target_price = prices_in_cat[idx]

        # 在该类中寻找“价格最接近 target_price 的菜”
        best_dish = None
        best_diff = None

        for d in dishes_in_cat:
            # 如果这个菜的子类已经在购物车中出现过（例如已点过 Pizza，不再推 Pizza）
            sub = d.get("subcategory")
            if sub and sub in used_subcats and cat == "Main":
                continue

            diff = abs(d["price"] - target_price)
            if (best_diff is None) or (diff < best_diff):
                best_diff = diff
                best_dish = d

        if best_dish and best_dish not in recommendations:
            recommendations.append(best_dish)

        if len(recommendations) >= top_n:
            break

    # 如果推荐数量还不够，可以适当补齐（可选，不补也行）
    if len(recommendations) < top_n:
        for d in menu:
            if d not in recommendations:
                recommendations.append(d)
            if len(recommendations) >= top_n:
                break

    return recommendations[:top_n]

def load_menu(csv_file="menu.csv"):
    menu = []

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            price_str = row.get("price", "").strip()

            # 跳过 price 为空或非法的行
            if price_str == "":
                continue

            item = {
                "id": row.get("id"),
                "name": row.get("name"),
                "category": row.get("category"),
                "subcategory": row.get("subcategory"),
                "price": float(row.get("price"))
            }
            menu.append(item)

    return menu

# 简单测试
if __name__ == "__main__":
    menu = load_menu()

    # 用户购物车：点了一份偏贵的 Pizza
    cart = [
        {"id": "21", "qty": 1},  # Pepperoni Pizza, 22 元
        {"id": "32", "qty": 1},
        {"id": "49", "qty": 1},
        {"id": "28", "qty": 1},
        {"id": "52", "qty": 1},
        {"id": "57", "qty": 1}
    ]

    recs = recommend_for_cart(cart, menu, top_n=3)
    print("推荐结果：")
    for r in recs:
        print(f"- {r['name']} ({r['category']}, {r['subcategory']}) RM{r['price']}")
