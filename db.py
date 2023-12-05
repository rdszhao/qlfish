# %%
import os
import re
import sys
import csv
import json
import argparse
import itertools
import numpy as np
from collections import defaultdict

from parserfile import get_parser

class Database:
    def __init__(self, core_lim)->None:
        self.tables = {}
        self.core_lim = core_lim
        self.chunk_size = 0

    def ingest(self, filename:str, table:str)->None:
        self.tables[table] = filename
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                total_bytes, rows = 0, 0
                for row in reader:
                    total_bytes += sys.getsizeof(row)
                    rows += 1
                avg_bytes = total_bytes / rows
                chunk_size = int(self.core_lim / avg_bytes)
                if chunk_size > self.chunk_size:
                    self.chunk_size = chunk_size
                print(self.chunk_size)
            return f"ingested {filename} into {table}"
        except Exception as e:
            return f"failed to ingest {filename} into {table} \n {e}"

    def open_stream(self, table:str):
        filename = self.tables[table]

        def factory():
            with open(filename, 'r') as file:
                header_line = file.readline()
                headers = header_line.strip().split(',')

                while True:
                    line = file.readline()
                    if not line:
                        break

                    reader = csv.DictReader([line], fieldnames=headers, quoting=csv.QUOTE_NONNUMERIC)
                    for item in reader:
                        yield item
        return factory

    def create_table(self, table:str)->str:
        if table not in self.tables:
            filename = f"data/{table}.csv"
            with open(filename, 'w') as file:
                file.write('')
            self.tables[table] = filename
            return f"table {table} created"
        else:
            return f"table {table} already exists"

    def insert(self, table:str, document:dict)->str:
        if table not in self.tables:
            return f"table {table} does not exist"
        else:
            filename = self.tables[table]
            with open(filename, 'a') as file:
                writer = csv.DictWriter(file, fieldnames=document.keys(), quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow(document)
            return f"{document} inserted into {table}"

    def update(self, table:str, on, document:dict)->str:
        if table not in self.tables:
            return f"table {table} does not exist"
        else:
            filename = self.tables[table]
            temp_filename = filename + '.tmp'
            updated = False

            with open(filename, 'r') as file, open(temp_filename, 'w', newline='') as temp_file:
                reader = csv.DictReader(file)
                writer = csv.DictWriter(temp_file, fieldnames=reader.fieldnames, quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()

                for row in reader:
                    if row[on] == str(document[on]):
                        for key, value in document.items():
                            row[key] = value
                        updated = True
                    writer.writerow(row)
            if updated:
                os.replace(temp_filename, filename)
                return f"{document} updated in '{table}'"
            else:
                os.remove(temp_filename)
                return f"no matching record found in '{table}'"

    def delete(self, table:str, document:dict)->str:
        if table not in self.tables:
            return f"table {table} does not exist"
        else:
            filename = self.tables[table]
            temp_filename = filename + '.tmp'
            deleted = False

            with open(filename, 'r') as file, open(temp_filename, 'w', newline='') as temp_file:
                reader = csv.DictReader(file)
                writer = csv.DictWriter(temp_file, fieldnames=reader.fieldnames, quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()

                for row in reader:
                    if not all(row[key] == str(document[key]) for key in document):
                        writer.writerow(row)
                    else:
                        deleted = True

            if deleted:
                os.replace(temp_filename, filename)
                return f"{document} deleted from '{table}'"
            else:
                os.remove(temp_filename)
                return f"no matching record found in '{table}'"

    def query(self, method:str, **kwargs:dict)->list:
            return Query(self, method, **kwargs).run()

class Query:
    def __init__(self, db:Database, method:str, **kwargs:dict)->None:
        self.kwargs = kwargs
        self.method = method
        self.db = db

    def run(self)->list:
        where = self.kwargs.get('where')
        subq = self.kwargs.get('subq')
        tables = self.kwargs.get('tables')

        if subq:
            if callable(subq) and self.method != 'group_by':
                self.data = subq()
            else:
                self.data = self.kwargs['subq']
        elif self.method == 'join':
            self.data = {table: self.db.open_stream(table) for table in tables}
        elif self.method != 'group_by':
            self.data = {table: self.db.open_stream(table)() for table in tables}
        try:

            if self.method == 'select':
                fields = self.kwargs['fields']
                sorting = self.kwargs.get('sorting')
                return self.select(tables, fields, where, sorting)

            elif self.method == 'join':
                on = self.kwargs['on']
                return self.join(tables, on)

            elif self.method == 'agg':
                agg_func = self.kwargs['agg_func']['function']
                agg_field = self.kwargs['agg_func']['field']
                sorting = self.kwargs.get('sorting')
                return self.agg(agg_func, agg_field, tables, where, sorting)

            elif self.method == 'group_by':
                group_by = self.kwargs['group_by']
                if 'subq' not in self.kwargs:
                    self.data = {table: self.db.tables[table] for table in self.kwargs['tables']}
                return self.group_by(tables, group_by, where)

        except KeyError as e:
            raise ValueError(f"{self.method} missing required argument: {e}")

    def select(self, table:list, fields:list, where:list, sorting:str)->list:
            data = self.data[table[0]] if table else self.data

            if where:
                data = self.where(data, where)()

            if '*' in fields:
                output = (doc for doc in data)
            else:
                output = ({field: doc[field] for field in fields} for doc in data)

            if sorting:
                sort_dict = {'field': fields[-1], 'order': sorting}
                return self.sort_large_data(output, sort_dict)
            else:
                return list(output)

    def sort_large_data(self, data_gen, sorting):
        chunk_size = self.db.chunk_size
        temp_files = []

        while True:
            chunk = list(itertools.islice(data_gen, chunk_size))
            if not chunk:
                break

            chunk.sort(key=lambda x: x[sorting['field']], reverse=(sorting['order'] != 'asc'))
            temp_file_path = f'temp_{len(temp_files)}.csv'
            with open(temp_file_path, 'w') as f:
                for line in chunk:
                    f.write(str(line) + '\n')
            temp_files.append(temp_file_path)

        # merge sorted files and clean up
        sorted_data = self.merge_sorted_files(temp_files)
        for temp_file in temp_files:
            os.remove(temp_file)
        return sorted_data

    def merge_sorted_files(self, sorted_files):
        sorted_data = []

        with open(sorted_files[0], 'r') as merged:
            for line in merged:
                sorted_data.append(eval(line.strip()))

        return sorted_data

    def join(self, tables, on):
        def factory():
            join_data = {table: self.data[table]() for table in tables}
            join_conditions = list(on.items())

            def join_two_tables_factory(table1, field1, table2, field2):
                def inner():
                    index = defaultdict(list)
                    for doc in table2:
                        index_key = f"{field2}"
                        index_value = {key: value for key, value in doc.items()}
                        index[doc[field2]].append(index_value)

                    for doc in table1:
                        matching_docs = index.get(doc[field1], [])
                        for match in matching_docs:
                            combined_doc = {**doc, **match}
                            yield combined_doc

                return inner

            base_table_key, join_field = join_conditions[0]
            base_table, base_field = base_table_key.split('.')
            join_table, join_table_field = join_field.split('.')
            join_result = join_two_tables_factory(join_data[base_table], base_field, join_data[join_table], join_table_field)()

            for join_condition, join_field in join_conditions[1:]:
                base_table, base_field = join_condition.split('.')
                join_table, join_table_field = join_field.split('.')
                join_result = join_two_tables_factory(join_result, base_field, join_data[join_table], join_table_field)()

            return join_result

        return factory

    def _stream_agg(self, chunked_data, agg_func):
        total, count, min_val, max_val = 0, 0, float('inf'), float('-inf')
        for value in chunked_data:
            if agg_func in ['avg', 'sum']:
                total += value
            if agg_func in ['avg', 'count']:
                count += 1
            if agg_func in ['min', 'max']:
                min_val = min(min_val, value)
                max_val = max(max_val, value)

        if agg_func == 'avg':
            return total / count if count else 0
        elif agg_func == 'sum':
            return total
        elif agg_func == 'count':
            return count
        elif agg_func == 'min':
            return min_val if count else None
        elif agg_func == 'max':
            return max_val if count else None


    def agg(self, agg_func:str, agg_field:str, table:str, where, sorting):
        chunk_size = self.db.chunk_size
        data = self.data[table] if table else self.data

        funcs = {
            'avg': np.mean,
            'sum': np.sum,
            'count': len,
            'min': np.max,
            'max': np.max
        }

        if where:
            data = self.where(data, where)()

        if type(data) == dict:
            result_dict = {}
            for key, datagen in data.items():
                intermediate_results = []
                while True:
                    chunk = list(itertools.islice(datagen, chunk_size))
                    if not chunk:
                        break

                    values = [doc[agg_field] for doc in chunk]
                    # agg_result = self._stream_agg(values, agg_func)
                    agg_result = funcs[agg_func](values)
                    intermediate_results.append(agg_result)
                results = self.combine_agg_results(intermediate_results, agg_func)
                result_dict[key] = results

            final_output = result_dict

        else:
            intermediate_results = []
            while True:
                chunk = list(itertools.islice(data, chunk_size))
                if not chunk:
                    break

                values = (doc[agg_field] for doc in chunk)
                agg_result = self._stream_agg(values, agg_func)
                intermediate_results.append(agg_result)

            final_output = self.combine_agg_results(intermediate_results, agg_func)

        if sorting:
            final_output = sorted(final_output.items(), key=lambda x: x[1], reverse=(sorting == 'desc'))

        return final_output
        

    def combine_agg_results(self, intermediate_results, agg_func):
        if agg_func == 'avg':
            total_sum = sum(intermediate_results)
            total_count = len(intermediate_results)
            return total_sum / total_count if total_count else 0
        elif agg_func == 'sum':
            return sum(intermediate_results)
        elif agg_func == 'count':
            return sum(intermediate_results)
        elif agg_func == 'min':
            return min(intermediate_results, default=None)
        elif agg_func == 'max':
            return max(intermediate_results, default=None)


    def open_csv(self, filename:str):
        with open(filename, 'r') as file:
            header_line = file.readline()
            headers = header_line.strip().split(',')

            while True:
                pos = file.tell()
                line = file.readline()
                if not line:
                    break

                reader = csv.DictReader([line], fieldnames=headers, quoting=csv.QUOTE_NONNUMERIC)
                for item in reader:
                    yield item, pos

    def make_index(self, stream, group_by_field):
        index = defaultdict(list)
        for item, pos in stream:
            index[item[group_by_field]].append(pos)
        return index

    def stream_from_indices(self, filename, indices):
        with open(filename, 'r') as file:
            header_line = file.readline()
            headers = header_line.strip().split(',')
            for pos in indices:
                file.seek(pos)
                line = file.readline()
                reader = csv.DictReader([line], fieldnames=headers, quoting=csv.QUOTE_NONNUMERIC)
                for item in reader:
                    yield item					

    def index_from_join(self, join_factory, group_by):
        index = defaultdict(list)
        join_gen = join_factory()
        for i, doc in enumerate(join_gen):
            index[doc[group_by]].append(i)
        return index

    def stream_from_join(self, join_factory, indices):
        join_gen = join_factory()
        for i, doc in enumerate(join_gen):
            if i in indices:
                yield doc

    def group_by(self, table:str, group_by:str, where:list)->list:
        if table:
            filename = self.data[table[0]]
            data = self.open_csv(filename)
        else:
            data = self.data

        if where:
            data = self.where(data, where)

        # not from subq
        if table:
            indices = self.make_index(data, group_by)
            grouped = {i: self.stream_from_indices(filename, indices[i]) for i in indices}
        else:
            indices = self.index_from_join(data, group_by)
            grouped = {i: self.stream_from_join(data, indices[i]) for i in indices}

        return grouped

    def where(self, data:list, conditions:list):
        def factory():
            for doc in data:
                if self._evaluate_conditions(doc, conditions):
                    yield doc
        return factory

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


class CommandInterface:
    @staticmethod
    def start(db_mem=2e5):
        db = Database(db_mem)
        parser = get_parser()
        while True:
            command = input('qlfish > ').strip()
            if command.lower() == 'exit':
                break
            else:
                cruds = ['ingest', 'create table', 'insert into', 'update', 'delete from']
                is_crud = any([command.startswith(crud) for crud in cruds])
                if not is_crud:
                    parsed = parser.parse(command)
                    query_results = CommandInterface.generate_query(parsed, db)
                    for result in query_results:
                        print(f">> {result}")
                else:
                    CommandInterface.handle_db_operations(command, db)

    @staticmethod
    def generate_query(parsed, db):
        try:
            if 'subq' in parsed:
                subq = parsed['subq']
                if type(subq) == str:
                    parsed['tables'] = [subq]
                    del parsed['subq']
                else:
                    parsed['subq'] = CommandInterface.generate_query(parsed['subq'], db)
            return db.query(**parsed)
        except:
            return db.query(**parsed)

    @staticmethod
    def handle_db_operations(command, db):
        if command.startswith('create table'):
            _, _, table_name = command.split()
            print(db.create_table(table_name))
        elif command.startswith('ingest'):
            # 'ingest [filename] into [table]'
            _, filename, _, table_name = command.split()
            print(db.ingest(filename, table_name))
        elif command.startswith('insert into'):
            # 'insert into [table] [json_document]'
            _, _, table_name, json_document = command.split(maxsplit=3)
            try:
                document = json.loads(json_document)
            except json.decoder.JSONDecodeError:
                print('invalid json')
            else:
                print(db.insert(table_name, document))
        elif command.startswith('update'):
            # 'update [table] on [key] [json_document]'
            _, table_name, _, key, json_document = command.split(maxsplit=4)
            try:
                document = json.loads(json_document)
            except json.decoder.JSONDecodeError:
                print('invalid json')
            else:
                print(db.update(table_name, key, document))
        elif command.startswith("delete from"):
            # 'delete from [table] [json_document]'
            _, _, table_name, json_document = command.split(maxsplit=3)
            try:
                document = json.loads(json_document)
            except json.decoder.JSONDecodeError:
                print('invalid json')
            else:
                print(db.delete(table_name, document))
        else:
            print('command not recognized')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--db_mem', type=int, default=2e5)
    db_mem = args.parse_args().db_mem
    CommandInterface.start(db_mem)