import psycopg2
import pandas as pd

# Database connection details
hostname = "localhost"
database = "final"
username = "postgres"
port_id = 5432
password = "admin"

cur = None
conn = None

# Load the CSV data
df = pd.read_csv("cpi group data.csv")
df.columns = df.columns.str.strip()

# Convert 'Month' to a numeric column
month_mapping = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}
df["month_numeric"] = df["Month"].map(month_mapping)

# Replace '*' with 0 in numeric columns
df["Index"] = df["Index"].replace('*', 0).astype(float)
df["Inflation (%)"] = df["Inflation (%)"].replace('*', 0).astype(float)

# Debugging: Check if the DataFrame is empty
print(df.head())  
print(df.columns)
print(f"Total rows to insert: {len(df)}")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=password, port=port_id)
    cur = conn.cursor()

    # Create table with 'month_numeric' column
    create_script = """
    CREATE TABLE IF NOT EXISTS cpi_data (
        id SERIAL PRIMARY KEY,
        base_year INT,
        year INT,
        month VARCHAR(20),
        month_numeric INT,
        state VARCHAR(50),
        sector VARCHAR(50),
        group_name VARCHAR(100),
        sub_group_name VARCHAR(100),
        index_value DECIMAL(10, 2),
        inflation_percentage DECIMAL(5, 2),
        UNIQUE (year, month, state, sector, group_name, sub_group_name, index_value, inflation_percentage)
    );
    """
    cur.execute(create_script)
    conn.commit()

    # Ensure DataFrame is not empty
    if not df.empty:
        # Insert data into the table
        insert_query = """ 
        INSERT INTO cpi_data (base_year, year, month, month_numeric, state, sector, group_name, sub_group_name, index_value, inflation_percentage) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (year, month, state, sector, group_name, sub_group_name, index_value, inflation_percentage) DO NOTHING;
        """
        # Prepare records for insertion
        records = df[['BaseYear', 'Year', 'Month', 'month_numeric', 'State', 'Sector', 'Group', 'SubGroup', 'Index', 'Inflation (%)']].values.tolist()
        cur.executemany(insert_query, records)
        conn.commit()

        print("Data inserted successfully!")
    else:
        print(" DataFrame is empty! No records inserted.")

except Exception as error:
    print("Error:", error)

finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()
