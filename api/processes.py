from fastapi import FastAPI, Query
import pymysql


app = FastAPI()

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="username",
        password="password",
        database="dbname",
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
