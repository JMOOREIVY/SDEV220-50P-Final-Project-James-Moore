#James Moore
#SDEV220-50P
#Module 08 Final Project

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3

class PearlStreetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pearl Street Games & Coffee - Management System")
        self.root.geometry("600x550")

        # Connect to your unified database
        self.conn = sqlite3.connect("pearl_street.db")
        self.cursor = self.conn.cursor()
        self.setup_db()

        self.create_widgets()
        self.refresh_inventory_view()

    def setup_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            stock INTEGER,
            threshold INTEGER
        )''')
        self.conn.commit()

    def create_widgets(self):
        # --- Input Section ---
        input_frame = tk.LabelFrame(self.root, text="Add/Update Item", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0)
        self.ent_name = tk.Entry(input_frame)
        self.ent_name.grid(row=0, column=1)

        tk.Label(input_frame, text="Category:").grid(row=0, column=2)
        self.combo_cat = ttk.Combobox(input_frame, values=["Coffee", "Game", "Facility"], width=10)
        self.combo_cat.grid(row=0, column=3)

        tk.Label(input_frame, text="Stock:").grid(row=1, column=0)
        self.ent_stock = tk.Entry(input_frame, width=5)
        self.ent_stock.grid(row=1, column=1, sticky="w")

        tk.Label(input_frame, text="Min Threshold:").grid(row=1, column=2)
        self.ent_min = tk.Entry(input_frame, width=5)
        self.ent_min.grid(row=1, column=3, sticky="w")

        btn_add = tk.Button(input_frame, text="Save Item", command=self.add_item, bg="#4CAF50", fg="white")
        btn_add.grid(row=1, column=4, padx=10)

        # --- Inventory Table ---
        self.tree = ttk.Treeview(self.root, columns=("ID", "Name", "Category", "Stock", "Min"), show='headings')
        for col in ("ID", "Name", "Category", "Stock", "Min"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Action Buttons ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Check Stock Alerts", command=self.check_alerts, bg="orange").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Generate Sales Report (Placeholder)", command=lambda: messagebox.showinfo("Report", "Feature coming soon!")).pack(side="left", padx=5)

    def add_item(self):
        try:
            name, cat = self.ent_name.get(), self.combo_cat.get()
            stock, threshold = int(self.ent_stock.get()), int(self.ent_min.get())
            
            self.cursor.execute("INSERT INTO inventory (name, category, stock, threshold) VALUES (?, ?, ?, ?)",
                                (name, cat, stock, threshold))
            self.conn.commit()
            self.refresh_inventory_view()
            messagebox.showinfo("Success", f"{name} saved.")
        except ValueError:
            messagebox.showerror("Error", "Stock and Threshold must be numbers.")

    def refresh_inventory_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT * FROM inventory")
        for row in self.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def check_alerts(self):
        self.cursor.execute("SELECT name, stock FROM inventory WHERE stock <= threshold")
        low_items = self.cursor.fetchall()
        if low_items:
            alert_msg = "\n".join([f"{item[0]}: {item[1]} units remaining" for item in low_items])
            messagebox.showwarning("Low Stock Alert", f"Alert: The following need restocking:\n\n{alert_msg}")
        else:
            messagebox.showinfo("Status", "All stock levels are above threshold.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PearlStreetGUI(root)
    root.mainloop()
