import sys; print("PYTHON=", sys.executable)
import os
import tkinter as tk
from tkinter import ttk, messagebox
import sys; print("PYTHON=", sys.executable)

import pairing_module
import cart_module
import checkout

try:
    import menu as tf_recommender
    TF_AVAILABLE = True
except Exception:
    tf_recommender = None
    TF_AVAILABLE = False

CATEGORIES = ["Main", "Soup", "Drink", "Dessert", "Side"]


class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartMenuAI - Ordering")
        self.root.geometry("1100x600")
        self.root.minsize(1000, 580)

        self.cart = []
        self.menu = []
        self.current_category = CATEGORIES[0]
        self.current_items = []
        self.selected_item = None

        self.embeddings = None

        self._load_menu()
        self._load_embeddings()

        self._build_ui()
        self._set_category(self.current_category)

    def _load_menu(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "menu.csv")
        self.menu = pairing_module.load_menu(csv_path)

    def _load_embeddings(self):
        if (not TF_AVAILABLE) or (tf_recommender is None):
            self.embeddings = None
            return
        try:
            self.embeddings = tf_recommender.load_embeddings(self.menu)
        except Exception:
            self.embeddings = None

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Category.TButton",
            font=("Segoe UI", 10),
            padding=(10, 6),
            anchor="w"
        )

        style.configure(
            "CategoryActive.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 6),
            anchor="w",
            background="#4f46e5",
            foreground="white"
        )
        # ====== Header ======
        top = ttk.Frame(self.root, padding=(12, 10))
        top.pack(fill="x")

        title = ttk.Label(
            top,
            text="SmartMenuAI",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(side="left")

        actions = ttk.Frame(top)
        actions.pack(side="right")

        ttk.Button(actions, text="AI Recommend", command=self.open_ai_window).pack(side="left", padx=4)
        ttk.Button(actions, text="Open Cart", command=self.open_cart_window).pack(side="left", padx=4)
        ttk.Button(actions, text="Checkout", command=self.checkout_popup).pack(side="left", padx=4)


        self.status_var = tk.StringVar()

        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#f3f4f6",
            fg="#333",
            anchor="w",
            padx=12,
            pady=6
        )
        status.pack(fill="x")


        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0)  # Categories
        main.columnconfigure(1, weight=3)  # Menu（主区域）
        main.columnconfigure(2, weight=2)  # Item Detail
        main.rowconfigure(0, weight=1)
        left = ttk.Frame(main, padding=10)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))

        mid = ttk.Frame(main, padding=10)
        mid.grid(row=0, column=1, sticky="nsew", padx=(0, 8))


        ttk.Label(
            left,
            text="Categories",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.category_buttons = {}

        for cat in CATEGORIES:
            btn = ttk.Button(
                left,
                text=cat,
                width=18,
                style="Category.TButton",
                command=lambda c=cat: self._set_category(c)
            )
            btn.pack(fill="x", pady=4)
            self.category_buttons[cat] = btn

        ttk.Label(mid, text="Menu", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.menu_list = tk.Listbox(
            mid,
            height=18,
            font=("Segoe UI", 10),
            activestyle="none",
            selectbackground="#4f46e5",
            selectforeground="white",
            relief="flat",
            highlightthickness=0
        )

        self.menu_list.pack(fill="both", expand=True, pady=6)
        self.menu_list.bind("<<ListboxSelect>>", self._on_select)

        self.add_btn = ttk.Button(mid, text="Add to Cart", command=self.add_selected_to_cart)
        self.add_btn.pack(pady=6)
        self.add_btn.state(["disabled"])

        right = ttk.Frame(main)
        right.grid(row=0, column=2, sticky="nsew")

        ttk.Label(right, text="Item Detail", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.detail = tk.Text(
            right,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#fafafa",
            relief="flat",
            highlightthickness=0
        )

        self.detail.pack(fill="both", expand=True, pady=6)
        self.detail.configure(state="disabled")

        self._refresh_status()

    def _refresh_status(self):
        try:
            total = cart_module.get_cart_total(self.cart)
        except Exception:
            total = 0.0

        ai_on = (TF_AVAILABLE and tf_recommender is not None and self.embeddings is not None)
        ai_text = "AI: ON" if ai_on else "AI: OFF"

        self.status_var.set(
            f"Category: {self.current_category}   |   Cart items: {len(self.cart)}   |   Total: RM {total:.2f}   |   {ai_text}"
        )

    def _set_category(self, category):
        self.current_category = category
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.configure(style="CategoryActive.TButton")
            else:
                btn.configure(style="Category.TButton")
        self.current_items = [
            it for it in self.menu
            if str(it.get("category", "")).strip().lower() == category.lower()
        ]
        self.selected_item = None

        self.menu_list.delete(0, tk.END)
        for it in self.current_items:
            name = it.get("name", "")
            price = it.get("price", 0)
            self.menu_list.insert(tk.END, f"{name}   (RM {price})")

        self._show_detail(None)
        self.add_btn.state(["disabled"])
        self._refresh_status()

    def _on_select(self, _evt=None):
        idx = self.menu_list.curselection()
        if not idx:
            self.selected_item = None
            self._show_detail(None)
            self.add_btn.state(["disabled"])
            return

        it = self.current_items[idx[0]]
        self.selected_item = it
        self._show_detail(it)
        self.add_btn.state(["!disabled"])

    def _show_detail(self, it):
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)

        if not it:
            self.detail.insert(tk.END, "Select an item from the menu to see details.")
        else:
            dish_id = it.get("id", "")
            name = it.get("name", "")
            category = it.get("category", "")
            price = it.get("price", 0)
            desc = it.get("description", "")
            spicy = it.get("spicy", "")
            cold = it.get("cold", "")

            self.detail.insert(tk.END, f"ID: {dish_id}\n")
            self.detail.insert(tk.END, f"Name: {name}\n")
            self.detail.insert(tk.END, f"Category: {category}\n")
            self.detail.insert(tk.END, f"Price: RM {price}\n\n")

            if desc:
                self.detail.insert(tk.END, f"Description:\n{desc}\n\n")

            self.detail.insert(tk.END, f"Spicy: {spicy}\n")
            self.detail.insert(tk.END, f"Cold: {cold}\n")

        self.detail.configure(state="disabled")

    def add_selected_to_cart(self):
        if not self.selected_item:
            return

        dish_id = str(self.selected_item.get("id", "")).strip()
        item = pairing_module.find_dish(self.menu, dish_id)
        if not item:
            messagebox.showerror("Error", "Item not found by ID.")
            return

        cart_module.add_item(self.cart, item)
        self._refresh_status()
        messagebox.showinfo("Added", f"Added to cart: {item.get('name', '')}")

    def open_ai_window(self):
        win = tk.Toplevel(self.root)
        win.title("AI Recommendation")
        win.geometry("720x520")

        if (not TF_AVAILABLE) or (tf_recommender is None):
            ttk.Label(win, text="AI not available in this environment.", font=("Segoe UI", 12)).pack(pady=18)
            ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)
            return

        if self.embeddings is None:
            try:
                ttk.Label(win, text="Loading AI model (first time may be slow)...", font=("Segoe UI", 11)).pack(pady=12)
                win.update()
                self.embeddings = tf_recommender.load_embeddings(self.menu)
            except Exception as e:
                ttk.Label(win, text=f"AI load failed:\n{e}", font=("Segoe UI", 11)).pack(pady=18)
                ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)
                return


        top = ttk.Frame(win)
        top.pack(fill="x", padx=12, pady=10)
        mode_var = tk.StringVar(value="Preference Text")
        modes = ["Preference Text", "Similar to Selected Item", "Keyword Search"]
        ttk.Label(top, text="Mode:").pack(side="left")
        ttk.Combobox(top, textvariable=mode_var, values=modes, state="readonly", width=24).pack(side="left", padx=8)

        ttk.Label(top, text="Top K:").pack(side="left", padx=(10, 0))
        k_var = tk.StringVar(value="3")
        ttk.Entry(top, textvariable=k_var, width=6).pack(side="left", padx=6)

        input_frame = ttk.Frame(win)
        input_frame.pack(fill="x", padx=12)

        ttk.Label(input_frame, text="Input:").pack(side="left")
        input_entry = ttk.Entry(input_frame, width=60)
        input_entry.pack(side="left", padx=8, fill="x", expand=True)

        result = tk.Listbox(win, height=16)
        result.pack(fill="both", expand=True, padx=12, pady=12)

        def run():
            result.delete(0, tk.END)

            try:
                top_k = int(k_var.get().strip())
            except Exception:
                top_k = 3

            mode = mode_var.get()
            text = input_entry.get().strip()


            if mode == "Preference Text":
                if not text:
                    messagebox.showwarning("Missing", "Please enter preference text.")
                    return
                recs = tf_recommender.recommend_from_preference(text, self.menu, self.embeddings, top_k)

            elif mode == "Similar to Selected Item":
                if not self.selected_item:
                    messagebox.showwarning("Missing", "Please select an item in the menu first.")
                    return
                recs = tf_recommender.recommend_similar_item(self.selected_item, self.menu, self.embeddings, top_k)

            elif mode == "Keyword Search":
                if not text:
                    messagebox.showwarning("Missing", "Please enter keyword(s).")
                    return
                recs = tf_recommender.semantic_search(text, self.menu, self.embeddings, top_k)

            else:
                return

            for it in recs:
                result.insert(tk.END, f"{it.get('name')}   (RM {it.get('price')})")

        def add_selected():
            sel = result.curselection()
            if not sel:
                return
            line = result.get(sel[0])
            name = line.split("   (RM")[0].strip()

            found = None
            for it in self.menu:
                if str(it.get("name", "")).strip().lower() == name.lower():
                    found = it
                    break

            if not found:
                messagebox.showerror("Error", "Item not found in menu.")
                return

            cart_module.add_item(self.cart, found)
            self._refresh_status()
            messagebox.showinfo("Added", f"Added to cart: {found.get('name', '')}")

        btn_row = ttk.Frame(win)
        btn_row.pack(pady=6)
        ttk.Button(btn_row, text="Run", command=run).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Add Selected to Cart", command=add_selected).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Close", command=win.destroy).pack(side="left", padx=6)

    def open_cart_window(self):
        win = tk.Toplevel(self.root)
        win.title("Cart")
        win.geometry("600x600")

        listbox = tk.Listbox(win, height=16)
        listbox.pack(fill="both", expand=True, padx=12, pady=12)

        total_var = tk.StringVar()
        ttk.Label(win, textvariable=total_var, font=("Segoe UI", 11, "bold")).pack(pady=6)

        # ====== Recommendation Section ======
        ttk.Label(
            win,
            text="Recommended for You",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=12, pady=(10, 4))

        rec_list = tk.Listbox(win, height=6)
        rec_list.pack(fill="x", padx=12, pady=(0, 8))
        rec_list.bind("<Double-Button-1>", lambda e: add_selected_recommendation())

        btn_row = ttk.Frame(win)
        btn_row.pack(pady=6)

        # ====== Functions ======
        def add_selected_recommendation():
            sel = rec_list.curselection()
            if not sel:
                messagebox.showwarning("No selection", "Please select a recommended item.")
                return

            line = rec_list.get(sel[0])
            name = line.split("   (RM")[0].strip()

            found = None
            for it in self.menu:
                if it.get("name", "").lower() == name.lower():
                    found = it
                    break

            if not found:
                messagebox.showerror("Error", "Item not found in menu.")
                return

            cart_module.add_item(self.cart, found)
            refresh()
            messagebox.showinfo("Added", f"Added to cart: {found.get('name')}")

        def refresh():
            listbox.delete(0, tk.END)
            items = cart_module.get_cart_items(self.cart)

            for it in items:
                name = it.get("name", "")
                price = float(it.get("price", 0))
                qty = int(it.get("quantity", 1))
                listbox.insert(tk.END, f"{name}  x{qty}   (RM {price} each)")

            total = cart_module.get_cart_total(self.cart)
            total_var.set(f"Total: RM {total:.2f}")
            self._refresh_status()

            # ====== Refresh Recommendations ======
            rec_list.delete(0, tk.END)


            cart_for_pairing = [
                 {"id": it.get("id"), "qty": int(it.get("quantity", 1))}
                for it in items
             ]

            recs = pairing_module.recommend_for_cart(
                cart_for_pairing,
                self.menu,
                top_n=3
                )

            for r in recs:
                rec_list.insert(
                    tk.END,
                    f"{r.get('name')}   (RM {r.get('price')})"
                )

        def remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            line = listbox.get(sel[0])
            name = line.split("  x")[0].strip()
            cart_module.remove_item(self.cart, name)
            refresh()

        def clear_cart():
            self.cart.clear()
            refresh()

        # ====== Buttons ======
        ttk.Button(btn_row, text="Add Selected Recommendation",
                   command=add_selected_recommendation).pack(side="left", padx=6)

        ttk.Button(btn_row, text="Remove Selected",
                   command=remove_selected).pack(side="left", padx=6)

        ttk.Button(btn_row, text="Clear Cart",
                   command=clear_cart).pack(side="left", padx=6)

        ttk.Button(btn_row, text="Checkout",
                   command=self.checkout_popup).pack(side="left", padx=6)

        ttk.Button(btn_row, text="Close",
                   command=win.destroy).pack(side="left", padx=6)

        refresh()

        def remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            line = listbox.get(sel[0])
            name = line.split("  x")[0].strip()
            ok = cart_module.remove_item(self.cart, name)
            if not ok:
                messagebox.showerror("Error", "Item not found in cart.")
            refresh()

        def clear_cart():
            self.cart.clear()
            refresh()

        ttk.Button(btn_row, text="Remove Selected", command=remove_selected).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Clear Cart", command=clear_cart).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Checkout", command=self.checkout_popup).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Close", command=win.destroy).pack(side="left", padx=6)

        refresh()

    def checkout_popup(self):
        if not self.cart:
            messagebox.showwarning("Empty", "Your cart is empty.")
            return

        win = tk.Toplevel(self.root)
        win.title("Receipt")
        win.geometry("680x520")

        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=12, pady=12)

        try:
            receipt = checkout.generate_receipt(self.cart)
            total = checkout.calculate_total(self.cart)
        except Exception as e:
            receipt = f"Checkout error:\n{e}"
            total = 0.0

        txt.insert(tk.END, receipt)
        txt.insert(tk.END, f"\n\nTotal: RM {total:.2f}")
        txt.configure(state="disabled")

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)
        self._refresh_status()


def main():
    root = tk.Tk()
    app = OrderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
