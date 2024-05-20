
CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL
);

INSERT INTO emails (email) VALUES ('dershtal@gmail.com'), ('dershtal@yandex.ru');
INSERT INTO phone_numbers (phone_number) VALUES ('89675431212'), ('+79685311551');

CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'Qq12345' LOGIN;
SELECT pg_create_physical_replication_slot('replication_slot');

-- CREATE USER ${DB_REPL_USER} REPLICATION LOGIN PASSWORD '${DB_REPL_PASSWORD}';

--CREATE USER ${DB_REPL_USER} WITH REPLICATION ENCRYPTED PASSWORD '${DB_REPL_PASSWORD}' LOGIN;

--ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';CREATE USER ${DB_REPL_USER} REPLICATION LOGIN PASSWORD '${DB_REPL_PASSWORD}';