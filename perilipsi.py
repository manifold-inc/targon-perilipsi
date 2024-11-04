import pymysql
import os
import time
import requests
import traceback

pymysql.install_as_MySQLdb()

db = pymysql.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    passwd=os.getenv("DATABASE_PASSWORD"),
    db=os.getenv("DATABASE"),
    autocommit=True,
    ssl={"ssl_ca": "/etc/ssl/certs/ca-certificates.crt"},
)

ENDON_URL = os.getenv("ENDON_URL")


def sendErrorToEndon(error: Exception, error_traceback: str, endpoint: str) -> None:
    try:
        error_payload = {
            "service": "targon-perilipsi",
            "endpoint": endpoint,
            "error": str(error),
            "traceback": error_traceback,
        }
        response = requests.post(
            str(ENDON_URL),
            json=error_payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"Failed to report error to Endon. Status code: {response.status_code}")
            print(f"Response: {response.text}")
        else:
            print("Error successfully reported to Endon")
    except Exception as e:
        print(f"Failed to report error to Endon: {str(e)}")


def calculate_and_insert_daily_stats():
    try:
        with db.cursor() as cursor:
            # Calculate daily averages and total tokens
            query = """
            SELECT 
                DATE(timestamp) as date,
                AVG(time_to_first_token) as avg_time_to_first_token,
                AVG(time_for_all_tokens) as avg_time_for_all_tokens,
                AVG(total_time) as avg_total_time,
                AVG(tps) as avg_tps,
                SUM(total_tokens) as total_tokens
            FROM miner_response
            WHERE timestamp >= CURDATE() - INTERVAL 1 DAY 
              AND timestamp < CURDATE()
            GROUP BY DATE(timestamp)
            """
            cursor.execute(query)
            result = cursor.fetchone()

            if not result:
                print("No data found for yesterday")
                return False

            # Insert the calculated stats into the historical stats table
            insert_query = """
            INSERT INTO miner_response_historical_stats
            (date, avg_time_to_first_token, avg_time_for_all_tokens, avg_total_time, avg_tps, total_tokens)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, result)
            print(f"Inserted daily stats for {result[0]}")
            return True

    except (pymysql.Error, Exception) as e:
        error_traceback = traceback.format_exc()
        sendErrorToEndon(
            e, error_traceback, "calcorinsertion"
        )
        print(
            f"{'Database' if isinstance(e, pymysql.Error) else 'An'} error occurred: {e}"
        )
        return False


def delete_processed_records():
    try:
        with db.cursor() as cursor:
            batch_size = 10000

            count_query = """
                SELECT COUNT(*) FROM miner_response
                WHERE timestamp < CURDATE() - INTERVAL 10 MINUTE
            """
            cursor.execute(count_query)
            result = cursor.fetchone()

            if result is None:
                print("No records found to delete")
                return

            total_count = result[0]
            print(f"Found {total_count} records to delete")

            delete_query = """
                DELETE FROM miner_response
                WHERE timestamp < CURDATE() - INTERVAL 10 MINUTE
                LIMIT %s
            """
            for offset in range(0, total_count, batch_size):
                cursor.execute(delete_query, (batch_size,))
                print(
                    f"Deleted batch of {cursor.rowcount} records. Progress: {offset + cursor.rowcount}/{total_count}"
                )
                time.sleep(0.5)

            print("Finished deleting all records")

    except pymysql.Error as e:
        error_traceback = traceback.format_exc()
        sendErrorToEndon(e, error_traceback, "deletion")
        print(f"Database error occurred: {e}")


if __name__ == "__main__":
    try:
        if calculate_and_insert_daily_stats():
            delete_processed_records()
    finally:
        db.close()
