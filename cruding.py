# %%
import json
from parserfile import get_parser
from db import Database
parser = get_parser()

db = Database(2e5)
db.ingest('data/students.csv', 'students')
db.ingest('data/courses.csv', 'courses')
db.ingest('data/enrollments.csv', 'enrollments')
# %%
entry = '{"student_id": 45006, "student_name": "James Wu", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.insert('students', entry_json)
# %%
entry = '{"student_id": 45006, "student_name": "James Woo", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.update('students', on='student_id', document=entry_json)
# %%
entry = '{"student_id": 45006, "student_name": "James Woo", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.delete('students', document=entry_json)
# %%
