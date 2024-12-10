import sqlite3
import csv
from datetime import datetime

def export_student_unpaid_amounts():
    # Database connection
    try:
        conn = sqlite3.connect('mclassbookstore.db')
        cursor = conn.cursor()

        # Modified SQL query to get only students with unpaid amounts
        query = """
        SELECT 
            s.name,
            COALESCE(SUM(CASE WHEN b.payment_date IS NULL THEN b.price ELSE 0 END), 0) as unpaid_amount
        FROM student s
        LEFT JOIN book b ON s.id = b.student_id
        GROUP BY s.name
        HAVING unpaid_amount > 0
        ORDER BY s.name
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Create CSV file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'student_unpaid_amounts_{timestamp}.csv'

        # Write to CSV with UTF-8 encoding
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['학생 이름', '미납 금액'])  # Header
            writer.writerows(results)

        print(f"CSV file '{filename}' has been created successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    export_student_unpaid_amounts()