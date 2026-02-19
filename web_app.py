import requests
import streamlit as st

API_URL = "https://open.er-api.com/v6/latest/{}"

st.set_page_config(page_title="Currency Converter Pro", page_icon="💱", layout="centered")

# -----------------------------
# CSS: fix top cut + strong card UI
# -----------------------------
st.markdown("""
<style>
/* ✅ FIX: add top padding so title isn't hidden */
.block-container{
  padding-top: 2.6rem !important;
  max-width: 900px;
}

/* Background */
.stApp{
  background:
    radial-gradient(circle at 15% 20%, rgba(59,130,246,0.35) 0%, transparent 40%),
    radial-gradient(circle at 85% 15%, rgba(236,72,153,0.30) 0%, transparent 45%),
    radial-gradient(circle at 20% 85%, rgba(34,197,94,0.25) 0%, transparent 50%),
    linear-gradient(135deg, #0f172a 0%, #020617 100%);
}

footer{visibility:hidden;}

/* Title */
.title{
  font-family: "Segoe UI", sans-serif;
  font-size: 44px;
  font-weight: 950;
  color: #fff;
  margin: 0;
  line-height: 1.05;
}
.sub{
  font-family: "Segoe UI", sans-serif;
  color:#cbd5e1;
  font-weight:650;
  margin: 8px 0 16px 0;
}

/* Ticker */
.ticker-wrap{
  background: rgba(11,18,32,0.72);
  border:1px solid rgba(148,163,184,0.25);
  border-radius: 14px;
  padding: 10px 12px;
  overflow: hidden;
  box-shadow: 0 12px 24px rgba(0,0,0,0.25);
  margin-bottom: 16px;
}
.ticker{
  display:inline-block;
  white-space:nowrap;
  color:#38bdf8;
  font-weight:900;
  font-family: "Segoe UI", sans-serif;
  text-shadow: 0 0 10px rgba(56,189,248,0.25);
  animation: tickerMove 18s linear infinite;
}
@keyframes tickerMove{
  0%{ transform: translateX(100%); }
  100%{ transform: translateX(-100%); }
}

/* Card */
.card{
  background: rgba(17,24,39,0.78);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 18px 40px rgba(0,0,0,0.35);
  backdrop-filter: blur(10px);
}

/* Labels */
[data-testid="stWidgetLabel"] p{
  color:#e5e7eb !important;
  font-weight:850 !important;
  font-family:"Segoe UI", sans-serif !important;
}

/* Inputs */
[data-testid="stTextInput"] input{
  background:#ffffff !important;
  color:#0b1220 !important;
  border-radius: 12px !important;
  border:2px solid #334155 !important;
  padding: 0.65rem 0.85rem !important;
  font-weight:750 !important;
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
  background:#ffffff !important;
  border-radius: 12px !important;
  border:2px solid #334155 !important;
}
[data-testid="stSelectbox"] *{
  color:#0b1220 !important;
  font-weight:750 !important;
}

/* Button base (no hover) */
div[data-testid="stButton"] > button{
  border-radius: 14px !important;
  border: 0 !important;
  padding: 0.75rem 0.9rem !important;
  font-weight: 900 !important;
  box-shadow: 0 12px 22px rgba(0,0,0,0.25);
}

/* ✅ Colour the SECONDARY buttons using stable text selector (works in most versions) */
div[data-testid="stButton"] > button:has(span:contains("⇄ Swap")),
div[data-testid="stButton"] > button:has(span:contains("Swap")){
  background:#f59e0b !important; color:#111827 !important;
}
div[data-testid="stButton"] > button:has(span:contains("Clear")){
  background:#ef4444 !important; color:#ffffff !important;
}
div[data-testid="stButton"] > button:has(span:contains("Refresh")){
  background:#3b82f6 !important; color:#ffffff !important;
}

/* Result */
.result{ margin-top: 16px; font-size: 30px; font-weight:1000; color:#fff; font-family:"Segoe UI", sans-serif; }
.rate{ margin-top:6px; color:#cbd5e1; font-weight:750; font-family:"Segoe UI", sans-serif; }
.status{ margin-top:10px; color:#94a3b8; font-weight:750; font-size:12px; font-family:"Segoe UI", sans-serif; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=300)
def fetch_rates(base: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(API_URL.format(base), headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        raise RuntimeError("API did not return success")
    return data.get("rates", {})

def parse_amount(text: str):
    t = (text or "").strip().replace(",", "")
    if not t:
        return None
    try:
        v = float(t)
        return v if v > 0 else None
    except:
        return None

def build_ticker(base: str, rates: dict) -> str:
    show = ["GBP","EUR","BDT","INR","JPY","AUD","CAD","CNY","SGD","AED","SAR"]
    parts = [f"{base}→{c} {rates[c]:.4f}" for c in show if c in rates]
    return "   |   ".join(parts) if parts else "Ticker: no rates"

# -----------------------------
# State
# -----------------------------
currencies = ["USD","GBP","EUR","BDT","INR","JPY","AUD","CAD","CNY","SGD","AED","SAR"]
st.session_state.setdefault("from_cur","USD")
st.session_state.setdefault("to_cur","GBP")
st.session_state.setdefault("result_text","Result: --")
st.session_state.setdefault("rate_text","Rate: --")
st.session_state.setdefault("status_text","Status: Ready")

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="title">💱 Currency Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Live rates • Swap • Clear • Rate display</div>', unsafe_allow_html=True)

# Ticker
try:
    ticker_rates = fetch_rates(st.session_state["from_cur"])
    ticker_text = "LIVE RATES   |   " + build_ticker(st.session_state["from_cur"], ticker_rates) + "   |   "
except Exception:
    ticker_text = "Ticker error: network/API blocked"

st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text}</div></div>', unsafe_allow_html=True)

# Card
st.markdown('<div class="card">', unsafe_allow_html=True)

amount_text = st.text_input("Amount", value="", placeholder="e.g., 100")

c1, c2, c3 = st.columns([1, 0.45, 1])
with c1:
    from_cur = st.selectbox("From", currencies, index=currencies.index(st.session_state["from_cur"]))
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    swap_clicked = st.button("⇄ Swap", use_container_width=True)
with c3:
    to_cur = st.selectbox("To", currencies, index=currencies.index(st.session_state["to_cur"]))

st.session_state["from_cur"] = from_cur
st.session_state["to_cur"] = to_cur

b1, b2, b3 = st.columns(3)
with b1:
    # ✅ Convert uses Streamlit PRIMARY (we'll make it green using config.toml below)
    convert_clicked = st.button("Convert", use_container_width=True, type="primary")
with b2:
    clear_clicked = st.button("Clear", use_container_width=True)
with b3:
    refresh_clicked = st.button("Refresh", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Actions
if refresh_clicked:
    fetch_rates.clear()
    st.session_state["status_text"] = "Status: Rates refreshed ✅"
    st.rerun()

if swap_clicked:
    st.session_state["from_cur"], st.session_state["to_cur"] = st.session_state["to_cur"], st.session_state["from_cur"]
    st.session_state["status_text"] = "Status: Swapped ✅"
    st.rerun()

if clear_clicked:
    st.session_state["result_text"] = "Result: --"
    st.session_state["rate_text"] = "Rate: --"
    st.session_state["status_text"] = "Status: Cleared ✅"
    st.rerun()

if convert_clicked:
    amt = parse_amount(amount_text)
    if amt is None:
        st.session_state["status_text"] = "Status: Invalid input ❌"
        st.error("Enter a valid positive number (e.g., 100).")
    else:
        base = st.session_state["from_cur"]
        target = st.session_state["to_cur"]
        if base == target:
            st.session_state["result_text"] = f"Result: {amt:,.2f} {target}"
            st.session_state["rate_text"] = f"Rate: 1 {base} = 1 {target}"
            st.session_state["status_text"] = "Status: Done ✅"
        else:
            try:
                rates = fetch_rates(base)
                rate = float(rates[target])
                converted = amt * rate
                st.session_state["result_text"] = f"Result: {converted:,.2f} {target}"
                st.session_state["rate_text"] = f"Rate: 1 {base} = {rate:.6f} {target}"
                st.session_state["status_text"] = "Status: Done ✅"
            except Exception:
                st.session_state["status_text"] = "Status: Network error ❌"
                st.error("Network/API error. Check internet and try again.")

# Result
st.markdown(f'<div class="result">{st.session_state["result_text"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="rate">{st.session_state["rate_text"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="status">{st.session_state["status_text"]}</div>', unsafe_allow_html=True)
