from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from weapon_icons import get_icon

db = SQLAlchemy()

# Порядок редкостей — от дешёвых к дорогим (как в CS2, но это своя условная шкала)
RARITIES = [
    ("consumer", "Ширпотреб", "#b0c3d9"),
    ("industrial", "Промышленное", "#5e98d9"),
    ("milspec", "Армейское", "#4b69ff"),
    ("restricted", "Запрещённое", "#8847ff"),
    ("classified", "Засекреченное", "#d32ce6"),
    ("covert", "Тайное", "#eb4b4b"),
    ("contraband", "Контрабанда", "#e4ae39"),
]


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)  # виртуальная валюта
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    test_mode = db.Column(db.Boolean, default=False, nullable=False)  # просто баннер "TEST MODE", на исход не влияет
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("InventoryItem", backref="owner", lazy=True,
                             cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Skin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weapon = db.Column(db.String(64), nullable=False)      # напр. "AK-47"
    name = db.Column(db.String(64), nullable=False)        # напр. "Redline"
    rarity = db.Column(db.String(20), nullable=False)      # ключ из RARITIES
    price = db.Column(db.Integer, nullable=False)          # виртуальная цена
    image_url = db.Column(db.String(255), nullable=True)   # путь к своей картинке (опционально)

    def rarity_info(self):
        for key, label, color in RARITIES:
            if key == self.rarity:
                return {"key": key, "label": label, "color": color}
        return {"key": self.rarity, "label": self.rarity, "color": "#888"}

    def icon_filename(self):
        return f"img/weapons/{get_icon(self.weapon)}.svg"

    def to_dict(self):
        info = self.rarity_info()
        return {
            "id": self.id,
            "weapon": self.weapon,
            "name": self.name,
            "full_name": f"{self.weapon} | {self.name}",
            "price": self.price,
            "rarity": info["key"],
            "rarity_label": info["label"],
            "color": info["color"],
            "image_url": self.image_url,
            "icon": get_icon(self.weapon),
        }


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skin_id = db.Column(db.Integer, db.ForeignKey("skin.id"), nullable=False)
    obtained_at = db.Column(db.DateTime, default=datetime.utcnow)

    skin = db.relationship("Skin", lazy=True)

    def to_dict(self):
        d = self.skin.to_dict()
        d["inventory_id"] = self.id
        return d


class UpgradeHistory(db.Model):
    """Лог апгрейдов — чисто для истории на странице пользователя."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stake_value = db.Column(db.Integer, nullable=False)
    target_value = db.Column(db.Integer, nullable=False)
    chance = db.Column(db.Float, nullable=False)
    roll = db.Column(db.Float, nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    result_skin_name = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
