#James Moore
#SDEV220-50P
#Module 08 Final Project


import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class PearlStreetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pearl Street Games & Coffee System")
        self.root.geometry("1100x850")
        
        self.db_path = "pearl_street_final.db"
        self.init_db()

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(expand=True, fill="both")

        self.inventory_tab = ttk.Frame(self.tabs)
        self.sales_tab = ttk.Frame(self.tabs)
        self.loyalty_tab = ttk.Frame(self.tabs)
        
        self.tabs.add(self.inventory_tab, text=" Inventory Management ")
        self.tabs.add(self.sales_tab, text=" Point of Sale ")
        self.tabs.add(self.loyalty_tab, text=" Loyalty Program ")

        self.setup_inventory_ui()
        self.setup_sales_ui()
        self.setup_loyalty_ui()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                stock INTEGER NOT NULL,
                min_threshold INTEGER NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                phone TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                order_count INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS sales_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                items_sold TEXT,
                customer_phone TEXT)''')
            conn.commit()

    # --- INVENTORY SECTION ---
    def setup_inventory_ui(self):
        frame = tk.LabelFrame(self.inventory_tab, text="Item Details", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        self.ent_name = self.labeled_entry(frame, "Name:", 0, 0)
        self.cb_cat = ttk.Combobox(frame, values=["Coffee", "Game", "Facility"], state="readonly")
        tk.Label(frame, text="Category:").grid(row=0, column=2)
        self.cb_cat.grid(row=0, column=3, padx=5)
        self.ent_stock = self.labeled_entry(frame, "Stock:", 1, 0)
        self.ent_min = self.labeled_entry(frame, "Min Alert:", 1, 2)

        btn_f = tk.Frame(self.inventory_tab)
        btn_f.pack(fill="x", padx=10)
        tk.Button(btn_f, text="Save/Add", command=self.add_item, bg="#d4edda", width=12).pack(side="left", padx=2)
        tk.Button(btn_f, text="Update", command=self.update_item, bg="#fff3cd", width=12).pack(side="left", padx=2)
        tk.Button(btn_f, text="Delete", command=self.delete_item, bg="#f8d7da", width=12).pack(side="left", padx=2)

        self.tree_inv = ttk.Treeview(self.inventory_tab, columns=("ID", "Name", "Category", "Stock", "Min"), show="headings")
        for col in ("ID", "Name", "Category", "Stock", "Min"): self.tree_inv.heading(col, text=col)
        self.tree_inv.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree_inv.bind("<<TreeviewSelect>>", self.fill_inputs_from_selection)
        self.update_inventory_table()

    # --- SALES SECTION ---
    def setup_sales_ui(self):
        frame = tk.LabelFrame(self.sales_tab, text="New Order", padx=20, pady=20)
        frame.pack(pady=20)
        self.sale_phone = self.labeled_entry(frame, "Phone:", 0, 0)
        self.sale_cust_name = self.labeled_entry(frame, "Name:", 1, 0)
        self.sale_items = self.labeled_entry(frame, "Item IDs:", 2, 0)
        self.redeem_var = tk.BooleanVar()
        tk.Checkbutton(frame, text="Redeem 100 Pts?", variable=self.redeem_var).grid(row=3, columnspan=2)
        tk.Button(frame, text="Process Sale", command=self.process_multi_sale, bg="#cce5ff").grid(row=4, columnspan=2, sticky="ew")
        tk.Button(self.sales_tab, text="Generate Sales Report File", command=self.generate_sales_report).pack(pady=5)
        tk.Button(self.sales_tab, text="Print Inventory to Terminal", command=self.print_inv_to_terminal, bg="black", fg="white").pack(pady=5)

    # --- LOYALTY SECTION ---
    def setup_loyalty_ui(self):
        search_f = tk.Frame(self.loyalty_tab, pady=10)
        search_f.pack(fill="x", padx=10)
        tk.Label(search_f, text="Search Phone:").pack(side="left")
        self.loyalty_search = tk.Entry(search_f)
        self.loyalty_search.pack(side="left", padx=5)
        self.loyalty_search.bind("<KeyRelease>", lambda e: self.update_loyalty_table())

        # NEW DELETE CUSTOMER BUTTON
        tk.Button(search_f, text="Remove Selected Customer", command=self.delete_customer, bg="#f8d7da").pack(side="right", padx=10)

        self.tree_loyalty = ttk.Treeview(self.loyalty_tab, columns=("Name", "Phone", "Orders", "Points"), show="headings")
        for col in ("Name", "Phone", "Orders", "Points"): self.tree_loyalty.heading(col, text=col)
        self.tree_loyalty.pack(fill="both", expand=True, padx=10, pady=5)
        self.update_loyalty_table()

    # --- CORE LOGIC ---
    def delete_customer(self):
        selected = self.tree_loyalty.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a customer to remove.")
            return
        
        # Get phone number (Phone is index 1 in this treeview)
        cust_vals = self.tree_loyalty.item(selected)['values']
        phone = cust_vals[1]
        name = cust_vals[0]

        confirm = messagebox.askyesno("Confirm", f"Remove {name} ({phone}) from loyalty program?")
        if confirm:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM customers WHERE phone = ?", (phone,))
            self.update_loyalty_table()
            messagebox.showinfo("Success", "Customer removed.")

    def add_item(self):
        name, cat, s_in, m_in = self.ent_name.get().strip(), self.cb_cat.get(), self.ent_stock.get(), self.ent_min.get()
        if not name or not cat or not s_in.isdigit():
            messagebox.showerror("Error", "Check inputs."); return
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, stock FROM inventory WHERE LOWER(name)=LOWER(?) AND category=?", (name, cat))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("UPDATE inventory SET stock=stock+?, min_threshold=? WHERE id=?", (int(s_in), int(m_in), exists[0]))
            else:
                cursor.execute("INSERT INTO inventory (name,category,stock,min_threshold) VALUES (?,?,?,?)", (name,cat,int(s_in),int(m_in)))
        self.update_inventory_table(); self.clear_inputs([self.ent_name, self.ent_stock, self.ent_min], self.cb_cat); self.check_alerts()

    def process_multi_sale(self):
        p, n, items, rdm = self.sale_phone.get(), self.sale_cust_name.get(), self.sale_items.get(), self.redeem_var.get()
        if not p or not items: return
        try:
            ids = [i.strip() for i in items.split(",")]
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                if rdm:
                    cur.execute("SELECT points FROM customers WHERE phone=?", (p,))
                    res = cur.fetchone()
                    if not res or res[0] < 100:
                        messagebox.showerror("Error", "Insufficient points"); return
                    cur.execute("UPDATE customers SET points=points-100 WHERE phone=?", (p,))
                for iid in ids: cur.execute("UPDATE inventory SET stock=stock-1 WHERE id=?", (iid,))
                add_p = 0 if rdm else 10
                cur.execute("INSERT INTO customers (phone, name, order_count, points) VALUES (?, ?, 1, ?) ON CONFLICT(phone) DO UPDATE SET order_count=order_count+1, points=points+?", (p, n, add_p, add_p))
                cur.execute("INSERT INTO sales_log (timestamp, items_sold, customer_phone) VALUES (?,?,?)", (datetime.now().strftime("%Y-%m-%d %H:%M"), items, p))
            self.update_inventory_table(); self.update_loyalty_table(); self.clear_inputs([self.sale_phone, self.sale_cust_name, self.sale_items]); self.redeem_var.set(False)
            messagebox.showinfo("Success", "Order Processed!"); self.check_alerts()
        except Exception as e: messagebox.showerror("Error", str(e))

    # --- REFRESH & UI HELPERS ---
    def update_inventory_table(self):
        for i in self.tree_inv.get_children(): self.tree_inv.delete(i)
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute("SELECT * FROM inventory"): self.tree_inv.insert("", "end", values=row)

    def update_loyalty_table(self):
        search = f"%{self.loyalty_search.get()}%"
        for i in self.tree_loyalty.get_children(): self.tree_loyalty.delete(i)
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute("SELECT name, phone, order_count, points FROM customers WHERE phone LIKE ?", (search,)): 
                self.tree_loyalty.insert("", "end", values=row)

    def print_inv_to_terminal(self):
        print(f"\n--- PEARL STREET INVENTORY ---")
        with sqlite3.connect(self.db_path) as conn:
            for r in conn.execute("SELECT * FROM inventory"): print(r)

    def generate_sales_report(self):
        fn = f"Sales_{datetime.now().strftime('%Y%m%d')}.txt"
        with sqlite3.connect(self.db_path) as conn:
            logs = conn.execute("SELECT * FROM sales_log").fetchall()
            with open(fn, "w") as f:
                for l in logs: f.write(f"{l}\n")
        messagebox.showinfo("Done", f"Saved as {fn}")

    def update_item(self):
        sel = self.tree_inv.selection()
        if not sel: return
        iid = self.tree_inv.item(sel)['values'][0]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE inventory SET name=?, category=?, stock=?, min_threshold=? WHERE id=?", (self.ent_name.get(), self.cb_cat.get(), int(self.ent_stock.get()), int(self.ent_min.get()), iid))
        self.update_inventory_table()

    def delete_item(self):
        sel = self.tree_inv.selection()
        if sel:
            iid = self.tree_inv.item(sel)['values'][0]
            with sqlite3.connect(self.db_path) as conn: conn.execute("DELETE FROM inventory WHERE id=?", (iid,))
            self.update_inventory_table()

    def fill_inputs_from_selection(self, e):
        sel = self.tree_inv.selection()
        if sel:
            v = self.tree_inv.item(sel)['values']
            self.clear_inputs([self.ent_name, self.ent_stock, self.ent_min], self.cb_cat)
            self.ent_name.insert(0, v[1]); self.cb_cat.set(v[2]); self.ent_stock.insert(0, v[3]); self.ent_min.insert(0, v[4])

    def labeled_entry(self, parent, label, r, c):
        tk.Label(parent, text=label).grid(row=r, column=c, padx=5, sticky="e")
        ent = tk.Entry(parent); ent.grid(row=r, column=c+1, padx=5, pady=2); return ent

    def clear_inputs(self, es, c=None):
        for e in es: e.delete(0, tk.END)
        if c: c.set('')

    def check_alerts(self):
        with sqlite3.connect(self.db_path) as conn:
            low = conn.execute("SELECT name FROM inventory WHERE stock <= min_threshold").fetchall()
            if low: messagebox.showwarning("Restock", f"Low Items: {', '.join([x[0] for x in low])}")

if __name__ == "__main__":
    root = tk.Tk(); app = PearlStreetApp(root); root.mainloop()
