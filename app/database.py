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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            risk_level TEXT,
            fraud_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_session_id)
                REFERENCES chat_sessions(id)
                ON DELETE CASCADE
        )
        """
    )
    connection.commit()
    connection.close()

    print("FraudGuard database initialized.")


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

def create_chat_session(
    transaction_id=None,
    risk_level=None,
    fraud_score=None
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chat_sessions (
            transaction_id,
            risk_level,
            fraud_score
        )
        VALUES (?, ?, ?)
        """,
        (
            transaction_id,
            risk_level,
            fraud_score
        )
    )

    connection.commit()

    chat_session_id = cursor.lastrowid

    connection.close()

    return chat_session_id


def save_chat_message(
    chat_session_id,
    role,
    message
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chat_messages (
            chat_session_id,
            role,
            message
        )
        VALUES (?, ?, ?)
        """,
        (
            chat_session_id,
            role,
            message
        )
    )

    connection.commit()
    connection.close()


def get_chat_sessions():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            cs.*,
            COUNT(cm.id) AS message_count,
            (
                SELECT message
                FROM chat_messages
                WHERE chat_session_id = cs.id
                  AND role = 'user'
                ORDER BY id ASC
                LIMIT 1
            ) AS first_question
        FROM chat_sessions cs
        INNER JOIN chat_messages cm
            ON cm.chat_session_id = cs.id
        GROUP BY cs.id
        HAVING COUNT(cm.id) > 0
        ORDER BY cs.created_at DESC, cs.id DESC
        """
    )

    chat_sessions = cursor.fetchall()

    connection.close()

    return chat_sessions


def get_chat_messages(chat_session_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_messages
        WHERE chat_session_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (chat_session_id,)
    )

    messages = cursor.fetchall()

    connection.close()

    return messages

if __name__ == "__main__":
    initialize_database()