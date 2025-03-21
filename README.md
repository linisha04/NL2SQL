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
1. Clone the repository.
2. Install dependencies:
   ```sh
   pip install fastapi google-generativeai langchain-community python-dotenv
   ```
3. Set up environment variables:
   - `GOOGLE_API_KEY`
   - `ACQ_API_KEY`
4. Run the API:
   ```sh
   uvicorn cpi:app --reload
   ```

