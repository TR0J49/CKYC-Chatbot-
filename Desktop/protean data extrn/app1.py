# app.py
import os
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()  # optional .env with API keys etc.

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------
# DEMO DATA: replace these with real API calls if you want live data.
# ---------------------------------------------------------------------
DEMO_COUNTRY_TO_SITES = {
    "Ghana": [
        {"name": "Jumia Ghana", "domain": "jumia.com.gh"},
        {"name": "Tonaton", "domain": "tonaton.com"},
        {"name": "Melcom Online", "domain": "melcom.com.gh"},
        {"name": "Kaymu (example)", "domain": "kaymu.com.gh"},
        {"name": "Kikuu Ghana", "domain": "kikuu.com.gh"},
        {"name": "Zooba (example)", "domain": "zooba.com.gh"},
        {"name": "Electroland (example)", "domain": "electrolandgh.com"},
        {"name": "GhanaShop (example)", "domain": "ghshop.example"},
        {"name": "ClassifiedsGH", "domain": "classifiedsgh.com"},
        {"name": "MarketGH", "domain": "markethgh.example"}
    ],
    "India": [
        {"name": "Flipkart", "domain": "flipkart.com"},
        {"name": "Amazon India", "domain": "amazon.in"},
        {"name": "Myntra", "domain": "myntra.com"},
        {"name": "Snapdeal", "domain": "snapdeal.com"},
        {"name": "TataCliq", "domain": "tatacliq.com"},
    ],
    "USA": [
        {"name": "Amazon", "domain": "amazon.com"},
        {"name": "Walmart", "domain": "walmart.com"},
        {"name": "Target", "domain": "target.com"},
        {"name": "eBay", "domain": "ebay.com"},
    ]
}

# DEMO detailed info: in production you would replace this endpoint with API results
DEMO_SITE_DETAILS = {
    "jumia.com.gh": {
        "name": "Jumia Ghana",
        "domain": "jumia.com.gh",
        "description": "Leading e-commerce marketplace in Ghana (demo).",
        "founded": 2012,
        "monthly_visitors_est": "1.2M (demo)",
        "global_rank": 12000,
        "country_rank": 45,
        "top_categories": ["Electronics", "Phones", "Fashion", "Home"],
        "payment_methods": ["Mobile Money", "Credit Card", "Cash on Delivery"],
        "shipping_options": ["Home delivery", "Pick-up points"],
        "return_policy": "7 days for eligible items (demo)",
        "tech_stack": ["React", "Nginx", "PHP (legacy)", "Amazon S3"],
        "sample_top_products": [
            {"title": "Smartphone X - 64GB", "price": "GHS 1,200"},
            {"title": "LED TV 42in", "price": "GHS 2,800"},
        ],
    },
    "tonaton.com": {
        "name": "Tonaton",
        "domain": "tonaton.com",
        "description": "Popular classifieds in Ghana (demo).",
        "founded": 2013,
        "monthly_visitors_est": "800k (demo)",
        "global_rank": 25000,
        "country_rank": 80,
        "top_categories": ["Classifieds", "Autos", "Property"],
        "payment_methods": ["Cash", "Mobile Money"],
        "shipping_options": ["Buyer-seller arrangement"],
        "return_policy": "N/A - classifieds platform",
        "tech_stack": ["Vue.js", "Nginx", "Node.js"],
        "sample_top_products": [
            {"title": "Used Toyota Corolla 2015", "price": "GHS 30,000"},
        ],
    },
    # minimal example for other domains
    "amazon.com": {
        "name": "Amazon",
        "domain": "amazon.com",
        "description": "Global e-commerce giant.",
        "founded": 1994,
        "monthly_visitors_est": "2B+ (demo)",
        "global_rank": 1,
        "country_rank": 1,
        "top_categories": ["Everything"],
        "payment_methods": ["Cards", "Amazon Pay"],
        "shipping_options": ["Prime", "Standard", "Locker"],
        "return_policy": "30-day returns (demo)",
        "tech_stack": ["Java", "AWS", "React"],
        "sample_top_products": [{"title": "Echo Dot (demo)", "price": "$49"}],
    }
}

# ---------------------------------------------------------------------
# Helper: simulate delay for demo
# ---------------------------------------------------------------------
def demo_delay():
    time.sleep(0.2)


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/countries", methods=["GET"])
def get_countries():
    # return list of supported demo countries
    countries = sorted(DEMO_COUNTRY_TO_SITES.keys())
    return jsonify({"countries": countries})


@app.route("/api/sites", methods=["GET"])
def get_sites():
    """
    GET /api/sites?country=Ghana
    Returns list of site objects for given country.
    Replace internals with a proper API or scraper to get live lists.
    """
    country = request.args.get("country", "").strip()
    if not country:
        return jsonify({"error": "country required"}), 400

    demo_delay()
    sites = DEMO_COUNTRY_TO_SITES.get(country)
    if sites is None:
        # For countries not in demo map, return an empty list but allow expand later
        return jsonify({"sites": []})
    return jsonify({"sites": sites})


@app.route("/api/site_info", methods=["GET"])
def site_info():
    """
    GET /api/site_info?domain=jumia.com.gh
    Return full details for the selected domain.
    In production: call SimilarWeb / BuiltWith / Wappalyzer / scrape product/category pages.
    """
    domain = request.args.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "domain required"}), 400

    demo_delay()
    details = DEMO_SITE_DETAILS.get(domain)
    if details:
        return jsonify({"site": details})

    # If not prepopulated, return a structured fallback with suggestions on how to fetch
    fallback = {
        "domain": domain,
        "name": domain,
        "description": "No demo details available for this domain. Integrate APIs (SimilarWeb, BuiltWith) or scrape the site for more info.",
        "founded": None,
        "monthly_visitors_est": None,
        "global_rank": None,
        "country_rank": None,
        "top_categories": [],
        "payment_methods": [],
        "shipping_options": [],
        "return_policy": None,
        "tech_stack": [],
        "sample_top_products": [],
    }
    return jsonify({"site": fallback})


# ---------------------------------------------------------------------
# Example: Endpoint templates for production integrations (commented)
# ---------------------------------------------------------------------
# Example: fetch traffic data using SimilarWeb (pseudo-code)
# def fetch_similarweb(domain):
#     key = os.environ.get("SIMILARWEB_API_KEY")
#     if not key:
#         return None
#     url = f"https://api.similarweb.com/v1/website/{domain}/total-traffic-and-engagement/visits?api_key={key}&start_date=2023-01&end_date=2023-01"
#     resp = requests.get(url)
#     if resp.status_code == 200:
#         return resp.json()
#     return None
#
# Example: fetch tech stack using BuiltWith
# def fetch_builtwith(domain):
#     key = os.environ.get("BUILTWITH_API_KEY")
#     if not key:
#         return None
#     url = "https://api.builtwith.com/v20/api.json"
#     params = {"KEY": key, "LOOKUP": domain}
#     resp = requests.get(url, params=params, timeout=10)
#     if resp.status_code == 200:
#         return resp.json()
#     return None

if __name__ == "__main__":
    app.run(debug=True, port=5000)
