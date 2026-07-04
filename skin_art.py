# Генерация оригинальной графики для скинов.
#
# Важно: здесь НЕТ фото реальных скинов CS2 и нет чужих ассетов — только
# процедурно сгенерированный SVG (силуэт оружия + узор, зависящий от имени
# скина). Так каждая "шкурка" выглядит уникально и не является чьей-то
# интеллектуальной собственностью, которую нельзя тащить в проект.

import hashlib

# Силуэты категорий оружия — простые обобщённые формы (не копия конкретной
# модели/скина), используются как маска, внутрь которой заливается узор.
WEAPON_SHAPES = {
    "rifle": """
        <path d="M15 46 L150 40 L150 34 L165 34 L165 44 L178 44 L178 52 L150 52
                 L150 58 L120 60 L120 68 L108 68 L108 60 L60 62 L55 74 L44 74
                 L44 60 L15 58 Z"/>
    """,
    "pistol": """
        <path d="M40 40 L120 34 L128 34 L128 46 L120 46 L120 40 L60 44
                 L58 66 L46 78 L36 78 L36 50 L40 50 Z"/>
    """,
    "smg": """
        <path d="M20 44 L140 38 L150 38 L150 48 L160 48 L160 56 L140 56
                 L140 50 L60 54 L58 72 L46 72 L46 54 L20 56 Z"/>
    """,
    "sniper": """
        <path d="M10 48 L185 40 L185 34 L195 34 L195 44 L185 48 L150 50
                 L150 60 L130 62 L130 70 L118 70 L118 62 L70 64 L66 78 L54 78
                 L54 62 L10 58 Z"/>
    """,
    "shotgun": """
        <path d="M18 46 L160 40 L160 50 L150 50 L150 58 L120 60 L120 68
                 L106 68 L106 60 L60 62 L56 76 L44 76 L44 60 L18 58 Z"/>
    """,
    "knife": """
        <path d="M30 50 L150 20 C160 17 168 22 165 32 L120 56 L100 60
                 L100 70 L88 76 L80 70 L80 60 L60 58 L34 60 Z"/>
    """,
}

# Аббревиатуры состояний (wear) — для бейджа на карточке.
WEAR_BADGE = {
    "factory_new": "FN",
    "minimal_wear": "MW",
    "field_tested": "FT",
    "well_worn": "WW",
    "battle_scarred": "BS",
}


def _seeded(name: str, salt: str, lo: float, hi: float) -> float:
    """Детерминированное псевдослучайное число из имени скина — так у
    одного и того же скина всегда одна и та же графика."""
    h = hashlib.sha256(f"{name}:{salt}".encode("utf-8")).hexdigest()
    n = int(h[:8], 16) / 0xFFFFFFFF
    return lo + n * (hi - lo)


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _mix(c1, c2, t):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _rgb_str(rgb):
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def generate_skin_svg(weapon_category: str, full_name: str, rarity_color: str, wear: str = None) -> str:
    """Возвращает готовый <svg>...</svg> — уникальная текстура на силуэте
    категории оружия. Полностью сгенерировано, не является ничьей IP."""

    shape = WEAPON_SHAPES.get(weapon_category, WEAPON_SHAPES["rifle"])
    rarity_rgb = _hex_to_rgb(rarity_color)
    dark = _mix(rarity_rgb, (10, 10, 14), 0.75)
    light = _mix(rarity_rgb, (255, 255, 255), 0.35)

    angle = _seeded(full_name, "angle", 15, 165)
    spacing = _seeded(full_name, "spacing", 6, 18)
    stripe_w = max(2, spacing * _seeded(full_name, "width", 0.25, 0.55))
    pattern_kind = int(_seeded(full_name, "kind", 0, 3))
    uid = hashlib.sha256(full_name.encode("utf-8")).hexdigest()[:10]

    if pattern_kind == 0:
        # Диагональные полосы двух тонов
        pattern_body = f"""
            <rect width="20" height="20" fill="{_rgb_str(dark)}"/>
            <rect x="0" y="0" width="{stripe_w}" height="20" fill="{_rgb_str(light)}"/>
        """
        pattern_size = 20
    elif pattern_kind == 1:
        # "Мраморные" пятна (несколько кругов разного радиуса)
        r1 = _seeded(full_name, "r1", 4, 9)
        r2 = _seeded(full_name, "r2", 3, 7)
        pattern_body = f"""
            <rect width="40" height="40" fill="{_rgb_str(dark)}"/>
            <circle cx="10" cy="12" r="{r1}" fill="{_rgb_str(light)}" opacity="0.8"/>
            <circle cx="30" cy="28" r="{r2}" fill="{_rgb_str(light)}" opacity="0.6"/>
        """
        pattern_size = 40
    else:
        # Мелкая сетка / карбон
        pattern_body = f"""
            <rect width="14" height="14" fill="{_rgb_str(dark)}"/>
            <rect x="0" y="0" width="7" height="7" fill="{_rgb_str(light)}" opacity="0.5"/>
            <rect x="7" y="7" width="7" height="7" fill="{_rgb_str(light)}" opacity="0.5"/>
        """
        pattern_size = 14

    badge = WEAR_BADGE.get(wear, "")

    return f"""<svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="p{uid}" width="{pattern_size}" height="{pattern_size}"
             patternUnits="userSpaceOnUse" patternTransform="rotate({angle})">
      {pattern_body}
    </pattern>
    <linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{_rgb_str(light)}" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.35"/>
    </linearGradient>
    <clipPath id="c{uid}">
      {shape}
    </clipPath>
  </defs>

  <g clip-path="url(#c{uid})">
    <rect x="0" y="0" width="200" height="90" fill="url(#p{uid})"/>
    <rect x="0" y="0" width="200" height="90" fill="url(#g{uid})"/>
  </g>
  <g fill="none" stroke="{rarity_color}" stroke-width="1" opacity="0.55">
    {shape}
  </g>
  {f'<text x="192" y="14" text-anchor="end" font-family="monospace" font-size="11" font-weight="700" fill="{rarity_color}">{badge}</text>' if badge else ''}
</svg>"""
