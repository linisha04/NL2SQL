# CPI Data Loader - README

## Prerequisites
1. Install PostgreSQL and ensure it is running.
2. Install required Python packages:
   ```bash
   pip install psycopg2 pandas
   ```

## Setup & Configuration
1. Update database credentials in the script:
   ```python
   hostname = "localhost"
   database = "final"  # Change it as per your database name
   username = "postgres"  # Change it , write your username
   password = "admin"      # Change it , enter your password
   port_id = 5432
   ```
2. Ensure the CSV file (`cpi group data.csv`) is in the same directory as the script.

## Running the Script
Execute the script to load data into the database:
```bash
python3 cpi_data_loader.py
```

## Functionality
- Reads and cleans CPI data from `cpi group data.csv`.
- Maps month names to numeric values.
- Replaces missing values (`*`) with `0`.
- Creates `cpi_data` table if it doesn’t exist.
- Inserts unique records into PostgreSQL.

## Troubleshooting
- Ensure PostgreSQL is running and credentials are correct.
- Verify the CSV file exists and has the correct structure.




# FastAPI SQL Agent

## Overview
This FastAPI application serves as an intelligent SQL agent that processes natural language queries and converts them into SQL queries for a PostgreSQL database containing Consumer Price Index (CPI) and inflation data.

## Features
- **FastAPI Integration:** Provides an API endpoint for querying CPI data.
- **Google Generative AI (Gemini-2.0-Flash):** Generates SQL queries from user input.
- **LangChain SQL Agent:** Ensures query validity and execution.
- **Secure API Access:** Uses API key authentication.
- **PostgreSQL Connection:** Interacts with the `cpi_data` table to retrieve relevant economic data.

## Technologies Used
- FastAPI
- Google Generative AI (Gemini-2.0-Flash)
- LangChain
- PostgreSQL
- dotenv (for environment variable management)


## Installation & Setup
### 1. Clone the Repository
```sh
git clone <repository_url>
cd <repository_name>
```

### 2. Create a Virtual Environment (Optional but Recommended)
```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```
If `requirements.txt` is unavailable, install dependencies manually:
```sh
pip install fastapi google-generativeai langchain-community python-dotenv uvicorn psycopg2-binary
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root and add the following variables:
```
GOOGLE_API_KEY=your_google_api_key
ACQ_API_KEY=your_api_key

And database uri wrt to your username , password in cpi.py file

DATABASE_URL=postgresql://user:password@host:port/database
```
Replace `your_google_api_key`, `your_api_key`, and `DATABASE_URL` with your actual credentials.

### 5. Run the API
Use Uvicorn to start the FastAPI server:
```sh
uvicorn cpi:app --reload
```

## API Documentation
After running the server, access the API documentation at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


## Troubleshooting
- Ensure PostgreSQL is running and accessible using the provided `DATABASE_URL`.
- Check `.env` file formatting and variable values.
- If `psycopg2` installation fails, try `pip install psycopg2-binary`.



