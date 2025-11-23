
import os
import json
import uuid
import re
import copy


import requests
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from .search_api import BASE_DIR, NCP_API_KEY

# Kết nối MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://tatruongvuptit:3rAzJ2rPTw9yXkBN@cluster.znzh1.mongodb.net/career-advisor")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["clova_db"]
users_collection = db["users"]

app = FastAPI()

ROADMAP_DIR = BASE_DIR / "data" / "jobs"
JOB_NAME = "machine learning"

CHAT_COMPLETIONS_API_URL = (
    "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-007"
)


class PersonalizeRequest(BaseModel):
    user_id: str
    jobname: str | None = None


def load_canonical_roadmap(jobname: str = JOB_NAME) -> dict:
    """
    Load roadmap gốc theo jobname.
    """
    file_name = jobname.lower().replace(" ", "_") + ".json"
    path = ROADMAP_DIR / file_name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_profile_text(user: dict) -> str:
    """
    Chuẩn hóa profile user thành text cho prompt.
    Dựa trên normalize_user trong search_api.
    """
    it_skills = ", ".join(user.get("it_skills", []))
    soft_skills = ", ".join(user.get("soft_skills", []))

    tech_skills_str = ", ".join(
        f"{k}:{v}" for k, v in user.get("skills_technical", {}).items()
    )
    gen_skills_str = ", ".join(
        f"{k}:{v}" for k, v in user.get("skills_general", {}).items()
    )

    courses = user.get("course_scores", [])
    course_lines = []
    for c in courses:
        code = c.get("code")
        name = c.get("name")
        grade = c.get("grade")
        course_lines.append(f"- {code} | {name}: {grade}/10")
    scores_str = "\n".join(course_lines)

    interests = ", ".join(user.get("interests", []))
    projects = "\n".join(f"- {p}" for p in user.get("projects", []))

    text = (
        "PROFILE:\n"
        f"- user_id: {user.get('user_id')}\n"
        f"- Họ tên: {user.get('full_name')}\n"
        f"- current_semester: {user.get('current_semester')}\n"
        f"- GPA (thang 4): {user.get('gpa')}\n"
        f"- target_career_id: {user.get('target_career_id')}\n"
        f"- actual_career: {user.get('actual_career')}\n"
        f"- time_per_week_hours: {user.get('time_per_week_hours')}\n"
        f"- IT skills (label): {it_skills}\n"
        f"- Soft skills (label): {soft_skills}\n"
        f"- Technical skills (1-10): {tech_skills_str}\n"
        f"- General skills (1-10): {gen_skills_str}\n"
        f"- Interests: {interests}\n"
        f"- Projects:\n{projects}\n"
        f"- Điểm các môn (thang 10):\n{scores_str}\n"
    )
    return text


SYSTEM_PROMPT = """
You are a system that personalizes a learning roadmap for university students.

You will be given:
1. A student profile (current skills, soft skills, course grades, study time, interests, projects).
2. A canonical JSON roadmap that describes the target career path.

Your task:
- For EACH item in the roadmap, use the student profile to:
  - Decide whether the student has already mastered it or not.
  - Decide the priority level if the student should study it:
    high_priority / medium_priority / low_priority / optional / already_mastered.

For EVERY item, you MUST:

1. Set "check" to either true or false.
2. Set "personalization" with ALL of the following fields:
   - "status": one of "already_mastered", "high_priority", "medium_priority", "low_priority", "optional".
   - "priority": an integer (0 = highest priority, larger numbers = lower priority).
   - "personalized_description": 1–2 sentences that explain what this item means for THIS specific student, based on their profile (skills, grades, interests, time).
   - "reason": 1 short sentence that justifies the status/priority using concrete evidence from the profile.
If any item is missing "personalized_description" or "reason", your answer is considered incorrect.


HARD CONSTRAINTS (MUST FOLLOW):
- DO NOT change the overall JSON structure:
  - Do NOT add or remove stages, areas, or items.
  - Do NOT rename existing keys (career_id, career_name, stages, areas, items, id, name, description, skill_tags, prerequisites, required_skills, estimated_hours, order_index, etc.).
- You are ONLY allowed to add or modify the two fields at item level:
  - "check"
  - "personalization"
- The JSON you return MUST be strictly valid:
  - No comments.
  - No trailing commas.
  - No extra text before or after the JSON object.

STRICTLY FORBIDDEN:
- You MUST NOT use the token '...' anywhere in the JSON.
  - You MUST return the FULL data, you are not allowed to omit elements by writing '...'.
  - Do not shorten arrays or objects with '...'.
- You MUST NOT wrap the JSON inside markdown fences such as ```json ... ``` or ``` ... ```.

OUTPUT REQUIREMENT:
- Return EXACTLY ONE JSON object:
  - It must be the full roadmap JSON after you have added/updated "check" and "personalization" for every item.
"""


def _chat_headers() -> dict:
    """
    Header chuẩn cho Chat Completions v3 (HCX-007).
    """
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json", 
        "Authorization": f"Bearer {NCP_API_KEY}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
    }


def call_clova_chat(system_prompt: str, user_prompt: str) -> str:
    """
    Gọi CLOVA Studio Chat Completions v3 (HCX-007)
    """

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_prompt,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt,
                }
            ],
        },
    ]

    payload = {
        "messages": messages,
        "thinking": {
            "effort": "low"
        },
        "topP": 0.8,
        "topK": 0,
        "maxCompletionTokens": 20480,
        "temperature": 0.3,
        "repetitionPenalty": 1.1,
        "seed": 42,
        "includeAiFilters": True,
    }

    resp = requests.post(
        CHAT_COMPLETIONS_API_URL,
        headers=_chat_headers(),
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    content = data["result"]["message"]["content"]

    if isinstance(content, list):
        texts = []
        for seg in content:
            if isinstance(seg, dict) and seg.get("type") == "text":
                texts.append(seg.get("text", ""))
        content = "\n".join(texts)
    elif not isinstance(content, str):
        raise ValueError(f"Unexpected content type from CLOVA: {type(content)}")

    return content.strip()


def _normalize_json_candidate(s: str) -> str:
    """
    Làm sạch chuỗi JSON trước khi parse:
    - Xoá các dòng chỉ chứa '...' hoặc biến thể ', ...'
    - Fix trailing comma: ,] hoặc ,}
    """
    lines = s.splitlines()
    cleaned_lines = []
    for ln in lines:
        stripped = ln.strip()
        if stripped in ("...", ",...", "...,", ", ..."):
            continue
        cleaned_lines.append(ln)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r",(\s*[\]}])", r"\1", cleaned)
    return cleaned


def extract_json_from_text(text: str):
    text = text.strip()

    try:
        normalized = _normalize_json_candidate(text)
        return json.loads(normalized)
    except Exception:
        pass

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part_strip = part.strip()
            if not part_strip:
                continue

            if part_strip.lower().startswith("json"):
                part_strip = part_strip[4:].strip()

            try:
                normalized = _normalize_json_candidate(part_strip)
                return json.loads(normalized)
            except Exception:
                continue

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = text[first : last + 1]
        try:
            normalized = _normalize_json_candidate(candidate)
            return json.loads(normalized)
        except Exception:
            pass

    return text


def extract_item_personalization_from_roadmap(personalized: dict) -> dict:
    """
    Duyệt qua roadmap mà model trả về, gom lại thông tin check + personalization
    cho từng item theo id.

    Trả về:
    {
      "<item_id>": {
         "check": bool | None,
         "personalization": { ... } | None
      },
      ...
    }
    """
    item_map = {}

    stages = personalized.get("stages", [])
    if not isinstance(stages, list):
        return item_map

    for stage in stages:
        for area in stage.get("areas", []) or []:
            for item in area.get("items", []) or []:
                item_id = item.get("id")
                if not item_id:
                    continue

                item_map[item_id] = {
                    "check": item.get("check"),
                    "personalization": item.get("personalization"),
                }

    return item_map


def apply_personalization_to_canonical_roadmap(
    canonical: dict,
    personalized: dict
) -> dict:
    """
    - canonical: roadmap gốc (đầy đủ 4 stage).
    - personalized: roadmap (có thể chỉ có 1 stage) model trả về.
    -> Trả về: canonical nhưng đã gắn check + personalization vào từng item
       nếu model có đánh giá.
    """
    item_map = extract_item_personalization_from_roadmap(personalized)
    result = copy.deepcopy(canonical)

    for stage in result.get("stages", []):
        for area in stage.get("areas", []) or []:
            for item in area.get("items", []) or []:
                item_id = item.get("id")
                if not item_id:
                    continue

                p = item_map.get(item_id)
                if p:
                    if p.get("check") is not None:
                        item["check"] = bool(p["check"])
                    else:
                        item["check"] = item.get("check", False)

                    per = p.get("personalization") or {}
                    item["personalization"] = {
                        "status": per.get("status", "not_assigned"),
                        "priority": per.get("priority", 999),
                        "personalized_description": per.get(
                            "personalized_description", ""
                        ),
                        "reason": per.get("reason", ""),
                    }
                else:
                    item.setdefault("check", False)
                    item.setdefault(
                        "personalization",
                        {
                            "status": "not_assigned",
                            "priority": 999,
                            "personalized_description": "",
                            "reason": "",
                        },
                    )

    return result


@app.post("/roadmap/personalized")
async def get_personalized_roadmap(req: PersonalizeRequest):
    # Lấy user từ MongoDB
    user = users_collection.find_one({"user_id": req.user_id})
    if not user:
        return {"error": "Unknown user_id"}

    # Lấy student từ MongoDB (giả sử user có trường studentID)
    student_id = user.get("studentID")
    student = None
    if student_id:
        student = db["students"].find_one({"studentID": student_id})

    # Gộp thông tin user và student
    profile = dict(user)
    if student:
        profile.update(student)

    jobname = (req.jobname or 'JOB_NAME').strip()

    try:
        canonical_roadmap = load_canonical_roadmap(jobname)
    except FileNotFoundError:
        return {"error": f"Roadmap file for job '{jobname}' not found"}

    profile_text = build_profile_text(profile)
    roadmap_json_str = json.dumps(canonical_roadmap, ensure_ascii=False, indent=2)

    user_prompt = (
        profile_text
        + "\n\nCANONICAL ROADMAP JSON:\n"
        + roadmap_json_str
        + "\n\nTASK:\n"
        + "Return exactly ONE JSON object with the SAME structure, only adding or updating "
          "the fields 'check' and 'personalization' at item level. "
          "Do not remove any stages, areas, or items."
    )

    raw_answer = call_clova_chat(SYSTEM_PROMPT, user_prompt)
    model_roadmap = extract_json_from_text(raw_answer)

    if isinstance(model_roadmap, dict) and "stages" in model_roadmap:
        merged = apply_personalization_to_canonical_roadmap(
            canonical_roadmap,
            model_roadmap
        )
    else:
        merged = canonical_roadmap

    return merged