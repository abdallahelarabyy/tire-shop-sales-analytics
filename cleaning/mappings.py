"""Arabic -> English lookup tables used to parse DEXEF product names.

Keys are *normalized* Arabic (see `normalize`) with spaces removed, so
spelling variants like "تايلاندى"/"تايلاندي" or "ستار ماكس"/"ستارماكس"
collapse to one key. Entries marked "# ?" are best-guess transliterations
that should be confirmed with the shop.
"""

import re

_AR_FIXES = str.maketrans({"ى": "ي", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا"})


def normalize(text: str) -> str:
    """Unify Arabic letter variants and collapse whitespace."""
    text = str(text).translate(_AR_FIXES)
    return re.sub(r"\s+", " ", text).strip()


def key(text: str) -> str:
    """Normalized text with all spaces removed (lookup key)."""
    return normalize(text).replace(" ", "")


# --- Country of manufacture (as written in the product name) -------------
ORIGINS = {
    "صيني": "China",
    "تايواني": "Taiwan",
    "ياباني": "Japan",
    "كوري": "South Korea",
    "تايلاندي": "Thailand",
    "فيتنامي": "Vietnam",
    "اندونيسي": "Indonesia",
    "كمبودي": "Cambodia",
    "هندي": "India",
    "اوروبي": "Europe (unspecified)",
    "اوربي": "Europe (unspecified)",
    "مجري": "Hungary",
    "بولندي": "Poland",
    "الماني": "Germany",
    "ايطالي": "Italy",
    "اسباني": "Spain",
    "سلوفاني": "Slovenia",
    "تركي": "Turkey",
    "مصري": "Egypt",
    "سعودي": "Saudi Arabia",
    "جزائري": "Algeria",
    "مغربي": "Morocco",
}

REGIONS = {
    "China": "East Asia", "Taiwan": "East Asia", "Japan": "East Asia",
    "South Korea": "East Asia",
    "Thailand": "Southeast Asia", "Vietnam": "Southeast Asia",
    "Indonesia": "Southeast Asia", "Cambodia": "Southeast Asia",
    "India": "South Asia",
    "Europe (unspecified)": "Europe", "Hungary": "Europe", "Poland": "Europe",
    "Germany": "Europe", "Italy": "Europe", "Spain": "Europe",
    "Slovenia": "Europe",
    "Turkey": "Middle East & Africa", "Egypt": "Middle East & Africa",
    "Saudi Arabia": "Middle East & Africa", "Algeria": "Middle East & Africa",
    "Morocco": "Middle East & Africa",
    "Unknown": "Unknown", "Not applicable": "Not applicable",
}

# --- Tire brands ----------------------------------------------------------
TIRE_BRANDS = {
    "لينجلونج": "Linglong",
    "اوفيشن": "Ovation",
    "جالنت": "Gallant",
    "اطلس": "Atlas",
    "بلاكهوك": "Blackhawk",
    "سايلون": "Sailun",
    "ليو": "Leao",
    "نانكانج": "Nankang",
    "رودستون": "Roadstone",
    "صنوايد": "Sunwide",
    "اريسون": "Arisun",
    "دينامو": "Dynamo",
    "رودكس": "RoadX",
    "فورسلاند": "Forceland",
    "كروسويند": "Crosswind",
    "كورسويندا": "Crosswind",
    "لاندسبيدر": "Landspider",
    "لوفين": "Laufenn",
    "لينستون": "Linstone",  # ?
    "ماكسيس": "Maxxis",
    "هانكوك": "Hankook",
    "وانلي": "Wanli",
    "ترانسميت": "Transmate",
    "ايبلس": "E-Plus",  # ?
    "روفيلو": "Rovelo",
    "لاسا": "Lassa",
    "ويندا": "Winda",
    "فيرديشتاين": "Vredestein",
    "فريديشتاين": "Vredestein",
    "كمهو": "Kumho",
    "امريكانرودستار": "American Roadstar",
    "ستارماكس": "Starmaxx",
    "ايرس": "Iris",
    "ديليوم": "Delium",
    "زيتكس": "Zeetex",
    "ماتريكس": "Matrix",  # ?
    "ماتركس": "Matrix",  # ?
    "افانتك": "Avantech",  # ?
    "برينكس": "Prinx",
    "كورديان": "Cordiant",
    "جودترب": "Goodtrip",
    "جودتريب": "Goodtrip",
    "كينتو": "Kinto",  # ?
    "طرزانو": "Tarzano",  # ?
    "لاندسيل": "Landsail",
    "ارمسترونج": "Armstrong",
    "بلاكليون": "Black Lion",
    "لايكن": "Laiken",  # ?
    "تيبيبي": "TBB",
    "تيانفو": "Tianfu",
    "رودوينج": "Roadwing",
    "سوموتومو": "Sumitomo",
    "جيتي": "GT Radial",
    "ليونلورد": "Lionlord",  # ?
    "نكسن": "Nexen",
    "جويرود": "Joyroad",
    "يوكوهاما": "Yokohama",
    "صنفل": "Sunfull",
    "فورتين": "Fortune",
    "كريستال": "Kristal",  # ?
    "بريدجستون": "Bridgestone",
    "بطلس": "Petlas",
    "تويو": "Toyo",
    "كونتيننتال": "Continental",
    "ماكسن": "Maxxen",  # ?
    "ديستون": "Deestone",
    "مارشال": "Marshal",
    "ديلنتي": "Delinte",
    "فولدا": "Fulda",
    "جودرايد": "Goodride",
    "اوريو": "Orio",  # ?
}

# Descriptive words that can follow the brand/origin in tire names.
TIRE_TAGS = {
    "جديد": "New model",
    "خط ابيض": "White line",
    "خط": "Line",
    "دبل شفه": "Rim protector",
    "ربع نقل": "Light truck",
    "شجره": "Tree pattern",
    "ناعم": "Smooth tread",
    "ران فلات": "Run-flat",
}

# --- Batteries --------------------------------------------------------------
# key -> (brand, product line)
BATTERY_BRANDS = {
    "GMجيام": ("GM", "GM"),
    "ادلر": ("Adler", "Adler"),  # ?
    "اسيديلكو": ("ACDelco", "ACDelco"),
    "اكترون": ("Actron", "Actron"),  # ?
    "انجياكوا": ("Inci Aku", "Inci Aku Aqua"),
    "انرجايزر": ("Energizer", "Energizer"),
    "ايهسيباور": ("AC Power", "AC Power"),  # ?
    "بانثر": ("Panther", "Panther"),
    "بلاتين": ("Platin", "Platin"),
    "بوش": ("Bosch", "Bosch"),
    "بولو": ("Polo", "Polo"),  # ?
    "فارتا": ("Varta", "Varta"),
    "فلوستارك": ("Flow Stark", "Flow Stark"),  # ?
    "فولترونيك": ("Voltronic", "Voltronic"),
    "كلورايدجولد": ("Chloride", "Chloride Gold"),
    "كلورايدعاده": ("Chloride", "Chloride Standard"),
    "موتلو": ("Mutlu", "Mutlu"),
    "نسر": ("Nesr", "Nesr"),  # ?
    "هوجل": ("Hugel", "Hugel"),  # ?
}

# --- Rims (only 26, mapped by POS row number for accuracy) -----------------
# row number -> (brand, finish / style)
RIMS = {
    40: ("Mitsubishi Lancer OEM", "Original"),
    41: ("Unbranded", "White spider"),
    74: ("Unbranded", "New design"),
    75: ("Unbranded", "Gold, nickel lip"),
    76: ("Nissan Sunny OEM", "Original"),
    77: ("Work", "Gloss black"),
    78: ("BBS", "Gold"),
    79: ("Fosin", "Silver"),  # ?
    80: ("Volk", "Grey"),
    81: ("Work", "Black, nickel lip"),
    82: ("Volk", "Dark spider"),
    83: ("Chevrolet Optra OEM", "Original"),
    164: ("BBS", "Black spider"),
    165: ("HRS", "White"),
    166: ("OZ", "Gloss black"),
    167: ("Work", "Gold, nickel lip"),
    168: ("XXR", "Gold"),
    169: ("Enforged", "Blue, 7-spoke"),  # ?
    170: ("Rotiform", "Silver"),
    174: ("FR", "Silver"),
    175: ("Mazda OEM", "Spider"),
    176: ("Citroen OEM", "Original"),
    177: ("Lenso", "Wire spokes, nickel"),
    243: ("SSW", "Standard"),
    244: ("BBS", "Silver"),
    281: ("SSW", "Standard"),
}

# --- Services & accessories (mapped by normalized key) ---------------------
OTHER_PRODUCTS = {
    "خدمهاستعدالولحامجنط": ("Service", "Rim Straightening & Welding", "Shop Service"),
    "خدمهلحام": ("Service", "Welding", "Shop Service"),
    "طقمرينجبلاستيك73.1-57.1": ("Accessory", "Plastic Hub Ring Set 73.1-57.1", "Unbranded"),
}
