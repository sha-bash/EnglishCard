CREATE TABLE public.students (
	user_id serial4 NOT NULL,
	username varchar(255) NOT NULL,
	first_name varchar(255) NULL,
	last_name varchar(255) NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT students_pkey PRIMARY KEY (user_id),
	CONSTRAINT students_username_key UNIQUE (username)
);

CREATE TABLE public.words (
	id serial4 NOT NULL,
	english_word varchar(255) NOT NULL,
	russian_translation varchar(255) NOT NULL,
	retrieved_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT words_pkey PRIMARY KEY (id)
);


CREATE TABLE public.student_words (
	student_id int4 NOT NULL,
	word_id int4 NOT NULL,
	studied_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	review_count int4 DEFAULT 0 NULL,
	last_reviewed_at timestamptz NULL,
	CONSTRAINT student_words_pkey PRIMARY KEY (student_id, word_id),
	CONSTRAINT student_words_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(user_id),
	CONSTRAINT student_words_word_id_fkey FOREIGN KEY (word_id) REFERENCES public.words(id)
);