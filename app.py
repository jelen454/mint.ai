import streamlit as st
import time
import base64
import io
import json
import requests
import sqlite3
import os
from PIL import Image

# Zkusíme importovat rembg, pokud není, nevadí
try:
    from rembg import remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# ==========================================
# 1. KONFIGURACE A DATABÁZE
# ==========================================

st.set_page_config(page_title="INZO AI", page_icon="💎", layout="centered", initial_sidebar_state="collapsed")

# Bezpečné načtení API klíče
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = "SEM_VLOZ_TVUJ_OPENAI_API_KLIC"

# GUMROAD
GUMROAD_PERMALINK = "obrbuof"
GUMROAD_PRODUCT_URL = "https://michaelicious1.gumroad.com/l/obrbuof"
MASTER_KEY = "ADMIN" 

# --- DATABÁZE UŽIVATELŮ (SQLite) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, trials INTEGER, premium INTEGER)''')
    conn.commit()
    conn.close()

def get_user(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Nový uživatel má 3 pokusy a není premium (0)
    c.execute("INSERT INTO users VALUES (?, 3, 0)", (email,))
    conn.commit()
    conn.close()

def update_trials(email, new_trials):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET trials=? WHERE email=?", (new_trials, email))
    conn.commit()
    conn.close()

def set_premium(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET premium=1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

# Inicializace DB při startu
init_db()

# Kontrola OpenAI
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    st.error("⚠️ Chybí knihovna OpenAI. Nainstaluj: pip install openai")
    st.stop()

# ==========================================
# 2. DESIGN (GHOST MODE + CUSTOM MENU)
# ==========================================
st.markdown("""
<style>
    /* 1. POZADÍ */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
    
    /* 2. TEXTY APLIKACE = BÍLÉ */
    h1, h2, h3, h4, p, label, span, div.stMarkdown, div[data-testid="stCaptionContainer"] {
        color: white !important;
        text-shadow: 0px 1px 2px rgba(0,0,0,0.6);
    }
    
    /* 3. SKRYTÍ VŠECH LIŠT (ABY TO BYLO PROFI) */
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stHeader"] {visibility: hidden !important;}
    [data-testid="stDecoration"] {visibility: hidden !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* 4. HLAVNÍ PODLOŽKA */
    .block-container {
        background-color: rgba(0,0,0,0.6); 
        padding-top: 2rem; 
        padding-bottom: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        margin-top: 20px;
    }

    /* 5. INPUTY */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stTextArea > div > div > textarea, 
    .stNumberInput > div > div > input,
    .stMultiSelect > div > div > div {
        background-color: #f8f9fa !important; 
        color: #000000 !important;
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* 6. TLAČÍTKA */
    div.stButton > button {
        background-color: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        font-weight: bold !important;
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #ff00cc, #333399) !important;
        border: none !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GLOBALIZAČNÍ MATRIX (PŘEKLADY)
# ==========================================
TRANS = {
    "CZ": {
        "title": "INZO AI", "sub": "Tvůj prodejní expert", 
        "step0": "Co prodáváme?", "back": "Zpět",
        "cats": ["Oblečení", "Elektronika", "Auto-Moto", "Nábytek"],
        "tab_cam": "📷 Vyfotit", "tab_upl": "📂 Nahrát", "upl_label": "Vyber soubor",
        "bg": "Odebrat pozadí", "an": "🔍 Analyzovat", "gen": "🚀 Generovat inzerát",
        "platforms": ["Vinted", "Bazoš", "Facebook Marketplace", "Aukro"],
        "lbls": {
            "name": "Nadpis", "price": "Cena", "cond": "Stav", "def": "Vady (pokud jsou)", "loc": "📍 Lokalita / Kontakt",
            "brand": "Značka", "size": "Velikost", "mat": "Materiál", "col": "Barva", "cut": "Střih / Typ", "des": "Design / Logo",
            "type": "Typ zařízení", "model": "Model", "store": "Úložiště", "bat": "Baterie", "acc": "Příslušenství",
            "cpu": "Procesor (CPU)", "ram": "RAM", "gpu": "Grafika (GPU)",
            "body": "Karoserie", "year": "Rok", "km": "Km", "engine": "Motor / Palivo",
            "dims": "Rozměry"
        },
        "style": ["Prodejní expert", "Stručný", "Technický"],
        "buy_btn": "⭐ KOUPIT KLÍČ ($1.60)", 
        "limit_msg": "⛔ Došly pokusy zdarma! Pro pokračování si kupte klíč.",
        "acc_opts": ["Krabice", "Nabíječka", "Kabel", "Obal/Kryt", "Sluchátka", "Záruční list"],
        "types_elec": ["Mobil/Tablet", "Počítač/Notebook", "TV/Monitor", "Jiné"],
        "conds_cloth": ["Nový s visačkou", "Velmi dobrý", "Dobrý", "S vadou"],
        "conds_elec": ["Nové / Nerozbalené", "Použité - Jako nové", "Běžně opotřebené", "Na díly"],
        "conds_car": ["Ojeté", "Předváděcí / Nové", "Bourané", "Na díly"],
        "conds_furn": ["Jako nové", "Používané", "Poškozené"],
        "login_t": "Přihlášení", "email_l": "Zadej svůj email", "start": "Spustit aplikaci", "menu": "Můj účet", "buy": "Koupit neomezeně", "rem": "Zbývá pokusů:", "prem": "PREMIUM AKTIVNÍ 💎", "key_l": "Mám klíč"
    },
    "EN": {
        "title": "INZO AI", "sub": "Global Sales Expert", 
        "step0": "What are we selling?", "back": "Back",
        "cats": ["Clothes", "Electronics", "Cars", "Furniture"],
        "tab_cam": "📷 Camera", "tab_upl": "📂 Upload", "upl_label": "Choose file",
        "bg": "Remove Background", "an": "🔍 Analyze", "gen": "🚀 Generate Ad",
        "platforms": ["eBay", "Depop", "Facebook Marketplace", "Etsy"],
        "lbls": {
            "name": "Title", "price": "Price", "cond": "Condition", "def": "Defects (if any)", "loc": "📍 Location / Contact",
            "brand": "Brand", "size": "Size", "mat": "Material", "col": "Color", "cut": "Fit / Cut", "des": "Design / Logo",
            "type": "Type", "model": "Model", "store": "Storage", "bat": "Battery", "acc": "Accessories",
            "cpu": "Processor (CPU)", "ram": "RAM", "gpu": "Graphics (GPU)",
            "body": "Body type", "year": "Year", "km": "Mileage", "engine": "Engine / Fuel",
            "dims": "Dimensions"
        },
        "style": ["Sales Expert", "Short", "Technical"],
        "buy_btn": "⭐ BUY KEY ($1.60)", 
        "limit_msg": "⛔ Free trials ended! Buy a key to continue.",
        "acc_opts": ["Box", "Charger", "Cable", "Case", "Headphones", "Warranty"],
        "types_elec": ["Mobile/Tablet", "PC/Laptop", "TV/Monitor", "Other"],
        "conds_cloth": ["New with tags", "Very good", "Good", "With flaws"],
        "conds_elec": ["New / Sealed", "Used - Like New", "Used", "For parts"],
        "conds_car": ["Used", "New / Demo", "Damaged", "For parts"],
        "conds_furn": ["Like new", "Used", "Damaged"],
        "login_t": "Login", "email_l": "Enter your email", "start": "Start App", "menu": "My Account", "buy": "Buy Unlimited", "rem": "Trials left:", "prem": "PREMIUM ACTIVE 💎", "key_l": "I have a key"
    }
}

# Session state init
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'lang' not in st.session_state: st.session_state.lang = "CZ"
if 'step' not in st.session_state: st.session_state.step = 0
if 'cat' not in st.session_state: st.session_state.cat = ""
if 'ai_data' not in st.session_state: st.session_state.ai_data = {}

tx = TRANS[st.session_state.lang] if st.session_state.lang in TRANS else TRANS["CZ"]

# ==========================================
# 4. FUNKCE BACKENDU (VŠECHNO PŮVODNÍ ZDE)
# ==========================================

def verify_license(key):
    if key == MASTER_KEY: return True
    try:
        res = requests.post("https://api.gumroad.com/v2/licenses/verify", data={"product_permalink": GUMROAD_PERMALINK, "license_key": key})
        return res.json().get("success") == True and not res.json().get("purchase", {}).get("refunded")
    except: return False

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode == 'RGBA': image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_image_with_gpt(image, cat, lang):
    b64 = encode_image(image)
    instr = ""
    if cat == tx['cats'][0]: instr = "Find: Brand, Size, Material, Color, Cut/Fit, Logo/Design."
    elif cat == tx['cats'][1]: instr = "Find: Type, Brand, Model, Condition details."
    elif cat == tx['cats'][2]: instr = "Find: Brand, Model, Body type, Year, Fuel."
    
    prompt = f"Role: Sales Expert. Language: {lang}. Category: {cat}. Task: {instr}. IMPORTANT: Describe everything in {lang} language only. Translate specific terms like T-shirt to {lang}. Output JSON: {{'name': '...', 'price_estimate': '...', 'details': {{'Key': 'Value'}}}}"
    
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}])
        return json.loads(res.choices[0].message.content.replace("```json","").replace("```","").strip())
    except: return {}

def generate_ad_with_gpt(data, lang, platform, style, user_inputs):
    final_data = data.copy()
    clean_inputs = {k: v for k, v in user_inputs.items() if v and str(v).strip() != "" and v != []}
    final_data.update(clean_inputs)
    
    contact_logic = ""
    no_contact_plats = ["Vinted", "Vinted.de", "Vinted.pl", "Depop", "eBay", "eBay.de", "Etsy", "Allegro Lokalnie"]
    
    if platform in no_contact_plats:
        contact_logic = "STRICT RULE: Do NOT include phone number, email, or location in the text."
    else:
        contact_logic = "IMPORTANT: Include the location and contact info at the end."

    prompt = f"""
    Write a sales ad. Platform: {platform}. Language: {lang}. Style: {style}.
    Product Data: {json.dumps(final_data, ensure_ascii=False)}
    Instructions:
    1. {contact_logic}
    2. Use emojis and hashtags.
    3. Be persuasive.
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error generating text."

# --- UI: DIALOGOVÉ OKNO ÚČTU ---
@st.dialog("👤 Můj účet / My Account")
def account_dialog():
    email = st.session_state.user_email
    user = get_user(email)
    trials = user[1]
    is_premium = user[2]
    
    st.write(f"Email: **{email}**")
    
    if is_premium:
        st.success(tx['prem'])
        st.balloons()
    else:
        st.info(f"{tx['rem']} **{trials}**")
        st.progress(trials / 3)
        
        st.markdown("---")
        st.write("🚀 **Chceš neomezené generování?**")
        st.link_button(f"⭐ {tx['buy']} ($1.60)", GUMROAD_PRODUCT_URL)
        
        st.markdown("---")
        k = st.text_input("🔑 " + tx['key_l'], type="password")
        if st.button("Aktivovat / Activate"):
            if verify_license(k):
                set_premium(email)
                st.success("Aktivováno! / Activated!")
                st.rerun()
            else:
                st.error("Neplatný klíč / Invalid key")

# ==========================================
# 5. HLAVNÍ LOGIKA (LOGIN GATE)
# ==========================================

# A) POKUD NENÍ PŘIHLÁŠEN -> UKAŽ JEN LOGIN
if st.session_state.user_email is None:
    st.title("💎 INZO AI")
    st.subheader(tx['login_t'])
    
    # Jazyky na login obrazovce
    lc1, lc2, lc3, lc4 = st.columns(4)
    if lc1.button("🇨🇿"): st.session_state.lang = "CZ"; st.rerun()
    if lc2.button("🇬🇧"): st.session_state.lang = "EN"; st.rerun()
    if lc3.button("🇩🇪"): st.session_state.lang = "DE"; st.rerun()
    if lc4.button("🇵🇱"): st.session_state.lang = "PL"; st.rerun()
    
    with st.form("login_form"):
        email_input = st.text_input(tx['email_l'], placeholder="name@example.com").strip().lower()
        submit = st.form_submit_button(tx['start'], type="primary")
        
        if submit and email_input:
            if "@" not in email_input:
                st.error("Zadej platný email.")
            else:
                # Zkontrolovat nebo vytvořit uživatele v DB
                if not get_user(email_input):
                    create_user(email_input)
                
                st.session_state.user_email = email_input
                st.rerun()

# B) POKUD JE PŘIHLÁŠEN -> UKAŽ CELOU APLIKACI
else:
    # --- HORNÍ LIŠTA (HEADER) ---
    c_logo, c_menu = st.columns([3, 1])
    with c_logo:
        st.title(f"💎 {tx['title']}")
    with c_menu:
        # Tlačítko MENU - Vypadá jako 3 tečky nebo profil
        if st.button("👤 " + tx['menu']):
            account_dialog()

    # Načtení dat uživatele
    user = get_user(st.session_state.user_email)
    trials_left = user[1]
    is_premium = user[2]

    # --- PŮVODNÍ APLIKACE (KROK 0-3) ---
    
    # --- JAZYKOVÁ LIŠTA (UVNITŘ) ---
    cols = st.columns(4)
    if cols[0].button("🇨🇿 Česky", key="l1"): st.session_state.lang = "CZ"; st.rerun()
    if cols[1].button("🇬🇧 English", key="l2"): st.session_state.lang = "EN"; st.rerun()
    if cols[2].button("🇩🇪 Deutsch", key="l3"): st.session_state.lang = "DE"; st.rerun()
    if cols[3].button("🇵🇱 Polski", key="l4"): st.session_state.lang = "PL"; st.rerun()
    
    st.markdown(f"*{tx['sub']}*")

    # --- KROK 0: KATEGORIE ---
    if st.session_state.step == 0:
        st.subheader(tx['step0'])
        c1, c2 = st.columns(2)
        if c1.button(f"👕 {tx['cats'][0]}"): st.session_state.cat = tx['cats'][0]; st.session_state.step = 1; st.rerun()
        if c2.button(f"📱 {tx['cats'][1]}"): st.session_state.cat = tx['cats'][1]; st.session_state.step = 1; st.rerun()
        c3, c4 = st.columns(2)
        if c3.button(f"🚗 {tx['cats'][2]}"): st.session_state.cat = tx['cats'][2]; st.session_state.step = 1; st.rerun()
        if c4.button(f"🪑 {tx['cats'][3]}"): st.session_state.cat = tx['cats'][3]; st.session_state.step = 1; st.rerun()

    # --- KROK 1: UPLOAD ---
    elif st.session_state.step == 1:
        if st.button(tx['back']): st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
        st.info(f"{st.session_state.cat}")
        
        plat = st.selectbox("Marketplace", tx['platforms'])
        
        tab1, tab2 = st.tabs([tx['tab_cam'], tx['tab_upl']])
        img_file = None
        with tab1:
            cam = st.camera_input("Foto")
            if cam: img_file = cam
        with tab2:
            upl = st.file_uploader(tx['upl_label'], type=['jpg','png','jpeg'])
            if upl: img_file = upl
            
        rem_bg = st.toggle(tx['bg'], value=True) if HAS_REMBG else False
        
        if img_file:
            # KONTROLA POKUSŮ PŘED ANALÝZOU
            if st.button(tx['an'], type="primary"):
                if not is_premium and trials_left <= 0:
                     st.error("⛔ " + tx['limit_msg'])
                     if st.button("Otevřít menu"): account_dialog()
                else:
                    if "SEM_VLOZ" in OPENAI_API_KEY: st.error("Error: API Key missing."); st.stop()
                    with st.spinner("..."):
                        img = Image.open(img_file)
                        if rem_bg and HAS_REMBG: img = remove(img)
                        st.session_state.final_img = img
                        st.session_state.ai_data = analyze_image_with_gpt(img, st.session_state.cat, st.session_state.lang)
                        st.session_state.ai_data['platform'] = plat
                        st.session_state.step = 2
                        st.rerun()

    # --- KROK 2: FORMULÁŘ ---
    elif st.session_state.step == 2:
        if st.button(tx['back']): st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
        data = st.session_state.ai_data
        cat = st.session_state.cat
        
        c1, c2 = st.columns([1, 2])
        c1.image(st.session_state.final_img, use_container_width=True)
        
        lbl = tx['lbls']
        with c2:
            name = st.text_input(lbl['name'], value=data.get('name', ''))
            price = st.text_input(lbl['price'], value=data.get('price_estimate', ''))
            
            cond_list = ["New", "Used"]
            if cat == tx['cats'][0]: cond_list = tx['conds_cloth']
            elif cat == tx['cats'][1]: cond_list = tx['conds_elec']
            elif cat == tx['cats'][2]: cond_list = tx['conds_car']
            elif cat == tx['cats'][3]: cond_list = tx['conds_furn']
            
            cond = st.selectbox(lbl['cond'], cond_list)
            is_new = any(x in cond.lower() for x in ["nový", "new", "neu", "nowy", "nerozbalené"])
            defs = ""
            if not is_new: defs = st.text_input(lbl['def'])

        st.markdown("---")
        user_inputs = {}
        det = data.get('details', {})
        
        # 1. OBLEČENÍ
        if cat == tx['cats'][0]:
            c1, c2 = st.columns(2)
            user_inputs['Brand'] = c1.text_input(lbl['brand'], value=det.get('Značka', det.get('Brand', '')))
            user_inputs['Size'] = c2.text_input(lbl['size'], value=det.get('Velikost', det.get('Size', '')))
            user_inputs['Mat'] = st.text_input(lbl['mat'], value=det.get('Materiál', ''))
            c3, c4 = st.columns(2)
            user_inputs['Cut'] = c3.text_input(lbl['cut'])
            user_inputs['Des'] = c4.text_input(lbl['des'])

        # 2. ELEKTRONIKA
        elif cat == tx['cats'][1]:
            type_idx = st.radio(lbl['type'], range(len(tx['types_elec'])), format_func=lambda x: tx['types_elec'][x], horizontal=True)
            sel_type = tx['types_elec'][type_idx]
            user_inputs['Type'] = sel_type
            user_inputs['Model'] = st.text_input(lbl['model'], value=data.get('name', ''))
            
            if type_idx == 0: # Mobil
                c1, c2 = st.columns(2)
                user_inputs['Storage'] = c1.text_input(lbl['store'])
                user_inputs['Batt'] = c2.text_input(lbl['bat'])
            elif type_idx == 1: # PC
                c1, c2 = st.columns(2)
                user_inputs['CPU'] = c1.text_input(lbl['cpu'])
                user_inputs['RAM'] = c2.text_input(lbl['ram'])
                c3, c4 = st.columns(2)
                user_inputs['GPU'] = c3.text_input(lbl['gpu'])
                user_inputs['Storage'] = c4.text_input(lbl['store'])

            user_inputs['Accs'] = st.multiselect(lbl['acc'], tx['acc_opts'])

        # 3. AUTO
        elif cat == tx['cats'][2]:
            user_inputs['Model'] = st.text_input(lbl['model'], value=data.get('name', ''))
            c1, c2 = st.columns(2)
            user_inputs['Year'] = c1.text_input(lbl['year'])
            user_inputs['Km'] = c2.text_input(lbl['km'])
            user_inputs['Specs'] = st.text_input(lbl['engine'], placeholder="2.0 TDI, Manual...")
            user_inputs['Body'] = st.selectbox(lbl['body'], ["Sedan", "Combi", "SUV", "Hatchback", "Cabrio"])

        # 4. NÁBYTEK
        elif cat == tx['cats'][3]:
            user_inputs['Dims'] = st.text_input(lbl['dims'])
            user_inputs['Mat'] = st.text_input(lbl['mat'])

        # KONTAKT
        plat_name = data.get('platform', '')
        no_contact = ["Vinted", "Vinted.de", "Vinted.pl", "Depop", "eBay", "eBay.de", "Etsy", "Allegro Lokalnie"]
        if plat_name not in no_contact:
            st.markdown("---")
            user_inputs['Contact'] = st.text_input(lbl['loc'], placeholder="+420...")

        user_inputs.update({'Name': name, 'Price': price, 'Cond': cond, 'Defects': defs})
        style = st.selectbox("Styl", tx['style'])
        
        # GENERACE
        if st.button(tx['gen'], type="primary"):
            # ODEČTENÍ POKUSU (POKUD NENÍ PREMIUM)
            if not is_premium:
                update_trials(st.session_state.user_email, trials_left - 1)
            
            with st.spinner("..."):
                ad = generate_ad_with_gpt(data, st.session_state.lang, plat_name, style, user_inputs)
                st.session_state.final_text = ad
                st.session_state.step = 3
                st.rerun()

    # --- KROK 3: VÝSLEDEK ---
    elif st.session_state.step == 3:
        st.balloons()
        st.success("OK! 🎉")
        st.text_area("Result:", value=st.session_state.final_text, height=450)
        
        c1, c2 = st.columns(2)
        if c1.button(tx['back']): st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
        if not is_premium:
            if c2.button("⭐ " + tx['buy']):
                account_dialog()
