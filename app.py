from flask import Flask, render_template, request, redirect, url_for, jsonify
from bs4 import BeautifulSoup
import requests
import re
import os
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PRODUCTS_FILE = "products.json"

try:
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)
except FileNotFoundError:
    products = {
        "shopee": [],
        "lazada": [],
        "amazon": [],
        "digital": []
    }

categories = {
    "Home & Living": {
        "Bath": ["Bath Towel Rack"],
        "Kitchen": ["Cookware"]
    },
    "Electronics": {
        "Phones": ["Smartphones"],
        "Computers": ["Laptops"]
    }
}

def get_product_details(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        title = ""
        price = ""
        image_url = ""

        if "shopee.ph" in url:
            title_element = soup.find("div", class_=re.compile(r"product-detail__header"))
            if title_element:
                title = title_element.text.strip()
            price_element = soup.find("div", class_=re.compile(r"product-detail__price"))
            if price_element:
                price = price_element.text.strip()
            image_element = soup.find("img", class_=re.compile(r"product-detail__image"))
            if image_element:
                image_url = image_element["src"]

        elif "lazada.com.ph" in url:
            title_element = soup.find("h1", class_=re.compile(r"product-title"))
            if title_element:
                title = title_element.text.strip()
            price_element = soup.find("span", class_=re.compile(r"product-price"))
            if price_element:
                price = price_element.text.strip()
            image_element = soup.find("img", class_=re.compile(r"product-image"))
            if image_element:
                image_url = image_element["src"]

        elif "amazon.com" in url:
            title_element = soup.find("span", id="productTitle")
            if title_element:
                title = title_element.text.strip()
            price_element = soup.find("span", class_=re.compile(r"a-price-whole"))
            if price_element:
                price = price_element.text.strip()
            image_element = soup.find("img", id="landingImage")
            if image_element:
                image_url = image_element["src"]

        return {"title": title, "price": price, "image_url": image_url}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Error parsing product details: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html", products=products, categories=categories)

@app.route("/product_generator", methods=["GET", "POST"])
def product_generator():
    if request.method == "POST":
        product_url = request.form.get("product_url")
        affiliate_url = request.form.get("affiliate_url")
        platform = ""
        if "shopee.ph" in product_url:
            platform = "shopee"
        elif "lazada.com.ph" in product_url:
            platform = "lazada"
        elif "amazon.com" in product_url:
            platform = "amazon"
        details = get_product_details(product_url)
        if details:
            details["affiliate_url"] = affiliate_url
            products[platform].append(details)
            save_products()
            return redirect(url_for("product_generator"))
        else:
            return "Error fetching product details."
    return render_template("product_generator.html")

@app.route("/digital_product", methods=["GET", "POST"])
def digital_product():
    if request.method == "POST":
        title = request.form.get("title")
        details = request.form.get("details")
        image = request.files.get("image")
        image_url = None
        if image:
            filename = image.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            image_url = url_for('static', filename='uploads/' + filename)

        products["digital"].append({"title": title, "details": details, "image_url": image_url})
        save_products()
        return redirect(url_for("digital_product"))
    return render_template("digital_product.html")

def save_products():
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

if __name__ == "__main__":
    app.run(debug=True)