# Определяем, какую SVG-иконку (static/img/weapons/*.svg) показывать для оружия.
# Если позже добавишь реальные фото скинов через Skin.image_url — эти иконки
# используются только как fallback, когда image_url пустой.

WEAPON_ICON = {
    "AK-47": "rifle",
    "M4A4": "rifle",
    "M4A1-S": "rifle",
    "Galil AR": "rifle",
    "AWP": "sniper",
    "Desert Eagle": "pistol",
    "Glock-18": "pistol",
    "USP-S": "pistol",
    "Five-SeveN": "pistol",
    "P250": "pistol",
    "MP7": "smg",
    "MAC-10": "smg",
    "UMP-45": "smg",
    "P90": "smg",
    "Nova": "shotgun",
    "Karambit": "knife",
    "Butterfly Knife": "knife",
}


def get_icon(weapon: str) -> str:
    return WEAPON_ICON.get(weapon, "rifle")
