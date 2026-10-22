import io, json, os, re, time, uuid
import pandas as pd
import streamlit as st
from scrapfly import ScrapflyClient, ScrapeConfig

st.set_page_config(page_title="NexusAmz Suite", page_icon="🛡️", layout="wide")
st.markdown("""<style>
.stApp{background:#f8fafc;font-family:Inter,sans-serif}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1e293b,#0f172a)}
[data-testid="stSidebar"] *{color:#fff!important}
.stTextInput input,.stTextArea textarea,.stNumberInput input{background:#fff!important;color:#0f172a!important;
 border:1px solid #cbd5e1!important;border-radius:8px!important}
[data-testid="metric-container"]{background:#fff;border:1px solid #e2e8f0;border-left:4px solid #0284c7;
 padding:16px;border-radius:12px}
.stButton>button{background:linear-gradient(135deg,#0284c7,#0369a1);color:#fff;font-weight:600;
 border:none;border-radius:8px;padding:.6rem 1.2rem}
.sidebar-footer {
    position: fixed; 
    bottom: 0; 
    left: 0;
    width: 100%; 
    text-align: center; 
    padding: 15px; 
    font-size: 14px; 
    font-weight: bold;
    color: #cbd5e1; 
    border-top: 1px solid #334155; 
    background: #0f172a;
    z-index: 999;
}
</style>""", unsafe_allow_html=True)

TOKEN_FILE = "tokens.json"

# =========================================================================
# UNIVERSAL FILE READER
# =========================================================================
SUPPORTED_EXTS = ["csv", "xlsx", "xls", "xlsm"]

def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None, "No file uploaded."
    name = uploaded_file.name.lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    try:
        if ext == "csv":
            try:
                return pd.read_csv(uploaded_file), None
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding="latin-1"), None
        elif ext == "xlsx":
            return pd.read_excel(uploaded_file, engine="openpyxl"), None
        elif ext == "xls":
            return pd.read_excel(uploaded_file, engine="xlrd"), None
        elif ext == "xlsm":
            return pd.read_excel(uploaded_file, engine="openpyxl"), None
        else:
            try:
                return pd.read_excel(uploaded_file), None
            except Exception:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file), None
    except ImportError as ie:
        pkg = "openpyxl" if ext in ("xlsx", "xlsm") else "xlrd"
        return None, f"❌ Missing dependency. Run: pip install {pkg}\n_Detail: {ie}_"
    except Exception as e:
        return None, f"❌ Could not read **{uploaded_file.name}**: {e}"

# =========================================================================
# GTIN NORMALIZATION
# =========================================================================
def _norm_gtin(x):
    if pd.isna(x): return None
    s = str(x).strip()
    if s.endswith(".0"): s = s[:-2]
    s = re.sub(r"\D", "", s)
    if not s: return None
    if len(s) == 12: s = "0" + s
    if len(s) < 13: s = s.zfill(13)
    return s

# =========================================================================
# FULL TRANSLATIONS
# =========================================================================
LANGS = ["English","Deutsch","Español","Italiano","Türkçe","Polski",
         "Nederlands","Svenska","Português","Français","العربية"]

T = {
"auth":       ["🔐 Access & Authentication","🔐 Zugriff & Authentifizierung","🔐 Acceso y Autenticación","🔐 Accesso e Autenticazione","🔐 Erişim ve Kimlik Doğrulama","🔐 Dostęp i Uwierzytelnianie","🔐 Toegang & Authenticatie","🔐 Åtkomst & Autentisering","🔐 Acesso e Autenticação","🔐 Accès & Authentification","🔐 المصادقة والوصول"],
"calc":       ["FBA Profit & ROI Calculator","FBA Gewinn & ROI Rechner","Calculadora de Beneficios y ROI FBA","Calcolatore Profitto e ROI FBA","FBA Kar ve ROI Hesaplayıcı","Kalkulator Zysku i ROI FBA","FBA Winst & ROI Calculator","FBA Vinst & ROI Kalkylator","Calculadora de Lucro e ROI FBA","Calculateur de Profit & ROI FBA","حاسبة أرباح وعائد الاستثمار FBA"],
"gen":        ["Listing Generator & Builder","Listing Generator & Ersteller","Generador y Creador de Listings","Generatore e Creatore di Listing","İlan Oluşturucu ve Tasarlayıcı","Generator i Kreator Ofert","Listing Generator & Bouwer","Listing Generator & Byggare","Gerador e Criador de Anúncios","Générateur & Créateur de Listing","منشئ ومصمم القوائم"],
"val":        ["Listing & Byte Validator","Listing & Byte Prüfer","Validador de Listados y Bytes","Validatore Listing e Byte","İlan ve Byte Denetleyicisi","Walidator Ofert i Bajtów","Listing & Byte Validator","Listing & Byte Validerare","Validador de Anúncios e Bytes","Validateur de Listing & Octets","مدقق الأحرف والبايت للقوائم"],
"opt":        ["Backend Keyword Optimizer","Backend Keyword Optimierer","Optimizador de Palabras Clave Backend","Ottimizzatore Keyword Backend","Arka Plan Anahtar Kelime Optimizatörü","Optymalizator Słów Kluczowych Backend","Backend Trefwoorden Optimalisator","Backend Nyckelord Optimerare","Otimizador de Palavras-Chave Backend","Optimiseur de Mots-Clés Backend","مُحسّن الكلمات المفتاحية الخلفية"],
"inv":        ["Inventory Velocity & Restock Forecasting","Bestandsgeschwindigkeit & Nachbestellung","Velocidad de Inventario y Previsiones","Velocità Inventario e Previsione Rifornimento","Envanter Hızı ve Yeniden Sipariş Tahmini","Prędkość Magazynowa i Prognozowanie","Voorraadsnelheid & Herbestelling","Lagerhastighet & Prognos","Velocidade de Estoque e Recomposição","Vélocité des Stocks & Prévisions","تتبع سرعة المخزون والتنبؤ"],
"neg":        ["PPC Negative Keyword Finder","PPC Negativ-Keyword Finder","Buscador de Palabras Clave Negativas PPC","Trova Keyword Negative PPC","PPC Negatif Anahtar Kelime Bulucu","Wyszukiwarka Negatywnych Słów PPC","PPC Negatieve Trefwoorden Zoeker","PPC Negativa Nyckelord Hittare","Localizador de Termos Negativos PPC","Recherche de Mots-Clés Négatifs PPC","باحث الكلمات السلبية PPC"],
"bid":        ["PPC Bid Optimizer","PPC Gebotsoptimierer","Optimizador de Pujas PPC","Ottimizzatore Offerte PPC","PPC Teklif Optimizatörü","Optymalizator Stawek PPC","PPC Bod Optimalisator","PPC Bud Optimerare","Otimizador de Lances PPC","Optimiseur d'Enchères PPC","مُحسّن عروض الأسعار PPC"],
"acos":       ["ACOS Tracking & Budget","ACOS-Verfolgung & Budget","Seguimiento ACOS y Presupuesto","Monitoraggio ACOS e Budget","ACOS Takibi ve Bütçe","Śledzenie ACOS i Budżet","ACOS-tracking & Budget","ACOS-spårning & Budget","Rastreamento de ACOS e Orçamento","Suivi ACOS & Budget","تتبع ACOS والميزانية"],
"admin":      ["Admin Dashboard","Admin-Dashboard","Panel de Administración","Pannello di Amministrazione","Yönetici Paneli","Panel Administratora","Beheerdersdashboard","Adminpanel","Painel de Administração","Tableau de Bord Admin","لوحة الإدارة"],
"btn_auth":   ["Authenticate Securely","Sicher Authentifizieren","Autenticar de Forma Segura","Autentica in Modo Sicuro","Güvenli Doğrulama Yap","Uwierzytelnij Bezpiecznie","Beveiligd Authenticeren","Autentisera Säkert","Autenticar com Segurança","Authentification Sécurisée","مصادقة آمنة"],
"btn_logout": ["Secure Logout","Sicher Abmelden","Cerrar Sesión","Disconnessione Sicura","Güvenli Çıkış","Bezpieczne Wylogowanie","Veilig Uitloggen","Säker Logga Ut","Sair com Segurança","Déconnexion Sécurisée","تسجيل الخروج الآمن"],
"auth_sub":   ["Authenticate your secure access token below.","Authentifizieren Sie unten Ihren Zugangstoken.","Autentique su token de acceso seguro.","Autentica il tuo token di accesso sicuro.","Güvenli erişim token'ınızı doğrulayın.","Uwierzytelnij swój token dostępu.","Authenticeer uw beveiligde toegangstoken.","Autentisera din säkra åtkomsttoken.","Autentique seu token de acesso seguro.","Authentifiez votre jeton d'accès.","قم بالمصادقة باستخدام رمز الوصول الخاص بك."],
"auth_info":  ["🔒 Enter your token (single-device)","🔒 Token eingeben (Einzelgerät)","🔒 Introduzca su token (dispositivo único)","🔒 Inserisci il tuo token (dispositivo singolo)","🔒 Token'ınızı girin (tek cihaz)","🔒 Wprowadź token (jedno urządzenie)","🔒 Voer uw token in (één apparaat)","🔒 Ange din token (en enhet)","🔒 Insira seu token (dispositivo único)","🔒 Entrez votre jeton (monodispositif)","🔒 أدخل رمزك (جهاز واحد)"],
"auth_lbl":   ["Enter Access Token","Zugangstoken Eingeben","Introducir Token de Acceso","Inserisci Token di Accesso","Erişim Token'ını Girin","Wprowadź Token Dostępu","Voer Toegangstoken In","Ange Åtkomsttoken","Inserir Token de Acesso","Entrer le Jeton d'Accès","أدخل رمز الوصول"],
"credits":    ["⚡ Remaining Credits","⚡ Verbleibendes Guthaben","⚡ Créditos Restantes","⚡ Crediti Rimanenti","⚡ Kalan Krediler","⚡ Pozostałe Kredyty","⚡ Resterende Credits","⚡ Återstående Krediter","⚡ Créditos Restantes","⚡ Crédits Restants","⚡ الرصيد المتبقي"],
"auth_ok":    ["✅ Access Granted! 1 credit deducted.","✅ Zugriff gewährt! 1 Guthaben abgezogen.","✅ ¡Acceso concedido! 1 crédito descontado.","✅ Accesso consentito! 1 credito detratto.","✅ Erişim sağlandı! 1 kredi düşüldü.","✅ Dostęp przyznany! 1 kredyt pobrany.","✅ Toegang verleend! 1 credit afgetrokken.","✅ Åtkomst beviljad! 1 kredit avdragen.","✅ Acesso concedido! 1 crédito deduzido.","✅ Accès accordé ! 1 crédit déduit.","✅ تم منح الوصول! تم خصم رصيد واحد."],
"auth_bad":   ["❌ Invalid token.","❌ Ungültiger Token.","❌ Token no válido.","❌ Token non valido.","❌ Geçersiz token.","❌ Nieprawidłowy token.","❌ Ongeldig token.","❌ Ogiltig token.","❌ Token inválido.","❌ Jeton non valide.","❌ رمز غير صالح."],
"auth_off":   ["❌ Token disabled.","❌ Token deaktiviert.","❌ Token deshabilitado.","❌ Token disabilitato.","❌ Token devre dışı.","❌ Token wyłączony.","❌ Token uitgeschakeld.","❌ Token inaktiverad.","❌ Token desativado.","❌ Jeton désactivé.","❌ الرمز معطل."],
"auth_zero":  ["❌ No credits left.","❌ Keine Versuche übrig.","❌ Sin intentos restantes.","❌ Nessun tentativo rimasto.","❌ Deneme hakkı kalmadı.","❌ Brak prób.","❌ Geen pogingen over.","❌ Inga försök kvar.","❌ Sem tentativas.","❌ Aucune tentative restante.","❌ لا محاولات متبقية."],
"auth_lock":  ["🚨 Locked for 30s (3 failures).","🚨 30 Sek. gesperrt (3 Fehler).","🚨 Bloqueado 30s (3 fallos).","🚨 Bloccato 30s (3 errori).","🚨 30 sn kilit (3 hata).","🚨 Zablokowane 30s (3 błędy).","🚨 30s vergrendeld (3 fouten).","🚨 Låst i 30s (3 fel).","🚨 Bloqueado 30s (3 falhas).","🚨 Bloqué 30s (3 échecs).","🚨 مقفل 30 ثانية (3 أخطاء)."],
"auth_hij":   ["⚠️ Token used on another device.","⚠️ Token auf anderem Gerät.","⚠️ Token usado en otro dispositivo.","⚠️ Token su altro dispositivo.","⚠️ Token başka cihazda.","⚠️ Token na innym urządzeniu.","⚠️ Token op ander apparaat.","⚠️ Token på annan enhet.","⚠️ Token em outro dispositivo.","⚠️ Jeton sur un autre appareil.","⚠️ الرمز على جهاز آخر."],
"auth_warn":  ["🚨 Authentication required.","🚨 Authentifizierung erforderlich.","🚨 Autenticación requerida.","🚨 Autenticazione richiesta.","🚨 Kimlik doğrulama gerekli.","🚨 Wymagane uwierzytelnienie.","🚨 Authenticatie vereist.","🚨 Autentisering krävs.","🚨 Autenticação necessária.","🚨 Authentification requise.","🚨 المصادقة مطلوبة."],
"price":      ["Selling Price ($)","Verkaufspreis (€)","Precio de Venta (€)","Prezzo di Vendita (€)","Satış Fiyatı ($)","Cena Sprzedaży (zł)","Verkoopprijs (€)","Försäljningspris (kr)","Preço de Venda (R$)","Prix de Vente (€)","سعر البيع ($)"],
"cogs":       ["COGS Cost ($)","COGS-Kosten (€)","Costo COGS (€)","Costo COGS (€)","COGS Maliyeti ($)","Koszt COGS (zł)","COGS Kosten (€)","COGS-kostnad (kr)","Custo COGS (R$)","Coût COGS (€)","تكلفة COGS ($)"],
"ship":       ["Shipping per Unit ($)","Versand pro Einheit (€)","Envío por Unidad (€)","Spedizione per Unità (€)","Nakliye ($)","Wysyłka (zł)","Verzend (€)","Frakt (kr)","Envio (R$)","Expédition (€)","الشحن ($)"],
"referral":   ["Referral Fee (%)","Vermittlungsgebühr (%)","Tarifa de Referencia (%)","Commissione (%)","Komisyon (%)","Prowizja (%)","Verwijzingsvergoeding (%)","Hänvisningsavgift (%)","Intermediação (%)","Frais de Référence (%)","رسوم الإحالة (%)"],
"fba":        ["FBA Fee ($)","FBA Gebühr (€)","Tarifa FBA (€)","Tariffa FBA (€)","FBA Ücreti ($)","Opłata FBA (zł)","FBA Kosten (€)","FBA-avgift (kr)","Tarifa FBA (R$)","Frais FBA (€)","رسوم FBA ($)"],
"ppc":        ["PPC Cost per Unit ($)","PPC Kosten/Einheit (€)","Costo PPC por Unidad (€)","Costo PPC per Unità (€)","PPC Maliyeti ($)","Koszt PPC (zł)","PPC Kosten (€)","PPC-kostnad (kr)","Custo PPC (R$)","Coût PPC (€)","تكلفة PPC ($)"],
"calc_ok":    ["✅ Profitability calculated!","✅ Rentabilität berechnet!","✅ ¡Rentabilidad calculada!","✅ Redditività calcolata!","✅ Karlılık hesaplandı!","✅ Rentowność obliczona!","✅ Winstgevendheid berekend!","✅ Lönsamhet beräknad!","✅ Lucratividade calculada!","✅ Rentabilité calculée !","✅ تم حساب الربحية!"],
"summary":    ["📈 Financial Summary","📈 Finanzübersicht","📈 Resumen Financiero","📈 Riepilogo Finanziario","📈 Finansal Özet","📈 Podsumowanie Finansowe","📈 Financieel Overzicht","📈 Finansiell Sammanfattning","📈 Resumo Financeiro","📈 Résumé Financier","📈 الملخص المالي"],
"m_profit":   ["Net Profit/Unit","Nettogewinn/Einheit","Beneficio Neto/Unidad","Profitto Netto/Unità","Net Kar/Birim","Zysk Netto/Sztukę","Nettowinst/Eenheid","Nettovinst/Enhet","Lucro Líquido/Unidade","Bénéfice Net/Unité","صافي الربح/وحدة"],
"m_margin":   ["Profit Margin","Gewinnmarge","Margen de Beneficio","Margine di Profitto","Kar Marjı","Marża Zysku","Winstmarge","Vinstmarginal","Margem de Lucro","Marge Bénéficiaire","هامش الربح"],
"m_roi":      ["ROI","Kapitalrendite","ROI","ROI","ROI","ROI","ROI","ROI","ROI","ROI","ROI"],
"m_fees":     ["Total Amazon Fees","Amazon-Gebühren","Tarifas Amazon","Commissioni Amazon","Amazon Ücretleri","Opłaty Amazon","Amazon Kosten","Amazon-avgifter","Tarifas Amazon","Frais Amazon","رسوم أمازون"],
"curr":       ["$","€","€","€","$","zł","€","kr","R$","€","$"],
"brand":      ["Brand Name","Markenname","Nombre de la Marca","Nome Marchio","Marka Adı","Nazwa Marki","Merknaam","Varumärkesnamn","Nome da Marca","Nom de la Marque","اسم العلامة التجارية"],
"category":   ["Category","Kategorie","Categoría","Categoria","Kategori","Kategoria","Categorie","Kategori","Categoria","Catégorie","الفئة"],
"prod_name":  ["Product Name","Produktname","Nombre del Producto","Nome Prodotto","Ürün Adı","Nazwa Produktu","Productnaam","Produktnamn","Nome do Produto","Nom du Produit","اسم المنتج"],
"variant":    ["Variant / Color / Size","Variante / Farbe / Größe","Variante / Color / Talla","Variante / Colore / Taglia","Varyant / Renk / Boyut","Wariant / Kolor / Rozmiar","Variant / Kleur / Maat","Variant / Färg / Storlek","Variante / Cor / Tamanho","Variante / Couleur / Taille","المتغير / اللون / الحجم"],
"features":   ["Features (one per line)","Merkmale (eine pro Zeile)","Características (una por línea)","Caratteristiche (una per riga)","Özellikler (her satıra bir)","Cechy (jedna w wierszu)","Kenmerken (één per regel)","Funktioner (en per rad)","Recursos (um por linha)","Caractéristiques (une par ligne)","الميزات (واحدة في كل سطر)"],
"keywords":   ["Keywords (comma separated)","Keywords (kommagetrennt)","Palabras Clave (por comas)","Keyword (per virgola)","Anahtar Kelimeler (virgülle)","Słowa Kluczowe (przecinki)","Trefwoorden (komma)","Nyckelord (komma)","Palavras-Chave (vírgula)","Mots-Clés (virgules)","الكلمات المفتاحية (فواصل)"],
"lbl_title":  ["1. Product Title (75 chars):","1. Produkttitel (75 Zeichen):","1. Título (75 caracteres):","1. Titolo (75 caratteri):","1. Başlık (75 karakter):","1. Tytuł (75 znaków):","1. Titel (75 tekens):","1. Titel (75 tecken):","1. Título (75 caracteres):","1. Titre (75 caractères) :","1. العنوان (75 حرفًا):"],
"lbl_high":   ["2. Highlights (125 chars):","2. Highlights (125 Zeichen):","2. Destacados (125 caracteres):","2. Punti Salienti (125 caratteri):","2. Öne Çıkanlar (125 karakter):","2. Najważniejsze Cechy (125 znaków):","2. Hoogtepunten (125 tekens):","2. Höjdpunkter (125 tecken):","2. Destaques (125 caracteres):","2. Points Forts (125 caractères) :","2. أبرز الميزات (125 حرفًا):"],
"lbl_bullets":["3. Bullet Points (5 core):","3. Aufzählungspunkte (5):","3. Viñetas (5):","3. Punti Chiave (5):","3. Madde İşaretleri (5):","3. Punkty (5):","3. Opsommingspunten (5):","3. Punktlista (5):","3. Tópicos (5):","3. Puces (5) :","3. النقاط الرئيسية (5):"],
"lbl_desc":   ["4. Description (HTML, 2000 chars):","4. Beschreibung (HTML, 2000 Zeichen):","4. Descripción (HTML, 2000 caracteres):","4. Descrizione (HTML, 2000 caratteri):","4. Açıklama (HTML, 2000 karakter):","4. Opis (HTML, 2000 znaków):","4. Beschrijving (HTML, 2000 tekens):","4. Beskrivning (HTML, 2000 tecken):","4. Descrição (HTML, 2000 caracteres):","4. Description (HTML, 2000 caractères) :","4. الوصف (HTML، 2000 حرف):"],
"chars":      ["chars","Zeichen","caracteres","caratteri","karakter","znaków","tekens","tecken","caracteres","caractères","حرف"],
"bullet":     ["Bullet","Aufzählungspunkt","Viñeta","Punto Chiave","Madde İşareti","Punkt","Opsommingspunt","Punkt","Tópico","Puce","النقطة"],
"draft_hdr":  ["📋 Ready Listing Draft:","📋 Fertiger Listing-Entwurf:","📋 Borrador Listo:","📋 Bozza Listing Pronta:","📋 Hazır İlan Taslağı:","📋 Gotowy Szkic Oferty:","📋 Klaar Listing Concept:","📋 Klart Listing-utkast:","📋 Rascunho Pronto:","📋 Brouillon Prêt :","📋 مسودة جاهزة:"],
"gen_ok":     ["✅ Listing drafted!","✅ Entwurf erstellt!","✅ ¡Borrador creado!","✅ Bozza creata!","✅ Taslak oluşturuldu!","✅ Szkic utworzony!","✅ Concept aangemaakt!","✅ Utkast skapat!","✅ Rascunho criado!","✅ Brouillon créé !","✅ تم إنشاء المسودة!"],
"val_desc":   ["Check against Amazon limits.","Gegen Amazon-Limits prüfen.","Verificar contra límites de Amazon.","Controlla i limiti Amazon.","Amazon limitlerine karşı kontrol edin.","Sprawdź limity Amazon.","Controleer tegen Amazon-limieten.","Kontrollera mot Amazon-gränser.","Verifique contra limites da Amazon.","Vérifier contre les limites Amazon.","تحقق من حدود أمازون."],
"v_title":    ["Product Title (75)","Produkttitel (75)","Título (75)","Titolo (75)","Başlık (75)","Tytuł (75)","Titel (75)","Titel (75)","Título (75)","Titre (75)","العنوان (75)"],
"v_bp":       ["Bullet %d (250)","Aufzählungspunkt %d (250)","Viñeta %d (250)","Punto %d (250)","Madde %d (250)","Punkt %d (250)","Opsommingspunt %d (250)","Punkt %d (250)","Tópico %d (250)","Puce %d (250)","النقطة %d (250)"],
"v_report":   ["Validation Report:","Validierungsbericht:","Informe de Validación:","Report di Validazione:","Doğrulama Raporu:","Raport Walidacji:","Validatierapport:","Valideringsrapport:","Relatório de Validação:","Rapport de Validation :","تقرير التحقق:"],
"v_pass":     ["✅ Pass","✅ Bestanden","✅ Aprobado","✅ Superato","✅ Başarılı","✅ Pozytywny","✅ Goedgekeurd","✅ Godkänd","✅ Aprovado","✅ Validé","✅ نجاح"],
"v_warn":     ["⚠️ Over limit","⚠️ Limit überschritten","⚠️ Límite excedido","⚠️ Limite superato","⚠️ Limit aşıldı","⚠️ Przekroczono limit","⚠️ Limiet overschreden","⚠️ Över gränsen","⚠️ Acima do limite","⚠️ Limite dépassée","⚠️ تجاوز الحد"],
"v_suggest":  ["💡 Suggested:","💡 Vorschlag:","💡 Sugerencia:","💡 Suggerimento:","💡 Öneri:","💡 Sugestia:","💡 Suggestie:","💡 Förslag:","💡 Sugestão:","💡 Suggestion :","💡 المقترح:"],
"v_ok":       ["✅ Validation complete!","✅ Validierung abgeschlossen!","✅ ¡Validación completada!","✅ Validazione completata!","✅ Doğrulama tamamlandı!","✅ Walidacja zakończona!","✅ Validatie voltooid!","✅ Validering slutförd!","✅ Validação concluída!","✅ Validation terminée !","✅ اكتمل التحقق!"],
"opt_desc":   ["Clean backend keywords: removes commas, filters stopwords, enforces 249-byte limit.","Backend-Keywords bereinigen: Kommas entfernen, Füllwörter filtern, 249-Byte-Limit.","Limpiar palabras clave: quita comas, filtra stopwords, límite de 249 bytes.","Pulisci keyword: rimuove virgole, filtra stopword, limite 249 byte.","Anahtar kelimeleri temizle: virgül kaldır, stopword filtrele, 249 bayt limiti.","Oczyść słowa kluczowe: usuwa przecinki, filtruje stopwords, limit 249 bajtów.","Schoon zoekwoorden: verwijdert komma's, filtert stopwoorden, 249-byte limiet.","Rensa nyckelord: tar bort kommatecken, filtrerar stoppord, 249-byte gräns.","Limpar palavras-chave: remove vírgulas, filtra stopwords, limite 249 bytes.","Nettoyer les mots-clés : supprime virgules, filtre stopwords, limite 249 octets.","تنظيف الكلمات: إزالة الفواصل، تصفية الكلمات، حد 249 بايت."],
"opt_input":  ["Paste raw keywords:","Rohe Keywords einfügen:","Pegar palabras clave:","Incolla keyword:","Ham anahtar kelimeler:","Wklej słowa kluczowe:","Plak zoekwoorden:","Klistra in nyckelord:","Colar palavras-chave:","Coller les mots-clés :","الصق الكلمات:"],
"opt_output": ["Copy to Seller Central (≤249 bytes):","In Seller Central kopieren (≤249 Byte):","Copiar a Seller Central (≤249 bytes):","Copia in Seller Central (≤249 byte):","Seller Central'a kopyala (≤249 bayt):","Kopiuj do Seller Central (≤249 bajtów):","Kopieer naar Seller Central (≤249 bytes):","Kopiera till Seller Central (≤249 byte):","Copiar para Seller Central (≤249 bytes):","Copier dans Seller Central (≤249 octets) :","انسخ إلى Seller Central (≤249 بايت):"],
"opt_ok":     ["✅ Optimized!","✅ Optimiert!","✅ ¡Optimizado!","✅ Ottimizzato!","✅ Optimize edildi!","✅ Zoptymalizowano!","✅ Geoptimaliseerd!","✅ Optimerad!","✅ Otimizado!","✅ Optimisé !","✅ تم التحسين!"],
"opt_stats":  ["Final: {c} chars | {b}/249 bytes","Endstatistik: {c} Zeichen | {b}/249 Byte","Final: {c} caracteres | {b}/249 bytes","Finale: {c} caratteri | {b}/249 byte","Son: {c} karakter | {b}/249 bayt","Statystyki: {c} znaków | {b}/249 bajtów","Eind: {c} tekens | {b}/249 bytes","Slutlig: {c} tecken | {b}/249 byte","Final: {c} caracteres | {b}/249 bytes","Final : {c} caractères | {b}/249 octets","النهائي: {c} حرف | {b}/249 بايت"],
"inv_desc":   ["Calculate daily velocity and reorder schedule.","Tägliche Verkaufsgeschwindigkeit und Nachbestellplan berechnen.","Calcular velocidad de ventas y calendario.","Calcola velocità di vendita e rifornimento.","Günlük satış hızı ve yeniden sipariş planı.","Oblicz prędkość sprzedaży i harmonogram.","Bereken dagelijkse snelheid en herbestelling.","Beräkna daglig hastighet och påfyllning.","Calcular velocidade de vendas e reestocagem.","Calculer la vélocité et le réapprovisionnement.","حساب سرعة المبيعات وجدول إعادة الطلب."],
"inv_units":  ["Units Sold","Verkaufte Einheiten","Unidades Vendidas","Unità Vendute","Satılan Birim","Sprzedane Sztuki","Verkochte Eenheden","Sålda Enheter","Unidades Vendidas","Unités Vendues","الوحدات المباعة"],
"inv_days":   ["Window (Days)","Zeitfenster (Tage)","Ventana (Días)","Finestra (Giorni)","Pencere (Gün)","Okno (Dni)","Periode (Dagen)","Fönster (Dagar)","Janela (Dias)","Fenêtre (Jours)","النافذة (أيام)"],
"inv_stockout":["Stockout Days","Bestandsfreie Tage","Días sin Stock","Giorni di Esaurimento","Stoksuz Gün","Dni Braku Towaru","Dagen Zonder Voorraad","Dagar Utan Lager","Dias sem Estoque","Jours de Rupture","أيام نفاد المخزون"],
"inv_curr":   ["Current Stock","Aktueller Bestand","Inventario Actual","Inventario Attuale","Mevcut Stok","Aktualne Zapasy","Huidige Voorraad","Aktuellt Lager","Estoque Atual","Stock Actuel","المخزون الحالي"],
"inv_lead":   ["Lead Time (Days)","Lieferzeit (Tage)","Plazo de Entrega (Días)","Tempo di Consegna (Giorni)","Teslim Süresi (Gün)","Czas Realizacji (Dni)","Levertijd (Dagen)","Leveranstid (Dagar)","Prazo de Entrega (Dias)","Délai de Livraison (Jours)","مهلة التوريد (أيام)"],
"inv_safety": ["Safety Days","Sicherheitspolster (Tage)","Stock Seguridad (Días)","Scorta Sicurezza (Giorni)","Güvenlik Stoku (Gün)","Zapasy Bezpieczeństwa (Dni)","Veiligheidsvoorraad (Dagen)","Säkerhetslager (Dagar)","Estoque de Segurança (Dias)","Stock de Sécurité (Jours)","أيام الأمان"],
"inv_ok":     ["✅ Restock schedule calculated!","✅ Nachbestellplan berechnet!","✅ ¡Calendario calculado!","✅ Programma calcolato!","✅ Yeniden sipariş takvimi hesaplandı!","✅ Harmonogram obliczony!","✅ Herbestelschema berekend!","✅ Påfyllningsschema beräknat!","✅ Cronograma calculado!","✅ Calendrier calculé !","✅ تم حساب الجدول!"],
"inv_summary":["📈 Forecast Summary","📈 Prognose-Zusammenfassung","📈 Resumen de Previsión","📈 Riepilogo Previsioni","📈 Tahmin Özeti","📈 Podsumowanie Prognozy","📈 Prognose Overzicht","📈 Prognossammanfattning","📈 Resumo da Previsão","📈 Résumé des Prévisions","📈 ملخص التنبؤ"],
"inv_m1":     ["Days of Supply","Verbleibende Reichweite","Días de Suministro","Giorni di Copertura","Kalan Stok Günleri","Pozostałe Dni Zapasu","Resterende Voorraaddagen","Återstående Lagerdagar","Dias de Cobertura","Jours de Stock","أيام المخزون"],
"inv_m2":     ["Reorder Threshold","Nachbestell-Schwelle","Umbral de Reabastecimiento","Soglia di Rifornimento","Yeniden Sipariş Eşiği","Próg Zamówienia","Herbesteldrempel","Tröskel för Beställning","Ponto de Reabastecimento","Seuil de Réapprovisionnement","عتبة إعادة الطلب"],
"inv_m3":     ["Recommended Qty","Empfohlene Menge","Cant. Recomendada","Qtà Consigliata","Önerilen Miktar","Zalecana Ilość","Aanbevolen Hoeveelheid","Rekommenderad Kvantitet","Quantidade Recomendada","Qté Recommandée","الكمية الموصى بها"],
"inv_true":   ["True Velocity","Echte Geschwindigkeit","Velocidad Real","Velocità Reale","Gerçek Hız","Rzeczywista Prędkość","Echte Snelheid","Sann Hastighet","Velocidade Real","Vélocité Réelle","السرعة الحقيقية"],
"inv_unit":   ["Units","Einheiten","Unidades","Unità","Birim","Sztuk","Eenheden","Enheter","Unidades","Unités","وحدة"],
"inv_day":    ["Days","Tage","Días","Giorni","Gün","Dni","Dagen","Dagar","Dias","Jours","أيام"],
"neg_sample_h":["📄 Sample CSV: Customer Search Term, Clicks, Orders, Spend","📄 Beispiel-CSV: Suchbegriff, Klicks, Bestellungen, Ausgaben","📄 Ejemplo CSV: Término, Clics, Pedidos, Gasto","📄 Esempio CSV: Termine, Click, Ordini, Spesa","📄 Örnek CSV: Arama Terimi, Tıklama, Sipariş, Harcama","📄 Przykład CSV: Fraza, Kliknięcia, Zamówienia, Wydatki","📄 Voorbeeld CSV: Zoekterm, Clicks, Bestellingen, Besteding","📄 Exempel CSV: Sökterm, Klick, Beställningar, Kostnad","📄 Exemplo CSV: Termo, Cliques, Pedidos, Gasto","📄 Exemple CSV : Terme, Clics, Commandes, Dépense","📄 نموذج CSV: المصطلح، النقرات، الطلبات، الإنفاق"],
"neg_sample_btn":["📥 Download Sample CSV","📥 Muster-CSV Herunterladen","📥 Descargar CSV de Ejemplo","📥 Scarica CSV di Esempio","📥 Örnek CSV İndir","📥 Pobierz Przykładowy CSV","📥 Download Voorbeeld CSV","📥 Ladda ner Exempel CSV","📥 Baixar CSV de Exemplo","📥 Télécharger le CSV d'Exemple","📥 تنزيل نموذج CSV"],
"neg_upload": ["Upload PPC Search Term Report (.csv, .xlsx, .xls)","PPC Suchbegriff-Bericht hochladen (.csv, .xlsx, .xls)","Subir Informe PPC (.csv, .xlsx, .xls)","Carica Report PPC (.csv, .xlsx, .xls)","PPC Raporu Yükle (.csv, .xlsx, .xls)","Prześlij Raport PPC (.csv, .xlsx, .xls)","Upload PPC Rapport (.csv, .xlsx, .xls)","Ladda upp PPC Rapport (.csv, .xlsx, .xls)","Enviar Relatório PPC (.csv, .xlsx, .xls)","Télécharger le Rapport PPC (.csv, .xlsx, .xls)","تحميل تقرير PPC (.csv, .xlsx, .xls)"],
"neg_min":    ["Min Clicks","Min. Klicks","Clics Mín.","Click Min.","Min Tıklama","Min. Kliknięcia","Min. Clicks","Min. Klick","Cliques Mín.","Clics Min.","أدنى نقرات"],
"neg_max":    ["Max Orders","Max. Bestellungen","Pedidos Máx.","Ordini Max.","Maks Sipariş","Maks. Zamówienia","Max. Bestellingen","Max. Beställningar","Pedidos Máx.","Commandes Max.","أقصى طلبات"],
"neg_ok":     ["✅ Found {n} wasteful terms!","✅ {n} unrentable Begriffe gefunden!","✅ ¡{n} términos inútiles encontrados!","✅ Trovati {n} termini inutili!","✅ {n} verimsiz terim bulundu!","✅ Znaleziono {n} nieefektywnych fraz!","✅ {n} onrendabele termen gevonden!","✅ Hittade {n} onödiga termer!","✅ Encontrados {n} termos ineficientes!","✅ {n} termes inutiles trouvés !","✅ تم العثور على {n} مصطلحات هادرة!"],
"neg_download":["📥 Download Negative Keywords CSV","📥 Negativ-Keywords CSV Herunterladen","📥 Descargar CSV de Negativas","📥 Scarica CSV Negative","📥 Negatif Kelimeler CSV İndir","📥 Pobierz CSV Negatywnych","📥 Download Negatieve CSV","📥 Ladda ner Negativa CSV","📥 Baixar CSV de Negativas","📥 Télécharger le CSV des Négatifs","📥 تنزيل ملف CSV للكلمات السلبية"],
"neg_err":    ["❌ Could not identify Term/Clicks/Orders columns.","❌ Spalten Suchbegriff/Klicks/Bestellungen nicht erkannt.","❌ No se pudieron identificar las columnas.","❌ Impossibile identificare le colonne.","❌ Sütunlar tanınamadı.","❌ Nie można zidentyfikować kolumn.","❌ Kolommen niet herkend.","❌ Kunde inte identifiera kolumner.","❌ Não foi possível identificar colunas.","❌ Impossible d'identifier les colonnes.","❌ تعذر تحديد الأعمدة."],
"bid_desc":   ["Upload Amazon report; auto-detects Spend, Sales, Bid columns. Supports CSV, XLSX, XLS.","Amazon-Bericht hochladen; erkennt Ausgaben, Umsatz, Gebot. CSV, XLSX, XLS.","Subir informe; detecta Gasto, Ventas, Puja. CSV, XLSX, XLS.","Carica report; rileva Spesa, Vendite, Offerta. CSV, XLSX, XLS.","Rapor yükle; Harcama, Satış, Teklif algılanır. CSV, XLSX, XLS.","Prześlij raport; wykrywa Wydatki, Sprzedaż, Stawkę. CSV, XLSX, XLS.","Upload rapport; detecteert Besteding, Verkoop, Bod. CSV, XLSX, XLS.","Ladda upp rapport; hittar Kostnad, Försäljning, Bud. CSV, XLSX, XLS.","Enviar relatório; detecta Gasto, Vendas, Lance. CSV, XLSX, XLS.","Télécharger rapport ; détecte Dépense, Ventes, Enchère. CSV, XLSX, XLS.","تحميل التقرير؛ يكشف الإنفاق والمبيعات والعرض. CSV, XLSX, XLS."],
"bid_target": ["Target ACoS (%)","Ziel-ACoS (%)","ACoS Objetivo (%)","ACoS Obiettivo (%)","Hedef ACoS (%)","Docelowy ACoS (%)","Doel ACoS (%)","Mål-ACoS (%)","ACoS Meta (%)","ACoS Cible (%)","ACoS المستهدف (%)"],
"bid_min":    ["Min Bid ($)","Min. Gebot (€)","Puja Mín. (€)","Offerta Min. (€)","Min Teklif ($)","Min. Stawka (zł)","Min. Bod (€)","Min. Bud (kr)","Lance Mín. (R$)","Enchère Min. (€)","أدنى عرض ($)"],
"bid_max":    ["Max Bid ($)","Max. Gebot (€)","Puja Máx. (€)","Offerta Max. (€)","Maks Teklif ($)","Maks. Stawka (zł)","Max. Bod (€)","Max. Bud (kr)","Lance Máx. (R$)","Enchère Max. (€)","أقصى عرض ($)"],
"bid_upload": ["Upload PPC Report (.csv, .xlsx, .xls)","PPC-Bericht hochladen (.csv, .xlsx, .xls)","Subir Informe PPC (.csv, .xlsx, .xls)","Carica Report PPC (.csv, .xlsx, .xls)","PPC Raporu Yükle (.csv, .xlsx, .xls)","Prześlij Raport PPC (.csv, .xlsx, .xls)","Upload PPC Rapport (.csv, .xlsx, .xls)","Ladda upp PPC Rapport (.csv, .xlsx, .xls)","Enviar Relatório PPC (.csv, .xlsx, .xls)","Télécharger Rapport PPC (.csv, .xlsx, .xls)","تحميل تقرير PPC (.csv, .xlsx, .xls)"],
"bid_preview":["📊 Raw Campaign Data:","📊 Rohdaten der Kampagne:","📊 Datos Crudos de Campaña:","📊 Dati Grezzi Campagna:","📊 Ham Kampanya Verisi:","📊 Surowe Dane Kampanii:","📊 Ruwe Campagnegegevens:","📊 Rå Kampanjdata:","📊 Dados Brutos da Campanha:","📊 Données Brutes de Campagne :","📊 بيانات الحملة الخام:"],
"bid_ok":     ["✅ Bids optimized!","✅ Gebote optimiert!","✅ ¡Pujas optimizadas!","✅ Offerte ottimizzate!","✅ Teklifler optimize edildi!","✅ Stawki zoptymalizowane!","✅ Biedingen geoptimaliseerd!","✅ Bud optimerade!","✅ Lances otimizados!","✅ Enchères optimisées !","✅ تم تحسين العروض!"],
"bid_download":["📥 Download Optimized Bids CSV","📥 Optimierte Gebote CSV","📥 Descargar CSV de Pujas","📥 Scarica CSV Offerte","📥 Optimize Teklifler CSV","📥 Pobierz CSV Stawek","📥 Download Biedingen CSV","📥 Ladda ner Bud CSV","📥 Baixar CSV de Lances","📥 Télécharger le CSV des Enchères","📥 تنزيل ملف CSV للعروض المحسّنة"],
"bid_col_acos":["Actual_ACoS","Tatsächlicher_ACoS","ACoS_Real","ACoS_Reale","Gerçek_ACoS","Rzeczywisty_ACoS","Werkelijke_ACoS","Faktisk_ACoS","ACoS_Real","ACoS_Réel","ACoS_الفعلي"],
"bid_col_new": ["Optimized_New_Bid","Optimiertes_Neues_Gebot","Nueva_Puja_Optimizada","Nuova_Offerta_Ottimizzata","Optimize_Edilmis_Yeni_Teklif","Zoptymalizowana_Nowa_Stawka","Geoptimaliseerd_Nieuw_Bod","Optimerat_Nytt_Bud","Novo_Lance_Otimizado","Nouvelle_Enchère_Optimisée","عرض_السعر_المحسن"],
"bid_err":    ["❌ Could not find Spend/Sales/Bid columns.","❌ Spalten Ausgaben/Umsatz/Gebot nicht gefunden.","❌ No se encontraron las columnas.","❌ Colonne non trovate.","❌ Sütunlar bulunamadı.","❌ Nie znaleziono kolumn.","❌ Kolommen niet gevonden.","❌ Kunde inte hitta kolumner.","❌ Colunas não encontradas.","❌ Colonnes introuvables.","❌ لم يتم العثور على الأعمدة."],
"acos_desc":  ["Monitor ad efficiency and organic growth.","Werbeeffizienz und organisches Wachstum überwachen.","Monitorear eficiencia y crecimiento orgánico.","Monitora efficienza e crescita organica.","Reklam verimliliği ve organik büyümeyi izle.","Monitoruj wydajność i wzrost organiczny.","Bewaak efficiëntie en organische groei.","Övervaka effektivitet och organisk tillväxt.","Monitore eficiência e crescimento orgânico.","Surveiller l'efficacité et la croissance organique.","راقب الكفاءة والنمو العضوي."],
"acos_sales": ["Total Gross Sales","Gesamtumsatz","Ventas Brutas Totales","Vendite Lorde Totali","Toplam Satış","Całkowita Sprzedaż","Totale Verkoop","Total Försäljning","Vendas Brutas Totais","Ventes Brutes Totales","إجمالي المبيعات"],
"acos_spend": ["PPC Ad Spend","PPC-Werbeausgaben","Gasto PPC","Spesa PPC","PPC Harcama","Wydatki PPC","PPC Besteding","PPC Kostnad","Gasto PPC","Dépenses PPC","إنفاق PPC"],
"acos_adsales":["PPC Ad Sales","PPC-Werbeumsatz","Ventas PPC","Vendite PPC","PPC Satış","Sprzedaż PPC","PPC Verkoop","PPC Försäljning","Vendas PPC","Ventes PPC","مبيعات PPC"],
"acos_target":["Target TACOS (%)","Ziel-TACOS (%)","TACOS Objetivo (%)","TACOS Obiettivo (%)","Hedef TACOS (%)","Docelowy TACOS (%)","Doel TACOS (%)","Mål-TACOS (%)","TACOS Meta (%)","TACOS Cible (%)","TACOS المستهدف (%)"],
"acos_dash":  ["📉 Executive Dashboard:","📉 Executive-Dashboard:","📉 Panel Ejecutivo:","📉 Pannello Esecutivo:","📉 Yönetici Paneli:","📉 Panel Menedżerski:","📉 Executive Dashboard:","📉 Executive Dashboard:","📉 Painel Executivo:","📉 Tableau Exécutif :","📉 لوحة الإدارة:"],
"acos_m1":    ["ACoS","ACoS","ACoS","ACoS","ACoS","ACoS","ACoS","ACoS","ACoS","ACoS","ACoS"],
"acos_m2":    ["TACOS","TACOS","TACOS","TACOS","TACOS","TACOS","TACOS","TACOS","TACOS","TACOS","TACOS"],
"acos_m3":    ["Organic Sales","Organische Verkäufe","Ventas Orgánicas","Vendite Organiche","Organik Satış","Sprzedaż Organiczna","Organische Verkoop","Organisk Försäljning","Vendas Orgânicas","Ventes Organiques","المبيعات العضوية"],
"acos_m4":    ["Organic Ratio","Organischer Anteil","Proporción Orgánica","Rapporto Organico","Organik Oran","Udział Organiczny","Organisch Aandeel","Organisk Andel","Proporção Orgânica","Ratio Organique","نسبة عضوية"],
"acos_insight":["💡 Insights:","💡 Einblicke:","💡 Perspectivas:","💡 Approfondimenti:","💡 İçgörüler:","💡 Wskazówki:","💡 Inzichten:","💡 Insikter:","💡 Insights:","💡 Analyses :","💡 الرؤى:"],
"acos_ok":    ["✅ TACOS analyzed!","✅ TACOS analysiert!","✅ ¡TACOS analizado!","✅ TACOS analizzato!","✅ TACOS analiz edildi!","✅ TACOS przeanalizowany!","✅ TACOS geanalyseerd!","✅ TACOS analyserad!","✅ TACOS analisado!","✅ TACOS analysé !","✅ تم تحليل TACOS!"],
"acos_healthy":["✅ Healthy: TACOS {v}% ≤ target {t}%.","✅ Gesund: TACOS {v}% ≤ Ziel {t}%.","✅ Saludable: TACOS {v}% ≤ objetivo {t}%.","✅ Sano: TACOS {v}% ≤ obiettivo {t}%.","✅ Sağlıklı: TACOS {v}% ≤ hedef {t}%.","✅ Zdrowy: TACOS {v}% ≤ cel {t}%.","✅ Gezond: TACOS {v}% ≤ doel {t}%.","✅ Hälsosam: TACOS {v}% ≤ mål {t}%.","✅ Saudável: TACOS {v}% ≤ meta {t}%.","✅ Sain : TACOS {v}% ≤ cible {t}%.","✅ سليم: TACOS {v}% ≤ الهدف {t}%."],
"acos_warn":  ["⚠️ High spend: TACOS {v}% > target {t}%.","⚠️ Hohe Ausgaben: TACOS {v}% > Ziel {t}%.","⚠️ Gasto alto: TACOS {v}% > objetivo {t}%.","⚠️ Spesa alta: TACOS {v}% > obiettivo {t}%.","⚠️ Yüksek harcama: TACOS {v}% > hedef {t}%.","⚠️ Wysokie wydatki: TACOS {v}% > cel {t}%.","⚠️ Hoge uitgaven: TACOS {v}% > doel {t}%.","⚠️ Hög kostnad: TACOS {v}% > mål {t}%.","⚠️ Gasto alto: TACOS {v}% > meta {t}%.","⚠️ Dépense élevée : TACOS {v}% > cible {t}%.","⚠️ إنفاق مرتفع: TACOS {v}% > الهدف {t}%."],
"admin_title":["👥 Client Token Security & Control","👥 Client-Token-Sicherheit & Steuerung","👥 Seguridad de Tokens","👥 Sicurezza Token Clienti","👥 İstemci Token Güvenliği","👥 Bezpieczeństwo Tokenów","👥 Client Token Beveiliging","👥 Klienttoken-säkerhet","👥 Segurança de Tokens","👥 Sécurité des Tokens","👥 أمان رموز العملاء"],
"admin_remain":["Remaining","Verbleibend","Restante","Rimanenti","Kalan","Pozostało","Resterend","Återstående","Restantes","Restant","المتبقي"],
"admin_reset":["🔄 Reset","🔄 Zurücksetzen","🔄 Restablecer","🔄 Reimposta","🔄 Sıfırla","🔄 Resetuj","🔄 Reset","🔄 Återställ","🔄 Redefinir","🔄 Réinitialiser","🔄 إعادة تعيين"],
"admin_delete":["🗑️ Delete","🗑️ Löschen","🗑️ Eliminar","🗑️ Elimina","🗑️ Sil","🗑️ Usuń","🗑️ Verwijderen","🗑️ Ta bort","🗑️ Excluir","🗑️ Supprimer","🗑️ حذف"],
"admin_gen":  ["➕ Generate New Token","➕ Neuen Token Generieren","➕ Generar Nuevo Token","➕ Genera Nuovo Token","➕ Yeni Token Oluştur","➕ Generuj Nowy Token","➕ Genereer Nieuw Token","➕ Generera Ny Token","➕ Gerar Novo Token","➕ Générer un Nouveau Token","➕ إنشاء رمز جديد"],
"admin_tid":  ["Token Identifier","Token-Kennung","Identificador de Token","Identificativo Token","Token Tanımlayıcısı","Identyfikator Tokena","Token Identificatie","Tokenidentifierare","Identificador do Token","Identifiant du Token","معرف الرمز"],
"admin_att":  ["Credits","Guthaben","Créditos","Crediti","Krediler","Kredyty","Credits","Krediter","Créditos","Crédits","أرصدة"],
"admin_genbtn":["Generate Token","Token Generieren","Generar Token","Genera Token","Token Oluştur","Generuj Token","Genereer Token","Generera Token","Gerar Token","Générer le Token","إنشاء الرمز"],
"admin_pwd_t":["🔑 Update Master Password","🔑 Master-Passwort Aktualisieren","🔑 Actualizar Contraseña","🔑 Aggiorna Password","🔑 Ana Şifreyi Güncelle","🔑 Zaktualizuj Hasło","🔑 Update Hoofdwachtwoord","🔑 Uppdatera Huvudlösenord","🔑 Atualizar Senha Mestra","🔑 Mettre à Jour le Mot de Passe","🔑 تحديث كلمة المرور"],
"admin_new_pwd":["New Password","Neues Passwort","Nueva Contraseña","Nuova Password","Yeni Şifre","Nowe Hasło","Nieuw Wachtwoord","Nytt Lösenord","Nova Senha","Nouveau Mot de Passe","كلمة مرور جديدة"],
"admin_pwd_btn":["Update Password","Passwort Aktualisieren","Actualizar Contraseña","Aggiorna Password","Şifreyi Güncelle","Zaktualizuj Hasło","Update Wachtwoord","Uppdatera Lösenord","Atualizar Senha","Mettre à Jour","تحديث كلمة المرور"],
"admin_lock": ["🔒 Lock Admin Panel","🔒 Admin-Bereich Sperren","🔒 Bloquear Panel","🔒 Blocca Pannello","🔒 Paneli Kilitle","🔒 Zablokuj Panel","🔒 Vergrendel Paneel","🔒 Lås Panel","🔒 Bloquear Painel","🔒 Verrouiller le Panneau","🔒 قفل اللوحة"],
"admin_unlock_t":["Restricted Area. Password Required.","Geschützter Bereich. Passwort Erforderlich.","Área Restringida. Contraseña Requerida.","Area Riservata. Password Richiesta.","Kısıtlı Alan. Şifre Gerekli.","Obszar Zastrzeżony. Wymagane Hasło.","Beveiligde Zone. Wachtwoord Vereist.","Skyddat Område. Lösenord Krävs.","Área Restrita. Senha Necessária.","Zone Restreinte. Mot de Passe Requis.","منطقة مقيدة. كلمة المرور مطلوبة."],
"admin_unlock_l":["Enter Admin Password","Admin-Passwort Eingeben","Introducir Contraseña","Inserisci Password","Yönetici Şifresini Girin","Wprowadź Hasło","Voer Wachtwoord In","Ange Lösenord","Inserir Senha","Entrer le Mot de Passe","أدخل كلمة المرور"],
"admin_unlock_b":["Unlock Admin Panel","Admin-Bereich Entsperren","Desbloquear Panel","Sblocca Pannello","Paneli Aç","Odblokuj Panel","Ontgrendel Paneel","Lås Upp Panel","Desbloquear Painel","Déverrouiller le Panneau","فتح اللوحة"],
"admin_pwd_ok":["✅ Password updated!","✅ Passwort aktualisiert!","✅ ¡Contraseña actualizada!","✅ Password aggiornata!","✅ Şifre güncellendi!","✅ Hasło zaktualizowane!","✅ Wachtwoord bijgewerkt!","✅ Lösenord uppdaterat!","✅ Senha atualizada!","✅ Mot de passe mis à jour !","✅ تم تحديث كلمة المرور!"],
"admin_pwd_empty":["Password cannot be empty.","Passwort darf nicht leer sein.","La contraseña no puede estar vacía.","La password non può essere vuota.","Şifre boş olamaz.","Hasło nie może być puste.","Wachtwoord mag niet leeg zijn.","Lösenordet kan inte vara tomt.","A senha não pode estar vazia.","Le mot de passe ne peut pas être vide.","لا يمكن أن تكون كلمة المرور فارغة."],
"admin_bad_pwd":["❌ Invalid admin password.","❌ Ungültiges Admin-Passwort.","❌ Contraseña inválida.","❌ Password non valida.","❌ Geçersiz şifre.","❌ Nieprawidłowe hasło.","❌ Ongeldig wachtwoord.","❌ Ogiltigt lösenord.","❌ Senha inválida.","❌ Mot de passe invalide.","❌ كلمة مرور غير صالحة."],
"admin_new_ok":["✅ Token {t} created with {n} credits!","✅ Token {t} mit {n} Guthaben erstellt!","✅ ¡Token {t} creado con {n} créditos!","✅ Token {t} creato con {n} crediti!","✅ Token {t} oluşturuldu ({n} kredi)!","✅ Token {t} utworzony ({n} kredytów)!","✅ Token {t} aangemaakt ({n} credits)!","✅ Token {t} skapad ({n} krediter)!","✅ Token {t} criado ({n} créditos)!","✅ Token {t} créé avec {n} crédits !","✅ تم إنشاء الرمز {t} بـ {n} رصيد!"],
"ws_prepare": ["📥 Vendor File Preparation","📥 Lieferanten-Datei Aufbereitung","📥 Preparación de Archivo","📥 Preparazione File Fornitore","📥 Tedarikçi Dosyası Hazırlığı","📥 Przygotowanie Pliku","📥 Leverancier Bestand Voorbereiding","📥 Leverantörsfil Förberedelse","📥 Preparação de Arquivo","📥 Préparation du Fichier","📥 إعداد ملف المورد"],
"ws_catalog": ["📦 Supplier Catalog Analyzer","📦 Lieferanten-Katalog-Analysator","📦 Analizador de Catálogo","📦 Analizzatore Catalogo","📦 Tedarikçi Katalog Analizörü","📦 Analizator Katalogu","📦 Leverancier Catalogus","📦 Leverantörskatalog","📦 Analisador de Catálogo","📦 Analyseur de Catalogue","📦 محلل كتالوج المورد"],
"ws_deal":    ["🎯 Deal Verifier (Single ASIN)","🎯 Deal-Prüfer (Einzelne ASIN)","🎯 Verificador de Ofertas","🎯 Verificatore Offerte","🎯 Fırsat Doğrulayıcı","🎯 Weryfikator Ofert","🎯 Deal Verificator","🎯 Affärsverifierare","🎯 Verificador de Ofertas","🎯 Vérificateur d'Offre","🎯 مدقق الصفقات"],
"ws_portfolio":["📊 Wholesale Portfolio Tracker","📊 Großhandels-Portfolio-Tracker","📊 Rastreador de Cartera","📊 Tracker Portafoglio","📊 Toptan Portföy Takipçisi","📊 Tracker Portfela","📊 Groothandel Portfolio","📊 Grossistportfölj","📊 Rastreador de Portfólio","📊 Suivi de Portefeuille","📊 متتبع المحفظة"],
"ws_heading": ["🏷️ WholeSale Features","🏷️ Großhandel-Funktionen","🏷️ Funciones de Mayoreo","🏷️ Funzionalità Ingrosso","🏷️ Toptan Özellikleri","🏷️ Funkcje Hurtowe","🏷️ Groothandel Functies","🏷️ Grossistfunktioner","🏷️ Recursos de Atacado","🏷️ Fonctionnalités de Gros","🏷️ ميزات البيع بالجملة"],
"def_prod":   ["Nutcracker Clara Ballerina Doll","Nussknacker Clara Ballerina Puppe","Muñeca Bailarina Clara","Bambola Ballerina Clara","Fındıkkıran Clara Bebeği","Lalka Baletnica Klara","Notenkraker Clara Pop","Nötknäpparen Clara Docka","Boneca Bailarina Clara","Poupée Ballerine Clara","دمية باليرينا كلارا"],
"def_var":    ["Ombre Tutu Transformation","Ombre Tutu Verwandlung","Transformación Tutú Ombre","Trasformazione Tutù Ombre","Ombre Tütü Dönüşümü","Transformacja Tutu Ombre","Ombre Tutu Transformatie","Ombre Tutu Transformation","Transformação Tutu Ombre","Transformation Tutu Ombré","تحول توتو أومبريه"],
"def_feat":   ["Surprise tutu transformation when arms twirl\nIncludes bow headband, heart locket, gift box\n7 poseable joints for realistic ballet practice\nRecommended for kids ages 3+","Überraschende Tutu-Verwandlung beim Drehen\nEnthält Schleifen-Haarband, Herz-Medaillon, Geschenkbox\n7 bewegliche Gelenke für Ballett-Üben\nEmpfohlen für Kinder ab 3 Jahren","Transformación sorpresa al girar los brazos\nIncluye diadema, colgante de corazón, caja de regalo\n7 articulaciones para ballet\nRecomendado para niños 3+","Trasformazione sorpresa quando le braccia girano\nInclude fascia, ciondolo cuore, confezione regalo\n7 articolazioni per balletto\nConsigliato dai 3 anni","Kollar döndüğünde sürpriz tütü dönüşümü\nKurdele, kalp kolye, hediye kutusu içerir\n7 hareketli eklem\n3 yaş ve üzeri için","Niespodziewana transformacja tutu\nZawiera opaskę, naszyjnik serce, pudełko\n7 ruchomych przegubów\nDla dzieci od 3 lat","Verrassende tutu transformatie\nInclusief strik, hart ketting, cadeaudoos\n7 buigbare gewrichten\nAanbevolen vanaf 3 jaar","Överraskande tutu-transformation\nInnehåller hårband, hjärtmedaljong, presentlåda\n7 rörliga leder\nRekommenderas från 3 år","Transformação surpresa ao girar os braços\nInclui tiara, colar coração, caixa presente\n7 articulações para balé\nRecomendado para 3+","Transformation tutu surprise\nComprend serre-tête, collier cœur, boîte cadeau\n7 articulations pour ballet\nRecommandé dès 3 ans","تحول توتو مفاجئ عند دوران الذراعين\nيشمل عصابة، قلادة قلب، صندوق هدايا\n7 مفاصل للباليه\nموصى به من 3 سنوات"],
"def_kw":     ["ballerina doll, nutcracker toy, princess gift set, dance toy, kids ballet doll","ballerina puppe, nussknacker spielzeug, prinzessin geschenkset, tanzspielzeug, kinder ballettpuppe","muñeca bailarina, juguete cascanueces, set regalo princesa, juguete baile, muñeca ballet niños","bambola ballerina, giocattolo schiaccianoci, set regalo principessa, giocattolo danza, bambola balletto","bale bebeği, fındıkkıran oyuncak, prenses hediye seti, dans oyuncağı, çocuk bale bebeği","lalka baletnica, zabawka dziadek, zestaw księżniczki, zabawka taniec, lalka baletowa","ballerina pop, notenkraker speelgoed, prinses cadeauset, dansspeelgoed, balletpop","ballerinadocka, nötknäpparleksak, prinsesspresentset, dansleksak, balettdocka","boneca bailarina, brinquedo quebra-nozes, conjunto princesa, brinquedo dança, boneca balé","poupée ballerine, jouet casse-noisette, coffret princesse, jouet danse, poupée ballet","دمية باليرينا, لعبة كسارة البندق, طقم هدايا أميرة, لعبة رقص, دمية باليه للأطفال"],
}

def L(key, i):
    vals = T.get(key)
    if not vals: return key
    return vals[i] if i < len(vals) else vals[0]

# =========================================================================
# TOKEN STORAGE
# =========================================================================
def _normalize_tokens(tokens):
    out = {}
    for k, v in tokens.items():
        if isinstance(v, dict):
            out[k] = {"attempts": int(v.get("attempts", v.get("credits", 100))), "active": bool(v.get("active", True)), "session_id": v.get("session_id", None)}
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = {"attempts": int(v), "active": True, "session_id": None}
        elif isinstance(v, bool):
            out[k] = {"attempts": 100, "active": v, "session_id": None}
        else:
            out[k] = {"attempts": 100, "active": True, "session_id": None}
    return out

def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        defaults = {"NEXUS-DEMO-2026": {"attempts": 1000, "active": True, "session_id": None}, "ADMIN-SECRET-KEY": {"attempts": 999999, "active": True, "session_id": None}}
        with open(TOKEN_FILE, "w") as f: json.dump(defaults, f, indent=4)
        return defaults
    with open(TOKEN_FILE, "r") as f:
        try: raw = json.load(f)
        except: raw = {}
    return _normalize_tokens(raw)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f: json.dump(tokens, f, indent=4)

# =========================================================================
# SESSION STATE
# =========================================================================
for k, v in {
    "tokens": load_tokens(), "authenticated": False, "current_token": None,
    "admin_unlocked": False, "failed_attempts": 0, "lockout_time": 0,
    "master_admin_password": "admin", "session_id": str(uuid.uuid4()),
    "scrapfly_key": "", "prepared_catalog": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================================
# SIDEBAR
# =========================================================================
st.sidebar.markdown("## 🌐 Market & Language")
lang_name = st.sidebar.selectbox("Language", LANGS)
LANG = LANGS.index(lang_name)
st.sidebar.title("🛡️ NexusAmz Suite")
st.sidebar.markdown("---")

# We must use st.session_state to track which tab is active. 
# When the app first loads, 'active_tab' is not set, so it defaults to 'auth'.
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "auth"

def change_tab(new_tab):
    st.session_state.active_tab = new_tab

# ACCESS & AUTHENTICATION
st.sidebar.markdown("### 🔐 Access")
if st.sidebar.button(L("auth", LANG), use_container_width=True):
    change_tab("auth")

# PL FEATURES
st.sidebar.markdown("### 🚀 PL Features")
pl_modules = ["calc", "gen", "val", "opt", "inv"]
for mod in pl_modules:
    if st.sidebar.button(L(mod, LANG), use_container_width=True, key=f"btn_{mod}"):
        change_tab(mod)

# PPC FEATURES
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 PPC Features")
ppc_modules = ["neg", "bid", "acos"]
for mod in ppc_modules:
    if st.sidebar.button(L(mod, LANG), use_container_width=True, key=f"btn_{mod}"):
        change_tab(mod)

# WHOLESALE FEATURES
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {L('ws_heading', LANG)}")
ws_modules = ["ws_prepare", "ws_catalog", "ws_deal", "ws_portfolio"]
for mod in ws_modules:
    if st.sidebar.button(L(mod, LANG), use_container_width=True, key=f"btn_{mod}"):
        change_tab(mod)

# ADMIN
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Administration")
if st.sidebar.button(L("admin", LANG), use_container_width=True):
    change_tab("admin")

# Footer
st.sidebar.markdown('<div class="sidebar-footer">Prepared By Ai Engineer : Muhammad Habib</div>', unsafe_allow_html=True)

app_mode = st.session_state.active_tab

# =========================================================================
# AUTHENTICATION GUARD
# =========================================================================
if time.time() < st.session_state.lockout_time:
    st.error(f"🚨 {int(st.session_state.lockout_time - time.time())}s")
    st.stop()

# Require authentication for all tabs EXCEPT auth and admin
if not st.session_state.authenticated and app_mode not in ("auth", "admin"):
    st.warning(L("auth_warn", LANG))
    st.info("Please click the 'Access & Authentication' tab in the sidebar to log in.")
    st.stop()

if st.session_state.authenticated and st.session_state.current_token:
    st.session_state.tokens = load_tokens()
    cur = st.session_state.tokens.get(st.session_state.current_token, {})
    if cur.get("session_id") != st.session_state.session_id:
        st.session_state.authenticated = False
        st.session_state.current_token = None
        st.error(L("auth_hij", LANG))
        st.stop()

# =========================================================================
# MODULE: AUTH
# =========================================================================
if app_mode == "auth":
    st.title(L("auth", LANG))
    st.caption(L("auth_sub", LANG))
    st.info(L("auth_info", LANG))
    if st.session_state.authenticated:
        tok = st.session_state.tokens.get(st.session_state.current_token, {})
        st.success(f"✅ **{st.session_state.current_token}**")
        st.metric(L("credits", LANG), int(tok.get("attempts", 0)))
        if st.button(L("btn_logout", LANG)):
            st.session_state.authenticated = False
            st.session_state.current_token = None
            st.rerun()
    else:
        token_in = st.text_input(L("auth_lbl", LANG), type="password")
        if st.button(L("btn_auth", LANG)):
            tokens = load_tokens()
            if token_in in tokens:
                entry = tokens[token_in]
                if not entry.get("active", True):
                    st.error(L("auth_off", LANG))
                elif int(entry.get("attempts", 0)) <= 0:
                    st.error(L("auth_zero", LANG))
                else:
                    entry["attempts"] = int(entry.get("attempts", 0)) - 1
                    entry["session_id"] = st.session_state.session_id
                    tokens[token_in] = entry
                    save_tokens(tokens)
                    st.session_state.tokens = tokens
                    st.session_state.authenticated = True
                    st.session_state.current_token = token_in
                    st.session_state.failed_attempts = 0
                    st.success(L("auth_ok", LANG))
                    st.rerun()
            else:
                st.session_state.failed_attempts += 1
                if st.session_state.failed_attempts >= 3:
                    st.session_state.lockout_time = time.time() + 30
                    st.error(L("auth_lock", LANG))
                else:
                    st.error(L("auth_bad", LANG))

# =========================================================================
# MODULE: PROFIT CALCULATOR
# =========================================================================
elif app_mode == "calc":
    st.title(L("calc", LANG))
    c1, c2 = st.columns(2)
    with c1:
        price = st.number_input(L("price", LANG), min_value=0.0, value=29.99, step=1.0)
        cogs = st.number_input(L("cogs", LANG), min_value=0.0, value=6.5, step=0.5)
        ship = st.number_input(L("ship", LANG), min_value=0.0, value=2.0, step=0.5)
    with c2:
        ref = st.number_input(L("referral", LANG), min_value=0.0, max_value=100.0, value=15.0, step=0.5)
        fba = st.number_input(L("fba", LANG), min_value=0.0, value=5.4, step=0.5)
        ppc = st.number_input(L("ppc", LANG), min_value=0.0, value=3.0, step=0.5)
    if st.button(L("btn_calc", LANG)):
        ref_fee = price * ref / 100.0
        total_fees = ref_fee + fba
        total = cogs + ship + total_fees + ppc
        net = price - total
        margin = (net / price * 100) if price > 0 else 0
        roi = (net / (cogs + ship) * 100) if (cogs + ship) > 0 else 0
        st.success(L("calc_ok", LANG))
        st.subheader(L("summary", LANG))
        m1, m2, m3, m4 = st.columns(4)
        cur = L("curr", LANG)
        m1.metric(L("m_profit", LANG), f"{cur}{net:.2f}")
        m2.metric(L("m_margin", LANG), f"{margin:.2f}%")
        m3.metric(L("m_roi", LANG), f"{roi:.2f}%")
        m4.metric(L("m_fees", LANG), f"{cur}{total_fees:.2f}")

# =========================================================================
# MODULE: LISTING GENERATOR
# =========================================================================
elif app_mode == "gen":
    st.title(L("gen", LANG))
    c1, c2 = st.columns(2)
    with c1:
        brand = st.text_input(L("brand", LANG), value="LuminaDance")
        category = st.text_input(L("category", LANG), value="Toys & Games")
        pname = st.text_input(L("prod_name", LANG), value=L("def_prod", LANG))
        variant = st.text_input(L("variant", LANG), value=L("def_var", LANG))
    with c2:
        feats = st.text_area(L("features", LANG), value=L("def_feat", LANG), height=100)
        kws = st.text_input(L("keywords", LANG), value=L("def_kw", LANG))
    if st.button(L("btn_gen", LANG)):
        kw_list = [k.strip() for k in kws.split(",") if k.strip()]
        primary = kw_list[0] if kw_list else "Product"
        title = f"{brand} {pname} - {variant} | {primary.title()}"[:75]
        highlights = f"Official {brand} {pname}."[:125]
        feat_lines = [f.strip() for f in feats.split("\n") if f.strip()]
        bullets = []
        for i in range(5):
            if i < len(feat_lines): b = f"• {feat_lines[i]}"
            elif i < len(kw_list): b = f"• PREMIUM: {kw_list[i]}"
            else: b = f"• GUARANTEED by {brand}."
            bullets.append(b[:250])
        desc = f"<p><b>{brand} {pname}</b> - {variant}</p><ul>"
        for f in feat_lines[:4]: desc += f"<li>{f}</li>"
        desc += "</ul>"
        desc = desc[:2000]
        st.success(L("gen_ok", LANG))
        st.markdown(f"### {L('draft_hdr', LANG)}")
        ch = L("chars", LANG)
        st.markdown(f"**{L('lbl_title', LANG)}** ({len(title)} {ch})")
        st.code(title, language=None)
        st.markdown(f"**{L('lbl_high', LANG)}** ({len(highlights)} {ch})")
        st.code(highlights, language=None)
        st.markdown(f"**{L('lbl_bullets', LANG)}**")
        for i, b in enumerate(bullets, 1):
            st.code(f"{L('bullet', LANG)} {i} ({len(b)} {ch}):\n{b}", language=None)
        st.markdown(f"**{L('lbl_desc', LANG)}** ({len(desc)} {ch})")
        st.code(desc, language="html")

# =========================================================================
# MODULE: VALIDATOR
# =========================================================================
elif app_mode == "val":
    st.title(L("val", LANG))
    st.caption(L("val_desc", LANG))
    v_t = st.text_input(L("v_title", LANG), value=L("def_prod", LANG))
    v_b = []
    defaults = ["High quality ballet doll with transformation tutu.", "Includes bow headband and heart locket necklace.", "7 poseable joints for realistic dance poses.", "Made from child safe non-toxic materials.", "Recommended for children ages 3+."]
    for i in range(5):
        v_b.append(st.text_input(L("v_bp", LANG).replace("%d", str(i+1)), value=defaults[i]))
    if st.button(L("btn_val", LANG)):
        st.success(L("v_ok", LANG))
        st.markdown(f"### {L('v_report', LANG)}")
        ch = L("chars", LANG)
        fields = [(L("v_title", LANG), v_t, 75)] + [(L("v_bp", LANG).replace("%d", str(i+1)), v_b[i], 250) for i in range(5)]
        for name, text, lim in fields:
            n = len(text)
            status = L("v_pass", LANG) if n <= lim else L("v_warn", LANG)
            st.write(f"**{name}:** {n} {ch} | {status}")
            if n > lim: st.info(f"{L('v_suggest', LANG)} {text[:lim]}")

# =========================================================================
# MODULE: OPTIMIZER
# =========================================================================
elif app_mode == "opt":
    st.title(L("opt", LANG))
    st.caption(L("opt_desc", LANG))
    raw = st.text_area(L("opt_input", LANG), value=L("def_kw", LANG), height=120)
    if st.button(L("btn_opt", LANG)):
        words = re.sub(r"[^\w\s]", " ", raw).split()
        uniq = []
        for w in words:
            wl = w.lower()
            if wl not in uniq and len(wl) > 1: uniq.append(wl)
        packed = ""
        for w in uniq:
            cand = f"{packed} {w}".strip() if packed else w
            if len(cand.encode("utf-8")) <= 249: packed = cand
            else: break
        b = len(packed.encode("utf-8"))
        c = len(packed)
        st.success(L("opt_ok", LANG))
        st.markdown(f"**{L('opt_output', LANG)}**")
        st.code(packed, language=None)
        st.info(L("opt_stats", LANG).format(c=c, b=b))

# =========================================================================
# MODULE: INVENTORY
# =========================================================================
elif app_mode == "inv":
    st.title(L("inv", LANG))
    st.caption(L("inv_desc", LANG))
    c1, c2, c3 = st.columns(3)
    units = c1.number_input(L("inv_units", LANG), min_value=0, value=450, step=10)
    days = c2.number_input(L("inv_days", LANG), min_value=1, value=30, step=1)
    so = c3.number_input(L("inv_stockout", LANG), min_value=0, value=3, step=1)
    c4, c5, c6 = st.columns(3)
    curr = c4.number_input(L("inv_curr", LANG), min_value=0, value=220, step=10)
    lead = c5.number_input(L("inv_lead", LANG), min_value=1, value=14, step=1)
    safety = c6.number_input(L("inv_safety", LANG), min_value=0, value=7, step=1)
    if st.button(L("btn_inv", LANG)):
        active = max(1, days - so)
        vel = units / active
        dos = curr / vel if vel > 0 else 0
        rp = vel * (lead + safety)
        qty = max(0, int(rp * 2 - curr))
        st.success(L("inv_ok", LANG))
        st.markdown(f"### {L('inv_summary', LANG)}")
        m1, m2, m3 = st.columns(3)
        m1.metric(L("inv_m1", LANG), f"{dos:.1f} {L('inv_day', LANG)}")
        m2.metric(L("inv_m2", LANG), f"{rp:.0f} {L('inv_unit', LANG)}")
        m3.metric(L("inv_m3", LANG), f"{qty} {L('inv_unit', LANG)}")
        st.info(f"💡 **{L('inv_true', LANG)}:** {vel:.2f} {L('inv_unit', LANG)}/{L('inv_day', LANG)}")

# =========================================================================
# MODULE: NEGATIVE KEYWORDS
# =========================================================================
elif app_mode == "neg":
    st.title(L("neg", LANG))
    st.markdown(f"### {L('neg_sample_h', LANG)}")
    sample = pd.DataFrame({"Customer Search Term": ["cheap ballerina", "free dance toy", "best ballet doll"], "Clicks": [25, 18, 30], "Orders": [0, 0, 5], "Spend": [12.5, 9.0, 15.0]})
    st.dataframe(sample, use_container_width=True)
    st.download_button(L("neg_sample_btn", LANG), data=sample.to_csv(index=False).encode(), file_name="ppc_sample.csv", mime="text/csv")
    st.markdown("---")
    up = st.file_uploader(L("neg_upload", LANG), type=SUPPORTED_EXTS)
    c1, c2 = st.columns(2)
    mc = c1.number_input(L("neg_min", LANG), min_value=1, value=10, step=1)
    mo = c2.number_input(L("neg_max", LANG), min_value=0, value=0, step=1)
    if up and st.button(L("btn_neg", LANG)):
        df, err = read_uploaded_file(up)
        if err: st.error(err)
        else:
            tc = next((c for c in df.columns if "search term" in c.lower() or "keyword" in c.lower()), None)
            cc = next((c for c in df.columns if "click" in c.lower()), None)
            oc = next((c for c in df.columns if "order" in c.lower() or "conversion" in c.lower()), None)
            if tc and cc and oc:
                bad = df[(df[cc] >= mc) & (df[oc] <= mo)]
                st.success(L("neg_ok", LANG).format(n=len(bad)))
                st.dataframe(bad[[tc, cc, oc]], use_container_width=True)
                st.download_button(L("neg_download", LANG), data=bad.to_csv(index=False).encode(), file_name="negatives.csv", mime="text/csv")
            else: st.error(L("neg_err", LANG))

# =========================================================================
# MODULE: BID OPTIMIZER
# =========================================================================
elif app_mode == "bid":
    st.title(L("bid", LANG))
    st.caption(L("bid_desc", LANG))
    c1, c2, c3 = st.columns(3)
    tacos = c1.number_input(L("bid_target", LANG), min_value=1.0, value=25.0, step=1.0)
    mn = c2.number_input(L("bid_min", LANG), min_value=0.02, value=0.20, step=0.05)
    mx = c3.number_input(L("bid_max", LANG), min_value=0.10, value=5.00, step=0.20)
    up = st.file_uploader(L("bid_upload", LANG), type=SUPPORTED_EXTS)
    if up:
        df, err = read_uploaded_file(up)
        if err: st.error(err)
        else:
            st.markdown(f"### {L('bid_preview', LANG)}")
            st.dataframe(df.head(3), use_container_width=True)
            if st.button(L("btn_bid", LANG)):
                sc = next((c for c in df.columns if "spend" in c.lower() or "cost" in c.lower()), None)
                sl = next((c for c in df.columns if "sales" in c.lower() or "revenue" in c.lower()), None)
                bc = next((c for c in df.columns if "bid" in c.lower() or "cpc" in c.lower()), None)
                if sc and sl and bc:
                    acos_col = L("bid_col_acos", LANG)
                    new_col = L("bid_col_new", LANG)
                    df[acos_col] = (df[sc] / df[sl] * 100).fillna(0)
                    def opt(row):
                        cb = row[bc]
                        a = row[acos_col]
                        if a == 0: return max(mn, cb * 0.8)
                        return max(mn, min(mx, cb * (tacos / a)))
                    df[new_col] = df.apply(opt, axis=1)
                    st.success(L("bid_ok", LANG))
                    st.dataframe(df[[bc, sc, sl, acos_col, new_col]], use_container_width=True)
                    st.download_button(L("bid_download", LANG), data=df.to_csv(index=False).encode(), file_name="bids.csv", mime="text/csv")
                else: st.error(L("bid_err", LANG))

# =========================================================================
# MODULE: ACOS
# =========================================================================
elif app_mode == "acos":
    st.title(L("acos", LANG))
    st.caption(L("acos_desc", LANG))
    c1, c2 = st.columns(2)
    sales = c1.number_input(L("acos_sales", LANG), min_value=0.0, value=15000.0, step=500.0)
    spend = c2.number_input(L("acos_spend", LANG), min_value=0.0, value=2250.0, step=100.0)
    c3, c4 = st.columns(2)
    adsales = c3.number_input(L("acos_adsales", LANG), min_value=0.0, value=7500.0, step=250.0)
    target = c4.number_input(L("acos_target", LANG), min_value=1.0, value=15.0, step=0.5)
    if st.button(L("btn_acos", LANG)):
        a = (spend / adsales * 100) if adsales > 0 else 0
        t = (spend / sales * 100) if sales > 0 else 0
        org = max(0.0, sales - adsales)
        orgr = (org / sales * 100) if sales > 0 else 0
        st.success(L("acos_ok", LANG))
        st.markdown(f"### {L('acos_dash', LANG)}")
        m1, m2, m3, m4 = st.columns(4)
        cur = L("curr", LANG)
        m1.metric(L("acos_m1", LANG), f"{a:.1f}%")
        m2.metric(L("acos_m2", LANG), f"{t:.1f}%")
        m3.metric(L("acos_m3", LANG), f"{cur}{org:,.2f}")
        m4.metric(L("acos_m4", LANG), f"{orgr:.1f}%")
        st.markdown(f"### {L('acos_insight', LANG)}")
        if t <= target: st.info(L("acos_healthy", LANG).format(v=f"{t:.1f}", t=f"{target:.1f}"))
        else: st.warning(L("acos_warn", LANG).format(v=f"{t:.1f}", t=f"{target:.1f}"))

# =========================================================================
# MODULE: ADMIN
# =========================================================================
elif app_mode == "admin":
    st.title(L("admin", LANG))
    if not st.session_state.admin_unlocked:
        st.info(L("admin_unlock_t", LANG))
        pwd = st.text_input(L("admin_unlock_l", LANG), type="password")
        if st.button(L("admin_unlock_b", LANG)):
            if pwd == st.session_state.master_admin_password:
                st.session_state.admin_unlocked = True
                st.rerun()
            else: st.error(L("admin_bad_pwd", LANG))
    else:
        st.caption(L("admin_title", LANG))
        
        col_lock, _ = st.columns([1, 4])
        with col_lock:
            if st.button(L("admin_lock", LANG)):
                st.session_state.admin_unlocked = False
                st.rerun()
                
        st.markdown("---")
        tokens = load_tokens()
        for k, v in list(tokens.items()):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            c1.write(f"**{k}**")
            active = bool(v.get("active", True))
            label = "🟢" if active else "🔴"
            if c2.button(label, key=f"s_{k}"):
                tokens[k]["active"] = not active
                save_tokens(tokens)
                st.rerun()
            c3.write(f"{L('admin_remain', LANG)}: {int(v.get('attempts', 0))}")
            if c4.button(L("admin_reset", LANG), key=f"r_{k}"):
                tokens[k]["attempts"] = 100
                save_tokens(tokens)
                st.rerun()
            if c5.button(L("admin_delete", LANG), key=f"d_{k}"):
                del tokens[k]
                save_tokens(tokens)
                st.rerun()
        st.markdown("---")
        st.markdown(f"### {L('admin_gen', LANG)}")
        tid = st.text_input(L("admin_tid", LANG))
        att = st.number_input(L("admin_att", LANG), min_value=1, value=50, step=5)
        if st.button(L("admin_genbtn", LANG)):
            if tid:
                tokens[tid] = {"attempts": int(att), "active": True, "session_id": None}
                save_tokens(tokens)
                st.success(L("admin_new_ok", LANG).format(t=tid, n=att))
                st.rerun()
        st.markdown("---")
        
        st.markdown(f"### {L('admin_pwd_t', LANG)}")
        np = st.text_input(L("admin_new_pwd", LANG), type="password")
        if st.button(L("admin_pwd_btn", LANG)):
            if np:
                st.session_state.master_admin_password = np
                st.success(L("admin_pwd_ok", LANG))
            else: st.error(L("admin_pwd_empty", LANG))

# =========================================================================
# WHOLESALE MODULE 0: VENDOR FILE PREPARATION (SCRAPFLY)
# =========================================================================
elif app_mode == "ws_prepare":
    st.title(L("ws_prepare", LANG))
    st.caption("Step 1 of 2 — clean the raw vendor file, enrich it with real Amazon prices via Scrapfly, and export a prepared CSV.")

    st.markdown("### 1) Scrapfly API key")
    st.info("Your key is stored only in this browser session. Paste a **freshly regenerated** key from https://scrapfly.io/dashboard")
    st.session_state.scrapfly_key = st.text_input("Scrapfly API Key", value=st.session_state.scrapfly_key, type="password")

    st.markdown("### 2) Upload the raw vendor file")
    raw_file = st.file_uploader("Upload Vendor File (CSV, XLSX, XLS)", type=SUPPORTED_EXTS, key="ws_prep_raw")

    if raw_file:
        raw_df, err = read_uploaded_file(raw_file)
        if err:
            st.error(err)
            st.stop()

        expected_hints = {"gtin","upc","ean","asin","name","title","brand","cost","price","moq","quantity","stock","inventory","category"}
        header_row = 0
        preview = raw_df.head(15)
        for idx in range(len(preview)):
            row_vals = [str(v).strip().lower() for v in preview.iloc[idx].values if pd.notna(v)]
            hits = sum(1 for v in row_vals if any(h in v for h in expected_hints))
            if hits >= 3:
                header_row = idx
                break

        st.markdown("### 3) Cleanup settings")
        c1, c2 = st.columns(2)
        header_row = c1.number_input("Header row (0-indexed)", min_value=0, value=int(header_row), step=1)
        max_rows = c2.number_input("Max rows to scrape (credit cap)", min_value=1, value=5, step=1, help="Scrapfly charges credits per request. Start with 5 to test.")

        if st.button("🧹 Step A — Strip metadata & preview", key="btn_strip"):
            df = raw_df.copy()
            if header_row > 0:
                df.columns = df.iloc[header_row].astype(str).str.strip()
                df = df.iloc[header_row + 1:].reset_index(drop=True)
            df.columns = [str(c).strip() for c in df.columns]
            st.success(f"✅ Cleaned {len(df)} rows.")
            st.dataframe(df.head(10), use_container_width=True)
            st.session_state["_prep_df"] = df

        if "_prep_df" in st.session_state:
            df = st.session_state["_prep_df"].copy()
            def norm(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
            
            gtin_col = next((c for c in df.columns if any(k in norm(c) for k in ["gtin","upc","ean","barcode"])), None)
            if not gtin_col:
                st.error(f"❌ No GTIN/UPC/EAN column found. Columns: {list(df.columns)}")
                st.stop()

            st.info(f"Identifier column: **{gtin_col}**")
            work = df.head(int(max_rows)).copy()
            work["_gtin_clean"] = work[gtin_col].apply(_norm_gtin)
            work = work[work["_gtin_clean"].notna()].copy()
            gtins = work["_gtin_clean"].tolist()

            st.markdown(f"**Will submit {len(gtins)} GTINs.** First 3: `{gtins[:3]}`")

            if st.button("🌐 Step B — Fetch prices via Scrapfly", key="btn_fetch"):
                if not st.session_state.scrapfly_key:
                    st.error("❌ Paste your Scrapfly API key above first.")
                    st.stop()
                
                try:
                    client = ScrapflyClient(key=st.session_state.scrapfly_key)
                except Exception as e:
                    st.error(f"❌ Failed to initialize Scrapfly: {e}")
                    st.stop()

                results = []
                progress_bar = st.progress(0.0, text="Starting Scrapfly extraction...")
                
                for i, gtin in enumerate(gtins):
                    progress_bar.progress((i + 1) / len(gtins), text=f"Processing {gtin} ({i+1}/{len(gtins)})...")
                    
                    asin = None
                    price, bsr, offers = None, None, None
                    
                    try:
                        # STEP 1: Find the ASIN by scraping the search page
                        search_url = f"https://www.amazon.com/s?k={gtin}"
                        search_resp = client.scrape(ScrapeConfig(
                            url=search_url, asp=True, country="US", render_js=True
                        ))
                        
                        # Find the first /dp/ link
                        match = re.search(r'/dp/([A-Z0-9]{10})', search_resp.content)
                        if match:
                            asin = match.group(1)
                        
                        if not asin:
                            results.append({"GTIN": gtin, "Price": None, "BSR": None, "Offers": None, "Status": "No ASIN found in search"})
                            time.sleep(2)
                            continue
                            
                        # STEP 2: Scrape the actual product page using the ASIN
                        product_url = f"https://www.amazon.com/dp/{asin}"
                        prod_resp = client.scrape(ScrapeConfig(
                            url=product_url, 
                            asp=True, 
                            country="US", 
                            render_js=True,
                            extraction_model="product"
                        ))
                        
                        extracted_data = prod_resp.extraction_result
                        
                        if not extracted_data:
                             results.append({"GTIN": gtin, "Price": None, "BSR": None, "Offers": None, "Status": "Extraction returned empty"})
                             continue

                        product = extracted_data[0] if isinstance(extracted_data, list) else extracted_data

                        # Extract Price
                        if product.get("offers"):
                            for offer in product["offers"]:
                                if offer.get("price"):
                                    price = str(offer["price"])
                                    break
                        
                        # Extract BSR
                        if product.get("info_table"):
                            bsr_text = product["info_table"].get("Best Sellers Rank", "")
                            match_bsr = re.search(r"#([\d,]+)", bsr_text)
                            if match_bsr:
                                bsr = match_bsr.group(1).replace(",", "")
                        
                        # Extract Offer Count
                        if product.get("offers"):
                            offers = str(len(product["offers"]))
                        
                        results.append({
                            "GTIN": gtin, "Price": price, "BSR": bsr, "Offers": offers, 
                            "Status": "Success" if price else "No price found on product page"
                        })
                        
                    except Exception as e:
                        results.append({"GTIN": gtin, "Price": None, "BSR": None, "Offers": None, "Status": f"Error: {str(e)[:80]}"})
                    
                    time.sleep(3)

                prices_df = pd.DataFrame(results)
                st.session_state["_pm_prices"] = prices_df
                st.success(f"✅ Scrapfly extraction complete.")

        if "_pm_prices" in st.session_state:
            prices_df = st.session_state["_pm_prices"].copy()
            st.markdown("### 4) Scraped Data Preview")
            st.dataframe(prices_df, use_container_width=True)

            st.markdown("### 5) Merge price data back into the vendor catalog")
            if st.button("🔗 Step C — Build prepared catalog", key="btn_merge"):
                vendor = st.session_state["_prep_df"].copy()
                vendor["_gtin_clean"] = vendor[gtin_col].apply(_norm_gtin)
                
                pm = prices_df.copy()
                pm["_gtin_clean"] = pm["GTIN"].apply(_norm_gtin)

                rename_pm = {"_gtin_clean": "_gtin_clean", "Price": "AmazonBuyBoxPrice", "Offers": "AmazonNumberOfOffers", "BSR": "AmazonBSR"}
                pm_cols = [c for c in rename_pm.keys() if c in pm.columns]
                pm_slim = pm[pm_cols].rename(columns=rename_pm)

                merged = vendor.merge(pm_slim, on="_gtin_clean", how="inner")

                st.info(f"Vendor rows: **{len(vendor)}** | Scraped rows: **{len(pm_slim)}** | Matched: **{len(merged)}**")
                if len(merged) == 0:
                    st.error("❌ 0 matches. Check the GTIN formats.")
                    st.stop()

                st.session_state["prepared_catalog"] = merged
                st.success(f"✅ Prepared catalog built: **{len(merged)}** SKUs")
                st.dataframe(merged.head(20), use_container_width=True)
                st.download_button("📥 Download prepared_catalog.csv", data=merged.to_csv(index=False).encode(), file_name="prepared_catalog.csv", mime="text/csv")

# =========================================================================
# WHOLESALE MODULE 1: SUPPLIER CATALOG ANALYZER
# =========================================================================
elif app_mode == "ws_catalog":
    st.title(L("ws_catalog", LANG))
    st.caption("Step 2 of 2 — upload the **prepared_catalog.csv** from the previous tab to rank by ROI.")

    def get_referral_rate(category_str, sell_price):
        if not isinstance(category_str, str): return 15.0
        c = category_str.lower()
        if any(k in c for k in ["beauty", "health", "personal care", "dermacosmetics", "sun protection", "face cream", "body lotion", "shower", "deodorant", "shampoo", "hand cream", "micellar"]):
            return 8.0 if sell_price <= 10.0 else 15.0
        if any(k in c for k in ["electronic", "computer", "camera", "phone"]): return 8.0
        if any(k in c for k in ["clothing", "apparel", "fashion"]):
            if sell_price <= 15.0: return 5.0
            elif sell_price <= 20.0: return 10.0
            else: return 17.0
        if "device accessory" in c: return 45.0
        return 15.0

    col1, col2, col3, col4 = st.columns(4)
    target_roi = col1.number_input("Minimum ROI (%)", min_value=0.0, value=30.0, step=5.0)
    min_profit = col2.number_input("Minimum Profit per Unit ($)", min_value=0.0, value=3.0, step=0.5)
    default_fba = col3.number_input("Estimated FBA Fee ($)", min_value=0.0, value=5.40, step=0.50)
    max_offers = col4.number_input("Max Amazon sellers", min_value=1, value=25, step=1)

    catalog_file = st.file_uploader("Upload Prepared Catalog", type=SUPPORTED_EXTS, key="ws_cat_upload")
    if catalog_file:
        cat_df, err = read_uploaded_file(catalog_file)
        if err: st.error(err)
        else:
            cat_df.columns = [str(c).strip().lower() for c in cat_df.columns]
            def find_col(*patterns, exclude=()):
                def norm(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
                for c in cat_df.columns:
                    if any(ex in c for ex in exclude): continue
                    nc = norm(c)
                    if any(norm(p) in nc for p in patterns): return c
                return None

            asin_col = find_col("asin")
            upc_col = find_col("gtin", "upc", "ean", "isbn", "barcode", "identifier")
            cost_col = find_col("lowestprice", "unitcost", "cost", "price", exclude=("sell","retail","current","amazon"))
            moq_col = find_col("moq", "minimumorder", "minorder", "unitspercase", "packsize")
            if not moq_col: moq_col = find_col("unit", exclude=("unitcost","unitprice","profit"))
            qty_col = find_col("totalinventory", "quantity", "available", "stock", "inventory", "lowestpricedofferinventory")
            title_col = find_col("name", "title", "description", "productname")
            sell_col = find_col("amazonbuyboxprice", "buyboxprice", "buybox", "sellprice", "sellingprice", "marketprice", "retail", exclude=("lowest", "cost", "unit"))
            fba_col = find_col("fbafee", "fba_fee", "fulfillmentfee")
            cat_col = find_col("category", "product category", "producttype")
            offers_col = find_col("amazonnumberofoffers", "numberofoffers", "offers", "sellers")
            bsr_col = find_col("amazonbsr", "bsr", "rank")

            if not cost_col:
                st.error("❌ No cost/price column found. Expected `$ Lowest Price inc. shipping`.")
            elif not (upc_col or asin_col):
                st.error("❌ No identifier column found. Include `GTIN`, `UPC`, `EAN`, or `ASIN`.")
            else:
                def to_num(series):
                    if series is None: return None
                    return pd.to_numeric(series.astype(str).str.replace(r"[^\d\.\-]", "", regex=True).replace("", "0"), errors="coerce").fillna(0)

                cost_vals = to_num(cat_df[cost_col])
                st.markdown("---")
                if sell_col: st.success(f"✅ Using real Amazon price from `{sell_col}` column.")
                else: st.warning("⚠️ No `AmazonBuyBoxPrice` column — falling back to flat default price.")
                
                default_sell = st.number_input("Fallback Selling Price ($)", min_value=1.0, value=29.99, step=1.0)

                df = cat_df.copy()
                df["_sell"] = to_num(df[sell_col]) if sell_col else default_sell
                if sell_col and (df["_sell"].fillna(0) <= 0).all():
                    st.warning(f"⚠️ `{sell_col}` is present but empty — falling back to ${default_sell:.2f}.")
                    df["_sell"] = default_sell
                
                df["_cost"] = cost_vals

                if cat_col: df["_referral_pct"] = df.apply(lambda r: get_referral_rate(r.get(cat_col, ""), r["_sell"]), axis=1)
                else: df["_referral_pct"] = 15.0

                df["_referral"] = df["_sell"] * (df["_referral_pct"] / 100.0)

                if fba_col: df["_fba_fee"] = to_num(df[fba_col])
                else: df["_fba_fee"] = default_fba

                df["_total_fees"] = df["_referral"] + df["_fba_fee"]
                df["_profit"] = df["_sell"] - df["_cost"] - df["_total_fees"]
                df["_margin"] = (df["_profit"] / df["_sell"] * 100).round(1).replace([float("inf"), float("-inf")], 0)
                df["_roi"] = (df["_profit"] / df["_cost"] * 100).round(1).replace([float("inf"), float("-inf")], 0)

                if offers_col: df["_offers"] = to_num(df[offers_col])
                else: df["_offers"] = 0

                df = df[df["_cost"] > 0].copy()
                df["_pass_roi"] = df["_roi"] >= target_roi
                df["_pass_profit"] = df["_profit"] >= min_profit
                df["_pass_offers"] = df["_offers"] <= max_offers
                df["_pass"] = df["_pass_roi"] & df["_pass_profit"] & df["_pass_offers"]

                passed = df[df["_pass"]].copy()
                passed["_score"] = passed["_roi"] * passed["_profit"]
                top100 = passed.sort_values("_score", ascending=False).head(100).copy()
                failed = df[~df["_pass"]].copy()

                st.markdown("---")
                st.success(f"✅ {len(passed)} of {len(df)} SKUs pass your filters. Showing the **top 100 by ROI × Profit**.")

                with st.expander("🔍 Detected column mapping & fee logic"):
                    st.write(f"- **Identifier:** `{asin_col or upc_col}`")
                    st.write(f"- **Cost:** `{cost_col}`")
                    st.write(f"- **Sell price source:** `{sell_col or 'fallback default'}`")
                    st.write(f"- **Category (referral lookup):** `{cat_col or '— (default 15%)'}`")
                    st.write(f"- **FBA Fee source:** `{fba_col or f'flat ${default_fba:.2f}'}`")
                    st.write(f"- **Number of offers:** `{offers_col or '—'}`")
                    st.write(f"- **BSR:** `{bsr_col or '—'}`")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Passed filters", len(passed))
                m2.metric("Top 100 shown", len(top100))
                m3.metric("Avg ROI (top 100)", f"{top100['_roi'].mean():.1f}%" if len(top100) else "—")
                m4.metric("Avg Profit (top 100)", f"${top100['_profit'].mean():.2f}" if len(top100) else "—")

                if len(top100):
                    st.markdown("### ✅ Top 100 — Download for Review")
                    id_col = asin_col or upc_col
                    display_cols = [c for c in [id_col, title_col, cat_col, cost_col, moq_col, qty_col] if c and c in top100.columns]
                    display_cols += ["_sell", "_referral_pct", "_fba_fee", "_offers", "_profit", "_margin", "_roi", "_score"]
                    rename_map = {"_sell": "Sell Price", "_referral_pct": "Referral %", "_fba_fee": "FBA Fee", "_offers": "Offers", "_profit": "Profit", "_margin": "Margin %", "_roi": "ROI %", "_score": "Score"}
                    st.dataframe(top100[display_cols].rename(columns=rename_map), use_container_width=True)
                    st.download_button("📥 Download Top 100 CSV", data=top100.to_csv(index=False).encode(), file_name="wholesale_top100.csv", mime="text/csv")

                with st.expander("View rejected rows"):
                    if len(failed):
                        id_col = asin_col or upc_col
                        cols_show = [c for c in [id_col, cost_col, "_offers", "_referral_pct", "_profit", "_roi", "_pass_roi", "_pass_profit", "_pass_offers"] if c and c in failed.columns]
                        st.dataframe(failed[cols_show].head(500), use_container_width=True)
                    else: st.write("No rejected rows.")

# =========================================================================
# WHOLESALE MODULE 2: DEAL VERIFIER
# =========================================================================
elif app_mode == "ws_deal":
    st.title(L("ws_deal", LANG))
    st.caption("Enter one product's details and get an instant buy/pass verdict.")
    col1, col2 = st.columns(2)
    with col1:
        deal_cost = st.number_input("Supplier Unit Cost ($)", min_value=0.01, value=12.50, step=0.50)
        deal_sell = st.number_input("Amazon Selling Price ($)", min_value=0.01, value=29.99, step=0.50)
    with col2:
        deal_referral = st.number_input("Referral Fee (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
        deal_fba = st.number_input("FBA Fee ($)", min_value=0.0, value=5.40, step=0.50)
        deal_target_roi = st.number_input("Target ROI (%)", min_value=0.0, value=30.0, step=5.0)

    if st.button("🎯 Verify Deal"):
        ref_fee = deal_sell * (deal_referral / 100.0)
        total_fees = ref_fee + deal_fba
        profit = deal_sell - deal_cost - total_fees
        roi = (profit / deal_cost * 100) if deal_cost > 0 else 0
        margin = (profit / deal_sell * 100) if deal_sell > 0 else 0
        breakeven_sell = deal_cost + total_fees
        max_buy = (deal_sell - total_fees) / (1 + deal_target_roi / 100.0) if (1 + deal_target_roi / 100.0) > 0 else 0

        st.markdown("---")
        if roi >= deal_target_roi and profit > 0: st.success(f"✅ **BUY** — ROI {roi:.1f}% meets your target.")
        elif profit > 0: st.warning(f"⚠️ **NEGOTIATE** — Profitable (${profit:.2f}) but ROI is low.")
        else: st.error(f"❌ **PASS** — Unprofitable at this cost.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net Profit", f"${profit:.2f}")
        m2.metric("ROI", f"{roi:.1f}%")
        m3.metric("Margin", f"{margin:.1f}%")
        m4.metric("Total Fees", f"${total_fees:.2f}")

        g1, g2 = st.columns(2)
        g1.metric("Break-Even Sell Price", f"${breakeven_sell:.2f}")
        g2.metric(f"Max Buy @ {deal_target_roi:.0f}% ROI", f"${max_buy:.2f}")

# =========================================================================
# WHOLESALE MODULE 3: PORTFOLIO TRACKER
# =========================================================================
elif app_mode == "ws_portfolio":
    st.title(L("ws_portfolio", LANG))
    st.caption("Upload your purchase history to rank SKUs by ROI and flag aging inventory.")
    st.markdown("**Required columns:** `ASIN`, `Units`, `UnitCost`, `PurchaseDate`")
    
    port_file = st.file_uploader("Upload Purchase History File", type=SUPPORTED_EXTS, key="ws_port_file")
    if port_file:
        p_df, err = read_uploaded_file(port_file)
        if err: st.error(err)
        else:
            p_df.columns = [c.strip().lower().replace(" ", "_") for c in p_df.columns]
            asin_c = next((c for c in p_df.columns if c in ("asin", "sku")), None)
            units_c = next((c for c in p_df.columns if "unit" in c and "cost" not in c), None)
            cost_c = next((c for c in p_df.columns if "cost" in c), None)
            date_c = next((c for c in p_df.columns if "date" in c or "purchase" in c), None)
            price_c = next((c for c in p_df.columns if "current" in c or "sell" in c), None)
            stock_c = next((c for c in p_df.columns if "stock" in c or "qty" in c), None)

            if not all([asin_c, units_c, cost_c]):
                st.error("❌ Need at least `ASIN`, `Units`, and `UnitCost` columns.")
            else:
                p_df["_total_cost"] = p_df[units_c] * p_df[cost_c]
                if date_c:
                    p_df[date_c] = pd.to_datetime(p_df[date_c], errors="coerce")
                    p_df["_age_days"] = (pd.Timestamp.now() - p_df[date_c]).dt.days
                else:
                    p_df["_age_days"] = 0

                grouped = p_df.groupby(asin_c).agg(
                    TotalUnits=(units_c, "sum"), TotalCost=("_total_cost", "sum"),
                    AvgUnitCost=(cost_c, "mean"), OldestAge=("_age_days", "max"),
                    Purchases=(units_c, "count")
                ).reset_index()

                if price_c:
                    price_map = p_df.groupby(asin_c)[price_c].last()
                    grouped["CurrentPrice"] = grouped[asin_c].map(price_map)
                else: grouped["CurrentPrice"] = 29.99

                if stock_c:
                    stock_map = p_df.groupby(asin_c)[stock_c].last()
                    grouped["CurrentStock"] = grouped[asin_c].map(stock_map)
                else: grouped["CurrentStock"] = grouped["TotalUnits"]

                grouped["EstProfitPerUnit"] = grouped["CurrentPrice"] - grouped["AvgUnitCost"] - (grouped["CurrentPrice"] * 0.15) - 5.40
                grouped["EstROI"] = (grouped["EstProfitPerUnit"] / grouped["AvgUnitCost"] * 100).round(1)
                grouped["CapitalTied"] = grouped["CurrentStock"] * grouped["AvgUnitCost"]
                grouped["Aging"] = grouped["OldestAge"] > 90
                grouped["Underperforming"] = grouped["EstROI"] < 20

                st.markdown("---")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total SKUs", len(grouped))
                m2.metric("Capital Deployed", f"${grouped['CapitalTied'].sum():,.0f}")
                m3.metric("Avg ROI", f"{grouped['EstROI'].mean():.1f}%")
                m4.metric("Aging SKUs (>90d)", int(grouped["Aging"].sum()))

                st.markdown("### SKU Performance Ranking (by ROI)")
                rank_cols = [asin_c, "TotalUnits", "AvgUnitCost", "CurrentPrice", "EstProfitPerUnit", "EstROI", "CapitalTied", "OldestAge", "Aging"]
                st.dataframe(
                    grouped[rank_cols].sort_values("EstROI", ascending=False).rename(columns={
                        "AvgUnitCost": "Avg Cost", "CurrentPrice": "Sell", "EstProfitPerUnit": "Profit/Unit", "EstROI": "ROI %", "CapitalTied": "Capital Tied", "OldestAge": "Age (days)"
                    }), use_container_width=True
                )

                st.markdown("### 🚨 Action List")
                under = grouped[grouped["Underperforming"]]
                aging = grouped[grouped["Aging"]]
                if len(under): st.warning(f"**{len(under)} underperforming SKUs** (ROI < 20%).")
                if len(aging): st.error(f"**{len(aging)} SKUs older than 90 days**.")
                if not len(under) and not len(aging): st.success("✅ No underperformers or aging stock flagged.")

                st.download_button("📥 Download Portfolio Report CSV", data=grouped.to_csv(index=False).encode(), file_name="wholesale_portfolio.csv", mime="text/csv")