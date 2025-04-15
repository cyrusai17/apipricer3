import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from openai import OpenAI
import schedule
import time
import random
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Provider URLs
PROVIDERS = {
    'OpenAI': 'https://openai.com/pricing',
    'Anthropic': 'https://www.anthropic.com/pricing',
    'Mistral': 'https://mistral.ai/models/'  # Updated URL to models page
}

# Browser-like headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
}

def fetch_pricing_page(url):
    """Fetch the HTML content of a pricing page."""
    try:
        # Add a random delay to avoid being blocked
        time.sleep(random.uniform(1, 3))
        
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched {url}")
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_relevant_content(html_content, provider):
    """Extract only the relevant pricing sections from HTML content."""
    print(f"Extracting relevant content for {provider}")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Different extraction strategies based on provider
    if provider == 'OpenAI':
        # For OpenAI, look for specific pricing sections
        pricing_sections = []
        
        # Look for tables with pricing information
        tables = soup.find_all('table')
        for table in tables:
            # Check if table contains pricing information
            if table.find(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE)):
                pricing_sections.append(table)
        
        # Look for divs with pricing information
        pricing_divs = soup.find_all('div', class_=lambda c: c and ('pricing' in c.lower() or 'model' in c.lower()))
        for div in pricing_divs:
            if div.find(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE)):
                pricing_sections.append(div)
        
        # If no specific sections found, try to find any element with pricing information
        if not pricing_sections:
            pricing_elements = soup.find_all(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE))
            for element in pricing_elements:
                # Get the parent element that contains the pricing information
                parent = element.parent
                while parent and parent.name not in ['div', 'table', 'section']:
                    parent = parent.parent
                if parent:
                    pricing_sections.append(parent)
        
        print(f"Found {len(pricing_sections)} pricing sections for OpenAI")
        
    elif provider == 'Anthropic':
        # Look for pricing tables or sections
        pricing_sections = soup.find_all(['table', 'div'], class_=lambda c: c and ('pricing' in c.lower() or 'model' in c.lower()))
        if not pricing_sections:
            # If no specific class found, try to find any table
            pricing_sections = soup.find_all('table')
            print(f"Found {len(pricing_sections)} tables for Anthropic")
    else:  # Mistral or other providers
        # For Mistral, look for model cards or pricing sections
        pricing_sections = []
        
        # Look for model cards
        model_cards = soup.find_all(['div', 'section'], class_=lambda c: c and ('model' in c.lower() or 'card' in c.lower()))
        for card in model_cards:
            if card.find(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE)):
                pricing_sections.append(card)
        
        # Look for pricing tables
        pricing_tables = soup.find_all('table')
        for table in pricing_tables:
            if table.find(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE)):
                pricing_sections.append(table)
        
        # If no specific sections found, try to find any element with pricing information
        if not pricing_sections:
            pricing_elements = soup.find_all(string=re.compile(r'\$|price|token|input|output', re.IGNORECASE))
            for element in pricing_elements:
                # Get the parent element that contains the pricing information
                parent = element.parent
                while parent and parent.name not in ['div', 'table', 'section']:
                    parent = parent.parent
                if parent:
                    pricing_sections.append(parent)
        
        # If still no sections found, look for model names
        if not pricing_sections:
            model_elements = soup.find_all(string=re.compile(r'mistral|mixtral|model', re.IGNORECASE))
            for element in model_elements:
                # Get the parent element that contains the model information
                parent = element.parent
                while parent and parent.name not in ['div', 'section']:
                    parent = parent.parent
                if parent:
                    pricing_sections.append(parent)
        
        print(f"Found {len(pricing_sections)} pricing sections for {provider}")
    
    # If still no sections found, return a portion of the body
    if not pricing_sections:
        print(f"No specific pricing sections found for {provider}, extracting body content")
        body = soup.find('body')
        if body:
            # Get the first 5000 characters of the body
            return str(body)[:5000]
    
    # Combine all found sections
    relevant_content = ""
    for section in pricing_sections:
        relevant_content += str(section) + "\n\n"
    
    # If the content is still too large, truncate it
    if len(relevant_content) > 50000:
        print(f"Content too large ({len(relevant_content)} chars), truncating to 50000 chars")
        relevant_content = relevant_content[:50000] + "... [content truncated]"
    
    print(f"Extracted {len(relevant_content)} chars of relevant content for {provider}")
    return relevant_content

def extract_pricing_with_gpt(html_content, provider):
    """Use GPT-4 to extract pricing information from HTML content."""
    # Extract only relevant content to reduce token count
    relevant_content = extract_relevant_content(html_content, provider)
    
    # Customize prompt based on provider
    if provider == 'OpenAI':
        prompt = f"""You are an AI assistant. Extract a table in CSV format from the HTML of a pricing page for {provider}.

Columns:
- Provider
- Model Name
- Price per 1K tokens (input)
- Price per 1K tokens (output)
- Units (USD)

For OpenAI models, look for specific pricing information like:
- GPT-4: $0.03 per 1K input tokens, $0.06 per 1K output tokens
- GPT-3.5 Turbo: $0.0015 per 1K input tokens, $0.002 per 1K output tokens
- GPT-4 Turbo: $0.01 per 1K input tokens, $0.03 per 1K output tokens

If you find specific pricing information, include it. If not, mark as "Unavailable".
Output only the table — no explanation."""
    elif provider == 'Mistral':
        prompt = f"""You are an AI assistant. Extract a table in CSV format from the HTML of a pricing page for {provider}.

Columns:
- Provider
- Model Name
- Price per 1K tokens (input)
- Price per 1K tokens (output)
- Units (USD)

For Mistral models, look for specific pricing information like:
- Mistral Small: $0.20 per 1M tokens (same for input and output)
- Mistral Medium: $0.27 per 1M tokens (same for input and output)
- Mistral Large: $0.70 per 1M tokens (same for input and output)
- Mixtral 8x7B: $0.24 per 1M tokens (same for input and output)
- Mixtral 8x22B: $0.65 per 1M tokens (same for input and output)

Important: For Mistral models, use the same price for both input and output tokens since they charge the same rate. If you find a price for a model, use that same price for both input and output columns.
Output only the table — no explanation."""
    else:  # Anthropic
        prompt = f"""You are an AI assistant. Extract a table in CSV format from the HTML of a pricing page for {provider}.

Columns:
- Provider
- Model Name
- Price per 1K tokens (input)
- Price per 1K tokens (output)
- Units (USD)

For Anthropic models, look for specific pricing information like:
- Claude 3 Opus: $15 per 1M input tokens, $75 per 1M output tokens
- Claude 3 Sonnet: $3 per 1M input tokens, $15 per 1M output tokens
- Claude 3 Haiku: $0.25 per 1M input tokens, $1.25 per 1M output tokens

Important: Make sure to extract both input and output pricing separately. If you find a model's pricing, you must include both input and output prices. If you can't find a specific price, mark it as "Not provided".
Output only the table — no explanation."""

    try:
        print(f"Sending content to GPT-4 for {provider}")
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts pricing information from HTML content."},
                {"role": "user", "content": f"{prompt}\n\nHTML Content:\n{relevant_content}"}
            ]
        )
        result = response.choices[0].message.content
        print(f"Received response from GPT-4 for {provider}: {len(result)} chars")
        return result
    except Exception as e:
        print(f"Error extracting pricing with GPT: {e}")
        return None

def clean_csv_data(data):
    """Clean up the CSV data by removing duplicate headers and empty rows."""
    try:
        # Split the data into lines
        lines = data.strip().split('\n')
        
        # Find the header line
        header_line = None
        for i, line in enumerate(lines):
            if 'Provider,Model Name,Price per 1K tokens' in line:
                header_line = i
                break
        
        if header_line is None:
            return data  # Return original data if header not found
        
        # Keep only the first header and all data rows
        cleaned_lines = [lines[header_line]]  # Start with the header
        
        # Add all non-empty data rows after the header
        for line in lines[header_line+1:]:
            # Skip empty lines, lines with just commas, or lines that look like headers
            if (line.strip() and 
                not line.strip().startswith('```') and 
                not line.strip().startswith('Provider,Model Name') and
                not all(c == ',' for c in line.strip())):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    except Exception as e:
        print(f"Error cleaning CSV data: {e}")
        return data  # Return original data if cleaning fails

def save_to_csv(data, filename):
    """Save the extracted pricing data to a CSV file."""
    try:
        print(f"Saving data to {filename}")
        
        # Clean up the CSV data
        cleaned_data = clean_csv_data(data)
        
        # Use StringIO from io module instead of pandas.StringIO
        df = pd.read_csv(StringIO(cleaned_data))
        
        # Remove any rows where all values are NaN
        df = df.dropna(how='all')
        
        # Reset the index
        df = df.reset_index(drop=True)
        
        os.makedirs('data', exist_ok=True)
        df.to_csv(f'data/{filename}', index=False)
        print(f"Data saved to data/{filename}")
        print(f"CSV contents: {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {', '.join(df.columns)}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def compare_with_previous(filename):
    """Compare current pricing with the previous week's data."""
    current_file = f'data/{filename}'
    previous_file = f'data/previous_{filename}'
    
    if os.path.exists(previous_file):
        current_df = pd.read_csv(current_file)
        previous_df = pd.read_csv(previous_file)
        
        # Compare and print differences
        if not current_df.equals(previous_df):
            print("\nPricing changes detected:")
            # Implement detailed comparison logic here
            print("Please check the CSV files for detailed changes.")
    else:
        print("No previous data available for comparison.")

def main():
    """Main function to fetch and process pricing data."""
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f'pricing_{timestamp}.csv'
    
    all_pricing_data = []
    
    for provider, url in PROVIDERS.items():
        print(f"\nProcessing {provider}...")
        html_content = fetch_pricing_page(url)
        
        if html_content:
            pricing_data = extract_pricing_with_gpt(html_content, provider)
            if pricing_data:
                all_pricing_data.append(pricing_data)
    
    if all_pricing_data:
        # Combine all pricing data
        combined_data = "\n".join(all_pricing_data)
        save_to_csv(combined_data, filename)
        compare_with_previous(filename)
    else:
        print("No pricing data was successfully extracted.")

def run_scheduled_job():
    """Function to run the pricing monitor on a schedule."""
    print(f"\nRunning scheduled job at {datetime.now()}")
    main()

if __name__ == "__main__":
    # Run immediately if executed directly
    main()
    
    # Schedule weekly runs (every Monday at 9 AM)
    schedule.every().monday.at("09:00").do(run_scheduled_job)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60) 