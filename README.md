# LLM Pricing Monitor

A lightweight tool that automatically fetches and extracts per-token API pricing from major LLM providers (OpenAI, Anthropic, Mistral, etc.) on a weekly basis.

## Features

- Automatically fetches pricing pages from major LLM providers
- Uses GPT-4 Turbo to extract structured pricing data
- Saves results to CSV files
- Compares pricing changes with previous data
- Runs on a weekly schedule
- Easy to add new providers

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-pricing-monitor
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file and add your API keys.

## Usage

Run the script manually:
```bash
python pricing_monitor.py
```

The script will:
1. Fetch pricing pages from configured providers
2. Extract pricing information using GPT-4
3. Save the data to CSV files in the `data/` directory
4. Compare with previous data and alert on changes
5. Schedule weekly runs (every Monday at 9 AM)

## Adding New Providers

To add a new provider, update the `PROVIDERS` dictionary in `pricing_monitor.py`:

```python
PROVIDERS = {
    'NewProvider': 'https://newprovider.com/pricing',
    # ... existing providers ...
}
```

## Data Storage

Pricing data is stored in CSV files in the `data/` directory with the following format:
- Provider
- Model Name
- Price per 1K tokens (input)
- Price per 1K tokens (output)
- Units (USD)

## Contributing

Feel free to submit issues and enhancement requests! 