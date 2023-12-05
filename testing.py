# %%
from parserfile import get_parser
from db import Database
parser = get_parser()

db = Database(2e5)
db.ingest('data/students.csv', 'students')
db.ingest('data/courses.csv', 'courses')
db.ingest('data/enrollments.csv', 'enrollments')
# %%
def qquery(**kwargs):
    return kwargs

def generate_query(parsed):
	try:
		if 'subq' in parsed:
			subq = parsed['subq']
			if type(subq) == str:
				parsed['tables'] = [subq]
				del parsed['subq']
			else:
				parsed['subq'] = generate_query(parsed['subq'])
		return db.query(**parsed)
	except:
		return db.query(**parsed)

def generate_qquery(parsed):
	try:
		if 'subq' in parsed:
			subq = parsed['subq']
			if type(subq) == str:
				parsed['tables'] = [subq]
				del parsed['subq']
			else:
				parsed['subq'] = generate_qquery(parsed['subq'])
		return qquery(**parsed)
	except:
		return qquery(**parsed)
# %%
qstring2 = 'find avg(gpa) [asc] by major from students'
parsed2 = parser.parse(qstring2)
generate_query(parsed2)
# %%
qstring3 = 'find count(course_id) by instructor from courses'
parsed3 = parser.parse(qstring3)
generate_query(parsed3)
# %%
qstring4 = 'select semester, course_name [asc] where major == "Computer Engineering" from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id '
parsed4 = parser.parse(qstring4)
generate_query(parsed4)
# %%
qstring4 = 'find avg(gpa) by course_name from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id'
parsed4 = parser.parse(qstring4)
generate_query(parsed4)
# %%
query5 = 'select course_name where instructor == "Prof. Smith" from courses'
parsed5 = parser.parse(query5)
generate_query(parsed5)
# %%
qstring6 = 'select name where major == "Data Science", course_name == "Introduction to Online Optimization" from join students, courses, enrollments on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id'
parsed6 = parser.parse(qstring6)
generate_query(parsed6)
# %%
