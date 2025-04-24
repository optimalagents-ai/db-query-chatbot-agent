import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", None)
TABLE_NAME = os.getenv("TABLE_NAME", None)

def get_db_connection():
    """Create a database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def get_database_schema():
    """Get the database schema information"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all tables in the public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        schema = ""
        
        # For each table, get its columns
        for table in tables:
            table_name = table['table_name']
            
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type,
                    is_nullable
                FROM 
                    information_schema.columns 
                WHERE 
                    table_schema = 'public' 
                    AND table_name = %s
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            schema += f"Table: {table_name}\n"
            schema += "Columns:\n"
            
            for column in columns:
                nullable = "nullable" if column['is_nullable'] == "YES" else "not nullable"
                schema += f"  - {column['column_name']} ({column['data_type']}, {nullable})\n"
            
            schema += "\n"
        
        return schema
    
    except Exception as e:
        print(f"Error fetching database schema: {e}")
        return "Could not retrieve database schema."
    
    finally:
        cursor.close()
        conn.close()

def execute_query(query):
    """Execute a SQL query and return the results"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(query)
        if cursor.description:  # Check if the query returns data
            results = cursor.fetchall()
            return results
        return []
    
    except Exception as e:
        print(f"Error executing query: {e}")
        raise e
    
    finally:
        cursor.close()
        conn.close()


