# 💬 STC Query Assistant - Chat Interface

A conversational natural language to SQL query assistant powered by Cohere's Command R model and built with Streamlit. Ask questions in plain language and get intelligent responses about your data!

## ✨ Features

- 💬 **Chat Interface**: Natural conversation flow with the AI assistant
- 🤖 **Automatic Processing**: Ask questions and get complete responses without manual steps
- 🗣️ **Natural Language Responses**: Results summarized in conversational language
- 🌍 **Multilingual Support**: Ask questions in multiple languages (English, Arabic, etc.)
- 📊 **Rich Data Views**: Expandable details with SQL, tables, charts, and downloads
- 🎯 **Smart Examples**: Pre-built example questions to get started quickly
- 📈 **Auto Visualization**: Automatic chart generation when appropriate

## 🏗️ Database Schema

The application works with the following tables:

- **sales** (date DATE, region TEXT, product TEXT, units_sold INTEGER, revenue NUMERIC)
- **churn** (month DATE, segment TEXT, churned_customers INTEGER)

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file or set the following environment variable:

```bash
export COHERE_API_KEY="your-cohere-api-key-here"
```

### 3. Setup Database

Make sure your PostgreSQL database is running and contains the required tables. You can use the `seed_data.py` script to populate sample data.

## 🎮 Running the Application

### Option 1: Streamlit Chat Interface (Recommended)

```bash
python run_app.py
# OR
streamlit run streamlit_app.py
```

### Option 2: Command Line Chat

For testing the chat functionality in terminal:

```bash
python chat_agent.py
```

### Option 3: Original Agent (Legacy)

For the original step-by-step workflow:

```bash
python agent.py
```

## 💬 How the Chat Works

1. **Start a Conversation**: Open the app and see the welcome message
2. **Ask Questions**: Type naturally like "What were the sales by region?"
3. **Get Smart Responses**: The assistant will:
   - Generate appropriate SQL automatically
   - Execute the query against your database
   - Analyze the results
   - Respond in natural language with insights
4. **Explore Details**: Expand "View Details" to see:
   - The generated SQL query
   - Raw data in table format
   - Automatic charts (when possible)
   - Download options

## 🗣️ Example Conversations

**You:** "What were the total sales by region last quarter?"

**Assistant:** "Based on your sales data, I found sales across 4 regions for the last quarter. The North region performed best with $156,000 in revenue, followed by South with $142,000. The East and West regions had $128,000 and $134,000 respectively. Overall, your company generated $560,000 in total sales last quarter."

**You:** "Which customer segments churned the most?"

**Assistant:** "Looking at your churn data, the Enterprise segment had the highest churn with 45 customers, followed by SMB with 32 customers. The Startup segment had the lowest churn at 18 customers. This suggests you might want to focus retention efforts on your Enterprise clients."

**You:** "ما هي أعلى المنتجات مبيعاً؟" (Arabic: What are the top selling products?)

**Assistant:** "حسب بيانات المبيعات، المنتج الأعلى مبيعاً هو..." (Based on sales data, the top selling product is...)

## 📁 File Structure

```
├── streamlit_app.py      # Main Streamlit chat application
├── chat_agent.py         # Command-line chat version
├── agent.py              # Original step-by-step agent (legacy)
├── database.py           # Database connection and configuration
├── seed_data.py          # Sample data generation
├── run_app.py           # Application runner script
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🎨 Interface Features

### Chat Interface
- **Persistent History**: Your conversation is maintained throughout the session
- **Example Buttons**: Click example questions to try them instantly
- **Expandable Details**: See the "behind the scenes" SQL and data
- **Clear Chat**: Start fresh anytime

### Data Visualization
- **Smart Charts**: Automatic bar charts for numeric data
- **Data Tables**: Clean, sortable result tables
- **CSV Export**: Download results with timestamps
- **Error Handling**: Clear error messages when things go wrong

## 🔧 Troubleshooting

### Common Issues

1. **Cohere API Key Not Set**
   - Make sure `COHERE_API_KEY` environment variable is set
   - Check that your API key is valid and has credits

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database connection parameters in `database.py`
   - Run `seed_data.py` to ensure tables exist

3. **Chat Not Responding**
   - Check internet connection for Cohere API calls
   - Verify your API key has remaining credits
   - Check the Streamlit terminal for error messages

4. **Charts Not Displaying**
   - This is normal for non-numeric data
   - Charts appear only when data has appropriate structure

### Performance Tips

- **First Load**: Initial Cohere model loading may take a few seconds
- **Large Results**: Queries returning many rows may take longer to process
- **Network**: Response time depends on your internet connection to Cohere's API

## 🌟 Advanced Usage

### Custom Questions
You can ask complex questions like:
- "Compare sales between regions and show me the growth rate"
- "What's the correlation between product type and churn rate?"
- "Show me monthly trends for the past year"

### Multi-language Support
The assistant supports questions in:
- English
- Arabic (العربية)
- And other languages supported by Cohere's Command R model

## 🤝 Contributing

Feel free to submit issues and enhancement requests! Areas for contribution:
- Additional visualization types
- More example questions
- UI/UX improvements
- Performance optimizations

## 📄 License

This project is open source and available under the MIT License. 