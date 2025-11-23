import os
import json
import ast
import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
import requests
import random
import time
from typing import List, Optional

EMBEDDING_API_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
RERANKER_API_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/reranker"

BASE_DIR = Path(__file__).resolve().parent.parent  

load_dotenv(BASE_DIR.parent / '.env.local')

NCP_API_KEY = os.getenv("NCP_API_KEY")

app = FastAPI()

def get_embedding(text):
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {str(NCP_API_KEY)}',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': '5bf30d7bddc94b9694304d0d88f0cef6'
    }

    data = {'text': text}

    r = requests.post(EMBEDDING_API_URL, headers=headers, json=data)
    r.raise_for_status()
    time.sleep(random.uniform(0.3, 0.7)) 
    return r.json()['result']['embedding']

def cosine_similarity(vec1, vec2):
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def normalize_user(raw_user: dict) -> dict:
    academic = raw_user.get("academic", {})
    career = raw_user.get("career", {})
    availability = raw_user.get("availability", {})
    skills = raw_user.get("skills", {})
    skills_tech = skills.get("technical", {})
    skills_gen = skills.get("general", {})

    return {
        "user_id": raw_user.get("user_id"),
        "full_name": raw_user.get("full_name"),

        "current_semester": academic.get("current_semester"),
        "gpa": academic.get("gpa"),
        "course_scores": academic.get("courses", []),

        "target_career_id": career.get("target_career_id"),
        "actual_career": career.get("actual_career"),
        "target_confidence": career.get("target_confidence"),

        "time_per_week_hours": availability.get("time_per_week_hours"),

        "it_skills": raw_user.get("it_skill", []),
        "soft_skills": raw_user.get("soft_skill", []),

        "skills_technical": skills_tech,
        "skills_general": skills_gen,

        "interests": raw_user.get("interests", []),
        "projects": raw_user.get("projects", []),

        "meta": raw_user.get("meta", {})
    }


def load_docs(jobname: str):
    id_name = jobname.lower().replace(' ', '_')
    emb_path = BASE_DIR / f'data/roadmap_embeddings/{id_name}_embeddings.csv'
    df = pd.read_csv(emb_path)
    df['embedding'] = df['embedding'].apply(ast.literal_eval)
    return df

def load_users():
    users_path = BASE_DIR / 'data/users/users.json'
    with open(users_path, 'r', encoding='utf-8') as f:
        raw_users = json.load(f)
    
    users = {}
    for ru in raw_users:
        nu = normalize_user(ru)
        users[nu['user_id']] = nu
    
    return users

USERS = load_users()

class SearchInput(BaseModel):
    user_id: str
    jobname: Optional[str] = None
    query: Optional[str] = None
    top_k: int = 20

class SearchResult(BaseModel):
    id: str
    content: str
    career_id: str

class SearchOutput(BaseModel):
    results: List[SearchResult]

class RerankInput(BaseModel):
    user_id: str
    jobname: Optional[str] = None
    query: str
    top_k: int = 10   


class RerankOutput(BaseModel):
    answer: str             
    documents: List[dict]    
    reranker_raw: dict      


def build_personalized_query(user: dict, question: Optional[str]) -> str:
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

    base = (
        f"Hồ sơ sinh viên:\n"
        f"- user_id: {user.get('user_id')}\n"
        f"- Họ tên: {user.get('full_name')}\n"
        f"- Kỳ hiện tại: {user.get('current_semester')}\n"
        f"- GPA (thang 4): {user.get('gpa')}\n"
        f"- Target career: {user.get('target_career_id')}\n"
        f"- Actual career (nếu có): {user.get('actual_career')}\n"
        f"- Thời gian có thể học mỗi tuần (giờ): {user.get('time_per_week_hours')}\n"
        f"- IT skills (label): {it_skills}\n"
        f"- Soft skills (label): {soft_skills}\n"
        f"- Technical skills (1-10): {tech_skills_str}\n"
        f"- General skills (1-10): {gen_skills_str}\n"
        f"- Interests: {interests}\n"
        f"- Projects:\n{projects}\n"
        f"- Điểm các môn (thang 10):\n{scores_str}\n"
    )

    if question:
        return base + f"Câu hỏi: {question}"
    else:
        return base + (
            "Mục tiêu: tìm các mục trong roadmap phù hợp nhất với hồ sơ này, "
            "ưu tiên các mục nền tảng sinh viên còn yếu hoặc chưa học, "
            "và không vượt quá thời gian học {time_per_week_hours}h/tuần nếu có thể."
        )

def retrieve_docs(user: dict, question: Optional[str], top_k: int, jobname: str):
    query = build_personalized_query(user, question)
    q_emb = np.array(get_embedding(query))

    df = load_docs(jobname)
    
    df['similarity'] = df['embedding'].apply(lambda emb: cosine_similarity(q_emb, np.array(emb)))
    top_df = df.sort_values('similarity', ascending=False).head(top_k)

    results = []

    for _, row in top_df.iterrows():
        results.append(SearchResult(
            id=row['doc_id'],
            content=row['text'],
            career_id=row['career_id']
        ))
    
    return results

def call_reranker(documents, query: str):
    if not NCP_API_KEY:
        raise RuntimeError("NCP_API_KEY is not set in environment variables.")
    
    headers = {
        'Authorization': f'Bearer {str(NCP_API_KEY)}',
        'Content-Type': 'application/json; charset=utf-8',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': '16b838f6e947430298b7e2563948b402'
    }

    payload = {
        'documents': documents,
        'query': query,
        'maxTokens': 1024,
    }

    r = requests.post(RERANKER_API_URL, headers=headers, json=payload, timeout=60)

    r.raise_for_status()
    time.sleep(random.uniform(0.3, 0.7))
    return r.json()

@app.post('/search/', response_model=SearchOutput)
async def search(input: SearchInput) -> SearchOutput:
    user = USERS.get(input.user_id)
    if not user:
        return SearchOutput(results=[])
    
    jobname = (input.jobname or '').strip()

    if not jobname:
        return SearchOutput(results=[])

    docs = retrieve_docs(user, input.query, input.top_k, jobname)
    return SearchOutput(
        results = docs
    )

@app.post("/search_rerank/", response_model=RerankOutput)
async def search_rerank(input: RerankInput) -> RerankOutput:
    user = USERS.get(input.user_id)
    if not user:
        return RerankOutput(
            answer="Unknown user_id",
            documents=[],
            reranker_raw={},
        )
    
    jobname = (input.jobname or '').strip()

    if not jobname:
        return RerankOutput(
            answer="Missing jobname",
            documents=[],
            reranker_raw={},
        )

    docs = retrieve_docs(user, input.query, input.top_k, jobname)

    documents_for_rerank = [
        {
            "id": d.id,
            "doc": d.content,
        }
        for d in docs
    ]

    rerank_resp = call_reranker(documents_for_rerank, input.query)

    result_block = rerank_resp.get("result", {})
    answer_text = result_block.get("result", "")

    return RerankOutput(
        answer=answer_text,
        documents=documents_for_rerank,
        reranker_raw=rerank_resp,
    )
