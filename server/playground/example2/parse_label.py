import json

with open("label.json", "r") as f:
    data = json.load(f)


faults_list = []
for fault in data:
    faults_list.append({'start_time': fault['start_time'], 'end_time': fault['end_time']})

with open("fault.json", "w") as f:
    json.dump(faults_list, f, indent=4)