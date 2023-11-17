# %%
import ply.lex as lex
import ply.yacc as yacc

tokens = (
    'FIND', 'SELECT', 'FROM', 'JOIN', 'ON', 'WHERE', 'BY', 
    'AVG', 'COUNT', 'ASC', 'DESC',
    'IDENTIFIER', 'STRING', 
    'LBRACKET', 'RBRACKET', 'COMMA', 'COLON', 'EQUALS',
    'LPAREN', 'RPAREN', 'STAR'
)

t_FIND = r'find'
t_SELECT = r'select'
t_FROM = r'from'
t_JOIN = r'join'
t_ON = r'on'
t_WHERE = r'where'
t_BY = r'by'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','
t_COLON = r':'
t_EQUALS = r'=='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_STAR = r'\*'

def t_IDENTIFIER(t):
    r"[a-zA-Z_][a-zA-Z_0-9.]*"
    reserved = {
        'avg': 'AVG', 'count': 'COUNT', 'select': 'SELECT', 'find': 'FIND',
        'by': 'BY', 'from': 'FROM', 'where': 'WHERE', 'join': 'JOIN', 'on': 'ON',
        'asc': 'ASC', 'desc': 'DESC'
    }
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    return t

def t_STRING(t):
    r'\"[^\"]*\"'
    t.value = t.value[1:-1]
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

def p_query(p):
    '''query : select_query
             | find_query'''
    p[0] = p[1]

def p_select_query(p):
    '''select_query : SELECT fields optional_sorting WHERE conditions FROM IDENTIFIER
                    | SELECT fields optional_sorting WHERE conditions FROM join_expression'''
    if len(p) == 7:
        p[0] = {
            'method': 'select',
            'fields': p[2],
            'sorting': p[3],
            'where': p[5],
            'tables': [p[7]]
        }
    else:
        p[0] = {
            'method': 'select',
            'fields': p[2],
            'sorting': p[3],
            'where': p[5],
            'subq': p[7]
        }

def p_find_query(p):
    '''find_query : FIND agg_func optional_sorting BY IDENTIFIER FROM IDENTIFIER
                  | FIND agg_func optional_sorting BY IDENTIFIER FROM join_expression'''
    if len(p) == 7:
        p[0] = {
            'method': 'agg',
            'agg_func': p[2],
            'sorting': p[3],
            'subq': {
                'method': 'group_by',
                'tables': [p[6]],
                'group_by': p[5]
            }
        }
    else:
        p[0] = {
            'method': 'agg',
            'agg_func': p[2],
            'sorting': p[3],
            'subq': {
                'method': 'group_by',
                'group_by': p[5],
                'subq': p[7]
            }
        }

def p_agg_func(p):
    '''agg_func : AVG
                | COUNT'''
    p[0] = p[1].lower()

def p_agg_func_with_args(p):
    '''agg_func : AVG LPAREN IDENTIFIER RPAREN
                | COUNT LPAREN IDENTIFIER RPAREN'''
    p[0] = {'function': p[1].lower(), 'field': p[3]}

def p_fields(p):
    '''fields : field
              | field COMMA fields'''
    if len(p) == 2:  # Single field
        p[0] = [p[1]]
    else:  # Multiple fields separated by comma
        p[0] = [p[1]] + p[3]

def p_field(p):
    '''field : IDENTIFIER
             | STAR'''
    p[0] = p[1]

def p_optional_sorting(p):
    '''optional_sorting : LBRACKET sort_order RBRACKET
                        | '''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = None

# def p_optional_sorting(p):
#     '''optional_sorting : LBRACKET sort_spec RBRACKET
#                         | '''
#     if len(p) == 4:
#         p[0] = p[2]
#     else:
#         p[0] = None

def p_sort_order(p):
    '''sort_order : ASC
                  | DESC'''
    p[0] = p[1].lower()

# def p_sort_order(p):
#     '''sort_order : IDENTIFIER ASC
#                   | IDENTIFIER DESC
#                   | ASC
#                   | DESC'''
#     if len(p) == 3:
#         p[0] = {'field': p[1], 'order': p[2].lower()}
#     elif len(p) == 2:
#         p[0] = {'order': p[1].lower()}

# def p_sort_spec(p):
#     '''sort_spec : sort_order IDENTIFIER
#                  | IDENTIFIER sort_order
#                  | IDENTIFIER
#                  | sort_order'''
#     if len(p) == 2:
#         if p[1] in ['asc', 'desc']:
#             p[0] = {'field': None, 'order': p[1].lower()}
#         else:
#             p[0] = {'field': p[1], 'order': None}
#     elif len(p) == 3:
#         p[0] = {'field': p[2], 'order': p[1].lower()}
#     else:
#         p[0] = {'field': None, 'order': None}

def p_conditions(p):
    '''conditions : condition
                  | condition COMMA conditions'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_condition(p):
    '''condition : IDENTIFIER EQUALS STRING
                 | IDENTIFIER EQUALS IDENTIFIER'''
    if p[2] == '==':
        if isinstance(p[3], str):
            p[0] = f'{p[1]} == "{p[3]}"'
        else:
            p[0] = f'{p[1]} == {p[3]}'

def p_tables(p):
    '''tables : IDENTIFIER
              | IDENTIFIER COMMA tables'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_join_expression(p):
    '''join_expression : JOIN tables ON join_conditions'''
    p[0] = {
        'method': 'join',
        'tables': p[2],
        'on': p[4]
    }

def p_join_condition(p):
    'join_condition : IDENTIFIER COLON IDENTIFIER'
    p[0] = {p[1]: p[3]}

def p_join_conditions(p):
    '''join_conditions : join_condition
                       | join_condition COMMA join_conditions'''
    p[0] = p[1] if len(p) == 2 else {**p[1], **p[3]}

def p_error(p):
    print("Syntax error at '%s'" % p.value)

parser = yacc.yacc()

def get_parser():
    return parser

test_queries = [
	'find avg(gpa) by major from students',
	'select course_name where students.name == "Sean Collins" from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id',
	'find count(student_id) by course_id from enrollments',
	'find avg(gpa) by course_name from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id',
	'select course_name [desc] where instructor == "Prof. Smith" from courses',
	'select name where major == "Data Science", course_name == "Data Structures" from join students, courses, enrollments on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id'
]

qstring = 'select *, course_name [asc] where students.major == "Computer Engineering" from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id '
parser.parse(qstring)