# Демо-набор "скинов" со своими названиями (не копия реальных скинов CS2 —
# чтобы не тащить в проект чужую интеллектуальную собственность).
#
# Формат BASE_SKINS: (оружие, название, редкость, базовая_цена)
# Базовая цена соответствует состоянию "После полевых испытаний" (FT, x1.0).
# Реальные цены в БД получаются умножением на множитель состояния (WEAR_MULT
# в models.py): Прямо с завода (FN) дороже всего, Закалённое в боях (BS) —
# дешевле всего. Так каждая пушка представлена сразу 5 предметами разного
# состояния — каталог получается в разы больше и разнообразнее.

from models import WEAR_MULT

BASE_SKINS = [
    # ---------------- consumer ----------------
    ("AK-47", "Field Test", "consumer", 15),
    ("Glock-18", "Steel Grip", "consumer", 12),
    ("MP7", "Urban Mesh", "consumer", 10),
    ("P250", "Sandstorm", "consumer", 8),
    ("Nova", "Scrap Iron", "consumer", 9),
    ("Tec-9", "Rust Line", "consumer", 7),

    # ---------------- industrial ----------------
    ("M4A4", "Blue Circuit", "industrial", 40),
    ("USP-S", "Cold Frost", "industrial", 35),
    ("MAC-10", "Night Ops", "industrial", 30),
    ("Nova", "Rust Belt", "industrial", 25),
    ("SG 553", "Grey Panel", "industrial", 32),
    ("P90", "Static Fade", "industrial", 28),

    # ---------------- milspec ----------------
    ("AK-47", "Crimson Fang", "milspec", 120),
    ("M4A1-S", "Void Line", "milspec", 140),
    ("Desert Eagle", "Golden Hour", "milspec", 160),
    ("Galil AR", "Toxic Wave", "milspec", 90),
    ("UMP-45", "Arctic Camo", "milspec", 80),
    ("SSG 08", "Ash Bark", "milspec", 110),
    ("MP7", "Copper Flux", "milspec", 95),

    # ---------------- restricted ----------------
    ("AWP", "Phantom Strike", "restricted", 400),
    ("AK-47", "Serpent Coil", "restricted", 450),
    ("M4A4", "Neon Dragon", "restricted", 500),
    ("Five-SeveN", "Plasma Core", "restricted", 300),
    ("P90", "Circuit Board", "restricted", 280),
    ("SG 553", "Molten Core", "restricted", 420),
    ("R8 Revolver", "Iron Fang", "restricted", 260),

    # ---------------- classified ----------------
    ("AWP", "Frozen Abyss", "classified", 1200),
    ("AK-47", "Inferno Skull", "classified", 1400),
    ("M4A1-S", "Royal Crest", "classified", 1350),
    ("Desert Eagle", "Blood Moon", "classified", 1100),
    ("Karambit", "Shadow Edge", "classified", 1600),
    ("M4A4", "Storm Chaser", "classified", 1250),
    ("USP-S", "Ghost Signal", "classified", 1050),

    # ---------------- covert ----------------
    ("AWP", "Dragon Emperor", "covert", 4000),
    ("AK-47", "Phoenix Rising", "covert", 4500),
    ("M4A4", "Celestial Storm", "covert", 4200),
    ("USP-S", "Ghost Protocol", "covert", 3500),
    ("Butterfly Knife", "Void Reaper", "covert", 5000),
    ("Desert Eagle", "Solar Flare", "covert", 3800),
    ("M9 Bayonet", "Frost Bite", "covert", 5200),

    # ---------------- contraband (топ-уровень, самые дорогие) ----------------
    ("AK-47", "Legendary Wildfire", "contraband", 12000),
    ("Karambit", "Emperor's Blade", "contraband", 650000),
    ("Butterfly Knife", "Dragon Fury", "contraband", 600000),
    ("Talon Knife", "Void Monarch", "contraband", 520000),
    ("Skeleton Knife", "Ashen King", "contraband", 480000),
    ("Bowie Knife", "Crimson Throne", "contraband", 430000),
]


def _build_skins():
    """Разворачивает BASE_SKINS в полный список (оружие, название, редкость,
    цена, состояние) — по одной записи на каждое состояние (wear)."""
    skins = []
    for weapon, name, rarity, base_price in BASE_SKINS:
        for wear_key, mult in WEAR_MULT.items():
            skins.append((weapon, name, rarity, round(base_price * mult), wear_key))
    return skins


SKINS = _build_skins()
