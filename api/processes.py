from fastapi import FastAPI, Query, Request, Header, HTTPException
from .db import get_connection
from .auth_middleware import HeaderAuthMiddleware
import hmac
import hashlib


app = FastAPI()

app.add_middleware(HeaderAuthMiddleware)

# Get Operators 
@app.get("/operators")
def get_operators(
    api_key: str = Header(..., alias="api-key"),
):
    client_id_str, device_id_str = api_key.split(":", 1)
    client_id = client_id_str
    device_id = device_id_str

    print("clinet id from the get operators is ", client_id)
    try:
        db = get_connection()
        cursor = db.cursor()

        query = """
            SELECT 
                user_id,
                operator_id,
                name,
                email,
                mobile
            FROM user
            WHERE client_id = %s AND type_id_id = 4 AND is_active = 1
            ORDER BY id
        """

        cursor.execute(query, (client_id,))
        rows = cursor.fetchall()

        operators = []
        for r in rows:
            operator_id = r["user_id"]

            process_query = """
                SELECT process_id 
                FROM oprator_process
                WHERE operator_id = %s
                ORDER BY id
            """
            cursor.execute(process_query, (operator_id))
            processes = cursor.fetchall()

            process_list = []

            for process in processes:
                process_list.append({
                    "process_id" : process["process_id"]
                })
            operators.append({
                "operator_id": r["operator_id"],
                "user_id" : r["user_id"],
                "clien_id": client_id,
                "opertor_name": r["name"],
                "operator_email": r["email"],
                "operator_mobile": r["mobile"],
                "processes": process_list
            })

        return {"status": "success", "operators": operators}

    except Exception as e:
        return {"status": "error", "message": repr(e)}

@app.get("/processes")
def get_processes(
    api_key: str = Header(..., alias="api-key"),
):
    client_id_str, device_id_str = api_key.split(":", 1)
    client_id = client_id_str
    device_id = device_id_str

    try:
        db = get_connection()
        cursor = db.cursor()

        # Fetch processes
        query = """
            SELECT process_id, process_name, process_desc, est_process_time, no_of_steps
            FROM processes 
            WHERE client_id = %s AND is_active = 1;
        """ 
        cursor.execute(query, (client_id,))
        processes_rows = cursor.fetchall()

        processes = []

        for process in processes_rows:

            # Fetch steps for this process
            step_query = """
                SELECT step_id, step_name, step_desc, est_step_time, step_sr_no
                FROM steps 
                WHERE process_id = %s AND is_active = 1
                ORDER BY step_sr_no ASC;
            """
            cursor.execute(step_query, (process["process_id"],))
            steps_rows = cursor.fetchall()

            steps_list = []

            for step in steps_rows:
                
                step_id = step['step_id']
                print("step id is ",step_id)

                step_content_query = """
                    SELECT step_content_id, name, content_type
                    FROM step_contents
                    WHERE step_id = %s AND is_active = 1
                """

                cursor.execute(step_content_query, (step_id))
                step_conent_rows = cursor.fetchall()

                step_contents = []
                for step_content in step_conent_rows:
                    
                    step_content_id = step_content["step_content_id"]
                    print("step content_id is ",step_content_id)

                    step_content_details_query = """ 
                        SELECT step_content_detail_id, content_language_id, file_url, duration_or_no_pages
                        FROM step_content_details
                        WHERE step_content_id = %s AND is_active = 1
                    """
                    cursor.execute(step_content_details_query, (step_content_id))
                    step_content_details_rows = cursor.fetchall()

                    languages = []

                    for content_details in step_content_details_rows:

                        step_content_detail_id = content_details['step_content_detail_id']
                        print("step_content_detail_id is ", step_content_detail_id)

                        voice_over_query = """ 
                            SELECT step_content_voice_over_id, voice_over_file_type, language_id, language, file_url
                            FROM step_content_voice_over
                            WHERE step_content_detail_id = %s AND is_active = 1
                        """
                        cursor.execute(voice_over_query, (step_content_detail_id))
                        voice_overs_list = cursor.fetchall()

                        step_content_voice_over = []

                        for voice_over in voice_overs_list:

                            step_content_voice_over.append({
                                "step_content_voice_over_id" : voice_over["step_content_voice_over_id"],
                                "voice_over_type" : voice_over["voice_over_file_type"],
                                "language_id" : voice_over["language_id"],
                                "language" : voice_over["language"],
                                "file_url" : voice_over["file_url"]
                            })

                        captions_query = """
                            SELECT caption_id, file_url, caption_file_type
                            FROM step_content_captions
                            WHERE step_content_detail_id = %s AND is_active = 1
                        """
                        cursor.execute(captions_query, (step_content_detail_id))
                        captions_list = cursor.fetchall()

                        captions = []

                        for caption in captions_list:
                            captions.append({
                                "caption_id" : caption['caption_id'],
                                "file_url" : caption['file_url'],
                                "caption_file_type" : caption['caption_file_type']
                            })

                        languages.append({
                            "step_content_id" : step_content_id,
                            "step_content_detail_id" : content_details['step_content_detail_id'],
                            "content_language_id" : content_details['content_language_id'],
                            "file_url" : content_details['file_url'],
                            "duration_or_no_pages" : content_details['duration_or_no_pages'],
                            "step_content_voice_over" : step_content_voice_over,
                            "captions" : captions

                        })

                    step_contents.append({
                        "step_content_id" : step_content['step_content_id'],
                        "content_type" : step_content['content_type'],
                        "languages" : languages
                    })

                steps_list.append({
                    "step_id": step["step_id"],
                    "step_name": step["step_name"],
                    "step_desc": step["step_desc"],
                    "est_step_time": step["est_step_time"],
                    "step_sr_no": step["step_sr_no"],
                    "step_contents" : step_contents
                })

            # Build final process object
            processes.append({
                "client_id": client_id,
                "process_id": process["process_id"],
                "process_name": process["process_name"],
                "process_desc": process["process_desc"],
                "est_process_time": process["est_process_time"],
                "no_of_steps": process["no_of_steps"],
                "steps": steps_list
            })
        
        return {"status": "success", "processes": processes}

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}

#Operator stats
@app.post('/operator-stats')
async def receive_session_data(
    request: Request,
    api_key: str = Header(..., alias="api-key"),
):
    client_id_str, device_id_str = api_key.split(":", 1)
    client_id = client_id_str
    device_id = device_id_str

    try:
        # Read JSON body
        payload = await request.json()
        operator_session_list = payload["operator_session"]

        # Connect to DB
        conn = get_connection()
        cursor = conn.cursor()

        # 🔹 Collect stored data for response
        stored_data = []

        for session in operator_session_list:

            # 🔹 Collect step_session_id from API payload
            step_session_ids = []

            # ---------------------------------------
            # 1️⃣ Insert into operator_sessions table
            # ---------------------------------------
            insert_operator_session = """
                INSERT INTO operator_sessions 
                (session_id, operator_id, client_id, process_id, 
                start_time, end_time, total_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_operator_session, (
                session["session_id"],
                session["operator_id"],
                session["client_id"],
                session["process_id"],
                session["start_time"],
                session["end_time"],
                session["total_time"],
                session["status"]
            ))

            operator_session_db_id = cursor.lastrowid

            # ---------------------------------------
            # 2️⃣ Insert session steps
            # ---------------------------------------
            for step in session["session_steps"]:

                insert_session_step = """
                    INSERT INTO session_steps
                    (session_step_id, session_id, step_sr_no, started_at, 
                    ended_at, time_spent_sec, content_used, client_id, step_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(insert_session_step, (
                    step["step_session_id"],
                    step["session_id"],
                    step["step_sr_no"],
                    step["started_at"],
                    step["ended_at"],
                    step["time_spent_sec"],
                    str(step["content_used"]),
                    session["client_id"],
                    step["step_id"]
                ))

                # 🔹 STORE step_session_id FROM API PAYLOAD
                step_session_ids.append(step["step_session_id"])

                # ---------------------------------------
                # 3️⃣ Insert step content usage
                # ---------------------------------------
                for content in step["session_step_content"]:

                    insert_step_content = """
                        INSERT INTO session_step_content_usage
                        (usage_id, step_content_type, opened_at, closed_at, duration, 
                        client_id, step_session_id, step_content_id, language_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(insert_step_content, (
                        content["usage_id"],
                        content["step_content_type"],
                        content["opened_at"],
                        content["closed_at"],
                        content["duration"],
                        session["client_id"],
                        step["step_session_id"],  # payload value
                        content["step_content_id"],
                        content["content_language_id"]
                    ))

            # 🔹 Store session-level response data
            stored_data.append({
                "session_id": session["session_id"],
                "process_id": session["process_id"],
                "operator_id": session["operator_id"],
                "client_id": session["client_id"],
            })

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "message": "Session data stored in DB",
            "data": stored_data
        }

    except Exception as e:
        print("DB Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# To check this api endpoint comment the app.middleware to ignore the headers and authentiation
@app.get("/validate-code")
def validate_code(code: str):
    try:
        db = get_connection()
        cursor = db.cursor()

        query = """
            SELECT unique_id 
            FROM vr_device 
            WHERE unique_id = %s AND is_active = 1
        """
        cursor.execute(query, (code,))
        result = cursor.fetchone()

        if result:
            return {
                "status": "success",
                "valid": False,
                "message": "Code already exists, re-generate new code"
            }

        return {
            "status": "success",
            "valid": True,
            "message": "Code is unique"
        }

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}
