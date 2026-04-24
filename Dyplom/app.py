from flask import Flask, render_template, redirect, session
from data import products

app = Flask(__name__)
app.secret_key = "key"


# Головна сторінка (всі товари)
@app.route("/")
def index():
    return render_template("index.html", products=products)


# Сторінка товару
@app.route("/product/<int:id>")
def product(id):
    product = None

    for p in products:
        if p["id"] == id:
            product = p

    return render_template("product.html", product=product)


# Додати в кошик
@app.route("/add/<int:id>")
def add(id):
    cart = session.get("cart", [])
    cart.append(id)
    session["cart"] = cart

    return redirect("/cart")


# Кошик
@app.route("/cart")
def cart():
    cart_ids = session.get("cart", [])
    cart_products = []

    for id in cart_ids:
        for p in products:
            if p["id"] == id:
                cart_products.append(p)

    total = 0
    for p in cart_products:
        total += p["price"]

    return render_template("cart.html", cart=cart_products, total=total)


if __name__ == "__main__":
    app.run(debug=True)