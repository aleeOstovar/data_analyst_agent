# Kintern Data Analyst Agent

A sophisticated data analysis system built with Python, FastAPI, and LangChain that provides intelligent data analysis capabilities through an API interface.

## Overview

This project implements an AI-powered data analysis agent that can perform various analytical tasks using modern AI and data science tools. It combines the power of LangChain for AI operations with robust data analysis capabilities using pandas, scipy, and other data science libraries.

## Features

- FastAPI-based REST API
- AI-powered data analysis using LangChain and OpenAI
- Database integration with PostgreSQL
- Advanced data processing with pandas and scipy
- Interactive visualizations using matplotlib and seaborn
- Real-time updates with Socket.IO
- Gradio interface for interactive demonstrations

## Technology Stack

- **Framework:** FastAPI
- **AI/ML:** LangChain,LangGraph, OpenAI
- **Data Processing:** pandas, scipy,matplotlib,seaborn
- **Database:** PostgreSQL
- **Visualization:** matplotlib, seaborn


## Project Structure

```plaintext
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── config/             # Configuration settings
│   ├── core/              # Core functionality
│   ├── models/            # Data models and schemas
│   └── services/          # Business logic and services
├── requirements.txt       # Project dependencies
└── run.py                # Application entry point
```

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/aleeOstovar/data_analyst_agent.git
   cd data_analyst_agent
   ```

2. **Set up a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   - Copy `.env-example` to `.env`
   - Update the environment variables:
     - Set your OpenAI API key
     - Configure PostgreSQL connection details
     - Set other required environment variables

5. **Database Setup:**
   - Ensure PostgreSQL is installed and running
   - Create a database named 'kintern'
   - Update the database connection string in `.env`

## Running the Application

Start the application using:

```bash
python run.py
```

The server will start at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:

- API documentation: `http://localhost:8000/docs`
- Alternative documentation: `http://localhost:8000/redoc`

## Environment Variables

Required environment variables:

```env
OPENAI_API_KEY=your-api-key
DEFAULT_MODEL_NAME=llm-model
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kintern
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRESS_CONNECTION_STRING=postgresql://your-db-connection-string
```

## License

[Add your chosen license here]

## Contributing

[Add contribution guidelines here]

## Contact

[Add contact information here]
