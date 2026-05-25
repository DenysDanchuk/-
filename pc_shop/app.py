from flask import Flask, render_template, request, redirect, session
import json

app = Flask(__name__)
app.secret_key = "secret_key"

ADMIN_PASSWORD = "12345"


# -------------------- Робота з файлами --------------------

def load_products():
    with open("products.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_products(products):
    with open("products.json", "w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=4)


def load_orders():
    with open("orders.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_orders(orders):
    with open("orders.json", "w", encoding="utf-8") as file:
        json.dump(orders, file, ensure_ascii=False, indent=4)


def load_banners():
    with open("banners.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_banners(banners):
    with open("banners.json", "w", encoding="utf-8") as file:
        json.dump(banners, file, ensure_ascii=False, indent=4)


# -------------------- Допоміжні функції --------------------

def is_admin():
    return session.get("admin") == True


def find_product(products, product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None


def find_banner(banners, banner_id):
    for banner in banners:
        if banner["id"] == banner_id:
            return banner
    return None


def get_next_id(items):
    if len(items) == 0:
        return 1

    max_id = 0

    for item in items:
        if item["id"] > max_id:
            max_id = item["id"]

    return max_id + 1


# -------------------- Головна сторінка --------------------

@app.route("/")
def index():
    products = load_products()

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    sort = request.args.get("sort", "")

    if search:
        products = [
            product for product in products
            if search.lower() in product["name"].lower()
        ]

    if category:
        products = [
            product for product in products
            if product["category"] == category
        ]

    if sort == "cheap":
        products = sorted(products, key=lambda product: product["price"])
    elif sort == "expensive":
        products = sorted(products, key=lambda product: product["price"], reverse=True)
    elif sort == "available":
        products = [
            product for product in products
            if product["stock"] > 0
        ]

    all_products = load_products()
    categories = sorted(set(product["category"] for product in all_products))
    banners = load_banners()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category,
        sort=sort,
        banners=banners
    )


@app.route("/product/<int:product_id>")
def product_page(product_id):
    products = load_products()
    product = find_product(products, product_id)

    if product is None:
        return "Товар не знайдено"

    return render_template("product.html", product=product)


# -------------------- Кошик --------------------

@app.route("/add/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", [])
    cart.append(product_id)
    session["cart"] = cart

    return redirect("/cart")


@app.route("/cart")
def cart_page():
    products = load_products()
    cart = session.get("cart", [])

    cart_products = []

    for product_id in cart:
        product = find_product(products, product_id)

        if product:
            cart_products.append(product)

    total = 0

    for product in cart_products:
        total += product["price"]

    return render_template("cart.html", cart=cart_products, total=total)


@app.route("/clear-cart")
def clear_cart():
    session["cart"] = []
    return redirect("/cart")


# -------------------- Оформлення замовлення --------------------

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    products = load_products()
    cart = session.get("cart", [])

    if request.method == "POST":
        order_items = []
        total = 0

        for product_id in cart:
            product = find_product(products, product_id)

            if product and product["stock"] > 0:
                order_items.append(product.copy())
                total += product["price"]
                product["stock"] -= 1

        orders = load_orders()

        new_order = {
            "id": get_next_id(orders),
            "name": request.form["name"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "items": order_items,
            "total": total
        }

        orders.append(new_order)

        save_orders(orders)
        save_products(products)

        session["cart"] = []

        return redirect("/success")

    return render_template("checkout.html")


@app.route("/success")
def success():
    return render_template("success.html")


# -------------------- Вхід адміністратора --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        password = request.form["password"]

        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Неправильний пароль"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session["admin"] = False
    return redirect("/")


# -------------------- Адмін панель --------------------

@app.route("/admin")
def admin():
    if not is_admin():
        return redirect("/login")

    products = load_products()
    orders = load_orders()

    total_orders = len(orders)
    total_sales = 0

    for order in orders:
        total_sales += order["total"]

    low_stock = []

    for product in products:
        if product["stock"] <= 3:
            low_stock.append(product)

    return render_template(
        "admin.html",
        products=products,
        total_orders=total_orders,
        total_sales=total_sales,
        low_stock=low_stock
    )


@app.route("/orders")
def orders_page():
    if not is_admin():
        return redirect("/login")

    orders = load_orders()

    return render_template("orders.html", orders=orders)


# -------------------- Додавання товару --------------------

@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if not is_admin():
        return redirect("/login")

    if request.method == "POST":
        products = load_products()

        new_product = {
            "id": get_next_id(products),
            "name": request.form["name"],
            "category": request.form["category"],
            "price": int(request.form["price"]),
            "description": request.form["description"],
            "image": request.form["image"],
            "stock": int(request.form["stock"])
        }

        socket = request.form.get("socket")
        memory_type = request.form.get("memory_type")
        power = request.form.get("power")
        wattage = request.form.get("wattage")

        if socket:
            new_product["socket"] = socket

        if memory_type:
            new_product["memory_type"] = memory_type

        if power:
            new_product["power"] = int(power)

        if wattage:
            new_product["wattage"] = int(wattage)

        products.append(new_product)
        save_products(products)

        return redirect("/admin")

    return render_template("add_product.html")


# -------------------- Редагування товару в адмін панелі --------------------

@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not is_admin():
        return redirect("/login")

    products = load_products()
    product = find_product(products, product_id)

    if product is None:
        return "Товар не знайдено" 

    if request.method == "POST":
        product["name"] = request.form["name"]
        product["category"] = request.form["category"]
        product["price"] = int(request.form["price"])
        product["description"] = request.form["description"]
        product["image"] = request.form["image"]
        product["stock"] = int(request.form["stock"])

        socket = request.form.get("socket")
        memory_type = request.form.get("memory_type")
        power = request.form.get("power")
        wattage = request.form.get("wattage")

        if socket:
            product["socket"] = socket

        else:
            product.pop("socket", None)

        if memory_type:
            product["memory_type"] = memory_type

        else:
            product.pop("memory_type", None)

        if power:
            product["power"] = int(power)

        else:
            product.pop("power", None)

        if wattage:
            product["wattage"] = int(wattage)

        else:
            product.pop("wattage", None)

        save_products(products)

        return redirect("/admin")

    return render_template("edit_product.html", product=product)


# -------------------- Видалення та зміна кількості --------------------

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not is_admin():
        return redirect("/login")

    products = load_products()
    new_products = []

    for product in products:
        if product["id"] != product_id:
            new_products.append(product)

    save_products(new_products)

    return redirect("/admin")


@app.route("/remove-product/<int:product_id>", methods=["POST"])
def remove_product(product_id):
    if not is_admin():
        return redirect("/login")

    products = load_products()
    product = find_product(products, product_id)

    if product:
        amount = int(request.form["amount"])
        product["stock"] -= amount

        if product["stock"] < 0:
            product["stock"] = 0

        save_products(products)

    return redirect("/admin")


@app.route("/increase-stock/<int:product_id>", methods=["POST"])
def increase_stock(product_id):
    if not is_admin():
        return redirect("/login")

    products = load_products()
    product = find_product(products, product_id)

    if product:
        amount = int(request.form["amount"])
        product["stock"] += amount
        save_products(products)

    return redirect("/admin")


# -------------------- Перевірка сумісності --------------------

@app.route("/check-compatibility", methods=["GET", "POST"])
def check_compatibility():
    products = load_products()

    processors = []
    motherboards = []
    ram_list = []
    gpus = []
    power_supplies = []

    for product in products:
        if product["category"] == "Процесори":
            processors.append(product)
        elif product["category"] == "Материнські плати":
            motherboards.append(product)
        elif product["category"] == "Оперативна пам’ять":
            ram_list.append(product)
        elif product["category"] == "Відеокарти":
            gpus.append(product)
        elif product["category"] == "Блоки живлення":
            power_supplies.append(product)

    selected_processor = ""
    selected_motherboard = ""
    selected_ram = ""
    selected_gpu = ""

    selected_products = request.args.getlist("selected_products")

    for selected_id in selected_products:
        selected_id = int(selected_id)
        product = find_product(products, selected_id)

        if product:
            if product["category"] == "Процесори":
                selected_processor = selected_id
            elif product["category"] == "Материнські плати":
                selected_motherboard = selected_id
            elif product["category"] == "Оперативна пам’ять":
                selected_ram = selected_id
            elif product["category"] == "Відеокарти":
                selected_gpu = selected_id

    result = ""
    status = ""
    psu_result = ""

    if request.method == "POST":
        processor = find_product(products, int(request.form["processor"]))
        motherboard = find_product(products, int(request.form["motherboard"]))
        ram = find_product(products, int(request.form["ram"]))
        gpu = find_product(products, int(request.form["gpu"]))

        selected_processor = processor["id"]
        selected_motherboard = motherboard["id"]
        selected_ram = ram["id"]
        selected_gpu = gpu["id"]

        if processor["socket"] != motherboard["socket"]:
            result = "Процесор не сумісний з материнською платою: сокети відрізняються."
            status = "bad"

        elif ram["memory_type"] != motherboard["memory_type"]:
            result = "Оперативна пам’ять не сумісна з материнською платою: тип пам’яті відрізняється."
            status = "bad"

        else:
            result = "Обрані процесор, материнська плата та оперативна пам’ять сумісні."
            status = "good"

        recommended_wattage = processor.get("power", 0) + gpu.get("power", 0) + 200

        suitable_psu = []

        for psu in power_supplies:
            if psu.get("wattage", 0) >= recommended_wattage:
                suitable_psu.append(psu)

        if suitable_psu:
            psu_names = []

            for psu in suitable_psu:
                psu_names.append(psu["name"])

            psu_result = (
                "Рекомендована потужність блока живлення: від "
                + str(recommended_wattage)
                + "W. Підходять: "
                + ", ".join(psu_names)
            )
        else:
            psu_result = (
                "Рекомендована потужність блока живлення: від "
                + str(recommended_wattage)
                + "W. У каталозі немає достатньо потужного блока живлення."
            )

    return render_template(
        "compatibility.html",
        processors=processors,
        motherboards=motherboards,
        ram_list=ram_list,
        gpus=gpus,
        result=result,
        status=status,
        psu_result=psu_result,
        selected_processor=selected_processor,
        selected_motherboard=selected_motherboard,
        selected_ram=selected_ram,
        selected_gpu=selected_gpu
    )


# -------------------- Рекламні банери --------------------

@app.route("/admin/banners")
def admin_banners():
    if not is_admin():
        return redirect("/login")

    banners = load_banners()

    return render_template("admin_banners.html", banners=banners)


@app.route("/edit-banner/<int:banner_id>", methods=["GET", "POST"])
def edit_banner(banner_id):
    if not is_admin():
        return redirect("/login")

    banners = load_banners()
    banner = find_banner(banners, banner_id)

    if banner is None:
        return "Банер не знайдено"

    if request.method == "POST":
        banner["title"] = request.form["title"]
        banner["description"] = request.form["description"]
        banner["image"] = request.form["image"]
        banner["button_text"] = request.form["button_text"]
        banner["button_link"] = request.form["button_link"]

        save_banners(banners)

        return redirect("/admin/banners")

    return render_template("edit_banner.html", banner=banner)


if __name__ == "__main__":
    app.run(debug=True)