import json
import pandas as pd
from glob import glob
import os

def flatten_roadmap(roadmap_path, output_csv):
    with open(roadmap_path, 'r', encoding='utf-8') as f:
        roadmap = json.load(f)
    
    docs = []
    career_id = roadmap['career_id']
    career_name = roadmap.get('career_name', '')

    for stage in roadmap.get('stages', []):
        stage_id = stage['id']
        stage_name = stage.get('name', '')
        recommended_semesters = stage.get('recommended_semesters', '')

        for area in stage.get('areas', []):
            area_id = area['id']
            area_name = area.get('name', '')

            for item in area.get('items', []):
                item_id = item['id']
                title = item.get('title', '')
                desc = item.get('description', '')
                tags = ', '.join(item.get('tags', []))

                text = (
                    f'Nghề: {career_name} ({career_id})\n'
                    f'Giai đoạn: {stage_name}\n'
                    f'Lĩnh vực: {area_name}\n'
                    f'Mục: {title}\n'
                    f'Mô tả: {desc}\n'
                    f'Tags: {tags}\n'
                    f'Kỳ khuyến nghị: {recommended_semesters}'
                )

                docs.append({
                    'doc_id': item_id,
                    'career_id': career_id,
                    'stage_id': stage_id,
                    'area_id': area_id,
                    'text': text
                })

    df = pd.DataFrame(docs)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f'Saved {len(docs)} records to {output_csv}')

if __name__ == '__main__':
    for roadmap_file in glob('../data/jobs/*.json'):
        career_id = os.path.splitext(os.path.basename(roadmap_file))[0]
        output_csv = f'../data/flatten_roadmaps/{career_id}_flat.csv'
        flatten_roadmap(roadmap_file, output_csv)