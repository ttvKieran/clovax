import os
import ast
import json
import pandas as pd
import requests
import time
import random
from glob import glob
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv('../../.env.local')
NCP_API_KEY = os.getenv("NCP_API_KEY")

EMBEDDING_API_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"

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

if __name__ == '__main__':
    csv_files = glob('../data/flatten_roadmaps/*.csv')

    dfs = []
    for csv_file in csv_files:
        jobname = os.path.splitext(os.path.basename(csv_file))[0].replace('_flat', '')
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        dfs.append((jobname, df))

    for jobname, df in dfs:
        embeddings = []
        for i, row in tqdm(df.iterrows(), total=len(df), desc=f"Generating embeddings for {jobname}", unit="rows"):
            emb = get_embedding(row['text'])
            embeddings.append({
                'doc_id': row['doc_id'],
                'career_id': row['career_id'],
                'stage_id': row['stage_id'],
                'area_id': row['area_id'],
                'text': row['text'],
                'embedding': emb
            })
        
        df = pd.DataFrame(embeddings)
        df.to_csv(f'../data/roadmap_embeddings/{jobname}_embeddings.csv', index=False, encoding='utf-8-sig')