import pymysql
import os

pymysql.install_as_MySQLdb()

db = pymysql.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    passwd=os.getenv("DATABASE_PASSWORD"),
    db=os.getenv("DATABASE"),
    autocommit=True,
    ssl={"ssl_ca": "/etc/ssl/certs/ca-certificates.crt"},
)


def calculate_and_insert_daily_stats():
    try:
        cursor = db.cursor()
        # Calculate daily averages and total tokens
        query = """
        SELECT 
            DATE(timestamp) as date,
            AVG(time_to_first_token) as avg_time_to_first_token,
            AVG(time_for_all_tokens) as avg_time_for_all_tokens,
            AVG(total_time) as avg_total_time,
            AVG(tps) as avg_tps,
            SUM(JSON_LENGTH(tokens)) as total_tokens
        FROM miner_response
        WHERE timestamp >= CURDATE() - INTERVAL 1 DAY 
          AND timestamp < CURDATE()
        GROUP BY DATE(timestamp)
        """
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            # Insert the calculated stats into the historical stats table
            insert_query = """
            INSERT INTO miner_response_historical_stats
            (date, avg_time_to_first_token, avg_time_for_all_tokens, avg_total_time, avg_tps, total_tokens)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, result)
            print(f"Inserted daily stats for {result[0]}")
        else:
            print("No data found for yesterday")
            return False

        return True
    except pymysql.Error as e:
        print(f"Database error occurred: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def delete_processed_records():
    try:
        cursor = db.cursor()

        delete_query = """
            DELETE FROM miner_response
            WHERE timestamp <= CURDATE() - INTERVAL 1 DAY 10 MINUTE
        """

        cursor.execute(delete_query)
        print("Processed records deleted")
    except pymysql.Error as e:
        print(f"Database error occured: {e}")

if __name__ == "__main__":
    try:
        if calculate_and_insert_daily_stats():
            delete_processed_records()
    finally:
        db.close()
