import sqlite3
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATABASE_PATH = (
    BASE_DIR
    / "data"
    / "fraudguard.db"
)


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            demo_position INTEGER,
            transaction_amount REAL,
            product_code TEXT,
            card_network TEXT,
            card_type TEXT,
            fraud_probability REAL,
            risk_level TEXT,
            model_decision TEXT,
            analyst_decision TEXT,
            case_status TEXT DEFAULT 'New Alert',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()

    print("FraudGuard case database initialized.")


def save_case(
    demo_position,
    transaction_amount,
    product_code,
    card_network,
    card_type,
    fraud_probability,
    risk_level,
    model_decision,
    analyst_decision,
    case_status
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO cases (
            demo_position,
            transaction_amount,
            product_code,
            card_network,
            card_type,
            fraud_probability,
            risk_level,
            model_decision,
            analyst_decision,
            case_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            demo_position,
            transaction_amount,
            product_code,
            card_network,
            card_type,
            fraud_probability,
            risk_level,
            model_decision,
            analyst_decision,
            case_status
        )
    )

    connection.commit()

    case_id = cursor.lastrowid

    connection.close()

    return case_id


def get_all_cases():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cases
        ORDER BY created_at DESC, id DESC
        """
    )

    cases = cursor.fetchall()

    connection.close()

    return cases

if __name__ == "__main__":
    initialize_database()