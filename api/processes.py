from fastapi import FastAPI, Query, Request, Header, HTTPException
from .db import get_connection
from .auth_middleware import HeaderAuthMiddleware

app = FastAPI()

app.add_middleware(HeaderAuthMiddleware)

# ---------------- DATABASE CONNECTION ----------------

# ---------------- API ----------------
# @app.get("/processes")
# def get_processes(client_id: int = Query(..., description="ID of the client")):
#     conn = get_connection()
#     try:
#         with conn.cursor() as cursor:
#             # Fetch all processes for the given client_id
#             cursor.execute("SELECT * FROM processes WHERE client_id=%s", (client_id,))
#             processes = cursor.fetchall()
            
#             result = []
            
#             for process in processes:
#                 # Fetch steps for this process
#                 cursor.execute(
#                     "SELECT * FROM steps WHERE process_id=%s ORDER BY step_sr_no", 
#                     (process['process_id'],)
#                 )
#                 steps = cursor.fetchall()
                
#                 steps_list = []
                
#                 for step in steps:
#                     # Fetch step contents
#                     cursor.execute(
#                         "SELECT * FROM step_contents WHERE step_id=%s",
#                         (step['step_id'],)
#                     )
#                     contents = cursor.fetchall()
                    
#                     contents_list = []
                    
#                     for content in contents:
#                         # Fetch languages / content details
#                         cursor.execute(
#                             "SELECT * FROM step_content_details WHERE step_content_id=%s",
#                             (content['step_content_id'],)
#                         )
#                         languages = cursor.fetchall()
                        
#                         languages_list = []
#                         for lang in languages:
#                             # Example voice_over, replace with actual table if exists
#                             voice_over = [{
#                                 "step_content_voice_over_id": f"VO{lang['step_content_detail_id']:03}",
#                                 "voice_over_type": "audio",
#                                 "file_url": "https://example.com/voiceover/machine_sound.mp3"
#                             }]
#                             languages_list.append({
#                                 "step_content_language_id": f"LANG{lang['step_content_detail_id']:03}",
#                                 "language_id": lang['language_id'],
#                                 "file_url": lang['file_url'],
#                                 "duration_or_no_pages": lang['duration_or_no_pages'],
#                                 "step_content_voice_over": voice_over
#                             })
                        
#                         contents_list.append({
#                             "step_content_id": f"CNT{content['step_content_id']:03}",
#                             "content_type": content['content_type'],
#                             "languages": languages_list
#                         })
                    
#                     steps_list.append({
#                         "step_id": f"STEP{step['step_id']:03}",
#                         "step_name": step['step_name'],
#                         "step_desc": step['step_desc'],
#                         "est_step_time": step['est_step_time'],
#                         "step_sr_no": step['step_sr_no'],
#                         "step_contents": contents_list
#                     })
                
#                 result.append({
#                     "client_id": str(process['client_id']),
#                     "process_id": f"PROC{process['process_id']:03}",
#                     "process_name": process['process_name'],
#                     "process_desc": process['process_desc'],
#                     "est_process_time": process['est_process_time'],
#                     "no_of_steps": process['no_of_steps'],
#                     "steps": steps_list
#                 })
            
#             return {"processes": result}
#     finally:
#         conn.close()

# @app.post("/save-operator-session")
# async def save_operator_session(request: Request):

#     data = await request.json()
#     sessions = data.get("operator_session", [])

#     conn = get_connection()
#     cursor = conn.cursor()

#     try:
#         for session in sessions:

#             client_id = session.get("client_id")
#             operator_id = session.get("operator_id")

#             # ========== 1) operator_sessions INSERT ==========
#             op_sql = """
#                 INSERT INTO operator_sessions
#                 (session_id, operator_id, process_id, start_time, end_time,
#                  total_time, status, client_id)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """

#             cursor.execute(op_sql, (
#                 session["session_id"],
#                 operator_id,
#                 session["process_id"],
#                 session["start_time"],
#                 session["end_time"],
#                 session["total_time"],
#                 session["status"],
#                 client_id
#             ))

#             operator_session_id = cursor.lastrowid

#             # ========== 2) session_steps INSERT ==========
#             for step in session["session_steps"]:

#                 step_sql = """
#                     INSERT INTO session_steps
#                     (step_session_id, session_id, step_id, step_sr_no,
#                      started_at, ended_at, time_spent_sec, content_used, client_id)
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 """

#                 cursor.execute(step_sql, (
#                     step["step_session_id"],
#                     step["session_id"],
#                     step["step_id"],
#                     step["step_sr_no"],
#                     step["started_at"],
#                     step.get("ended_at"),
#                     step.get("time_spent_sec"),
#                     "yes" if step["content_used"] else "no",
#                     client_id
#                 ))

#                 # ========== 3) session_step_content_usage INSERT ==========
#                 if "session_step_content" in step:
#                     for content in step["session_step_content"]:

#                         content_sql = """
#                             INSERT INTO session_step_content_usage
#                             (usage_id, step_content_type, opened_at, closed_at,
#                              duration, client_id, step_session_id, step_content_id, language_id)
#                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                         """

#                         cursor.execute(content_sql, (
#                             content["usage_id"],
#                             content["step_content_type"],
#                             content["opened_at"],
#                             content["closed_at"],
#                             content["duration"],
#                             client_id,
#                             step["step_session_id"],
#                             content["step_content_id"],
#                             content["language_id"]
#                         ))

#         conn.commit()

#         return {"status": "success", "message": "Operator session saved successfully"}

#     except Exception as e:
#         conn.rollback()
#         return {"status": "error", "message": str(e)}

#     finally:
#         cursor.close()
#         conn.close()

#Get Operators 
@app.get("/operators")
def get_operators(
    client_id: int = Header(..., alias="client-id"),
    device_id: int = Header(..., alias="device-id")
):
    try:
        print("Received client_id:", client_id)
        print("Received device_id:", device_id)

        db = get_connection()
        cursor = db.cursor()

        query = """
            SELECT 
                user_id,
                name,
                email,
                mobile
            FROM user
            WHERE client_id = %s AND type_id_id = 4
        """
        
        # print("Running query:", query % client_id)

        cursor.execute(query, (client_id,))
        rows = cursor.fetchall()

        # print("Fetched rows:", rows)

        operators = []
        for r in rows:
            operators.append({
                "operator_id": r["user_id"],
                "opertor_name": r["name"],
                "operator_email": r["email"],
                "operator_mobile": r["mobile"],
                "clien_id" : client_id
            })

        return {"status": "success", "operators": operators}

    except Exception as e:
        # print("REAL ERROR:", repr(e))   # <-- THIS SHOWS THE ACTUAL ERROR
        return {"status": "error", "message": repr(e)}

@app.get("/processes")
def get_processes(
    client_id: int = Header(..., alias="client-id"),
    device_id: int = Header(..., alias="device-id")
):
    try:
        # print("Received client_id:", client_id)
        # print("Received device_id:", device_id)

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
