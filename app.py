from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key in production

@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('index.html')
    
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    try:
        # Read the CSV file
        data = pd.read_csv(file)
        
        # Perform analysis
        total_revenue = data['Revenue'].sum()
        best_performing_products = data.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(5)
        monthly_trends = data.groupby(data['Date'].str[:7])['Revenue'].sum()
        
        # Calculate additional metrics
        average_order_value = data['Revenue'].mean()
        total_orders = len(data)
        product_categories = data['Product'].nunique()

        # Generate visualizations
        plt.figure(figsize=(10, 6))
        sns.barplot(x=monthly_trends.index, y=monthly_trends.values)
        plt.title('Monthly Revenue Trends')
        plt.xlabel('Month')
        plt.ylabel('Revenue')
        plt.xticks(rotation=45)
        monthly_trend_img = get_image_base64(plt)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=best_performing_products.index, y=best_performing_products.values)
        plt.title('Top 5 Best Performing Products')
        plt.xlabel('Product')
        plt.ylabel('Revenue')
        plt.xticks(rotation=45)
        top_products_img = get_image_base64(plt)

        plt.figure(figsize=(10, 6))
        sns.histplot(data['Revenue'], kde=True)
        plt.title('Revenue Distribution')
        plt.xlabel('Revenue')
        plt.ylabel('Frequency')
        revenue_dist_img = get_image_base64(plt)

        # Prepare data for interactive charts
        monthly_trends_data = [{"month": month, "revenue": revenue} for month, revenue in monthly_trends.items()]
        best_products_data = [{"product": product, "revenue": revenue} for product, revenue in best_performing_products.items()]

        # Store the data in session for comparison
        session['file1_data'] = {
            'total_revenue': total_revenue,
            'best_performing_products': best_performing_products.to_dict(),
            'monthly_trends': monthly_trends.to_dict()
        }

        # Render results
        return render_template('result.html',
                               total_revenue=total_revenue,
                               average_order_value=average_order_value,
                               product_categories=product_categories,
                               monthly_trends_data=json.dumps(monthly_trends_data),
                               best_products_data=json.dumps(best_products_data),
                               revenue_dist_img=revenue_dist_img)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/compare', methods=['POST'])
def compare():
    if 'file2' not in request.files:
        return "No file uploaded for comparison", 400

    file2 = request.files['file2']
    if file2.filename == '':
        return "No file selected for comparison", 400

    try:
        # Get data from the first file (stored in session)
        file1_data = session.get('file1_data')
        if not file1_data:
            return "No data available for comparison. Please upload the first file again.", 400

        # Read the second CSV file
        data2 = pd.read_csv(file2)
        
        # Perform analysis on the second file
        total_revenue2 = data2['Revenue'].sum()
        best_performing_products2 = data2.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(5)
        monthly_trends2 = data2.groupby(data2['Date'].str[:7])['Revenue'].sum()

        # Prepare comparison data
        total_revenue1 = file1_data['total_revenue']
        best_performing_products1 = file1_data['best_performing_products']
        monthly_trends1 = file1_data['monthly_trends']

        # Generate comparison visualizations
        plt.figure(figsize=(12, 6))
        plt.bar(['File 1', 'File 2'], [total_revenue1, total_revenue2], color=['#00BFFF', '#1E90FF'])
        plt.title('Total Revenue Comparison')
        plt.ylabel('Revenue')
        revenue_comparison_img = get_image_base64(plt)

        # Prepare data for interactive charts
        products = list(set(best_performing_products1.keys()) | set(best_performing_products2.keys()))
        products_comparison_data = [
            {
                "product": product,
                "revenue1": best_performing_products1.get(product, 0),
                "revenue2": best_performing_products2.get(product, 0)
            }
            for product in products
        ]

        # Render comparison results
        return render_template('comparison_result.html',
                               total_revenue1=total_revenue1,
                               total_revenue2=total_revenue2,
                               revenue_comparison_img=revenue_comparison_img,
                               products_comparison_data=json.dumps(products_comparison_data))

    except Exception as e:
        return f"An error occurred during comparison: {str(e)}", 500

def get_image_base64(plt):
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

if __name__ == '__main__':
    app.run(debug=True)

