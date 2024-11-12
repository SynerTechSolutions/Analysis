from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Replace 'YOUR_SCRAPER_API_KEY' with your actual Scraper API key
SCRAPER_API_KEY = '2c3b8d9a4d5f3e1eb56aaca0d22b7840'

def scrape_amazon(query):
    url = f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url=https://www.amazon.com/s?k={query}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        products = []
        for item in soup.select('.s-main-slot .s-result-item'):
            title = item.select_one('.a-text-normal')
            price = item.select_one('.a-price .a-offscreen')
            rating = item.select_one('.a-icon-alt')
            link_tag = item.select_one('.a-link-normal')
            link = 'https://www.amazon.com' + link_tag['href'] if link_tag else None

            if title and price:
                product_name = title.text.strip()
                if query.lower() in product_name.lower():
                    # Extract only the numeric part of the rating
                    rating_value = 'N/A'
                    if rating:
                        rating_text = rating.text.strip()
                        # Extract the numeric rating (before "out of 5 stars")
                        rating_value = rating_text.split(' ')[0] if 'out of' in rating_text else 'N/A'

                    products.append({
                        'name': product_name,
                        'price': price.text.strip().replace('$', '').strip(),
                        'rating': rating_value,
                        'link': link
                    })

        return products[:5]  # Limit to 5 products
    except Exception as e:
        print(f"Error while scraping Amazon: {e}")
        return []

def scrape_ebay(query):
    url = f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url=https://www.ebay.com/sch/i.html?_nkw={query}'
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        products = []
        for item in soup.select('.s-item'):
            title = item.select_one('.s-item__title')
            price = item.select_one('.s-item__price')
            rating = item.select_one('.b-starrating__star span')
            link_tag = item.select_one('.s-item__link')
            link = link_tag['href'] if link_tag else None

            if title and price:
                product_name = title.text.strip()
                if query.lower() in product_name.lower():
                    # Extract the rating (if available)
                    rating_value = 'N/A'
                    if rating:
                        rating_value = rating.text.strip()

                    products.append({
                        'name': product_name,
                        'price': price.text.strip().replace('$', '').strip(),
                        'rating': rating_value,
                        'link': link
                    })

        return products[:5]  # Limit to 5 products
    except Exception as e:
        print(f"Error while scraping eBay: {e}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    amazon_products = scrape_amazon(query)
    ebay_products = scrape_ebay(query)

    if not amazon_products and not ebay_products:
        error_message = "No products found or an error occurred while fetching data."
        return render_template('index.html', error=error_message)

    # Prepare data for visualization
    amazon_prices = [float(product['price']) for product in amazon_products if product['price'].replace('.', '', 1).isdigit()]
    ebay_prices = [float(product['price']) for product in ebay_products if product['price'].replace('.', '', 1).isdigit()]
    
    amazon_ratings = [
        float(product['rating']) if product['rating'] != 'N/A' else 0 
        for product in amazon_products
        if product['rating'] != 'N/A'
    ]
    ebay_ratings = [
        float(product['rating']) if product['rating'] != 'N/A' else 0
        for product in ebay_products
        if product['rating'] != 'N/A'
    ]

    return render_template('index.html', query=query, 
                           amazon_products=amazon_products, ebay_products=ebay_products,
                           amazon_prices=amazon_prices, ebay_prices=ebay_prices,
                           amazon_ratings=amazon_ratings, ebay_ratings=ebay_ratings)

if __name__ == '__main__':
    app.run(debug=True)
