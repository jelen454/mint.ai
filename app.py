import streamlit as st
import time
import base64
import io
import json
import requests
import os
from PIL import Image
from rembg import remove

# ==========================================
# 1. KONFIGURACE A SETUP
# ==========================================

# ZMĚNA: initial_sidebar_state="expanded" -> Panel bude při startu OTEVŘENÝ
st.set_page_config(page_title="INZO AI", page_icon="💎", layout="centered", initial_sidebar_state="expanded")

# Bezpečné načtení API klíče
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = "SEM_VLOZ_TVUJ_OPENAI_API_KLIC"

# GUMROAD
GUMROAD_PERMALINK = "obrbuof"
GUMROAD_PRODUCT_URL = "https://michaelicious1.gumroad.com/l/obrbuof"
MASTER_KEY = "ADMIN" 

# Kontrola knihovny OpenAI
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    st.error("⚠️ Chybí knihovna OpenAI. Nainstaluj: pip install openai")
    st.stop()

# ==========================================
# 2. DESIGN (SIDEBAR ZPĚT + SKRYTÍ BRANDINGU)
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
    
    /* --- 3. SELEKTIVNÍ SKRYTÍ (Branding pryč, Sidebar zůstává) --- */
    
    /* Skryje Menu vpravo nahoře (tři tečky -> tam je Created by) */
    #MainMenu {visibility: hidden;}
    [data-testid="stMainMenu"] {visibility: hidden;}
    
    /* Skryje patičku (Made with Streamlit) */
    footer {visibility: hidden;}
    
    /* Skryje Toolbar (kde je View counter a tvoje fotka pro tebe) */
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stDecoration"] {visibility: hidden;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    
    /* Ale HLAVIČKU necháme (jen ji zprůhledníme), aby fungovalo tlačítko pro Sidebar vlevo */
    header {
        background: transparent !important;
    }
    
    /* ------------------------------------------------ */
    
    /* 4. HLAVNÍ PODLOŽKA */
    .block-container {
        background-color: rgba(0,0,0,0.5); 
        padding-top: 2rem; 
        border-radius: 15px;
        backdrop-filter: blur(5px);
    }

    /* 5. SIDEBAR (Vzhled panelu) */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: white !important; text-shadow: none !important;
    }
    /* Tlačítko křížku pro zavření panelu na mobilu */
    button[kind="header"] {
        color: white !important;
    }
    
    /* 6. INPUTY */
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
    span[data-baseweb="tag"] span { color: black !important; }
    .stSelectbox svg { fill: black !important; }
    div[data-baseweb="select"] > div { color: black !important; }
    
    /* 7. UPLOADER */
    [data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px; border-radius: 12px;
    }
    [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small {
        color: black !important; text-shadow: none !important;
    }
    [data-testid="stFileUploader"] button {
        color: black !important; border-color: black !important;
    }

    /* 8. TLAČÍTKA */
    div.stButton > button {
        background-color: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: white !important;
        color: black !important;
        transform: scale(1.02);
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #ff00cc, #333399) !important;
        border: none !important;
        color: white !important;
    }
    
    /* 9. GUMROAD */
    a[href*="gumroad"] {
        display: inline-block;
        background-color: #ff4b4b;
        color: white !important;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
        width: 100%;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    a[href*="gumroad"]:hover {
        background-color: #ff0000;
        transform: scale(1.02);
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
        "conds_furn": ["Jako nové", "Používané", "Poškozené"]
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
        "conds_furn": ["Like new", "Used", "Damaged"]
    },
    "DE": {
        "title": "INZO AI", "sub": "Verkaufsexperte", 
        "step0": "Was verkaufen wir?", "back": "Zurück",
        "cats": ["Kleidung", "Elektronik", "Auto", "Möbel"],
        "tab_cam": "📷 Kamera", "tab_upl": "📂 Datei", "upl_label": "Datei wählen",
        "bg": "Hintergrund entfernen", "an": "🔍 Analysieren", "gen": "🚀 Erstellen",
        "platforms": ["Kleinanzeigen", "Vinted.de", "eBay.de", "Facebook Marketplace"],
        "lbls": {
            "name": "Titel", "price": "Preis", "cond": "Zustand", "def": "Mängel", "loc": "📍 Ort / Kontakt",
            "brand": "Marke", "size": "Größe", "mat": "Material", "col": "Farbe", "cut": "Schnitt", "des": "Design",
            "type": "Typ", "model": "Modell", "store": "Speicher", "bat": "Batterie", "acc": "Zubehör",
            "cpu": "Prozessor (CPU)", "ram": "RAM", "gpu": "Grafikkarte (GPU)",
            "body": "Karosserie", "year": "Jahr", "km": "Km", "engine": "Motor / Kraftstoff",
            "dims": "Maße"
        },
        "style": ["Verkaufsexperte", "Kurz", "Technisch"],
        "buy_btn": "⭐ SCHLÜSSEL KAUFEN ($1.60)",
        "limit_msg": "⛔ Testphase beendet! Kaufen Sie einen Schlüssel.",
        "acc_opts": ["OVP", "Ladegerät", "Kabel", "Hülle", "Kopfhörer", "Garantie"],
        "types_elec": ["Handy/Tablet", "PC/Laptop", "TV/Monitor", "Andere"],
        "conds_cloth": ["Neu mit Etikett", "Sehr gut", "Gut", "Mängel"],
        "conds_elec": ["Neu / OVP", "Gebraucht - Wie neu", "Gebraucht", "Defekt"],
        "conds_car": ["Gebraucht", "Neu / Vorführwagen", "Unfallwagen", "Ersatzteile"],
        "conds_furn": ["Wie neu", "Gebraucht", "Beschädigt"]
    },
    "PL": {
        "title": "INZO AI", "sub": "Ekspert sprzedaży", 
        "step0": "Co sprzedajemy?", "back": "Wróć",
        "cats": ["Ubrania", "Elektronika", "Samochody", "Meble"],
        "tab_cam": "📷 Aparat", "tab_upl": "📂 Plik", "upl_label": "Wybierz plik",
        "bg": "Usuń tło", "an": "🔍 Analizuj", "gen": "🚀 Generuj",
        "platforms": ["OLX.pl", "Vinted.pl", "Allegro Lokalnie", "Facebook"],
        "lbls": {
            "name": "Tytuł", "price": "Cena", "cond": "Stan", "def": "Wady", "loc": "📍 Lokalizacja / Kontakt",
            "brand": "Marka", "size": "Rozmiar", "mat": "Materiał", "col": "Kolor", "cut": "Krój", "des": "Design",
            "type": "Typ", "model": "Model", "store": "Pamięć", "bat": "Bateria", "acc": "Akcesoria",
            "cpu": "Procesor (CPU)", "ram": "RAM", "gpu": "Karta graficzna",
            "body": "Nadwozie", "year": "Rok", "km": "Przebieg", "engine": "Silnik / Paliwo",
            "dims": "Wymiary"
        },
        "style": ["Ekspert sprzedaży", "Krótki", "Techniczny"],
        "buy_btn": "⭐ KUP KLUCZ ($1.60)",
        "limit_msg": "⛔ Koniec wersji próbnej! Kup klucz.",
        "acc_opts": ["Pudełko", "Ładowarka", "Kabel", "Etui", "Słuchawki", "Gwarancja"],
        "types_elec": ["Telefon/Tablet", "Komputer/Laptop", "TV/Monitor", "Inne"],
        "conds_cloth": ["Nowy z metką", "Bardzo dobry", "Dobry", "Z wadami"],
        "conds_elec": ["Nowy / Zapakowany", "Używany - Jak nowy", "Używany", "Uszkodzony"],
        "conds_car": ["Używany", "Nowy / Demo", "Uszkodzony", "Na części"],
        "conds_furn": ["Jak nowy", "Używany", "Uszkodzony"]
    }
}

# ==========================================
# 4. BACKEND LOGIKA
# ==========================================

# Session State
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'premium' not in st.session_state: st.session_state.premium = False
if 'lang' not in st.session_state: st.session_state.lang = "CZ"
if 'step' not in st.session_state: st.session_state.step = 0
if 'cat' not in st.session_state: st.session_state.cat = ""
if 'ai_data' not in st.session_state: st.session_state.ai_data = {}

tx = TRANS[st.session_state.lang]

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

# ==========================================
# 5. UI APLIKACE (FRONTEND)
# ==========================================

# --- JAZYKOVÁ LIŠTA ---
cols = st.columns(4)
if cols[0].button("🇨🇿 Česky"): 
    st.session_state.lang = "CZ"; st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
if cols[1].button("🇬🇧 English"): 
    st.session_state.lang = "EN"; st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
if cols[2].button("🇩🇪 Deutsch"): 
    st.session_state.lang = "DE"; st.session_state.step = 0; st.session_state.cat = ""; st.rerun()
if cols[3].button("🇵🇱 Polski"): 
    st.session_state.lang = "PL"; st.session_state.step = 0; st.session_state.cat = ""; st.rerun()

st.title(f"💎 {tx['title']}")
st.markdown(f"*{tx['sub']}*")

# --- SIDEBAR (Zpět a funkční!) ---
with st.sidebar:
    st.header("Můj účet" if st.session_state.lang == "CZ" else "My Account")
    if st.session_state.premium:
        st.success("PREMIUM ✅")
    else:
        st.warning(f"Free: {st.session_state.trials}")
        st.link_button(tx['buy_btn'], GUMROAD_PRODUCT_URL)
        k = st.text_input("Key / Klíč", type="password")
        if st.button("Activate / Aktivovat"):
            if verify_license(k): st.session_state.premium = True; st.rerun()
            else: st.error("❌")

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
        
    try: from rembg import remove; has_rembg = True
    except: has_rembg = False
    
    rem_bg = st.toggle(tx['bg'], value=True) if has_rembg else False
    
    if img_file:
        if st.button(tx['an'], type="primary"):
            if "SEM_VLOZ" in OPENAI_API_KEY: st.error("Error: API Key missing."); st.stop()
            with st.spinner("..."):
                img = Image.open(img_file)
                if rem_bg and has_rembg: img = remove(img)
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
        if not st.session_state.premium and st.session_state.trials <= 0:
            st.error(tx['limit_msg']) 
            st.link_button(tx['buy_btn'], GUMROAD_PRODUCT_URL)
            st.stop()
            
        if not st.session_state.premium: st.session_state.trials -= 1
        
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
    if not st.session_state.premium: c2.link_button(tx['buy_btn'], GUMROAD_PRODUCT_URL)
