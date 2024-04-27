import datetime
from db_config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
import psycopg2


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def insert_student(user_id, username, first_name=None, last_name=None):
    connection = get_connection()
    insert_query = """
    INSERT INTO students (user_id, username, first_name, last_name)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (user_id) DO NOTHING;
    """
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (user_id, username, first_name, last_name))
        connection.commit()  # Добавлен вызов commit для фиксации транзакции

def process_user_data(user_id, username, first_name, last_name):
    # Нет необходимости переопределять аргументы функции, просто вызовите insert_student
    insert_student(user_id, username, first_name, last_name)

def add_word_to_student(user_id, english_word):
    conn = get_connection()
    with conn.cursor() as cursor:
        # Получаем word_id для данного английского слова
        cursor.execute("SELECT id FROM words WHERE english_word = %s;", (english_word,))
        word_id = cursor.fetchone()
        if word_id:
            # Проверяем, существует ли уже запись для данного пользователя и слова
            cursor.execute("SELECT word_id FROM student_words WHERE student_id = %s AND word_id = %s;", (user_id, word_id[0]))
            result = cursor.fetchone()

            current_time = datetime.datetime.now()
            if result:
                cursor.execute("UPDATE student_words SET last_reviewed_at = %s WHERE student_id = %s AND word_id = %s;",
                               (current_time, user_id, word_id[0]))
            else:
                # Если записи нет, создаем новую с review_count = 1
                cursor.execute("INSERT INTO student_words (student_id, word_id, studied_at, last_reviewed_at) VALUES (%s, %s, %s, %s);",
                               (user_id, word_id[0], current_time, current_time))
            conn.commit()
    conn.close()

