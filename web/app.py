from flask import Flask, render_template
import pandas as pd

df = pd.read_excel('test.xlsx')
app = Flask(__name__)

@app.route('/')
def hello():
    product_list = df['NAME'].to_list()
    flipkart_price_list = df['price_flipkart'].to_list()
    amazon_price_list = df['price_amazon'].to_list()
    imgs = df['product_img'].to_list()
    return render_template('index.html',product_list= enumerate(product_list),
    flipkart_price_list=flipkart_price_list,
    amazon_price_list=amazon_price_list,
    imgs=imgs
    )

if __name__ == '__main__':
    app.run()