
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security.api_key import APIKeyHeader
import google.generativeai as genai
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv
from langchain.agents import AgentType
from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent

import re

import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


load_dotenv()

API_KEY = os.getenv("ACQ_API_KEY")
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

app = FastAPI()

DATABASE_URI = "postgresql://postgres:admin@localhost:5432/final"
db = SQLDatabase.from_uri(DATABASE_URI)

llm = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
table_names = db.get_usable_table_names()
table_info = db.get_table_info()

table_context = f"""

# STRICTLY FOLLOW BELOW RULES

You are an expert SQL agent with access to a PostgreSQL database. Your task is to generate, validate, and execute SQL queries on the `cpi_data` table. **Ensure that the queries retrieve meaningful and accurate data while following best practices.**  

## **MOST IMPORTANT RULES**
1. **WHEN A QUESTION IS AMBIGUOUS (MISSING YEAR, MONTH, SECTOR, OR GROUP_NAME):**  
   - CHOOSE THE **LATEST YEAR** (`MAX(year)`) AND **LATEST MONTH** (`MAX(month_numeric)`).  
   - DEFAULT **sector = "Combined"**, **group_name = "General"**, **sub_group_name = "*"**.  

2. **ENSURE ALL SELECT STATEMENTS INCLUDE THE FOLLOWING FIELDS:**  
   - `year`, `month`, `month_numeric`, `state`, `sector`, `group_name`, `sub_group_name`.  
   - Queries **must be fully structured and accurate**.  

3. **DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):**  
   - `WHERE year = MAX(year) AND month_numeric = MAX(month_numeric) AND state = 'All India' AND sector = 'Combined' AND sub_group_name = '*'`.  

---

## **Understanding the Database Schema (`cpi_data` Table)**

This table contains the **Consumer Price Index (CPI) and inflation data**, structured as follows:

- **id** (INTEGER, PRIMARY KEY) → Unique identifier for each record.  
- **base_year** (INTEGER) → The base year used for CPI calculation.  
- **year** (INTEGER) → The year of the reported CPI data.  
- **month** (VARCHAR) → The month for which the CPI data is reported.  
- **month_numeric** (INTEGER) → Numeric representation of the month (1 for January, 2 for February, ..., 12 for December). **Use it for getting the latest month**.  
- **state** (VARCHAR) → The geographic region or state.  
- **sector** (VARCHAR) → Categorization into `Combined`, `Rural`, or `Urban`. **(If no sector is specified, use `Combined`.)**  
- **group_name** (VARCHAR) → High-level category of goods and services (e.g., `"Food and Beverages"`, `"Housing"`). **(If no group_name is specified, return `group_name = 'General' AND sub_group_name = '*'`.)**  
- **sub_group_name** (VARCHAR) → More specific breakdown (e.g., `"Cereals and Products"`, `"Meat and Fish"`, or `"*"` if no further division).  
- **index_value** (FLOAT) → CPI value for the specific category in the given month and year.  
- **inflation_percentage** (FLOAT) → Year-on-year inflation rate for the category.  
---

## **Handling Sectors and Sub-Groups**
- **If no `sub_group_name` is specified, use `sub_group_name = '*'`.**  
- **If a sub-group is explicitly requested, return only that sub-group.**  
- **If no `sector` is specified, default to `sector = 'Combined'`.**  
- **Do NOT include `Rural` or `Urban` data unless explicitly asked.**  

---

## **Critical SQL Query Rules**
### **1 Handling General vs. Category-Level Queries**
- If a user asks for **general inflation** (e.g., *"What is the inflation rate in Gujarat?"*):  
  - Use **`group_name = 'General'`**  
  - Use **`sub_group_name = '*'`**  
  - Use **`sector = 'Combined'`** (unless another sector is mentioned)  

- If a user asks for **Food & Beverages inflation**:  
  - Use **`group_name = 'Food and Beverages'`**  
  - Use **`sub_group_name = '*'`** (unless a specific sub-group is requested)  
  - Use **`sector = 'Combined'`** (unless another sector is specified)  

- If a user asks for **a specific sub-group** (e.g., *"What is the inflation rate for Vegetables?"*):  
  - Use **`group_name = 'Food and Beverages'`**  
  - Use **`sub_group_name = 'Vegetables'`**  
  - Use **`sector = 'Combined'`** (unless another sector is specified)  

---

### **2 Strict Data Separation Rules**
- **Do NOT mix group-level (`Food and Beverages`) and sub-group-level (`Vegetables`) data in a single response.**  
- **Ensure filters are applied correctly to avoid redundant or incorrect results.**  
- **Default assumptions must always align with `MAX(year)`, `MAX(month_numeric)`, and `state = 'All India'` unless specified.**  

---

### **3 Handling Latest and Recent Data**
   -If a user asks for **"latest"** or **"recent"**,  
   - Dynamically **find the most recent year and month** available in the database.  
   - Return only **one value per group** (avoid multiple duplicate values).  

 **Do NOT return outdated records when "recent" data is requested.**  

---

 **Query Formatting & Execution Rules**
 **Use `AVG(inflation_percentage)` when aggregating multiple records per month.**  
 **Always `GROUP BY month, sector, group_name` for proper categorization.**  
 **Use `ORDER BY year DESC, month DESC` when sorting by recent data.**  
 **If comparing multiple states or categories, include `state` in the `GROUP BY` clause.**  
 **Do NOT include markdown formatting (` ```sql ` or ` ``` `).**  


### **Agent Responsibilities**
1. **SQL Query Generation:**
   - Generate only `SELECT` statements (No `UPDATE`, `DELETE`, or `INSERT` or `DROP` or `TRUNCATE`).
   - Construct queries based on user intent while ensuring accuracy.
   - Handle aggregation (`AVG`, `SUM`, `MAX`, `MIN`), filtering (`WHERE`),when needed use groupby(), and sorting (`ORDER BY`) based on context ,also use other sql functions (for example LAG(),STDDEV() etc) if needed.

2. **High-Level Validation:**
   - Ensure the generated SQL query is syntactically valid.
   - Verify column names and table existence before execution.
   - Prevent SQL injection by sanitizing input.
   - If the query is ambiguous, infer intent based on available metadata.

3. **Execution & JSON Output:**
   - Execute the validated SQL query on the `cpi_data` table.
   - Return results in structured **JSON format** for downstream consumption.
   - If no results are found, return an appropriate message instead of an empty response.
   -for example json should be with  below  fields:
  "query": "Tell me the Egg inflation rate for bihar for rural  for year feb 2025 ",
  "result": "The Egg inflation rate for Bihar for rural sector for February 2025 is 1.24%."

### **Important Rules for Query Output**
- **DO NOT** format the SQL query with ` ``` ` or `sql` tags.
- **Always return the SQL query as plain text without markdown formatting.**
- **Return SQL as a simple string without any additional formatting or explanations.**



### Rules for Query Generation:
1. **Only use the `cpi_data` table**; do not query any other tables.
2. Ensure queries are **optimized** and **structured correctly**.
3. If the user asks for trends, perform **aggregations** or **time-series comparisons** as needed.
4. If the user asks for a summary, **group data** by relevant fields.
5. If the user asks for state-wise comparisons, include **GROUP BY state**.
6. If the user asks for inflation-related queries, focus on **inflation_percentage**.
7. If the user requests data for a specific period, use **year** and **month** to filter.
8.Most important1 :when  saying the last or recent , it means same , for recent or last  you have to calulate for most recent year , and months
9. Most important2: when you query the database , dont inlude the ``` or sql or  ```sql or , only query you should use
10 : For a query if different sub-categories exists and always return results with subcategory (e.g sector ,group_name ,sub_group_name)along with values.


#Learning Examples for SQL Query Generation

## **Simple Queries**
### **Example 1: Inflation Rate for a Specific Category in a Given Year**
**User Input:**  
*"What is the inflation rate for Food and Beverages in India in 2025?"*  
SELECT inflation_percentage  
FROM cpi_data  
WHERE year = 2025  
  AND state = 'All India'  
  AND sector = 'Combined'  
  AND group_name = 'Food and Beverages'  
  AND sub_group_name = '*';


**User Input:**
*"Give me the inflation rate for Meat and Fish in Maharashtra for February 2024."*
SELECT inflation_percentage  
FROM cpi_data  
WHERE year = 2024  
  AND month = 'February'  
  AND state = 'Maharashtra'  
  AND sector = 'Combined'  
  AND group_name = 'Food and Beverages'  
  AND sub_group_name = 'Meat and Fish';


User Input:
"Compare the inflation rates of Urban and Rural sectors for Cereals and Products in 2023."
SELECT sector, AVG(inflation_percentage) AS avg_inflation  
FROM cpi_data  
WHERE year = 2023  
  AND state = 'All India'  
  AND group_name = 'Food and Beverages'  
  AND sub_group_name = 'Cereals and Products'  
GROUP BY sector;


User Input:
"Show the top 5 states with the highest inflation rate for Vegetables in March 2024."
SELECT state, inflation_percentage  
FROM cpi_data  
WHERE year = 2024  
  AND month = 'March'  
  AND group_name = 'Food and Beverages'  
  AND sub_group_name = 'Vegetables'  
ORDER BY inflation_percentage DESC  
LIMIT 5;


User Input:
"What was the average inflation percentage for Food and Beverages in Tamil Nadu for 2022?"
SELECT AVG(inflation_percentage) AS avg_inflation  
FROM cpi_data  
WHERE year = 2022  
  AND state = 'Tamil Nadu'  
  AND sector = 'Combined'  
  AND group_name = 'Food and Beverages';



"""
# ZERO_SHOT_REACT_DESCRIPTION
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": table_context,"handle_parsing_errors": True}  
    # ,handle_parsing_errors=True
)


def parse_inflation_result(text):
  
    pattern = r"(\d{4}) (\w+): ([\d.]+)%"
    matches = re.findall(pattern, text)
    
    result_list = [
        {"year": int(year), "month": month, "inflation_rate": float(rate)}
        for year, month, rate in matches
    ]

    return result_list if result_list else {"result": text}



@app.get("/query")
async def run_query(user_query: str = Query(..., description="Natural language SQL query")):
    """Convert user query to SQL and execute it using an agent with table context."""
    try:
        # info="FOLLOW instruction carefully"
        # full_query = f"{info }\n\n and here is the User Query: {user_query}"  
        response = sql_agent.invoke(user_query) 
        print("Raw LLM Response:", response)  
        raw_result = response.get("output", "No result found")
        structured_result = parse_inflation_result(raw_result)
        structured_response = {
            "query": user_query,  
            
            "result": structured_result
        }
        return structured_response










    
        
       
    

    except Exception as e:
        return {"error": str(e)}






