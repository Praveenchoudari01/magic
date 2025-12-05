
#Optimised 
@app.get("/client-processes")
def get_processes(
    client_id: int = Header(..., alias="client-id"),
    device_id: int = Header(..., alias="device-id")
):
    try:
        db = get_connection()
        cursor = db.cursor()

        # Single JOIN query fetching EVERYTHING
        query = """
        SELECT 
            p.process_id, p.process_name, p.process_desc, p.est_process_time, p.no_of_steps, 
            
            s.step_id, s.step_name, s.step_desc, s.est_step_time, s.step_sr_no,
            
            sc.step_content_id, sc.name AS content_name, sc.content_type,
            
            scd.step_content_detail_id, scd.content_language_id, scd.file_url AS detail_file_url,
            scd.duration_or_no_pages,
            
            vo.step_content_voice_over_id, vo.voice_over_file_type, vo.language_id AS vo_language_id,
            vo.language AS vo_language, vo.file_url AS vo_file_url,
            
            cap.caption_id, cap.file_url AS caption_file_url, cap.caption_file_type

        FROM processes p
        LEFT JOIN steps s ON p.process_id = s.process_id AND s.is_active = 1
        LEFT JOIN step_contents sc ON s.step_id = sc.step_id AND sc.is_active = 1
        LEFT JOIN step_content_details scd ON sc.step_content_id = scd.step_content_id AND scd.is_active = 1
        LEFT JOIN step_content_voice_over vo ON scd.step_content_detail_id = vo.step_content_detail_id AND vo.is_active = 1
        LEFT JOIN step_content_captions cap ON scd.step_content_detail_id = cap.step_content_detail_id AND cap.is_active = 1

        WHERE p.client_id = %s AND p.is_active = 1
        ORDER BY p.process_id, s.step_sr_no, sc.step_content_id, scd.step_content_detail_id;
        """

        cursor.execute(query, (client_id,))
        rows = cursor.fetchall()

        # -------------------------
        # RECONSTRUCT NESTED STRUCTURE
        # -------------------------

        processes_map = {}

        for row in rows:

            # Process level
            pid = row["process_id"]
            if pid not in processes_map:
                processes_map[pid] = {
                    "client_id": client_id,
                    "process_id": pid,
                    "process_name": row["process_name"],
                    "process_desc": row["process_desc"],
                    "est_process_time": row["est_process_time"],
                    "no_of_steps": row["no_of_steps"],
                    "steps": {}
                }

            process = processes_map[pid]

            # Step level
            sid = row["step_id"]
            if sid and sid not in process["steps"]:
                process["steps"][sid] = {
                    "step_id": sid,
                    "step_name": row["step_name"],
                    "step_desc": row["step_desc"],
                    "est_step_time": row["est_step_time"],
                    "step_sr_no": row["step_sr_no"],
                    "step_contents": {}
                }

            if not sid:
                continue  # no steps

            step = process["steps"][sid]

            # Step content level
            scid = row["step_content_id"]
            if scid and scid not in step["step_contents"]:
                step["step_contents"][scid] = {
                    "step_content_id": scid,
                    "content_type": row["content_type"],
                    "languages": {}
                }

            if not scid:
                continue  # no step contents

            content = step["step_contents"][scid]

            # Step content details (languages)
            scdid = row["step_content_detail_id"]
            if scdid and scdid not in content["languages"]:
                content["languages"][scdid] = {
                    "step_content_id": scid,
                    "step_content_detail_id": scdid,
                    "content_language_id": row["content_language_id"],
                    "file_url": row["detail_file_url"],
                    "duration_or_no_pages": row["duration_or_no_pages"],
                    "step_content_voice_over": [],
                    "captions": []
                }

            if not scdid:
                continue

            lang = content["languages"][scdid]

            # Voice overs
            if row["step_content_voice_over_id"]:
                lang["step_content_voice_over"].append({
                    "step_content_voice_over_id": row["step_content_voice_over_id"],
                    "voice_over_type": row["voice_over_file_type"],
                    "language_id": row["vo_language_id"],
                    "language": row["vo_language"],
                    "file_url": row["vo_file_url"]
                })

            # Captions
            if row["caption_id"]:
                lang["captions"].append({
                    "caption_id": row["caption_id"],
                    "file_url": row["caption_file_url"],
                    "caption_file_type": row["caption_file_type"]
                })

        # Convert structure to clean nested list format
        final_processes = []
        for p in processes_map.values():
            p["steps"] = [
                {
                    **step,
                    "step_contents": [
                        {
                            **content,
                            "languages": list(content["languages"].values())
                        }
                        for content in step["step_contents"].values()
                    ]
                }
                for step in p["steps"].values()
            ]
            final_processes.append(p)

        return {"status": "success", "processes": final_processes}

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}
