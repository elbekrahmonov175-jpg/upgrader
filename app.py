import random
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config
from models import db, User, Skin, InventoryItem, UpgradeHistory, RARITIES
from seed_skins import SKINS


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Доступ только для админов.", "error")
            return redirect(url_for("upgrade_page"))
        return view_func(*args, **kwargs)
    return wrapped


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Сначала войдите в аккаунт."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()
        _seed_skins_if_empty()

    # ---------- РЕГИСТРАЦИЯ / ВХОД ----------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if len(username) < 3 or len(password) < 4:
                flash("Логин от 3 символов, пароль от 4 символов.", "error")
                return render_template("register.html")

            if User.query.filter_by(username=username).first():
                flash("Такой логин уже занят.", "error")
                return render_template("register.html")

            user = User(username=username, balance=Config.START_BALANCE)
            user.set_password(password)

            if Config.ADMIN_USERNAME and username.lower() == Config.ADMIN_USERNAME.lower():
                user.is_admin = True

            db.session.add(user)
            db.session.commit()

            # выдаём пару стартовых скинов, чтобы сразу было с чем апгрейдить
            starter_skins = Skin.query.filter_by(rarity="consumer").limit(2).all()
            for s in starter_skins:
                db.session.add(InventoryItem(user_id=user.id, skin_id=s.id))
            db.session.commit()

            login_user(user)
            flash("Аккаунт создан! Это демо-версия, баланс не настоящий.", "success")
            return redirect(url_for("dashboard"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("dashboard"))

            flash("Неверный логин или пароль.", "error")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ---------- ОСНОВНЫЕ СТРАНИЦЫ ----------

    @app.route("/")
    @login_required
    def dashboard():
        return redirect(url_for("upgrade_page"))

    @app.route("/inventory")
    @login_required
    def inventory():
        items = InventoryItem.query.filter_by(user_id=current_user.id).all()
        return render_template("inventory.html", items=items)

    @app.route("/upgrade")
    @login_required
    def upgrade_page():
        items = InventoryItem.query.filter_by(user_id=current_user.id).all()
        history = (
            UpgradeHistory.query.filter_by(user_id=current_user.id)
            .order_by(UpgradeHistory.created_at.desc())
            .limit(15)
            .all()
        )
        return render_template(
            "upgrade.html", items=items, history=history, rtp=Config.RTP,
            debug_tools_enabled=Config.DEBUG_TOOLS_ENABLED,
        )

    # ---------- API АПГРЕЙДА ----------

    @app.route("/api/upgrade", methods=["POST"])
    @login_required
    def api_upgrade():
        data = request.get_json(force=True) or {}

        stake_source = data.get("source")          # "balance" или "item"
        inventory_id = data.get("inventory_id")     # если source == "item"
        multiplier = float(data.get("multiplier", 2))

        if multiplier < 1.05 or multiplier > 50:
            return jsonify({"error": "Некорректный множитель"}), 400

        # Определяем ставку
        stake_value = 0
        staked_item = None

        if stake_source == "balance":
            stake_value = int(data.get("amount", 0))
            if stake_value <= 0 or stake_value > current_user.balance:
                return jsonify({"error": "Недостаточно средств"}), 400
        elif stake_source == "item":
            staked_item = InventoryItem.query.filter_by(
                id=inventory_id, user_id=current_user.id
            ).first()
            if not staked_item:
                return jsonify({"error": "Предмет не найден"}), 404
            stake_value = staked_item.skin.price
        else:
            return jsonify({"error": "Не указан источник ставки"}), 400

        # Шанс на успех: чем выше множитель, тем ниже шанс.
        # RTP < 1 создаёт "домашнее преимущество", как на реальных сайтах.
        chance = (1 / multiplier) * Config.RTP
        chance = max(0.01, min(chance, Config.MAX_CHANCE))

        roll = random.random()
        win = roll < chance

        # Тестовая кнопка форс-результата — работает ТОЛЬКО если явно включена
        # переменная окружения DEBUG_TOOLS_ENABLED и только для админов.
        # По умолчанию выключена и не должна включаться в проде/на публичном сайте.
        if Config.DEBUG_TOOLS_ENABLED and current_user.is_admin and "force_result" in data:
            win = bool(data["force_result"])
            roll = (chance * 0.5) if win else (chance + (1 - chance) * 0.5)

        target_value = round(stake_value * multiplier)

        result_skin = None

        # Списываем ставку сразу
        if stake_source == "balance":
            current_user.balance -= stake_value
        else:
            db.session.delete(staked_item)

        if win:
            # Подбираем скин с ценой, ближайшей к целевой стоимости
            result_skin = (
                Skin.query.order_by(db.func.abs(Skin.price - target_value)).first()
            )
            if result_skin:
                db.session.add(
                    InventoryItem(user_id=current_user.id, skin_id=result_skin.id)
                )

        history_entry = UpgradeHistory(
            user_id=current_user.id,
            stake_value=stake_value,
            target_value=target_value,
            chance=chance,
            roll=roll,
            win=win,
            result_skin_name=result_skin.to_dict()["full_name"] if result_skin else None,
        )
        db.session.add(history_entry)
        db.session.commit()

        return jsonify({
            "win": win,
            "chance": round(chance * 100, 2),
            "roll": round(roll * 100, 2),
            "stake_value": stake_value,
            "target_value": target_value,
            "new_balance": current_user.balance,
            "result_skin": result_skin.to_dict() if result_skin else None,
        })

    # ---------- АДМИНКА ----------

    @app.route("/admin")
    @login_required
    @admin_required
    def admin_panel():
        users = User.query.order_by(User.id).all()
        all_skins = Skin.query.order_by(Skin.price).all()
        return render_template(
            "admin.html",
            users=users,
            all_skins=all_skins,
            debug_tools_enabled=Config.DEBUG_TOOLS_ENABLED,
        )

    @app.route("/admin/toggle-test-mode/<int:user_id>", methods=["POST"])
    @login_required
    @admin_required
    def admin_toggle_test_mode(user_id):
        user = db.session.get(User, user_id)
        if user:
            user.test_mode = not user.test_mode
            db.session.commit()
            flash(f"У {user.username} баннер TEST MODE: {'включён' if user.test_mode else 'выключен'}.", "success")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/grant-item", methods=["POST"])
    @login_required
    @admin_required
    def admin_grant_item():
        user_id = request.form.get("user_id", type=int)
        skin_id = request.form.get("skin_id", type=int)
        user = db.session.get(User, user_id)
        skin = db.session.get(Skin, skin_id)
        if user and skin:
            db.session.add(InventoryItem(user_id=user.id, skin_id=skin.id))
            db.session.commit()
            flash(f"Выдан предмет «{skin.weapon} | {skin.name}» пользователю {user.username}.", "success")
        else:
            flash("Не удалось выдать предмет — проверь выбор.", "error")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/toggle-admin/<int:user_id>", methods=["POST"])
    @login_required
    @admin_required
    def admin_toggle_admin(user_id):
        user = db.session.get(User, user_id)
        if user and user.id != current_user.id:  # чтобы не снять админку с себя случайно
            user.is_admin = not user.is_admin
            db.session.commit()
            flash(f"У {user.username} права админа: {'включены' if user.is_admin else 'выключены'}.", "success")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/set-balance/<int:user_id>", methods=["POST"])
    @login_required
    @admin_required
    def admin_set_balance(user_id):
        user = db.session.get(User, user_id)
        amount = request.form.get("balance", type=int)
        if user and amount is not None and amount >= 0:
            user.balance = amount
            db.session.commit()
            flash(f"Баланс {user.username} изменён на {amount}.", "success")
        return redirect(url_for("admin_panel"))

    return app


def _seed_skins_if_empty():
    if Skin.query.first() is not None:
        return
    for weapon, name, rarity, price, image_url, wear in SKINS:
        db.session.add(Skin(weapon=weapon, name=name, rarity=rarity, price=price,
                             image_url=image_url, wear=wear))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
