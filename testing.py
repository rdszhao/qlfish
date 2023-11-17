# %%
from parserfile import get_parser
from db import Database
parser = get_parser()
# %%
db = Database(2e5)
db.ingest('data/students.csv', 'students')
db.ingest('data/courses.csv', 'courses')
db.ingest('data/enrollments.csv', 'enrollments')
# %%
qstring = 'select semester, course_name [asc] where major == "Computer Engineering" from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id '
parsed = parser.parse(qstring)
# %%
query1 = db.query(
	'join',
	tables=['students', 'courses', 'enrollments'],
	on={
		'students.student_id': 'enrollments.student_id',
		'enrollments.course_id': 'courses.course_id'
	}
)
query2 = db.query(
	'select',
	fields=['semester', 'course_name'],
	where=['major == "Computer Engineering"'],
	sorting='asc',
	subq=query1
)
query2
# %%
# def qquery(*args, **kwargs):
#     return kwargs

def generate_query(parsed):
	try:
		if 'subq' in parsed:
			subq = parsed['subq']
			if type(subq) == str:
				parsed['tables'] = [subq]
			else:
				parsed['subq'] = generate_query(parsed['subq'])
		return db.query(**parsed)
	except:
		return db.query(**parsed)
# %%
generate_query(parsed)
# %%
'''
find avg(gpa) [asc] by major
from students
'''
query1 = db.query(
	'agg',
	agg_func='avg',
	agg_field='gpa',
	sorting='asc',
	subq=db.query(
		'group_by',
		tables=['students'],
		group_by='major'
	)
)
query1
# %%
db.query(
	'select',
	fields=['*'],
	tables=['courses']
)
# %%
'''
find count(course_id) by instructor
from courses
'''
db.query(
	'agg',
	agg_func='count',
	agg_field='course_id',
	subq=db.query(
		'group_by',
		tables=['courses'],
		group_by='instructor'
	)
)
# %%
'''
select course_name [asc], semester where students.major == "Computer Engineering"
from join students, enrollments, courses 
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id 
'''
query2 = db.query(
	'select',
	fields=['semester', 'course_name'],
	where=['major == "Computer Engineering"'],
	sorting='asc',
	subq=db.query(
		'join',
		tables=['students', 'courses', 'enrollments'],
		on={
			'students.student_id': 'enrollments.student_id',
			'enrollments.course_id': 'courses.course_id'
		}
	)
)
query2
# %%
# 3. number of students enrolled in each course
'''
find count(student_id) by course_id
from enrollments
'''
query3 = db.query(
	'agg',
	agg_func='count',
	agg_field='student_id',
	subq=db.query(
		'group_by',
		tables=['enrollments'],
		group_by='course_id'
	)
)
query3
# %%
# 4. average gpa of students in each course
'''
find avg(gpa) by course_name
from join students, enrollments, courses
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id
'''
query4 = db.query(
	'agg',
	agg_func='avg',
	agg_field='gpa',
	sorting='asc',
	subq= db.query(
		'group_by',
		group_by='course_name',
		subq= db.query(
			'join',
			tables=['students', 'enrollments', 'courses'],
			on={
				'students.student_id': 'enrollments.student_id',
				'enrollments.course_id': 'courses.course_id'
			}
		)
	)
)
query4
# %%
# 5. courses taught by prof. smith
'''
select course_name where instructor == Prof. Smith
from courses
'''
query5 = db.query(
	'select',
	tables=['courses'],
	fields=['course_name'],
	where=['instructor == Prof. Smith']
)
list(query5)
# %%
# 6. students in 'data science' major enrolled in 'data structures'
'''
select name
where major == Data Science, course_name == Data Structures
from join students, courses, enrollments
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id
'''
query6 = db.query(
	'select',
	fields=['name'],
	where=[
		'major == Data Science',
		'course_name == Introduction to Online Optimization'
	],
	subq=db.query(
		'join',
		tables=['students', 'courses', 'enrollments'],
		on={
			'students.student_id': 'enrollments.student_id',
			'enrollments.course_id': 'courses.course_id'
		},
	)
)
list(query6)
# %%
