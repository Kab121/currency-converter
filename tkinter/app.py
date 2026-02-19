import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading

API_URL = "https://open.er-api.com/v6/latest/{}"


class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter Pro")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        # ----- ttk style -----
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="white", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 22, "bold"), foreground="white", background="#0f172a")
        style.configure("Sub.TLabel", font=("Segoe UI", 11), foreground="#cbd5e1", background="#0f172a")

        style.configure("TCombobox", font=("Segoe UI", 11))
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "white")],
            background=[("readonly", "white")],
            foreground=[("readonly", "black")]
        )

        # ----- Main container -----
        main = tk.Frame(root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=18, pady=18)

        # ----- Header -----
        ttk.Label(main, text="💱 Currency Converter", style="Header.TLabel").pack(pady=(0, 4))
        ttk.Label(main, text="Live rates • Swap • Clear • Rate display", style="Sub.TLabel").pack(pady=(0, 10))

        # =========================
        # ✅ LIVE MOVING TICKER BAR
        # =========================
        self.ticker_frame = tk.Frame(main, bg="#0b1220")
        self.ticker_frame.pack(fill="x", pady=(0, 16))

        self.ticker_label = tk.Label(
            self.ticker_frame,
            text="Loading live rates ticker...",
            font=("Segoe UI", 10, "bold"),
            bg="#0b1220",
            fg="#38bdf8",
            anchor="w"
        )
        self.ticker_label.pack(fill="x", padx=10, pady=8)

        self.ticker_text = "   Loading live rates ticker...   "
        self.ticker_running = True

        # Start scrolling animation
        self.animate_ticker()

        # ----- Card -----
        card = tk.Frame(main, bg="#111827", bd=0, highlightthickness=0)
        card.pack(fill="x", pady=(0, 16))

        # Amount
        ttk.Label(card, text="Amount").grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        self.amount_var = tk.StringVar()
        self.amount_entry = tk.Entry(
            card,
            textvariable=self.amount_var,
            font=("Segoe UI", 13),
            bg="white",
            fg="black",
            relief="flat",
            highlightthickness=2,
            highlightbackground="#334155",
            highlightcolor="#38bdf8"
        )
        self.amount_entry.grid(row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 14), ipady=8)

        # From / To labels
        ttk.Label(card, text="From").grid(row=2, column=0, sticky="w", padx=14, pady=(0, 6))
        ttk.Label(card, text="To").grid(row=2, column=2, sticky="w", padx=14, pady=(0, 6))

        # From / To dropdowns
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()

        self.from_combo = ttk.Combobox(card, textvariable=self.from_var, state="readonly")
        self.to_combo = ttk.Combobox(card, textvariable=self.to_var, state="readonly")

        self.from_combo.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 16))
        self.to_combo.grid(row=3, column=2, sticky="ew", padx=14, pady=(0, 16))

        # Swap button
        self.swap_btn = tk.Button(
            card,
            text="⇄ Swap",
            font=("Segoe UI", 11, "bold"),
            bg="#f59e0b",
            fg="black",
            activebackground="#fbbf24",
            relief="flat",
            cursor="hand2",
            command=self.swap
        )
        self.swap_btn.grid(row=3, column=1, padx=10, pady=(0, 16), ipadx=10, ipady=12)

        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        card.grid_columnconfigure(2, weight=1)

        # ----- Buttons Row -----
        btn_row = tk.Frame(main, bg="#0f172a")
        btn_row.pack(pady=(0, 18))

        self.convert_btn = tk.Button(
            btn_row,
            text="Convert",
            font=("Segoe UI", 12, "bold"),
            bg="#22c55e",
            fg="black",
            activebackground="#4ade80",
            relief="flat",
            cursor="hand2",
            command=self.convert_thread
        )
        self.convert_btn.grid(row=0, column=0, padx=10, ipadx=30, ipady=14)

        self.clear_btn = tk.Button(
            btn_row,
            text="Clear",
            font=("Segoe UI", 12, "bold"),
            bg="#ef4444",
            fg="white",
            activebackground="#f87171",
            relief="flat",
            cursor="hand2",
            command=self.clear
        )
        self.clear_btn.grid(row=0, column=1, padx=10, ipadx=30, ipady=14)

        # ----- Result -----
        self.result_label = tk.Label(
            main,
            text="Result: --",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="white"
        )
        self.result_label.pack(pady=(0, 6))

        self.rate_label = tk.Label(
            main,
            text="Rate: --",
            font=("Segoe UI", 11),
            bg="#0f172a",
            fg="#cbd5e1"
        )
        self.rate_label.pack(pady=(0, 10))

        # ----- Status -----
        self.status_label = tk.Label(
            main,
            text="Status: Ready",
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#94a3b8"
        )
        self.status_label.pack(pady=(0, 6))

        # Load currencies
        self.load_currencies()

        # Enter key convert
        self.root.bind("<Return>", lambda e: self.convert_thread())
        self.amount_entry.focus()

        # ✅ Auto-fit window to content
        self.root.update_idletasks()
        w = main.winfo_reqwidth() + 36
        h = main.winfo_reqheight() + 36
        self.root.geometry(f"{w}x{h}")

        # ✅ Start ticker fetching + auto refresh every 5 minutes
        self.auto_refresh_minutes = 5
        self.start_ticker_fetch()
        self.schedule_ticker_refresh()

    # ---------------------------
    # TICKER FUNCTIONS
    # ---------------------------
    def animate_ticker(self):
        """Scroll ticker text from right to left by rotating characters."""
        if self.ticker_running and self.ticker_text:
            self.ticker_text = self.ticker_text[1:] + self.ticker_text[0]
            self.ticker_label.config(text=self.ticker_text)
        self.root.after(70, self.animate_ticker)  # speed (lower = faster)

    def build_ticker_text(self, base, rates):
        """Build ticker string from selected currencies."""
        show = ["GBP", "EUR", "BDT", "INR", "JPY", "AUD", "CAD", "CNY", "SGD", "AED", "SAR"]
        parts = []
        for c in show:
            if c in rates:
                parts.append(f"{base}→{c} {rates[c]:.4f}")
        return "   |   ".join(parts)

    def set_ticker_text(self, txt):
        self.ticker_text = "   LIVE RATES   |   " + txt + "   |   "

    def start_ticker_fetch(self):
        threading.Thread(target=self.fetch_ticker_rates, daemon=True).start()

    def fetch_ticker_rates(self):
        """Fetch rates for ticker based on current FROM currency."""
        try:
            base = self.from_var.get().strip() or "USD"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(API_URL.format(base), headers=headers, timeout=15)

            if res.status_code != 200:
                self.root.after(0, lambda: self.set_ticker_text("Ticker API blocked / network issue"))
                return

            data = res.json()
            if data.get("result") != "success":
                self.root.after(0, lambda: self.set_ticker_text("Ticker error: could not load rates"))
                return

            rates = data.get("rates", {})
            txt = self.build_ticker_text(base, rates)

            self.root.after(0, lambda: self.set_ticker_text(txt))

        except Exception:
            self.root.after(0, lambda: self.set_ticker_text("Ticker error: network problem"))

    def schedule_ticker_refresh(self):
        """Auto refresh ticker every X minutes."""
        self.root.after(self.auto_refresh_minutes * 60 * 1000, self._refresh_ticker)

    def _refresh_ticker(self):
        self.start_ticker_fetch()
        self.schedule_ticker_refresh()

    # ---------------------------
    # MAIN APP FUNCTIONS
    # ---------------------------
    def load_currencies(self):
        currencies = ["USD", "GBP", "EUR", "BDT", "INR", "JPY", "AUD", "CAD", "CNY", "SGD", "AED", "SAR"]
        self.from_combo["values"] = currencies
        self.to_combo["values"] = currencies
        self.from_combo.set("USD")
        self.to_combo.set("GBP")

    def set_status(self, msg):
        self.status_label.config(text=f"Status: {msg}")
        self.root.update_idletasks()

    def swap(self):
        f, t = self.from_var.get(), self.to_var.get()
        self.from_var.set(t)
        self.to_var.set(f)
        self.set_status("Swapped ✅")
        self.start_ticker_fetch()  # ✅ update ticker base currency

    def clear(self):
        self.amount_var.set("")
        self.result_label.config(text="Result: --")
        self.rate_label.config(text="Rate: --")
        self.set_status("Cleared ✅")
        self.amount_entry.focus()

    def convert_thread(self):
        threading.Thread(target=self.convert, daemon=True).start()

    def convert(self):
        amount_text = self.amount_var.get().strip()
        from_cur = self.from_var.get().strip()
        to_cur = self.to_var.get().strip()

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except:
            self.root.after(0, lambda: messagebox.showerror("Invalid Input", "Enter a valid positive number."))
            return

        if from_cur == to_cur:
            self.root.after(0, lambda: self.result_label.config(text=f"Result: {amount:,.2f} {to_cur}"))
            self.root.after(0, lambda: self.rate_label.config(text=f"Rate: 1 {from_cur} = 1 {to_cur}"))
            self.root.after(0, lambda: self.set_status("Done ✅"))
            return

        try:
            self.root.after(0, lambda: self.set_status("Fetching live rates..."))
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(API_URL.format(from_cur), headers=headers, timeout=15)

            if res.status_code != 200:
                self.root.after(0, lambda: messagebox.showerror("API Error", f"API returned {res.status_code}"))
                self.root.after(0, lambda: self.set_status("API failed ❌"))
                return

            data = res.json()
            if data.get("result") != "success":
                self.root.after(0, lambda: messagebox.showerror("API Error", "Could not fetch live rates."))
                self.root.after(0, lambda: self.set_status("API error ❌"))
                return

            rate = float(data["rates"][to_cur])
            converted = amount * rate

            self.root.after(0, lambda: self.result_label.config(text=f"Result: {converted:,.2f} {to_cur}"))
            self.root.after(0, lambda: self.rate_label.config(text=f"Rate: 1 {from_cur} = {rate:.6f} {to_cur}"))
            self.root.after(0, lambda: self.set_status("Done ✅"))

        except Exception:
            self.root.after(0, lambda: messagebox.showerror("Network Error", "Internet/API blocked. Try again."))
            self.root.after(0, lambda: self.set_status("Network error ❌"))


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
