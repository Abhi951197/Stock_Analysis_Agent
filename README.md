
# Stock Analysis Flask App Setup
### Output
![Screenshot 2025-05-26 141739](https://github.com/user-attachments/assets/ee24a3f0-df09-4a84-adb8-ed5b24f34a8f)
![Screenshot 2025-05-26 141748](https://github.com/user-attachments/assets/6918b6db-eb21-4902-91d0-7327a6591e42)
![Screenshot 2025-05-26 153526](https://github.com/user-attachments/assets/a040c16c-eb60-4583-9478-be7aea8cee26)
![Uploading Screenshot 2025-05-26 153533.png…]()




## Project Structure
Create the following folder structure:

```
stock_analysis_app/
├── agent.py                 # Main Flask application
├── templates/
│   └── stock.html        # HTML template
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Installation & Setup

### 1. Create the project directory
```bash
mkdir stock_analysis_app
cd stock_analysis_app
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
Create `requirements.txt`:
```
Flask==2.3.3
requests==2.31.0
```

Then install:
```bash
pip install -r requirements.txt
```

### 4. Create the templates directory
```bash
mkdir templates
```

### 5. Add the files
- Copy the Flask app code to `app.py`
- Copy the HTML template to `templates/index.html`

### 6. Run the application
```bash
python agent.py
```

The app will be available at: http://localhost:5000

## Features

### 🎯 Multi-Agent Analysis System
- **Ticker Identification Agent**: Extracts stock symbols from natural language
- **Price Fetching Agent**: Gets current stock prices via Alpha Vantage API
- **Price Change Agent**: Calculates price movements and trends
- **News Agent**: Fetches recent news and sentiment analysis
- **Analysis Agent**: Provides comprehensive stock analysis

### 🌐 Modern Web Interface
- Responsive design that works on all devices
- Real-time stock analysis with loading indicators
- Beautiful gradient backgrounds and smooth animations
- Example queries to help users get started
- Comprehensive results display with:
  - Current price and price changes
  - Market sentiment indicators
  - Recent news with sentiment analysis
  - AI-generated analysis and insights

### 📊 Data Display
- **Stock Header**: Company name, ticker, current price
- **Metrics Grid**: Sentiment, news count, price change percentage
- **AI Analysis**: Comprehensive text analysis of stock movement
- **Recent News**: Up to 3 recent news articles with sentiment
- **Error Handling**: User-friendly error messages

## API Endpoints

- `GET /` - Main application page
- `POST /analyze` - Stock analysis endpoint
  - Accepts JSON: `{"query": "your stock query"}`
  - Returns comprehensive stock analysis
- `GET /health` - Health check endpoint

## Example Queries

- "Why did Tesla stock drop today?"
- "AAPL stock performance"
- "How is Nvidia doing?"
- "Microsoft earnings impact"
- "What's happening with Meta stock?"

## Configuration

The app uses Alpha Vantage API for stock data. The API key is already configured in the code, but you can replace it with your own key if needed.

## Customization

### Adding New Stock Mappings
Edit the `ticker_map` in `IdentifyTickerAgent` class to add more company name to ticker mappings.

### Styling Changes
Modify the CSS in the HTML template to customize the appearance.

### API Integration
The system is designed to be modular - you can easily add new data sources or modify existing agents.

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the virtual environment and all dependencies are installed
2. **Template Not Found**: Ensure the `templates/` folder exists and contains `index.html`
3. **API Limits**: The Alpha Vantage free tier has rate limits - the app includes error handling for this
4. **Port Already in Use**: Change the port in `app.run()` if 5000 is occupied

### Production Deployment

For production deployment:
1. Set `debug=False` in `app.run()`
2. Use a production WSGI server like Gunicorn
3. Set up proper environment variables for API keys
4. Configure logging for production monitoring

## License

This project is for educational and demonstration purposes.
