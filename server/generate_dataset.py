import os
import json
import random

EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), 'playground', 'example')
TEMPLATES = [
    "A fault occurred from {start_time} to {end_time}. Please identify the root cause.",
    "Please analyze the abnormal event between {start_time} and {end_time} and provide the root cause.",
    "The system experienced an anomaly from {start_time} to {end_time}. Please infer the possible cause.",
    "A fault was detected from {start_time} to {end_time}. Please analyze its root cause.",
    "Determine the root cause of the system fault during {start_time} to {end_time}."
]

def process_label_json(label_path, output_dir):
    with open(label_path, 'r') as f:
        labels = json.load(f)
    
    # Generate descriptions and fault.json content
    descriptions = []
    faults = []
    for case in labels:
        template = random.choice(TEMPLATES)
        desc = template.format(start_time=case['start_time'], end_time=case['end_time'])
        descriptions.append({"Anomaly Description": desc})
        faults.append({
            'start_time': case['start_time'],
            'end_time': case['end_time']
        })
    # Save descriptions
    with open(os.path.join(output_dir, 'fault.json'), 'w') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=4)

    # with open(os.path.join(output_dir, 'fault.json'), 'w') as f:
    #     json.dump(faults, f, ensure_ascii=False, indent=4)

def main():
    label_path = os.path.join(EXAMPLE_DIR, 'label.json')
    if os.path.exists(label_path):
        process_label_json(label_path, EXAMPLE_DIR)
    else:
        print(f"label.json not found in {EXAMPLE_DIR}")

if __name__ == '__main__':
    main()