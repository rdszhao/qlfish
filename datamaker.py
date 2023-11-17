# %%
import numpy as np 
import pandas as pd
import csv
from faker import Faker

n = 20000
fake = Faker('en_US')

student_names = [fake.name() for _ in range(n)]
student_ages = np.random.randint(18, 25, n)
student_gpas = np.random.uniform(2.8, 4.0, n).round(2)
student_majors = np.random.choice(['Computer Science', 'Computer Engineering', 'Data Science'], n)

df_students = pd.DataFrame(
    [student_names, student_ages, student_majors, student_gpas ]
).T.reset_index()
df_students.to_csv('data/students1.csv', index=False, header=['student_id', 'name', 'age', 'major', 'gpa'], quoting=csv.QUOTE_NONNUMERIC)


df_courses = pd.read_csv('data/courses1.csv')
profs = [f"Prof. {fake.name().split(' ')[1]}" for _ in range(44)]
df_courses['instructor'] = [np.random.choice(profs) for _ in range(len(df_courses))]
df_courses.to_csv('data/courses1.csv', index=False, header=True, quoting=csv.QUOTE_NONNUMERIC)

def sample_courses(dF_courses):
	courses = np.random.choice(dF_courses['course_id'], 8, replace=False).tolist()
	return courses[:4], courses[4:]

semesters = ['Fall 2023', 'Spring 2024']

enrollments = []
for student in df_students['index']:
	for semester, courses in zip(semesters, sample_courses(df_courses)):
		for course in courses:
			enrollments.append([student, course, semester])

enrollments_df = pd.DataFrame(
    enrollments,
    columns=['student_id', 'course_id', 'semester']
).reset_index().rename(columns={'index': 'enrollment_id'})

enrollments_df.to_csv('data/enrollments1.csv', index=False, header=True, quoting=csv.QUOTE_NONNUMERIC)
# %%
