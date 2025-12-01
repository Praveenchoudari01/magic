from fastapi import FastAPI, Query, Request
import pymysql


app = FastAPI()

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1619",
        database="magic",
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------------- API ----------------
@app.get("/processes")
def get_processes(client_id: int = Query(..., description="ID of the client")):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch all processes for the given client_id
            cursor.execute("SELECT * FROM processes WHERE client_id=%s", (client_id,))
            processes = cursor.fetchall()
            
            result = []
            
            for process in processes:
                # Fetch steps for this process
                cursor.execute(
                    "SELECT * FROM steps WHERE process_id=%s ORDER BY step_sr_no", 
                    (process['process_id'],)
                )
                steps = cursor.fetchall()
                
                steps_list = []
                
                for step in steps:
                    # Fetch step contents
                    cursor.execute(
                        "SELECT * FROM step_contents WHERE step_id=%s",
                        (step['step_id'],)
                    )
                    contents = cursor.fetchall()
                    
                    contents_list = []
                    
                    for content in contents:
                        # Fetch languages / content details
                        cursor.execute(
                            "SELECT * FROM step_content_details WHERE step_content_id=%s",
                            (content['step_content_id'],)
                        )
                        languages = cursor.fetchall()
                        
                        languages_list = []
                        for lang in languages:
                            # Example voice_over, replace with actual table if exists
                            voice_over = [{
                                "step_content_voice_over_id": f"VO{lang['step_content_detail_id']:03}",
                                "voice_over_type": "audio",
                                "file_url": "https://example.com/voiceover/machine_sound.mp3"
                            }]
                            languages_list.append({
                                "step_content_language_id": f"LANG{lang['step_content_detail_id']:03}",
                                "language_id": lang['language_id'],
                                "file_url": lang['file_url'],
                                "duration_or_no_pages": lang['duration_or_no_pages'],
                                "step_content_voice_over": voice_over
                            })
                        
                        contents_list.append({
                            "step_content_id": f"CNT{content['step_content_id']:03}",
                            "content_type": content['content_type'],
                            "languages": languages_list
                        })
                    
                    steps_list.append({
                        "step_id": f"STEP{step['step_id']:03}",
                        "step_name": step['step_name'],
                        "step_desc": step['step_desc'],
                        "est_step_time": step['est_step_time'],
                        "step_sr_no": step['step_sr_no'],
                        "step_contents": contents_list
                    })
                
                result.append({
                    "client_id": str(process['client_id']),
                    "process_id": f"PROC{process['process_id']:03}",
                    "process_name": process['process_name'],
                    "process_desc": process['process_desc'],
                    "est_process_time": process['est_process_time'],
                    "no_of_steps": process['no_of_steps'],
                    "steps": steps_list
                })
            
            return {"processes": result}
    finally:
        conn.close()

@app.post("/save-operator-session")
async def save_operator_session(request: Request):

    data = await request.json()
    sessions = data.get("operator_session", [])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for session in sessions:

            client_id = session.get("client_id")
            operator_id = session.get("operator_id")

            # ========== 1) operator_sessions INSERT ==========
            op_sql = """
                INSERT INTO operator_sessions
                (session_id, operator_id, process_id, start_time, end_time,
                 total_time, status, client_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(op_sql, (
                session["session_id"],
                operator_id,
                session["process_id"],
                session["start_time"],
                session["end_time"],
                session["total_time"],
                session["status"],
                client_id
            ))

            operator_session_id = cursor.lastrowid

            # ========== 2) session_steps INSERT ==========
            for step in session["session_steps"]:

                step_sql = """
                    INSERT INTO session_steps
                    (step_session_id, session_id, step_id, step_sr_no,
                     started_at, ended_at, time_spent_sec, content_used, client_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(step_sql, (
                    step["step_session_id"],
                    step["session_id"],
                    step["step_id"],
                    step["step_sr_no"],
                    step["started_at"],
                    step.get("ended_at"),
                    step.get("time_spent_sec"),
                    "yes" if step["content_used"] else "no",
                    client_id
                ))

                # ========== 3) session_step_content_usage INSERT ==========
                if "session_step_content" in step:
                    for content in step["session_step_content"]:

                        content_sql = """
                            INSERT INTO session_step_content_usage
                            (usage_id, step_content_type, opened_at, closed_at,
                             duration, client_id, step_session_id, step_content_id, language_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                        cursor.execute(content_sql, (
                            content["usage_id"],
                            content["step_content_type"],
                            content["opened_at"],
                            content["closed_at"],
                            content["duration"],
                            client_id,
                            step["step_session_id"],
                            content["step_content_id"],
                            content["language_id"]
                        ))

        conn.commit()

        return {"status": "success", "message": "Operator session saved successfully"}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()