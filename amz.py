import io
import json
import os
import re
import time
import uuid
import pandas as pd
import streamlit as st

# =========================================================================
# 1. PAGE CONFIGURATION & MODERN SAAS STYLING
# =========================================================================
st.set_page_config(
    page_title="NexusAmz | Ultimate Amazon VA & Merchant Suite",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    .stTextInput input, .stSelectbox select, .stNumberInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0284c7 !important;
        box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2) !important;
    }

    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0284c7;
        padding: 16px;
        border-radius: 12px;
        color: #0f172a;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.2);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369a1 100%, #075985 100%);
        box-shadow: 0 6px 12px -2px rgba(2, 132, 199, 0.3);
        transform: translateY(-1px);
    }

    h1, h2, h3 {
        color: #0f172a;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TOKEN_FILE = "tokens.json"


# =========================================================================
# FILE PERSISTENCE HELPERS
# =========================================================================
def load_token_database():
  if os.path.exists(TOKEN_FILE):
    try:
      with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
        if isinstance(data, dict) and len(data) > 0:
          return data
    except Exception:
      pass

  default_db = {
      "VIP-CLIENT-01": {
          "max_attempts": 20,
          "remaining": 20,
          "active_session": None,
          "status": "Active",
      },
      "TEST-TOKEN-99": {
          "max_attempts": 100,
          "remaining": 100,
          "active_session": None,
          "status": "Active",
      },
  }
  save_token_database(default_db)
  return default_db


def save_token_database(db):
  try:
    with open(TOKEN_FILE, "w") as f:
      json.dump(db, f, indent=4)
      f.flush()
      os.fsync(f.fileno())
  except Exception as e:
    st.error(f"Error saving tokens to disk: {e}")


def get_current_attempts():
  db = load_token_database()
  token = st.session_state.get("logged_in_token")
  if token and token in db:
    return db[token]["remaining"]
  return 0


# =========================================================================
# SESSION STATE INITIALIZATION
# =========================================================================
if "admin_password" not in st.session_state:
  st.session_state["admin_password"] = "Muhammad&021"

if "admin_logged_in" not in st.session_state:
  st.session_state["admin_logged_in"] = False

if "logged_in_token" not in st.session_state:
  st.session_state["logged_in_token"] = None

if "token_charged_this_session" not in st.session_state:
  st.session_state["token_charged_this_session"] = False

if "my_session_id" not in st.session_state:
  st.session_state["my_session_id"] = str(uuid.uuid4())

if "failed_login_attempts" not in st.session_state:
  st.session_state["failed_login_attempts"] = 0
if "lockout_until" not in st.session_state:
  st.session_state["lockout_until"] = 0

if "selected_page" not in st.session_state:
  st.session_state["selected_page"] = "🔐 Access & Authentication"


# =========================================================================
# 2. LEFT SIDEBAR: EXACT CUSTOM STRUCTURED NAVIGATION
# =========================================================================
with st.sidebar:
  col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
  with col_l2:
    st.image("https://img.icons8.com/color/96/amazon.png", width=65)

  st.write("")

  st.markdown(
      "Prepared by AI Engineer: **Muhammad Habib**", unsafe_allow_html=True
  )

  st.write("")

  if st.button(
      "🔐 Access & Authentication",
      use_container_width=True,
      type=(
          "primary"
          if st.session_state["selected_page"] == "🔐 Access & Authentication"
          else "secondary"
      ),
  ):
    st.session_state["selected_page"] = "🔐 Access & Authentication"
    st.rerun()

  st.write("")

  st.markdown("**Core Features:**")

  core_tools = [
      "FBA Profit & ROI Calculator",
      "Listing Generator & Builder",
      "Listing & Byte Validator",
      "Backend Keyword Optimizer",
      "Inventory Velocity & Restock Forecasting",
  ]

  for tool in core_tools:
    if st.button(
        tool,
        key=f"nav_{tool}",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["selected_page"] == tool
            else "secondary"
        ),
    ):
      st.session_state["selected_page"] = tool
      st.rerun()

  st.write("")

  st.markdown("**Advance Features:**")

  adv_tools = [
      "PPC Negative Keyword Finder",
      "PPC Bid Optimizer",
      "ACOS Tracking & Budget",
  ]

  for tool in adv_tools:
    if st.button(
        tool,
        key=f"nav_{tool}",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["selected_page"] == tool
            else "secondary"
        ),
    ):
      st.session_state["selected_page"] = tool
      st.rerun()

  st.write("")

  if st.button(
      "🔐 Admin Dashboard",
      use_container_width=True,
      type=(
          "primary"
          if st.session_state["selected_page"] == "🔐 Admin Dashboard"
          else "secondary"
      ),
  ):
    st.session_state["selected_page"] = "🔐 Admin Dashboard"
    st.rerun()

  st.markdown("---")
  st.caption("© 2026 NexusAmz Suite | Secure IP Protected")


# =========================================================================
# 3. MAIN INTERFACE HEADER
# =========================================================================
selected_page = st.session_state["selected_page"]

st.title("📦 NexusAmz VA & Merchant Automation Suite")
st.markdown(
    "**The All-In-One Enterprise Toolkit for Daily Amazon Store Management,"
    " FBA Calculations, and PPC Optimization**"
)
st.markdown("---")


# =========================================================================
# 4. MAIN CONTENT SECTIONS
# =========================================================================

# -------------------------------------------------------------------------
# ACCESS & AUTHENTICATION
# -------------------------------------------------------------------------
if selected_page == "🔐 Access & Authentication":
  st.subheader("🛡️ Secure Access Control & Token Management")
  st.write(
      "Authenticate your secure access token below to unlock suite capabilities"
      " and monitor your live credit balance."
  )

  db = load_token_database()
  current_time = time.time()

  if current_time < st.session_state["lockout_until"]:
    remaining_lockout = int(st.session_state["lockout_until"] - current_time)
    st.error(
        f"🚨 Too many failed attempts. Security lockout active for"
        f" {remaining_lockout}s."
    )
  else:
    logged_token = st.session_state["logged_in_token"]

    if logged_token and logged_token in db:
      current_active_session = db[logged_token].get("active_session")
      if current_active_session != st.session_state["my_session_id"]:
        st.session_state["logged_in_token"] = None
        st.session_state["token_charged_this_session"] = False
        st.warning(
            "⚠️ Security Alert: Token logged in from another device/browser."
        )
        st.rerun()

    if st.session_state["logged_in_token"]:
      token_key = st.session_state["logged_in_token"]
      rem_att = get_current_attempts()

      st.success(f"Securely Authenticated: `{token_key}`")
      st.metric("⚡ Remaining Credits", rem_att)

      if st.button("Secure Logout"):
        if token_key in db:
          db[token_key]["active_session"] = None
          save_token_database(db)
        st.session_state["logged_in_token"] = None
        st.session_state["token_charged_this_session"] = False
        st.rerun()
    else:
      st.info("🔒 Enter your assigned access token to begin (Single-Device)")
      user_token_input = st.text_input(
          "Enter Access Token", type="default", max_chars=50
      )

      if st.button("Authenticate Securely"):
        clean_input = user_token_input.strip()
        if clean_input in db:
          token_data = db[clean_input]

          if token_data.get("status") != "Active":
            st.error("❌ Token has been disabled by Admin.")
          elif token_data["remaining"] <= 0:
            st.error("❌ Token has zero attempts remaining.")
          else:
            if not st.session_state["token_charged_this_session"]:
              if db[clean_input]["remaining"] > 0:
                db[clean_input]["remaining"] -= 1
                db[clean_input]["active_session"] = st.session_state[
                    "my_session_id"
                ]
                save_token_database(db)
                st.session_state["token_charged_this_session"] = True
                widget_key = f"edit_rem_{clean_input}"
                if widget_key in st.session_state:
                  del st.session_state[widget_key]

            st.session_state["logged_in_token"] = clean_input
            st.session_state["failed_login_attempts"] = 0
            st.success("✅ Secure Access Granted! 1 credit deducted.")
            st.rerun()
        else:
          st.session_state["failed_login_attempts"] += 1
          if st.session_state["failed_login_attempts"] >= 3:
            st.session_state["lockout_until"] = time.time() + 30
            st.error(
                "🚨 Multiple invalid attempts detected. Locked out for 30"
                " seconds."
            )
          else:
            st.error("❌ Invalid Access Token.")


# -------------------------------------------------------------------------
# CORE FEATURE 1: FBA PROFIT & ROI CALCULATOR
# -------------------------------------------------------------------------
elif selected_page == "FBA Profit & ROI Calculator":
  st.subheader("💰 Amazon FBA Profit, Margin & ROI Calculator")
  col_p1, col_p2 = st.columns(2)
  with col_p1:
    selling_price = st.number_input(
        "Selling Price ($)", min_value=1.0, value=29.99
    )
    manufacturing_cost = st.number_input(
        "Manufacturing / COGS Cost ($)", min_value=0.0, value=5.50
    )
    shipping_to_amz = st.number_input(
        "Shipping & Prep Cost per Unit ($)", min_value=0.0, value=1.50
    )
  with col_p2:
    referral_fee_pct = (
        st.slider(
            "Amazon Referral Fee (%)", min_value=5.0, max_value=20.0, value=15.0
        )
        / 100.0
    )
    fba_fulfillment_fee = st.number_input(
        "Amazon FBA Fulfillment Fee ($)", min_value=0.0, value=5.20
    )
    ppc_est_cost = st.number_input(
        "Estimated PPC Ad Cost per Unit ($)", min_value=0.0, value=3.00
    )

  if st.button("🧮 Calculate FBA Profitability", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      ref_fee_amt = selling_price * referral_fee_pct
      total_cost = (
          manufacturing_cost
          + shipping_to_amz
          + ref_fee_amt
          + fba_fulfillment_fee
      )
      net_profit = selling_price - total_cost - ppc_est_cost
      profit_margin = (net_profit / selling_price) * 100
      roi = (net_profit / (manufacturing_cost + shipping_to_amz)) * 100

      st.success("✅ Profitability calculated successfully!")
      st.write("### 📈 Financial Summary:")
      res_col1, res_col2, res_col3, res_col4 = st.columns(4)
      res_col1.metric("Net Profit per Unit", f"${net_profit:.2f}")
      res_col2.metric("Profit Margin", f"{profit_margin:.1f}%")
      res_col3.metric("Return on Investment (ROI)", f"{roi:.1f}%")
      res_col4.metric(
          "Total Amazon Fees", f"${ref_fee_amt + fba_fulfillment_fee:.2f}"
      )


# -------------------------------------------------------------------------
# CORE FEATURE 2: DYNAMIC LISTING GENERATOR & BUILDER
# -------------------------------------------------------------------------
elif selected_page == "Listing Generator & Builder":
  st.subheader("🛠️ Amazon Dynamic Listing & HTML Description Builder")
  st.write(
      "Generate an optimized, policy-compliant Amazon product listing that"
      " adapts dynamically to **any product type** (Toys, Apparel, Electronics,"
      " Household). Includes **Title**, **Highlights**, **5 Bullet Points**, and"
      " a **Formatted HTML Product Description** (under 2,000 chars)."
  )

  col_g1, col_g2 = st.columns(2)
  with col_g1:
    brand_name = st.text_input(
        "Brand Name",
        value="TrendHiveCo",
        help="Your registered brand name (e.g., Barbie, Nike, TrendHiveCo)",
    )
    product_type = st.selectbox(
        "Product Category / Type",
        [
            "Toys & Games",
            "Apparel & Shoes",
            "Home & Kitchen",
            "Sports & Outdoors",
            "Electronics",
            "Beauty & Personal Care",
        ],
    )
    product_name = st.text_input(
        "Product Name / Model", value="Nutcracker Clara Ballerina Doll"
    )
    target_variant = st.text_input(
        "Style / Variant / Color / Size",
        value="Ombre Tutu Transformation & Locket",
    )

  with col_g2:
    key_features = st.text_area(
        "Product Details & Key Features (One per line)",
        value=(
            "Surprise tutu transformation feature when arms twirl\nIncludes bow"
            " headband, heart locket necklace, and gift box\n7 poseable"
            " joints for realistic ballet skill practice\nRecommended for"
            " kids ages 3 years and up"
        ),
        height=110,
    )
    target_keywords = st.text_area(
        "Target Keywords (Comma separated)",
        value=(
            "ballerina doll, nutcracker toy, princess gift set, dance toy,"
            " kids ballet doll"
        ),
        height=90,
    )

  if st.button("🚀 Generate Adaptive Listing", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      kw_list = [
          k.strip() for k in re.split(r"[,\n]", target_keywords) if k.strip()
      ]
      feat_list = [f.strip() for f in key_features.split("\n") if f.strip()]

      main_kw = kw_list[0].title() if kw_list else product_name.title()

      # SMART TEXT TRIMMING HELPER FUNCTION (NO TRAILING CONJUNCTIONS/PUNCTUATION)
      def clean_smart_text(text, max_limit=75):
        if len(text) <= max_limit:
          return text.strip()

        trimmed = text[:max_limit]
        if " " in trimmed:
          trimmed = trimmed.rsplit(" ", 1)[0]

        dangling_words = [
            "&",
            "and",
            "with",
            "for",
            "or",
            "of",
            "in",
            "by",
            "-",
            ",",
        ]
        words = trimmed.split()
        while words and words[-1].lower() in dangling_words:
          words.pop()

        final_str = " ".join(words)
        return final_str.rstrip(",-& ")

      # 1. Smart Title Generation (Strict 75-Char Cap)
      raw_title = f"{brand_name} {product_name} - {target_variant}".strip()
      generated_title = clean_smart_text(raw_title, max_limit=75)

      # 2. Smart Item Highlights Generation (Strict 125-Char Cap)
      raw_highlights = (
          f"{product_name} with {target_variant}. Ideal for"
          f" {product_type.lower()}."
      )
      item_highlights = clean_smart_text(raw_highlights, max_limit=125)

      # 3. Dynamic Bullet Points Generation based on category & details
      f1 = feat_list[0] if len(feat_list) > 0 else "High quality construction"
      f2 = (
          feat_list[1]
          if len(feat_list) > 1
          else "Versatile features and easy operation"
      )
      f3 = (
          feat_list[2]
          if len(feat_list) > 2
          else "Durable non-toxic materials for longevity"
      )
      f4 = (
          feat_list[3]
          if len(feat_list) > 3
          else "Complete set with authentic accessories"
      )

      if product_type == "Toys & Games":
        bullets = [
            f"INTERACTIVE PLAY FEATURE: {f1}.",
            f"COMPLETE ACCESSORY SET: {f2}.",
            f"POSEABLE BALLET DESIGN: {f3}.",
            (
                "SAFE & DURABLE FOR KIDS: Built with child-safe, non-toxic"
                f" materials. {f4}."
            ),
            (
                "PERFECT GIFT FOR AGES 3+: Ideal birthday or holiday surprise"
                f" for kids who love {main_kw.lower()}."
            ),
        ]
      elif product_type in ["Apparel & Shoes"]:
        bullets = [
            (
                "PREMIUM COMFORT & FIT: Crafted for all-day wearable"
                f" flexibility. {f1}."
            ),
            f"ELEGANT STYLING: Designed with refined detail. {f2}.",
            f"DURABLE MATERIALS: High-grade fabric and sturdy stitching. {f3}.",
            f"VERSATILE DAILY WEAR: {f4}.",
            f"CARE INSTRUCTIONS: Easy maintenance and machine washable.",
        ]
      else:
        bullets = [
            f"KEY BENEFIT & DESIGN: {f1}.",
            f"FUNCTIONAL PERFORMANCE: {f2}.",
            f"PREMIUM BUILD QUALITY: {f3}.",
            f"CONVENIENT & PORTABLE: {f4}.",
            f"SATISFACTION GUARANTEED: Engineered to meet strict standards.",
        ]

      # 4. Amazon Product Description HTML (Under 2,000 Chars Limit)
      desc_body = (
          f"<p>Bring home the ultimate <b>{brand_name} {product_name}</b>"
          f" ({target_variant}). Engineered to deliver top performance in"
          f" <b>{product_type}</b>, this item offers exceptional value and"
          " engaging functionality.</p>"
      )
      desc_body += "<b>Key Highlights & Features:</b><ul>"
      for f_item in feat_list:
        desc_body += f"<li>{f_item}</li>"
      desc_body += "</ul>"
      desc_body += (
          f"<p>Whether buying as a special gift or upgrading your collection, the"
          f" <b>{brand_name} {product_name}</b> provides unmatched durability"
          " and style.</p>"
      )

      st.success("✅ Intelligent Amazon Listing Drafted Successfully!")
      st.write("### 📋 Copy & Paste Ready Amazon Listing Draft:")

      st.markdown(
          f"**1. Product Title (75 Chars Max):** `{len(generated_title)} Chars`"
      )
      st.code(generated_title, language="text")

      st.markdown(
          f"**2. Item Highlights (125 Chars Max):** `{len(item_highlights)} Chars`"
      )
      st.code(item_highlights, language="text")

      st.markdown("**3. Bullet Points (5 Core Attributes):**")
      for idx, b_text in enumerate(bullets, 1):
        st.markdown(f"**Bullet {idx}:**")
        st.code(b_text, language="text")

      st.markdown(
          f"**4. Product Description (HTML Formatted - Max 2,000 Chars):**"
          f" `{len(desc_body)} Chars`"
      )
      st.code(desc_body, language="html")


# -------------------------------------------------------------------------
# CORE FEATURE 3: LISTING & BYTE VALIDATOR
# -------------------------------------------------------------------------
elif selected_page == "Listing & Byte Validator":
  st.subheader("📝 Amazon Listing Character & Byte Validator & Auto-Suggester")
  st.write(
      "Check your Amazon Titles, Bullet Points, and Descriptions against"
      " official Amazon limits."
  )

  col1, col2 = st.columns(2)
  with col1:
    val_title = st.text_input(
        "Product Title (Max 75 chars recommended)",
        value="TrendHiveCo Nutcracker Clara Ballerina Doll - Ombre Tutu",
    )
    val_bullet1 = st.text_area(
        "Bullet Point 1 (Max 250 chars)",
        value=(
            "INTERACTIVE PLAY FEATURE: Surprise tutu transformation feature"
            " when arms twirl."
        ),
    )
    val_bullet2 = st.text_area(
        "Bullet Point 2 (Max 250 chars)",
        value=(
            "COMPLETE ACCESSORY SET: Includes bow headband, heart locket"
            " necklace, and gift box."
        ),
    )

  with col2:
    val_bullet3 = st.text_area(
        "Bullet Point 3 (Max 250 chars)",
        value=(
            "POSEABLE BALLET DESIGN: 7 poseable joints for realistic ballet"
            " skill practice."
        ),
    )
    val_bullet4 = st.text_area(
        "Bullet Point 4 (Max 250 chars)",
        value=(
            "SAFE & DURABLE FOR KIDS: Built with child-safe, non-toxic"
            " materials."
        ),
    )
    val_bullet5 = st.text_area(
        "Bullet Point 5 (Max 250 chars)",
        value=(
            "PERFECT GIFT FOR AGES 3+: Ideal birthday or holiday surprise for"
            " kids."
        ),
    )

  if st.button(
      "🔍 Validate Listing & Generate Suggestions", use_container_width=True
  ):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      st.success("✅ Validation completed successfully!")
      st.write("### 📊 Validation Report & Smart Suggestions:")

      def analyze_and_suggest(text, max_limit, field_name):
        chars = len(text)
        if chars <= max_limit:
          st.markdown(
              f"**{field_name}:** {chars} Characters | Status: **✅ Pass**"
          )
        else:
          st.markdown(
              f"**{field_name}:** {chars} Characters | Status: **⚠️ Warning (Over"
              f" {max_limit} chars)**"
          )
          trimmed = text[:max_limit]
          last_space = trimmed.rfind(" ")
          if last_space > 0:
            trimmed = trimmed[:last_space]
          st.info(
              f"💡 **Suggested Compliant {field_name} (Trimmed):**\n`{trimmed}`"
          )

      analyze_and_suggest(val_title, 75, "Product Title")
      analyze_and_suggest(val_bullet1, 250, "Bullet Point 1")
      analyze_and_suggest(val_bullet2, 250, "Bullet Point 2")
      analyze_and_suggest(val_bullet3, 250, "Bullet Point 3")
      analyze_and_suggest(val_bullet4, 250, "Bullet Point 4")
      analyze_and_suggest(val_bullet5, 250, "Bullet Point 5")


# -------------------------------------------------------------------------
# CORE FEATURE 4: BACKEND KEYWORD OPTIMIZER
# -------------------------------------------------------------------------
elif selected_page == "Backend Keyword Optimizer":
  st.subheader("🔍 Amazon Backend Search Terms Optimizer & Deduplicator")
  st.write(
      "Clean your backend keywords: removes commas, filters stop words, and"
      " enforces the 249-byte limit."
  )

  raw_keywords = st.text_area(
      "Paste your raw keyword list (comma or space separated):",
      value=(
          "ballerina doll, nutcracker toy, princess gift set, dance toy, kids"
          " ballet doll"
      ),
      key="raw_kw_box",
  )

  if st.button("⚙️ Optimize & Pack Backend Terms", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      cleaned_input = re.sub(r"[^\w\s]", " ", raw_keywords)
      tokens = cleaned_input.lower().split()
      stop_words = {
          "and",
          "or",
          "the",
          "a",
          "an",
          "for",
          "with",
          "to",
          "in",
          "on",
          "of",
          "by",
      }
      filtered_tokens = [t for t in tokens if t not in stop_words]
      unique_tokens = []
      for token in filtered_tokens:
        if token not in unique_tokens:
          unique_tokens.append(token)

      packed_string = ""
      for token in unique_tokens:
        test_str = (packed_string + " " + token).strip()
        if len(test_str.encode("utf-8")) <= 249:
          packed_string = test_str
        else:
          break

      byte_count = len(packed_string.encode("utf-8"))
      st.success("✅ Backend Search Terms Optimized Successfully!")
      st.text_area(
          "Copy into Amazon Seller Central (Max 249 bytes):",
          value=packed_string,
          height=100,
          key="packed_out_box",
      )
      st.info(
          f"📊 **Final Stats:** {len(packed_string)} Characters | **{byte_count} /"
          " 249 Bytes Used**"
      )


# -------------------------------------------------------------------------
# CORE FEATURE 5: INVENTORY VELOCITY & RESTOCK FORECASTING
# -------------------------------------------------------------------------
elif selected_page == "Inventory Velocity & Restock Forecasting":
  st.subheader(
      "📦 Amazon FBA Inventory Velocity Tracking & Days-of-Supply Forecaster"
  )
  st.write(
      "Calculate real daily sales velocity over custom windows and plan"
      " precise reorder schedules."
  )

  st.write("### 📊 1. Sales Velocity Calculator")
  col_v1, col_v2, col_v3 = st.columns(3)
  with col_v1:
    total_units_sold = st.number_input(
        "Units Sold in Period", min_value=1, value=750
    )
  with col_v2:
    days_in_period = st.number_input(
        "Timeframe Window (Days)", min_value=1, value=30
    )
  with col_v3:
    out_of_stock_days = st.number_input(
        "Stockout Days in Period", min_value=0, value=0
    )

  effective_days = max(1, days_in_period - out_of_stock_days)
  calculated_velocity = total_units_sold / effective_days

  st.info(
      f"⚡ **True Sales Velocity:** `{calculated_velocity:.2f}` Units / Day"
      f" (Adjusted for {out_of_stock_days} stockout days)"
  )

  st.markdown("---")
  st.write("### 📋 2. Reorder Schedule & Days of Supply")
  col_inv1, col_inv2 = st.columns(2)
  with col_inv1:
    current_stock = st.number_input(
        "Current FBA Inventory (Units)", min_value=0, value=1250
    )
    daily_sales_velocity = st.number_input(
        "Daily Sales Velocity (Units / Day)",
        min_value=0.1,
        value=float(round(calculated_velocity, 2)),
    )
  with col_inv2:
    supplier_lead_time = st.number_input(
        "Supplier Lead Time (Days)", min_value=1, value=45
    )
    safety_stock_days = st.number_input(
        "Safety Buffer Stock (Days)", min_value=0, value=15
    )

  if st.button("📊 Calculate Restock Schedule", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      days_of_supply = current_stock / daily_sales_velocity
      reorder_point_days = supplier_lead_time + safety_stock_days
      target_inventory_days = reorder_point_days + 30
      recommended_order_qty = max(
          0, int((target_inventory_days * daily_sales_velocity) - current_stock)
      )

      st.success("✅ Restock schedule calculated successfully!")
      st.write("### 📈 Forecast Summary:")
      r_col1, r_col2, r_col3 = st.columns(3)
      r_col1.metric("Days of Supply Remaining", f"{days_of_supply:.1f} Days")
      r_col2.metric("Reorder Threshold", f"{reorder_point_days} Days")
      r_col3.metric("Recommended Reorder Qty", f"{recommended_order_qty} Units")


# -------------------------------------------------------------------------
# ADVANCE FEATURE 1: PPC NEGATIVE KEYWORD FINDER
# -------------------------------------------------------------------------
elif selected_page == "PPC Negative Keyword Finder":
  st.subheader("📉 Amazon PPC Search Term Negatives Analyzer")
  ppc_file = st.file_uploader(
      "Upload Amazon PPC Search Term Report (.csv)", type=["csv"]
  )
  col_th1, col_th2 = st.columns(2)
  with col_th1:
    min_clicks = st.number_input(
        "Minimum Clicks Threshold", min_value=1, value=10
    )
  with col_th2:
    max_orders = st.number_input(
        "Maximum Orders Threshold", min_value=0, value=0
    )

  if ppc_file is not None:
    try:
      ppc_df = pd.read_csv(ppc_file)
      st.dataframe(ppc_df.head(3), use_container_width=True, hide_index=True)
      if st.button(
          "🔍 Extract Wasteful Search Terms", use_container_width=True
      ):
        if not st.session_state["logged_in_token"]:
          st.error("🚨 Secure authentication required.")
        else:
          clicks_col = next(
              (c for c in ppc_df.columns if "click" in c.lower()), None
          )
          orders_col = next(
              (
                  c
                  for c in ppc_df.columns
                  if "order" in c.lower() or "conversion" in c.lower()
              ),
              None,
          )
          term_col = next(
              (
                  c
                  for c in ppc_df.columns
                  if "search term" in c.lower() or "keyword" in c.lower()
              ),
              None,
          )

          if clicks_col and term_col:
            if orders_col:
              wasteful_df = ppc_df[
                  (ppc_df[clicks_col] >= min_clicks)
                  & (ppc_df[orders_col] <= max_orders)
              ]
            else:
              wasteful_df = ppc_df[ppc_df[clicks_col] >= min_clicks]

            st.success(
                f"✅ Found {len(wasteful_df)} wasteful search terms ready for"
                " negative targeting!"
            )
            st.dataframe(
                wasteful_df[[term_col, clicks_col]],
                use_container_width=True,
                hide_index=True,
            )
            csv_neg = wasteful_df[[term_col]].to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Negative Keywords CSV",
                data=csv_neg,
                file_name="amazon_negative_keywords.csv",
                mime="text/csv",
                use_container_width=True,
            )
          else:
            st.error("🚨 Could not detect required columns in CSV.")
    except Exception as e:
      st.error(f"Error reading file: {e}")


# -------------------------------------------------------------------------
# ADVANCE FEATURE 2: PPC BID OPTIMIZER
# -------------------------------------------------------------------------
elif selected_page == "PPC Bid Optimizer":
  st.subheader("🎯 Amazon PPC Bid Optimizer & Target Adjuster")
  st.write(
      "Upload your Amazon Advertising / Search Term / Targeting report. The"
      " app will automatically recognize **Spend**, **Sales**, and **Bids**"
      " (or estimate effective CPC from Spend/Clicks) to calculate optimized"
      " bids."
  )

  col_b1, col_b2, col_b3 = st.columns(3)
  with col_b1:
    target_acos = (
        st.number_input(
            "Target ACoS (%)", min_value=5.0, max_value=100.0, value=25.0
        )
        / 100.0
    )
  with col_b2:
    min_bid_limit = st.number_input(
        "Minimum Bid Guardrail ($)", min_value=0.05, value=0.20
    )
  with col_b3:
    max_bid_limit = st.number_input(
        "Maximum Bid Guardrail ($)", min_value=0.50, value=5.00
    )

  bid_file = st.file_uploader(
      "Upload Amazon PPC Report (.csv)", type=["csv"], key="bid_uploader"
  )

  if bid_file is not None:
    try:
      b_df = pd.read_csv(bid_file)
      st.write("### 📊 Raw Campaign Data Preview:")
      st.dataframe(b_df.head(3), use_container_width=True, hide_index=True)

      if st.button("🚀 Calculate Optimized Bids", use_container_width=True):
        if not st.session_state["logged_in_token"]:
          st.error("🚨 Secure authentication required.")
        else:
          spend_col = next(
              (c for c in b_df.columns if "spend" in c.lower()), None
          )
          sales_col = next(
              (
                  c
                  for c in b_df.columns
                  if "sale" in c.lower() or "sales" in c.lower()
              ),
              None,
          )
          bid_col = next(
              (
                  c
                  for c in b_df.columns
                  if "bid" in c.lower() or "cost per click" in c.lower()
              ),
              None,
          )
          clicks_col = next(
              (c for c in b_df.columns if "click" in c.lower()), None
          )

          if spend_col and sales_col:
            new_bids = []
            actual_acos_list = []

            for index, row in b_df.iterrows():
              spend = float(row[spend_col])
              sales = float(row[sales_col])

              if bid_col and pd.notna(row[bid_col]) and float(row[bid_col]) > 0:
                current_bid = float(row[bid_col])
              elif (
                  clicks_col
                  and pd.notna(row[clicks_col])
                  and float(row[clicks_col]) > 0
              ):
                current_bid = spend / float(row[clicks_col])
              else:
                current_bid = 1.00

              if sales > 0:
                actual_acos = spend / sales
                calculated_bid = current_bid * (target_acos / actual_acos)
              else:
                actual_acos = 9.99
                calculated_bid = current_bid * 0.80

              final_bid = max(
                  min_bid_limit, min(max_bid_limit, calculated_bid)
              )
              new_bids.append(round(final_bid, 2))
              actual_acos_list.append(
                  f"{actual_acos * 100:.1f}%"
                  if sales > 0
                  else "No Sales (Spend)"
              )

            optimized_df = b_df.copy()
            optimized_df["Actual_ACoS"] = actual_acos_list
            optimized_df["Optimized_New_Bid"] = new_bids

            st.success(
                "✅ PPC Bids successfully calculated and optimized using target"
                " ACoS!"
            )
            st.dataframe(optimized_df, use_container_width=True, hide_index=True)

            csv_bid_out = optimized_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Optimized Bids CSV",
                data=csv_bid_out,
                file_name="amazon_optimized_ppc_bids.csv",
                mime="text/csv",
                use_container_width=True,
            )
          else:
            st.error(
                "🚨 Could not detect required columns ('Spend' and 'Sales')"
                " in your uploaded CSV report."
            )
    except Exception as e:
      st.error(f"Error processing bid report: {e}")


# -------------------------------------------------------------------------
# ADVANCE FEATURE 3: ACOS TRACKING & BUDGET
# -------------------------------------------------------------------------
elif selected_page == "ACOS Tracking & Budget":
  st.subheader(
      "📊 Advanced ACoS, TACOS Tracking & Advertising Budget Optimizer"
  )
  st.write(
      "Monitor store-wide advertising efficiency, balance ad spend against"
      " total revenue, and track organic sales growth."
  )

  col_a1, col_a2 = st.columns(2)
  with col_a1:
    store_sales = st.number_input(
        "Total Gross Store Sales ($)", min_value=1.0, value=45000.0
    )
    total_spend = st.number_input(
        "Total PPC Ad Spend ($)", min_value=0.0, value=6750.0
    )
  with col_a2:
    ad_sales = st.number_input(
        "Total PPC Ad Sales ($)", min_value=0.0, value=18000.0
    )
    target_tacos_pct = st.number_input(
        "Target TACOS (%)", min_value=1.0, max_value=50.0, value=15.0
    )

  if st.button("📈 Analyze TACOS & Budget Health", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error("🚨 Secure authentication required.")
    else:
      acos_val = (total_spend / ad_sales * 100) if ad_sales > 0 else 0
      tacos_val = (
          (total_spend / store_sales * 100) if store_sales > 0 else 0
      )
      organic_val = max(0.0, store_sales - ad_sales)
      organic_ratio_val = (
          (organic_val / store_sales * 100) if store_sales > 0 else 0
      )

      st.success("✅ TACOS & Budget performance analyzed successfully!")
      st.write("### 📉 Executive Performance Dashboard:")

      res_c1, res_c2, res_c3, res_c4 = st.columns(4)
      res_c1.metric("ACoS (Ad Cost)", f"{acos_val:.1f}%")
      res_c2.metric("TACOS (Total Ad Cost)", f"{tacos_val:.1f}%")
      res_c3.metric("Organic Sales", f"${organic_val:,.2f}")
      res_c4.metric("Organic Sales Ratio", f"{organic_ratio_val:.1f}%")

      st.write("### 💡 Strategic Insights & Recommendations:")
      if tacos_val <= target_tacos_pct:
        st.info(
            "🟢 **Healthy Budget Allocation:** Your TACOS ("
            f"{tacos_val:.1f}%) is at or below your target ("
            f"{target_tacos_pct}%). Your advertising is efficiently driving"
            " both paid orders and strong organic rankings without hurting"
            " margins."
        )
      else:
        st.warning(
            "⚠️ **High Ad Spend Warning:** Your TACOS ("
            f"{tacos_val:.1f}%) exceeds your target ({target_tacos_pct}%)."
            " Advertising is consuming too much of your total revenue. Consider"
            " harvesting negative keywords and reducing bids on"
            " non-converting targets."
        )


# -------------------------------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------------------------------
elif selected_page == "🔐 Admin Dashboard":
  st.subheader("🔐 Admin Master Control Panel")

  if not st.session_state["admin_logged_in"]:
    st.warning("⚠️ Restricted Area. Master Password Required.")
    admin_input_pass = st.text_input(
        "Enter Admin Password", type="password", key="admin_pwd_login_box"
    )

    if st.button("Unlock Admin Panel"):
      if admin_input_pass == st.session_state["admin_password"]:
        st.session_state["admin_logged_in"] = True
        st.success("✅ Access Granted!")
        st.rerun()
      else:
        st.error("❌ Incorrect Admin Password.")
  else:
    st.success("🔓 Master Admin Access Verified")
    if st.button("🔒 Lock / Logout Admin Panel"):
      st.session_state["admin_logged_in"] = False
      st.rerun()

    st.markdown("---")

    st.write("### 👥 Client Token Security, Live Session & Status Control")
    token_db = load_token_database()

    if token_db:
      for t_name, data in list(token_db.items()):
        max_att = data["max_attempts"]
        rem_att = data["remaining"]
        used_att = max_att - rem_att
        active_sess = data.get("active_session")
        status = data.get("status", "Active")

        widget_key = f"edit_rem_{t_name}"
        if (
            widget_key not in st.session_state
            or st.session_state[widget_key] != rem_att
        ):
          st.session_state[widget_key] = rem_att

        col_a, col_b, col_c, col_d, col_e, col_f, col_g = st.columns([
            2,
            1,
            1,
            1,
            1,
            1.2,
            1,
        ])
        col_a.markdown(f"**Token:** `{t_name}`")
        col_b.metric("Used", f"{used_att}x")

        new_status = col_c.selectbox(
            "Status",
            ["Active", "Disabled"],
            index=0 if status == "Active" else 1,
            key=f"status_{t_name}",
        )
        if new_status != token_db[t_name].get("status"):
          token_db[t_name]["status"] = new_status
          save_token_database(token_db)

        if active_sess:
          col_d.markdown("🟢 **Locked**")
        else:
          col_d.markdown("⚪ **Free**")

        new_rem = col_e.number_input(
            "Remaining", key=widget_key, min_value=0
        )
        if new_rem != token_db[t_name]["remaining"]:
          token_db[t_name]["remaining"] = new_rem
          save_token_database(token_db)

        if col_f.button("🔄 Reset Counter", key=f"reset_{t_name}"):
          token_db[t_name]["remaining"] = max_att
          token_db[t_name]["active_session"] = None
          save_token_database(token_db)
          if widget_key in st.session_state:
            del st.session_state[widget_key]
          st.success(f"Reset {t_name} to full {max_att} attempts!")
          st.rerun()

        if col_g.button("🗑️ Delete", key=f"del_{t_name}"):
          del token_db[t_name]
          save_token_database(token_db)
          st.rerun()

    st.markdown("---")

    st.write("### ➕ Generate New Secure Client Token")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
      new_token_name = st.text_input(
          "Token Identifier (e.g., Client_Sara_VBA)"
      )
    with col_n2:
      new_token_attempts = st.number_input(
          "Allowed Attempts / Credits", min_value=1, value=10
      )

    if st.button("Generate Secure Token"):
      if new_token_name:
        clean_name = new_token_name.strip()
        current_db = load_token_database()
        current_db[clean_name] = {
            "max_attempts": new_token_attempts,
            "remaining": new_token_attempts,
            "active_session": None,
            "status": "Active",
        }
        save_token_database(current_db)
        st.success(
            f"✅ Secure token `{clean_name}` saved permanently to disk with"
            " single-device locking!"
        )
        st.rerun()
      else:
        st.error("Please enter a valid token name.")

    st.markdown("---")

    st.write("### 🔑 Update Master Admin Password")
    new_admin_pass = st.text_input("New Admin Password", type="password")
    if st.button("Update Admin Password"):
      if new_admin_pass:
        st.session_state["admin_password"] = new_admin_pass
        st.success("✅ Admin password updated successfully for this session!")
      else:
        st.error("Password cannot be empty.")