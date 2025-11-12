import random

LOG_CLEANUP_PROBABILITY = 0.01


def sql_insert_log(db_cursor, tag: str, msg: str) -> None:
    db_cursor.execute("INSERT INTO logs (t, tag, msg) VALUES (now(), %s, %s)", (tag, msg))
    if random.random() < LOG_CLEANUP_PROBABILITY:
        sql_delete_old_logs(db_cursor)


def sql_delete_old_logs(db_cursor) -> None:
    db_cursor.execute("DELETE FROM logs WHERE t < NOW() - INTERVAL '7 days'")
