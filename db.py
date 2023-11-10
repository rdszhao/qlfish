# %%
import os
import re
import sys
import json
import argparse
import numpy as np
from collections import defaultdict
# %%
class Database:
    def __init__(self, db_name:str)->None:
        '''
        initialize a database with a given name.

        db_name (str): name of the database file.

        initializes an empty database if the file doesn't exist, otherwise loads existing data.
        '''
        self.db_name = db_name
        self.data = {}
        if os.path.exists(db_name):
            with open(db_name, 'r') as f:
                self.data = json.load(f)
        else:
            with open(db_name, 'w') as f:
                json.dump(self.data, f)

    def save(self)->None:
        '''
        save the current database state to the file.
        '''
        with open(self.db_name, 'w') as f:
            json.dump(self.data, f)

    def create_collection(self, name:str)->str:
        '''
        create a new collection in the database.

        name (str): the name of the collection to create.

        returns:
            str: A message indicating the success or failure of the operation.
        '''
        if name not in self.data:
            self.data[name] = []
            self.save()
            return f"collection {name} created"
        return f"collection {name} already exists"

    def insert(self, collection_name:str, document:dict)->str:
        '''
        insert a document into a collection.

        collection_name (str): the name of the collection to insert into.
        document (dict): the document to insert.

        returns:
            str: a message indicating the success or failure of the operation.
        '''
        if collection_name not in self.data:
            return f"collection {collection_name} does not exist."
        self.data[collection_name].append(document)
        self.save()
        return f"document inserted into {collection_name}."

    def update(self, collection_name:str, condition:callable, update_values:dict)->str:
        '''
        update documents in a collection based on a condition and update values.

        collection_name (str): the name of the collection to update.
        condition (callable): a function to filter documents for updating.
        update_values (dict): a dictionary of field-value pairs to update.

        returns:
            str: a message indicating the number of documents updated.
        '''
        if collection_name not in self.data:
            return f"collection {collection_name} does not exist."
        updated_count = 0
        for doc in self.data[collection_name]:
            if condition(doc):
                for key, value in update_values.items():
                    doc[key] = value
                updated_count += 1
        self.save()
        return f"{updated_count} document(s) updated."

    def delete(self, collection_name:str, condition:callable)->str:
        '''
        delete documents in a collection based on a condition.

        args:
            collection_name (str): the name of the collection to delete from.
            condition (callable): a function to filter documents for deletion.

        returns:
            str: a message indicating the number of documents deleted.
        '''
        if collection_name not in self.data:
            return f"collection {collection_name} does not exist."
        original_count = len(self.data[collection_name])
        self.data[collection_name] = [doc for doc in self.data[collection_name] if not condition(doc)]
        deleted_count = original_count - len(self.data[collection_name])
        self.save()
        return f"{deleted_count} document(s) deleted."

    def query(self, method:str, **kwargs:dict)->list:
            return Query(self, method, **kwargs).run()

class Query:
    def __init__(self, db:Database, method:str, **kwargs:dict)->None:
        self.kwargs = kwargs
        self.method = method

        if 'subq' in self.kwargs:
            self.data = self.kwargs['subq']
        else:
            self.data = db.data

    def run(self)->list:
        if self.method == 'select':
            table = self.kwargs.get('table')
            fields = self.kwargs['fields']
            where = self.kwargs.get('where')
            return self.select(table, fields, where)

        elif self.method == 'join':
            tables = self.kwargs['tables']
            on = self.kwargs['on']
            where = self.kwargs.get('where')
            return self.join(tables, on, where)

        elif self.method == 'agg':
            agg_func = self.kwargs['agg_func']
            agg_field = self.kwargs['agg_field']
            table = self.kwargs.get('table')
            where = self.kwargs.get('where')
            return self.agg(agg_func, agg_field, table, where)

        elif self.method == 'group_by':
            table = self.kwargs.get('table')
            group_by = self.kwargs['group_by']
            where = self.kwargs.get('where')
            return self.group_by(table, group_by, where)

    def select(self, table:str, fields:list, where:list=None)->list:
            data = self.data[table] if table else self.data
            if where:
                data = self.where(data, where)
            return [{field: doc[field] for field in fields} for doc in data]

    def join(self, tables:list, on:dict, where:list=None)->list:
        join_data = {table: self.data[table] for table in tables}
        base_table = list(on.keys())[0].split('.')[0]
        join_result = [{f"{base_table}.{key}": value for key, value in doc.items()} for doc in join_data[base_table]]
        for join_condition, join_field in on.items():
            table1, field1 = join_condition.split('.')
            table2, field2 = join_field.split('.')
            new_join_result = []
            index = defaultdict(list)
            for doc in join_data[table2]:
                index_key = f"{table2}.{field2}"
                index_value = {f"{table2}.{key}": value for key, value in doc.items()}
                index[doc[field2]].append(index_value)
            for doc in join_result:
                matching_docs = index.get(doc[f"{table1}.{field1}"], [])
                for match in matching_docs:
                    combined_doc = {**doc, **match}
                    new_join_result.append(combined_doc)
            join_result = new_join_result
        if where:
            join_result = self.where(join_result, where)
        # remove the prefix from field names ("students." from "students.student_id")
        for doc in join_result:
            for key in list(doc.keys()):
                doc[key.split('.')[1]] = doc.pop(key)
        return join_result

    def agg(self, agg_func:str, agg_field:str, table:str=None, where:list=None)->list:
        data = self.data
        if table:
            data = data[table]
        if where:
            data = self.where(data, where)

        funcs = {
            'avg': np.mean, 'sum': np.sum, 'count': 
            len, 'min': np.min, 'max': np.max
        }
        afunc = funcs.get(agg_func)

        if not afunc:
            raise ValueError(f"unsupported aggregate function: {agg_func}")
        elif type(data) is not defaultdict:
            values = [doc[agg_field] for doc in data]
            return afunc(values) if values else None
        else:
            outputs = {key: afunc([v[agg_field] for v in val]) for key, val in data.items()}
            return outputs

    def group_by(self, table:str, group_by:str, where:list=None)->list:
        data = self.data[table] if table else self.data
        if where:
            data = self.where(data, where)
        grouped_data = defaultdict(list)
        for doc in data:
            key = doc[group_by]
            grouped_data[key].append(doc)
        return grouped_data

    def where(self, data:list, conditions:list):
        filtered_data = []
        for doc in data:
            if self._evaluate_conditions(doc, conditions):
                filtered_data.append(doc)
        return filtered_data

    def _evaluate_conditions(self, doc, conditions):
        operators = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            'like': lambda a, b: b in a
        }
        for condition in conditions:
            field, op, value = self._parse_condition(condition)
            if field in doc:
                if not operators[op](doc[field], value):
                    return False
            else:
                return False
        return True

    def _parse_condition(self, condition):
        pattern = re.compile(r"([\w+\.]*)\s*(<=|>=|!=|<|>|==)\s*(.*)")
        match = pattern.match(condition)

        if not match:
            raise ValueError(f"Unsupported condition format: {condition}")
        
        field, op, value = match.groups()

        value = value.strip("'").strip('"')

        if value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit():
            value = float(value)
        
        return field, op, value


# class CommandInterface:
#     @staticmethod
#     def start(db_name):
#         '''
#         Start the command-line interface for interacting with the database.

#         Args:
#             db_name (str): The name of the database file.
#         '''
#         db = Database(db_name)
#         while True:
#             command = input('qlfish > ').strip()
#             if command.lower() == 'exit':
#                 break
#             else:
#                 tokens = command.split()
#                 action = tokens[0].lower()

#                 if action == 'create':
#                     _, _, collection_name = tokens
#                     print(db.create_collection(collection_name))
#                 elif action == 'insert':
#                     _, _, collection_name, values = tokens
#                     document = json.loads(values)
#                     print(db.insert(collection_name, document))
#                 elif action == 'find':
#                     _, fields, from_clause, *rest = tokens[1:]
#                     fields = fields.split(',')
#                     collection_name = from_clause

#                     condition = None
#                     join = None
#                     sort_by = None
#                     group_by = None
#                     aggregate = None

#                     i = 0
#                     while i < len(rest):
#                         token = rest[i]
#                         if token == 'where':
#                             i += 1
#                             condition_str = rest[i:]
#                             condition = QueryParser.parse_condition(' '.join(condition_str))
#                             i += len(condition_str)
#                         elif token == 'join':
#                             join = (rest[i+1], rest[i+3])  # JOIN collection_name ON field
#                             i += 4
#                         elif token == 'order':
#                             sort_by = (rest[i+3], rest[i+4])  # ORDER BY field ASC/DESC
#                             i += 5
#                         elif token == 'group':
#                             group_by = rest[i+3]  # GROUP BY field
#                             aggregate = (rest[i+5], rest[i+6])  # AGGREGATE field FUNCTION
#                             i += 7
#                         else:
#                             i += 1

#                     results = db.find(
#                         collection_name,
#                         condition=condition,
#                         fields=fields,
#                         sort_by=sort_by,
#                         join=join,
#                         group_by=group_by,
#                         aggregate=aggregate
#                     )
#                     for res in results:
#                         print(res)

#                 elif action == 'delete':
#                     _, _, collection_name, condition = tokens
#                     condition = eval(condition)
#                     print(db.delete(collection_name, condition))

#                 elif action == 'update':
#                     _, _, collection_name, set_clause, where_clause = tokens
#                     set_values = json.loads(set_clause)
#                     condition = eval(where_clause)
#                     print(db.update(collection_name, condition, set_values))

#                 else:
#                     print('Command not recognized.')
# %%
db = Database('testdata.json')
# %% platonic queries
'select major, avg(gpa) from students by major'

subq = db.query(method='group_by', table='students', group_by='major')
q = db.query(method='agg', agg_func='avg', agg_field='gpa',subq=subq)

db.query(
    'agg',
    agg_func='avg',
    agg_field='gpa',
    subq=db.query(
        'group_by',
        table='students',
        group_by='major'
    )
)
# %%
'''
select course_name 
from join students, enrollments, courses 
on students.student_id -> enrollments.student_id, enrollments.course_id -> courses.course_id 
where students.name == Alice
'''

subq = db.query(method='join', tables=['students', 'courses', 'enrollments'], on={'students.student_id': 'enrollments.student_id', 'enrollments.course_id': 'courses.course_id'}, where=['students.name == Alice'])
q = db.query('select', fields=['course_name'], subq=subq)

db.query(
    'select',
    fields=['course_name'],
    subq=db.query(
        method='join',
        tables=['students',
                'courses',
                'enrollments'
            ],
        on={
            'students.student_id':
            'enrollments.student_id',
            'enrollments.course_id':
            'courses.course_id'
        },
        where=['students.name == "Alice"']
    )
)