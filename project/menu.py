# tf_recommender.py
"""
AI Recommendation Module for SmartMenuAI
----------------------------------------
这部分是你的分工：使用 TensorFlow 的预训练语义模型（Google USE）
根据用户输入的“喜好 / 口味描述”，找出语义上最相近的菜品并进行推荐。

核心思路：
1. 启动时加载菜单（main.py 负责）；
2. 在本模块中，用 TF Hub 的 Universal Sentence Encoder (multilingual) 为每道菜生成 embedding 向量；
3. 用户在 UI 中输入“自己现在想吃什么样的东西”（关键词 / 句子）；
4. 本模块把这句话也编码成向量；
5. 通过余弦相似度，找出与该向量最接近的若干道菜；
6. 返回菜品列表给 main.py 的 UI 层显示。
"""

from typing import List, Dict
import tensorflow_text as text
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

# 全局缓存预训练模型，避免重复加载
_use_model = None


def _load_use_model():
    """
    加载 Google 预训练好的语义模型（Universal Sentence Encoder，多语言版）。
    只加载一次，后续调用直接复用。
    """
    global _use_model
    if _use_model is None:
        # 多语言模型：支持中英文混合描述
        _use_model = hub.load(
            "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
        )
    return _use_model


def _build_item_text(item: Dict) -> str:
    """
    将一条菜单记录转换成一段简短的文本描述，作为语义模型的输入。

    你目前的 menu.csv 列大概有：
    - id
    - name
    - price
    - category
    - subcategory
    """
    name = item.get("name", "")
    category = item.get("category", "")
    subcat = item.get("subcategory", "")
    price = item.get("price", "")
    desc = item.get("description", "")

    if desc:
        # 有 description：用描述 + 基本信息
        text = (
            f"{name}. {desc}. "
            f"Category: {category}, {subcat}. Price around {price} ringgit."
        )
    else:
        # 没写 description：退回原来的写法
        text = f"{name}. Category: {category}, {subcat}. Price around {price} ringgit."

    return text


def load_embeddings(menu: List[Dict]) -> np.ndarray:
    """
    为整个菜单生成语义向量矩阵。
    main.py 会在程序启动时调用：
        embeddings = tf_recommender.load_embeddings(menu)

    :param menu: 菜单列表，每一项是一个 dict，包含 name/category/subcategory/price 等字段
    :return: embeddings，形状为 (N, 512) 的 NumPy 数组，
             其中第 i 行对应 menu[i] 的语义向量
    """
    model = _load_use_model()

    # 为每个菜单项构造一条文本描述
    texts = [_build_item_text(item) for item in menu]  # len = N

    # 调用 USE 模型得到句子 embedding（TensorFlow Tensor）
    emb_tensor = model(texts)           # shape: (N, 512)

    # 转成 NumPy 数组便于后续数值运算
    emb_array = emb_tensor.numpy()      # np.ndarray, shape: (N, 512)

    return emb_array


def _cosine_similarity(query_vec: np.ndarray,
                       item_matrix: np.ndarray) -> np.ndarray:
    """
    计算 query_vec 与 item_matrix 中每一行之间的余弦相似度。

    :param query_vec: 形状为 (D,) 的向量（比如 512 维）
    :param item_matrix: 形状为 (N, D) 的矩阵，每一行是一个菜品的 embedding
    :return: 形状为 (N,) 的相似度数组，相似度范围大致在 [-1, 1] 之间
    """
    # 确保 query_vec 是 (1, D)
    q = query_vec.reshape(1, -1)               # (1, D)
    m = item_matrix                            # (N, D)

    # 点积 (N,)
    dots = np.sum(m * q, axis=1)

    # 范数 (欧氏长度)
    q_norm = np.linalg.norm(q)
    m_norm = np.linalg.norm(m, axis=1) + 1e-8  # 防止除以 0

    sims = dots / (q_norm * m_norm)
    return sims


def recommend_from_preference(
    preference_text: str,
    menu: List[Dict],
    embeddings: np.ndarray,
    top_k: int = 3
) -> List[Dict]:
    """
    这是你描述的核心功能：
    当用户“不知道吃什么”的时候，点击推荐模块，
    输入自己的喜好 / 口味偏好（例如：
        - "spicy chicken with cheese"
        - "想吃一点清淡的汤面"
        - "cold drink not too sweet"
    ）
    本函数使用 TensorFlow 预训练语义模型，把这段描述编码成向量，
    然后在 embedding 空间中寻找最相近的菜品，并返回 top_k 个结果。

    :param preference_text: 用户输入的偏好描述字符串
    :param menu: 完整菜单（list[dict]）
    :param embeddings: 对应菜单的 embedding 矩阵 (N, 512)
    :param top_k: 返回几个推荐菜品
    :return: 推荐的菜品列表（list[dict]），不负责打印，由 UI 层展示
    """
    if not menu or embeddings is None or len(embeddings) == 0:
        return []

    model = _load_use_model()

    # 将用户输入的偏好描述编码成一个 embedding 向量
    # model([...]) 接受一个句子列表，这里只有一个
    pref_emb_tensor = model([preference_text])    # shape: (1, 512)
    pref_vec = pref_emb_tensor.numpy()[0]         # 取出 (512,) 向量

    # 计算与所有菜品的语义相似度
    sims = _cosine_similarity(pref_vec, embeddings)  # (N,)

    # 按相似度从高到低排序，取出前 top_k 个索引
    sorted_idx = np.argsort(-sims)

    results: List[Dict] = []
    for idx in sorted_idx[:top_k]:
        results.append(menu[idx])

    return results


# 如果你还保留 main.py 里的 “Similar to a selected item / Search by keyword” 菜单，
# 可以额外提供这两个接口，保持兼容：

def recommend_similar_item(
    base_item: Dict,
    menu: List[Dict],
    embeddings: np.ndarray,
    top_k: int = 3
) -> List[Dict]:
    """
   （可选）根据“已选中的某一道菜”推荐相似菜品。
    可以给 main.py 用在：
        1. 用户先选一项菜单
        2. 再根据该菜品做相似推荐
    """
    if not menu or embeddings is None or len(embeddings) == 0:
        return []

    base_id = base_item.get("id")
    base_index = None
    for i, item in enumerate(menu):
        if item.get("id") == base_id:
            base_index = i
            break

    if base_index is None:
        return []

    base_vec = embeddings[base_index]
    sims = _cosine_similarity(base_vec, embeddings)
    sorted_idx = np.argsort(-sims)

    results: List[Dict] = []
    for idx in sorted_idx:
        if idx == base_index:
            continue  # 跳过自己
        results.append(menu[idx])
        if len(results) >= top_k:
            break

    return results


def semantic_search(
    query: str,
    menu: List[Dict],
    embeddings: np.ndarray,
    top_k: int = 3
) -> List[Dict]:
    """
    （兼容版）如果 main.py UI 写的是“语义搜索 / keyword search”，
    可以直接复用 recommend_from_preference 的逻辑。

    query 本质上就是用户的偏好描述。
    """
    return recommend_from_preference(query, menu, embeddings, top_k=top_k)


if __name__ == "__main__":
    # ⚠ 只是测试用的简单菜单，真正项目里要从 CSV 读
    demo_menu = [
        {"id": 1, "name": "Spicy Chicken Rice", "price": 12.9, "category": "Main", "subcategory": "Rice"},
        {"id": 2, "name": "Curry Laksa", "price": 13.5, "category": "Main", "subcategory": "Noodles"},
        {"id": 3, "name": "Iced Lemon Tea", "price": 5.0, "category": "Drink", "subcategory": "Cold Drink"},
        {"id": 4, "name": "Hot Green Tea", "price": 4.5, "category": "Drink", "subcategory": "Hot Drink"},
        {"id": 5, "name": "Chocolate Cake", "price": 8.0, "category": "Dessert", "subcategory": "Cake"},
    ]

    print("Loading embeddings...")
    embs = load_embeddings(demo_menu)

    while True:
        text = input("\nDescribe what you want to eat (or 'q' to quit): ")
        if text.lower() == "q":
            break

        recs = recommend_from_preference(text, demo_menu, embs, top_k=3)
        print("Recommendations:")
        for item in recs:
            print(f"- {item['name']} (RM {item['price']})  [{item['category']}/{item['subcategory']}]")
