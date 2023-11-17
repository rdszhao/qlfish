'''
find avg(gpa) [asc] by major
from students
'''
{
	'method': 'agg',
	'agg_func': 'avg',
	'agg_field': 'gpa',
	'sorting': 'asc',
	'subq': {
		'method': 'group_by',
		'tables': ['students'],
		'group_by': 'major'
	}
}

'''
find count(course_id) by instructor
from courses
'''
{
	'method': 'agg',
	'agg_func': 'count',
	'agg_field': 'course_id',
	'subq': {
		'method': 'group_by',
		'tables': ['courses'],
		'group_by': 'instructor'
	} 
} 

'''
select course_name [asc], semester where students.major == Computer Engineering
from join students, enrollments, courses 
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id 
'''

{
	'method': 'select',
	'fields': ['course_name', 'semester'],
	'where': ['major == "Computer Engineering"'],
	'sorting': {'field': 'course_name', 'order': 'asc'},
	'subq': {
		'method': 'join',
		'tables': ['students', 'courses', 'enrollments'],
		'on': {
			'students.student_id': 'enrollments.student_id',
			'enrollments.course_id': 'courses.course_id'
		}
	}
}

'''
find count(student_id) by course_id
from enrollments
'''
{
	'method': 'agg',
	'agg_func': 'count',
	'agg_field': 'student_id',
	'subq': {
		'method': 'group_by',
		'tables': ['enrollments'],
		'group_by': 'course_id'
	}
}

'''
find avg(gpa) by course_name
from join students, enrollments, courses
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id
'''
{
	'method': 'agg',
	'agg_func': 'avg',
	'agg_field': 'gpa',
	'sorting': 'asc',
	'subq':  {
		'method': 'group_by',
		'group_by': 'course_name',
		'subq': {
			'method': 'join',
			'tables': ['students', 'enrollments', 'courses'],
			'on': {
				'students.student_id': 'enrollments.student_id',
				'enrollments.course_id': 'courses.course_id'
			}
		}
	}
}

'''
select course_name where instructor == 'Prof. Smith'
from courses
'''
{
	'method': 'select',
	'tables': ['courses'],
	'fields': ['course_name'],
	'where': ['instructor == "Prof. Smith"']
}

'''
select name
where major == 'Data Science', course_name == 'Data Structures'
from join students, courses, enrollments
on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id
'''
{
	'method': 'select',
	'fields': ['name'],
	'where': [
		'major == "Data Science"',
		'course_name == "Introduction to Online Optimization"'
	],
	'subq': {
		'method': 'join',
		'tables': ['students', 'courses', 'enrollments'],
		'on': {
			'students.student_id': 'enrollments.student_id',
			'enrollments.course_id': 'courses.course_id'
		},
	}
}