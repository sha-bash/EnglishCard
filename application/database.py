import datetime
from application.db_config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
import psycopg2


class DatabaseManager:

    @staticmethod
    def get_connection():
        return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

    def __init__(self):
        self.connection = DatabaseManager.get_connection()

    def create_schema(self):
    
        create_students = """
        CREATE TABLE IF NOT EXISTS public.students (
            user_id serial4 NOT NULL,
            username varchar(255) NOT NULL,
            first_name varchar(255) NULL,
            last_name varchar(255) NULL,
            created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
            CONSTRAINT students_pkey PRIMARY KEY (user_id),
            CONSTRAINT students_username_key UNIQUE (username)
        );
        """
        create_words = """
        CREATE TABLE IF NOT EXISTS public.words (
            id serial4 NOT NULL,
            english_word varchar(255) NOT NULL,
            russian_translation varchar(255) NOT NULL,
            retrieved_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
            CONSTRAINT words_pkey PRIMARY KEY (id)
        );
        """
        create_student_words = """
        CREATE TABLE IF NOT EXISTS public.student_words (
            student_id int4 NOT NULL,
            word_id int4 NOT NULL,
            studied_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
            review_count int4 DEFAULT 0 NULL,
            last_reviewed_at timestamptz NULL,
            CONSTRAINT student_words_pkey PRIMARY KEY (student_id, word_id),
            CONSTRAINT student_words_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(user_id),
            CONSTRAINT student_words_word_id_fkey FOREIGN KEY (word_id) REFERENCES public.words(id)
        );
        """
    
        with self.connection.cursor() as cursor:
            cursor.execute(create_students)
            cursor.execute(create_words)
            cursor.execute(create_student_words)
        self.connection.commit()


    def insert_student(self, user_id, username, first_name=None, last_name=None):
        insert_query = """
        INSERT INTO students (user_id, username, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING;
        """
        with self.connection.cursor() as cursor:
            cursor.execute(insert_query, (user_id, username, first_name, last_name))
        self.connection.commit()

    def process_user_data(self, user_id, username, first_name, last_name):
        self.insert_student(user_id, username, first_name, last_name)

    def add_word_to_student(self, user_id, english_word):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id FROM words WHERE english_word = %s;", (english_word,))
            word_id = cursor.fetchone()
            if word_id:
                cursor.execute("SELECT word_id FROM student_words WHERE student_id = %s AND word_id = %s;", (user_id, word_id[0]))
                result = cursor.fetchone()

                current_time = datetime.datetime.now()
                if result:
                    cursor.execute("UPDATE student_words SET last_reviewed_at = %s WHERE student_id = %s AND word_id = %s;",
                               (current_time, user_id, word_id[0]))
                else:
                    cursor.execute("INSERT INTO student_words (student_id, word_id, studied_at, last_reviewed_at) VALUES (%s, %s, %s, %s);",
                                   (user_id, word_id[0], current_time, current_time))
                self.connection.commit()

    def insert_words(self, words):
        with self.connection.cursor() as cursor:
            cursor.executemany("INSERT INTO words (english_word, russian_translation) VALUES (%s, %s);", words)
        self.connection.commit()

    def get_words(self):
        with self.connection.cursor() as cursor:
            query = "SELECT english_word, russian_translation FROM words;"
            cursor.execute(query)
            words = cursor.fetchall()
            en_to_ru_dict = {word[0]: word[1] for word in words}
            en_words = list(en_to_ru_dict.keys())
            return en_words, en_to_ru_dict

    def get_user_words(self, user_id):
        with self.connection.cursor() as cursor:
            query = """
                SELECT english_word, russian_translation FROM words w
                JOIN student_words sw ON w.id = sw.word_id
                WHERE sw.student_id = %s;
            """
            cursor.execute(query, (user_id,))
            words = cursor.fetchall()
            en_to_ru_user_dict = {word[0]: word[1] for word in words}
            en_user_words = list(en_to_ru_user_dict.keys())
            return en_user_words, en_to_ru_user_dict

    def close_connection(self):
        self.connection.close()