import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


def get_all_related_objects(conn, object_ids):
    all_ids = set(object_ids)
    with conn.cursor() as cur:
        queue = list(object_ids)
        while queue:
            current = queue.pop(0)
            cur.execute("SELECT object FROM data WHERE parent = %s", (current,))
            children = [row[0] for row in cur.fetchall()]
            for child in children:
                if child not in all_ids:
                    all_ids.add(child)
                    queue.append(child)
    return list(all_ids)


def process_document(conn):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM documents
                WHERE processed_at IS NULL
                  AND document_data->'document_data'->>'document_type' = 'transfer_document'
                ORDER BY recieved_at ASC
                LIMIT 1
            """)
            doc = cur.fetchone()
            if not doc:
                print("Не найден необработанный документ.")
                return False

            if isinstance(doc["document_data"], dict):
                document_data = doc["document_data"]
            else:
                document_data = json.loads(doc["document_data"])

            objects = document_data.get("objects", [])
            operation_details = document_data.get("operation_details", {})

            related_objects = get_all_related_objects(conn, objects)

            for obj_id in related_objects:
                cur.execute("SELECT * FROM data WHERE object = %s", (obj_id,))
                data_row = cur.fetchone()
                if not data_row:
                    continue

                update_needed = False
                update_fields = {}

                for field, change in operation_details.items():
                    if field in data_row:
                        old_val = change.get("old")
                        new_val = change.get("new")
                        current_val = data_row[field]

                        if isinstance(old_val, list):
                            if current_val in old_val:
                                update_fields[field] = new_val
                                update_needed = True
                        else:
                            if current_val == old_val:
                                update_fields[field] = new_val
                                update_needed = True

                if update_needed:
                    set_clause = ", ".join([f"{k} = %s" for k in update_fields.keys()])
                    values = list(update_fields.values())
                    values.append(obj_id)
                    sql = f"UPDATE data SET {set_clause} WHERE object = %s"
                    cur.execute(sql, values)

            cur.execute("UPDATE documents SET processed_at = %s WHERE doc_id = %s",
                        (datetime.utcnow(), doc["doc_id"]))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Ошибка при обработке документа:", e)
        return False


if __name__ == '__main__':
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRESS_DB'),
        user=os.getenv('POSTGRESS_USER'),
        password=os.getenv('POSTGRESS_PASSWORD'),
        host="localhost",
        port=5432
    )

    result = process_document(conn)
    print("Документ обработан:", result)
    conn.close()
