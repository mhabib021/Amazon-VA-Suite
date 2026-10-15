import io
import re
import time
import uuid
import pandas as pd
import streamlit as st

# 1. Page Configuration & Hardening Header
st.set_page_config(
    page_title="NexusAmz | Ultimate Amazon VA & Merchant Suite",
    page_icon="🛡️",
    layout="wide",
)

# Initialize Session State Security Database
if "admin_password" not in st.session_state:
  st.session_state["admin_password"] = "Muhammad&021"

# Store structure with advanced security metadata
if "token_database" not in st.session_state:
  st.session_state["token_database"] = {
      "VIP-CLIENT-01": {
          "max_attempts": 20,
          "remaining": 20,
          "active_session": None,
          "status": "Active",
      },
      "TEST-TOKEN-99": {
          "max_attempts": 5,
          "remaining": 5,
          "active_session": None,
          "status": "Active",
      },
  }

if "logged_in_token" not in st.session_state:
  st.session_state["logged_in_token"] = None

# Unique Cryptographic Fingerprint for this Browser Tab/Session
if "my_session_id" not in st.session_state:
  st.session_state["my_session_id"] = str(uuid.uuid4())

# Anti-Brute Force Protection State
if "failed_login_attempts" not in st.session_state:
  st.session_state["failed_login_attempts"] = 0
if "lockout_until" not in st.session_state:
  st.session_state["lockout_until"] = 0

# 2. Left Sidebar: Secure Authentication & Device Binding
with st.sidebar:
  st.image("https://img.icons8.com/color/96/amazon.png", width=60)
  st.title("NexusAmz Suite")
  st.markdown(
      "**Prepared by AI Engineer:**\n### Muhammad Habib",
      help="Secure Enterprise Amazon VA Automation Toolkit",
  )
  st.divider()

  st.header("🛡️ Secure Access Control")

  # Check active lockout timer against brute-force attempts
  current_time = time.time()
  if current_time < st.session_state["lockout_until"]:
    remaining_lockout = int(st.session_state["lockout_until"] - current_time)
    st.error(
        f"🚨 Too many failed attempts. Security lockout active for"
        f" {remaining_lockout}s."
    )
  else:
    # Validate session locking binding
    logged_token = st.session_state["logged_in_token"]
    db = st.session_state["token_database"]

    if logged_token and logged_token in db:
      current_active_session = db[logged_token].get("active_session")
      # Terminate session if another device hijacked the token
      if current_active_session != st.session_state["my_session_id"]:
        st.session_state["logged_in_token"] = None
        st.warning(
            "⚠️ Security Alert: Token logged in from another device/browser."
        )
        st.rerun()

    if st.session_state["logged_in_token"]:
      token_key = st.session_state["logged_in_token"]
      token_info = db.get(token_key, {})
      rem_att = token_info.get("remaining", 0)

      st.success(f"Securely Authenticated: `{token_key}`")
      st.info(f"⚡ Remaining Credits: **{rem_att}**")
      if st.button("Secure Logout"):
        if token_key in db:
          db[token_key]["active_session"] = None
        st.session_state["logged_in_token"] = None
        st.rerun()
    else:
      st.warning("🔒 Enter Token (Single-Device Hardened)")
      user_token_input = st.text_input(
          "Enter Access Token", type="default", max_chars=50
      )

      if st.button("Authenticate Securely"):
        clean_input = user_token_input.strip()
        if clean_input in db:
          token_data = db[clean_input]

          # Verify token status and remaining credits
          if token_data.get("status") != "Active":
            st.error("❌ Token has been disabled by Admin.")
          elif token_data["remaining"] <= 0:
            st.error("❌ Token has zero attempts remaining.")
          else:
            existing_session = token_data.get("active_session")
            # Prevent concurrent multi-system session sharing
            if (
                existing_session
                and existing_session != st.session_state["my_session_id"]
            ):
              st.error(
                  "❌ Security Violation: Token is already active on another"
                  " computer/browser!"
              )
            else:
              # Bind successfully and reset brute-force counters
              db[clean_input]["active_session"] = st.session_state[
                  "my_session_id"
              ]
              st.session_state["logged_in_token"] = clean_input
              st.session_state["failed_login_attempts"] = 0
              st.success("✅ Secure Access Granted!")
              st.rerun()
        else:
          # Track failed attempts for anti-brute force
          st.session_state["failed_login_attempts"] += 1
          if st.session_state["failed_login_attempts"] >= 3:
            st.session_state["lockout_until"] = time.time() + 30  # 30s lockout
            st.error(
                "🚨 Multiple invalid attempts detected. Locked out for 30"
                " seconds."
            )
          else:
            st.error("❌ Invalid Access Token.")

  st.divider()
  st.caption("© 2026 NexusAmz Suite | Secure IP Protected")

# 3. Main Interface Header
st.title("📦 NexusAmz VA & Merchant Automation Suite")
st.markdown(
    "**The All-In-One Enterprise Offline Toolkit for Daily Amazon Store"
    " Management, FBA Calculations, and PPC Optimization**"
)
st.divider()


# Secure attempt consumption helper
def consume_attempt():
  token = st.session_state["logged_in_token"]
  db = st.session_state["token_database"]
  if token and token in db:
    if db[token]["remaining"] > 0:
      db[token]["remaining"] -= 1
      return True
  return False


def get_current_attempts():
  token = st.session_state["logged_in_token"]
  db = st.session_state["token_database"]
  if token and token in db:
    return db[token]["remaining"]
  return 0


# 4. Multi-Arch Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab_admin = st.tabs([
    "📝 1. Listing & Byte Validator",
    "🔍 2. Backend Keyword Optimizer",
    "💰 3. FBA Profit & ROI Calculator",
    "📉 4. PPC Negative Keyword Finder",
    "📦 5. Inventory Restock Forecaster",
    "🎯 6. PPC Bid Optimizer",
    "🔐 Admin Dashboard",
])

# =========================================================================
# TAB 1: LISTING & BYTE VALIDATOR
# =========================================================================
with tab1:
  st.subheader("📝 Amazon Listing Character & Byte Validator & Auto-Suggester")
  st.write(
      "Check your Amazon Titles, Bullet Points, and Descriptions against"
      " official Amazon limits."
  )

  col1, col2 = st.columns(2)
  with col1:
    val_title = st.text_input(
        "Product Title (Max 200 chars recommended)",
        value=(
            "Premium Stainless Steel Insulated Water Bottle - Double Wall"
            " Vacuum Flask with Leak Proof Lid for Gym, Sports & Travel"
            " (24oz, Matte Black)"
        ),
    )
    val_bullet1 = st.text_area(
        "Bullet Point 1 (Max 500 chars)",
        value=(
            "KEEP DRINKS ICE COLD OR PIPING HOT: Advanced double-wall vacuum"
            " insulation technology keeps beverages cold for up to 24 hours"
            " and hot for up to 12 hours."
        ),
    )
    val_bullet2 = st.text_area(
        "Bullet Point 2 (Max 500 chars)",
        value=(
            "100% LEAK PROOF & SWEAT PROOF: Ergonomic spout lid with silicone"
            " seal ring completely prevents accidental spills and condensation"
            " buildup in your bag."
        ),
    )

  with col2:
    val_bullet3 = st.text_area(
        "Bullet Point 3 (Max 500 chars)",
        value=(
            "FOOD GRADE DURABILITY: Manufactured using premium 18/8 food-grade"
            " stainless steel that is rust-resistant and 100% BPA free for"
            " safe daily usage."
        ),
    )
    val_bullet4 = st.text_area(
        "Bullet Point 4 (Max 500 chars)",
        value=(
            "TRAVEL FRIENDLY FIT: Slim profile base fits comfortably into"
            " standard car cup holders, bicycle mounts, and side backpack"
            " pockets."
        ),
    )
    val_bullet5 = st.text_area(
        "Bullet Point 5 (Max 500 chars)",
        value=(
            "SATISFACTION GUARANTEED: Backed by our lifetime warranty against"
            " manufacturer defects. Order with total confidence!"
        ),
    )

  if st.button("🔍 Validate Listing & Generate Suggestions", use_container_width=True):
    if not st.session_state["logged_in_token"]:
      st.error(
          "🚨 Please enter a valid Secure Token in the left sidebar to run"
          " this tool."
      )
    elif get_current_attempts() <= 0:
      st.error("🚨 Token quota exhausted. Contact Admin.")
    else:
      consume_attempt()
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


      analyze_and_suggest(val_title, 200, "Product Title")
      analyze_and_suggest(val_bullet1, 500, "Bullet Point 1")
      analyze_and_suggest(val_bullet2, 500, "Bullet Point 2")
      analyze_and_suggest(val_bullet3, 500, "Bullet Point 3")
      analyze_and_suggest(val_bullet4, 500, "Bullet Point 4")
      analyze_and_suggest(val_bullet5, 500, "Bullet Point 5")
      st.info(
          f"⚡ 1 attempt deducted. Remaining attempts:"
          f" {get_current_attempts()}"
      )


# =========================================================================
# TAB 2: BACKEND SEARCH TERM OPTIMIZER
# =========================================================================
with tab2:
  st.subheader("🔍 Amazon Backend Search Terms Optimizer & Deduplicator")
  st.write(
      "Clean your backend keywords: removes commas, filters stop words, and"
      " enforces the 249-byte limit."
  )

  raw_keywords = st.text_area(
      "Paste your raw keyword list (comma or space separated):",
      value=(
          "water bottle, insulated flask, gym bottle for men, water bottle,"
          " vacuum cup, cold flask"
      ),
  )

  if st.button("⚙️ Optimize & Pack Backend Terms", use_container_width=True):
    if not st.session_state["logged_in_token"] or get_current_attempts() <= 0:
      st.error("🚨 Secure authentication required.")
    else:
      consume_attempt()
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
      )
      st.info(
          f"📊 **Final Stats:** {len(packed_string)} Characters | **{byte_count} /"
          f" 249 Bytes Used** | Attempts left: {get_current_attempts()}"
      )


# =========================================================================
# TAB 3: FBA PROFIT & ROI CALCULATOR
# =========================================================================
with tab3:
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
        st.slider("Amazon Referral Fee (%)", min_value=5.0, max_value=20.0, value=15.0)
        / 100.0
    )
    fba_fulfillment_fee = st.number_input(
        "Amazon FBA Fulfillment Fee ($)", min_value=0.0, value=5.20
    )
    ppc_est_cost = st.number_input(
        "Estimated PPC Ad Cost per Unit ($)", min_value=0.0, value=3.00
    )

  if st.button("🧮 Calculate FBA Profitability", use_container_width=True):
    if not st.session_state["logged_in_token"] or get_current_attempts() <= 0:
      st.error("🚨 Secure authentication required.")
    else:
      consume_attempt()
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

      st.write("### 📈 Financial Summary:")
      res_col1, res_col2, res_col3, res_col4 = st.columns(4)
      res_col1.metric("Net Profit per Unit", f"${net_profit:.2f}")
      res_col2.metric("Profit Margin", f"{profit_margin:.1f}%")
      res_col3.metric("Return on Investment (ROI)", f"{roi:.1f}%")
      res_col4.metric(
          "Total Amazon Fees", f"${ref_fee_amt + fba_fulfillment_fee:.2f}"
      )
      st.info(
          f"⚡ 1 attempt deducted. Remaining attempts:"
          f" {get_current_attempts()}"
      )


# =========================================================================
# TAB 4: PPC NEGATIVE KEYWORD FINDER
# =========================================================================
with tab4:
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
        if not st.session_state["logged_in_token"] or get_current_attempts() <= 0:
          st.error("🚨 Secure authentication required.")
        else:
          consume_attempt()
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


# =========================================================================
# TAB 5: INVENTORY RESTOCK FORECASTER
# =========================================================================
with tab5:
  st.subheader("📦 Amazon FBA Inventory Restock & Days-of-Supply Forecaster")
  col_inv1, col_inv2 = st.columns(2)
  with col_inv1:
    current_stock = st.number_input(
        "Current FBA Inventory (Units)", min_value=0, value=1250
    )
    daily_sales_velocity = st.number_input(
        "Average Daily Sales (Units / Day)", min_value=1.0, value=25.0
    )
  with col_inv2:
    supplier_lead_time = st.number_input(
        "Supplier Lead Time (Days)", min_value=1, value=45
    )
    safety_stock_days = st.number_input(
        "Safety Buffer Stock (Days)", min_value=0, value=15
    )

  if st.button("📊 Calculate Restock Schedule", use_container_width=True):
    if not st.session_state["logged_in_token"] or get_current_attempts() <= 0:
      st.error("🚨 Secure authentication required.")
    else:
      consume_attempt()
      days_of_supply = current_stock / daily_sales_velocity
      reorder_point_days = supplier_lead_time + safety_stock_days
      target_inventory_days = reorder_point_days + 30
      recommended_order_qty = max(
          0, int((target_inventory_days * daily_sales_velocity) - current_stock)
      )

      st.write("### 📋 Inventory Forecast Report:")
      r_col1, r_col2, r_col3 = st.columns(3)
      r_col1.metric("Days of Supply Remaining", f"{days_of_supply:.1f} Days")
      r_col2.metric("Reorder Threshold", f"{reorder_point_days} Days")
      r_col3.metric("Recommended Reorder Qty", f"{recommended_order_qty} Units")
      st.info(
          f"⚡ 1 attempt deducted. Remaining attempts:"
          f" {get_current_attempts()}"
      )


# =========================================================================
# TAB 6: PPC BID OPTIMIZER & TARGET ADJUSTER
# =========================================================================
with tab6:
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
        if not st.session_state["logged_in_token"] or get_current_attempts() <= 0:
          st.error("🚨 Secure authentication required.")
        else:
          consume_attempt()

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
            st.info(
                f"⚡ 1 attempt deducted. Remaining attempts:"
                f" {get_current_attempts()}"
            )
          else:
            st.error(
                "🚨 Could not detect required columns ('Spend' and 'Sales')"
                " in your uploaded CSV report."
            )
    except Exception as e:
      st.error(f"Error processing bid report: {e}")


# =========================================================================
# TAB 7: ADMIN DASHBOARD (SECURED & HARDENED)
# =========================================================================
with tab_admin:
  st.subheader("🔐 Admin Master Control Panel")
  st.write(
      "Restricted secure area. Enter your master password to manage client"
      " tokens, monitor session locks, and enforce security policies."
  )

  admin_input_pass = st.text_input(
      "Enter Admin Password", type="password", key="admin_pwd_box"
  )

  if admin_input_pass == st.session_state["admin_password"]:
    st.success("🔓 Master Admin Access Verified!")
    st.divider()

    # Section 1: Token Management & Security Status
    st.write(
        "### 👥 Client Token Security, Live Session & Status Control"
    )
    token_db = st.session_state["token_database"]

    if token_db:
      for t_name, data in list(token_db.items()):
        max_att = data["max_attempts"]
        rem_att = data["remaining"]
        used_att = max_att - rem_att
        active_sess = data.get("active_session")
        status = data.get("status", "Active")

        col_a, col_b, col_c, col_d, col_e, col_f = st.columns([
            2,
            1,
            1,
            1,
            1,
            1,
        ])
        col_a.markdown(f"**Token:** `{t_name}`")
        col_b.metric("Used", f"{used_att}x")

        # Status toggle (Active / Disabled)
        new_status = col_c.selectbox(
            "Status",
            ["Active", "Disabled"],
            index=0 if status == "Active" else 1,
            key=f"status_{t_name}",
        )
        token_db[t_name]["status"] = new_status

        # Show live session lock indicator
        if active_sess:
          col_d.markdown("🟢 **Locked**")
        else:
          col_d.markdown("⚪ **Free**")

        new_rem = col_e.number_input(
            "Remaining", value=rem_att, key=f"edit_rem_{t_name}", min_value=0
        )
        token_db[t_name]["remaining"] = new_rem

        if col_f.button("🗑️ Delete", key=f"del_{t_name}"):
          del token_db[t_name]
          st.rerun()
        st.markdown("---")

    st.divider()

    # Section 2: Generate New Secure Token
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
        st.session_state["token_database"][clean_name] = {
            "max_attempts": new_token_attempts,
            "remaining": new_token_attempts,
            "active_session": None,
            "status": "Active",
        }
        st.success(
            f"✅ Secure token `{clean_name}` generated successfully with"
            f" single-device locking!"
        )
        st.rerun()
      else:
        st.error("Please enter a valid token name.")

    st.divider()

    # Section 3: Change Admin Password
    st.write("### 🔑 Update Master Admin Password")
    new_admin_pass = st.text_input("New Admin Password", type="password")
    if st.button("Update Admin Password"):
      if new_admin_pass:
        st.session_state["admin_password"] = new_admin_pass
        st.success("✅ Admin password updated successfully!")
      else:
        st.error("Password cannot be empty.")

  elif admin_input_pass != "":
    st.error("❌ Incorrect Admin Password. Access Denied.")
  else:
    st.info(
        "💡 Default admin password is: `Muhammad&021`. Type it above to unlock"
        " control."
    )