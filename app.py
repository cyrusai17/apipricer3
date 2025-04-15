from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
from datetime import datetime
import glob

app = Flask(__name__)

def get_latest_pricing_data():
    """Get the latest pricing data from the most recent CSV file."""
    try:
        # Get the most recent CSV file
        csv_files = glob.glob('data/pricing_*.csv')
        if not csv_files:
            return None
        
        latest_file = max(csv_files, key=os.path.getctime)
        
        # Read the CSV file
        df = pd.read_csv(latest_file)
        
        # Convert to dict for JSON serialization
        data = df.to_dict(orient='records')
        
        # Get the date from the filename
        date_str = os.path.basename(latest_file).split('_')[1].split('.')[0]
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%B %d, %Y')
        
        return {
            'date': date,
            'data': data
        }
    except Exception as e:
        print(f"Error reading pricing data: {e}")
        return None

@app.route('/')
def index():
    """Render the main page."""
    pricing_data = get_latest_pricing_data()
    return render_template('index.html', pricing_data=pricing_data)

@app.route('/api/pricing')
def get_pricing():
    """API endpoint to get the latest pricing data."""
    pricing_data = get_latest_pricing_data()
    if pricing_data:
        return jsonify(pricing_data)
    return jsonify({'error': 'No pricing data available'}), 404

@app.route('/api/pricing/<provider>')
def get_provider_pricing(provider):
    """API endpoint to get pricing data for a specific provider."""
    pricing_data = get_latest_pricing_data()
    if pricing_data:
        # Filter data for the requested provider
        provider_data = [item for item in pricing_data['data'] if item['Provider'].lower() == provider.lower()]
        if provider_data:
            return jsonify({
                'date': pricing_data['date'],
                'provider': provider,
                'data': provider_data
            })
        return jsonify({'error': f'No data available for provider: {provider}'}), 404
    return jsonify({'error': 'No pricing data available'}), 404

@app.route('/api/pricing/model/<model_name>')
def get_model_pricing(model_name):
    """API endpoint to get pricing data for a specific model."""
    pricing_data = get_latest_pricing_data()
    if pricing_data:
        # Filter data for the requested model
        model_data = [item for item in pricing_data['data'] if model_name.lower() in item['Model Name'].lower()]
        if model_data:
            return jsonify({
                'date': pricing_data['date'],
                'model': model_name,
                'data': model_data
            })
        return jsonify({'error': f'No data available for model: {model_name}'}), 404
    return jsonify({'error': 'No pricing data available'}), 404

if __name__ == '__main__':
    app.run(debug=True) 