![Image Description](211.png)

# qlfish: database query system

## introduction

### overview
`qlfish` was designed for efficiency and user-friendliness while remaining robust for complex queries. It integrates advanced features such as data ingestion, complex query processing, and data streaming.

### objectives
1. **efficient data handling**: manages large volumes of data, ensuring quick access and manipulation, including the ability to ingest data from various sources, store it effectively, and retrieve it promptly when needed

2. **complex query processing**: executes a range of queries, from basic crud (create, read, update, delete) operations to more complex ones involving aggregation, joins, and group-by functionalities. the system is designed to handle these efficiently and accurately

3. **user-friendly interface**: provides an intuitive command interface that simplifies the process of executing queries and managing data, with a familiar `sql`-inspired syntax

in the following sections, we delve into the technical architecture, core functionalities, and the technical principles underpinning this database query system

## architecture

### overview
the architecture comprises several interconnected components, each designed to handle specific aspects of data management and query processing

### components

#### `database` class

- **role and functionality**: the `database` class is the backbone of the system. it manages the storage, retrieval, and manipulation of data. this class is initialized with a memory limit, which determines the chunk sizes for data to ensure nothing runs out of core
- **key methods**:
  - **`ingest`**: readies `csv`s for import into the system and calculating the chunk sizing
  - **`open_stream`**: creates a data stream from a specified table, enabling streamed data handling
  - **`create_table`**: creates new tables within the database for storing data.
  - **`insert`**, **`update`**, **`delete`**: these methods facilitate the basic crud operations on the data stored in the tables
  - **`query`**: endpoint for all query execution (select, join, aggregate, etc.) on the data

#### `query` class
- **purpose**: the `query` class is designed to handle the execution and management of different types of queries in the form of nested subqueries
- **functionality**: it interprets query parameters and calls appropriate methods in the `database` class to fetch or manipulate data. this class is critical for performing complex operations like joins, aggregations, and group-by
- **query processing**: it includes processing conditions, aggregating results, and managing the flow of data for join operations

#### command interface
- **function**: the `commandinterface` class serves as the user interface for interacting with the database. it interprets user inputs, converts them into commands or queries, and communicates with the `database` and `query` classes to execute these operations
- **user interaction**: through a simple command-line interface, users can input their queries, which are then parsed and executed by the system

### data flow and interaction
- **data ingestion and storage**: data is ingested through the `database` class and stored in a structured format within the system, streamed from when called upon
- **query execution**: when a query is input, the `commandinterface` parses it and interacts with the `query` class to process it, which then calls `open_stream` on the required data
- **result retrieval**: after processing, the results are sent back to the `commandinterface`, which displays them to the user

### scalability and performance optimization
- **memory management**: the system is designed to handle large datasets efficiently, utilizing streaming and chunking to optimize memory usage
- **indexing and caching strategies**: these are implemented for faster data joining and query execution

### robustness and error handling
- **error detection and handling**: the system includes mechanisms to detect and handle errors, providing feedback for any incorrect or invalid queries

## core functionalities

### data ingestion
- **process overview**: data ingestion is the first step in populating the database with data. the system focuses on `.csv` files
- **implementation**: the `ingest` and `open_stream` methods in `database` handle this. `ingest` computes the average chunk size for system-wide use and stores reference to the table for use by `open_stream` when called on to enable data streaming
- **chunk-based processing**: to efficiently manage large datasets, the system uses a chunk-based approach for specific types of aggregation while it uses streaming for others.

### query processing
#### select queries
- **methodology**: the `select` method in the `query` class is responsible for executing select queries. it involves filtering and projecting data based on user-defined criteria.
- **field specification**: users specify fields or use `*` for all fields. the method constructs a data generator that iterates over the dataset, yielding only the specified fields.
- **conditional filtering**: implemented via the `where` function in the `query` class. this function evaluates conditions against each data row. conditions are parsed into logical expressions that compare field values against user-defined criteria.
- **sorting**: achieved through the `sort_large_data` method. the method sorts data in memory-efficient chunks, using python’s built-in sorting functions. if specified, it uses a temporary file system for large datasets to avoid memory overload.
- **chunk-based processing**: for large datasets, data is processed in chunks determined by the `chunk_size` attribute in the `database` class. this approach reduces memory consumption and allows the system to handle larger datasets efficiently.

#### aggregation queries
- **function implementation**: the `agg` method in the `query` class handles aggregation queries. it supports operations like average (avg), sum, count, min, and max.
- **chunk-based aggregation**: data is processed in chunks. for each chunk, aggregation functions are applied to the specified field. the results from each chunk are then combined to produce the final result.
- **aggregation logic**: the system employs python's built-in functions (like `sum`, `min`, `max`) and numpy functions for efficient computation. custom logic is used for average and count to handle these operations across chunks.
- **group handling**: when used with `group_by`, the aggregation function is applied to each group separately. this is managed by iterating over the groups generated by the `group_by` method and applying the aggregation function to each group.

#### join operations
- **join logic**: the `join` function in the `query` class manages join operations. it creates a generator that yields rows from multiple tables based on the join condition.
- **join types**: currently focused on inner joins, where rows from different tables are combined based on matching values in specified fields.
- **data merging**: the function reads rows from each table and compares them based on the join condition. when a match is found, it combines the rows and yields the result.
- **handling large tables**: for large tables, the system uses a nested loop join approach. this method involves iterating over one table and for each row, searching for matching rows in the other table.

#### group by functionality
- **implementation**: the `group_by` method in the `query` class handles the grouping of data.
- **grouping mechanism**: the method iterates over the dataset and groups data based on the specified field. it maintains an index mapping group keys to data rows.
- **data streaming for groups**: each group is processed as a separate data stream. when combined with aggregation, the system applies the aggregation function to each group's data stream.
- **efficiency considerations**: for large datasets, the system processes each group individually to minimize memory usage. it uses a lazy evaluation approach, where data for a group is only processed when required.

### crud operations
- **create (create table)**:
    - **usage**: this operation involves creating new tables in the database, instantiating a new `.csv` file.
    - **process**: the `create_table` allows users to define new tables for storing data by creating a new `.csv` file and storing a reference to it for further inserting

- **read (query data)**:
    - **description**: reading data involves querying the database to retrieve specific information.
    - **functionality**: the `select` function underlies this operation, equipped to handle complex queries including conditions and joins.

- **update**:
    - **purpose**: this operation is used to modify existing data in the database.
    - **implementation**: the `update` method allows users to make changes to data entries based on a specified key

- **delete**:
    - **function**: this operation is used to remove data from the database.
    - **method**: the `delete` function handles this, enabling users to specify the deletion key

### parsing and lexical analysis
- **role of lexical analysis**: lexical analysis, or lexing, is the first step in interpreting user input. it involves breaking down the raw input (a string of characters) into a series of tokens. these tokens represent meaningful units like keywords, operators, identifiers, and literals
- **implementation with `ply.lex`**: we use the `ply.lex` module for lexical analysis. this module scans the input string and matches it against predefined patterns (regular expressions) to identify tokens
- **token definition**: tokens in our system include keywords like `select`, `from`, `join`, data types, operators (like `==`, `>`, `<`), and other syntax elements. each token type is defined with a regular expression that `ply.lex` uses to recognize and categorize input strings

#### syntax parsing with `ply.yacc`
- **implementation with `ply.yacc`**: we employ the `ply.yacc` module for syntax parsing. this module takes the stream of tokens produced by the lexer and constructs a parse tree based on the grammar rules we have defined. the parse tree represents the syntactic structure of the input
- **grammar rules definition**: the grammar rules specify how tokens can be combined to form valid statements and expressions. for example, a `select` statement must be followed by a list of fields, the keyword `from`, and a table name

#### handling complex queries
- **nested queries and sub-queries**: our system is capable of handling complex queries, including nested queries and sub-queries. the parsing logic is designed to recognize and correctly interpret these structures, ensuring accurate query execution.

#### integration with query processing
- **from parsing to execution**: once the input is successfully parsed, the resulting parse tree is used to generate a query object. this object is then passed to the query processing component of the system, which executes the query against the database.

## workflow + examples

importing the base files


```python
import json
from db import Database 
from parserfile import get_parser
```

demonstrating the ingestion process


```python
db = Database(100000)
parser = get_parser

db.ingest('data/students.csv', 'students')
db.ingest('data/courses.csv', 'courses')
db.ingest('data/enrollments.csv', 'enrollments')
```

    833
    1136
    1136





    'ingested data/enrollments.csv into enrollments'



demonstrating insert, update, and deletion


```python
entry = '{"student_id": 45006, "student_name": "James Wu", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.insert('students', entry_json)
```


    "{'student_id': 45006, 'student_name': 'James Wu', 'age': 20, 'major': 'Data Science', 'gpa': 3.86} inserted into students"



```python
entry = '{"student_id": 45006, "student_name": "James Woo", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.update('students', on='student_id', document=entry_json)
```


    "{'student_id': 45006, 'student_name': 'James Woo', 'age': 20, 'major': 'Data Science', 'gpa': 3.86} updated in 'students'"



```python
entry = '{"student_id": 45006, "student_name": "James Woo", "age": 20, "major": "Data Science", "gpa": 3.86}'
entry_json = json.loads(entry)
db.delete('students', document=entry_json)
```


    "{'student_id': 45006, 'student_name': 'James Woo', 'age': 20, 'major': 'Data Science', 'gpa': 3.86} deleted from 'students'"


demonstrate the query parsing process


```python
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

def qquery(**kwargs):
    return kwargs

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
```

the output from the parser


```python
qstring2 = 'find avg(gpa) [asc] by major from students'
parsed2 = parser.parse(qstring2)
parsed2
```


    {'method': 'agg',
     'agg_func': {'function': 'avg', 'field': 'gpa'},
     'sorting': 'asc',
     'subq': {'method': 'group_by', 'group_by': 'major', 'subq': 'students'}}


`qquery` is a toy function that shows how queries are recursively generated from nested subqueries


```python
generate_qquery(parsed2)
```


    {'method': 'agg',
     'agg_func': {'function': 'avg', 'field': 'gpa'},
     'sorting': 'asc',
     'subq': {'method': 'group_by', 'group_by': 'major', 'tables': ['students']}}


which then is passed to the actual `db` to make a real query


```python
generate_query(parsed2)
```


    [('Computer Science', 3.395110949963742),
     ('Data Science', 3.3997494653223344),
     ('Computer Engineering', 3.401678609544138)]


a more complex query


```python
qstring4 = 'find avg(gpa) by course_name from join students, enrollments, courses on students.student_id: enrollments.student_id, enrollments.course_id: courses.course_id'
parsed4 = parser.parse(qstring4)
parsed4
```


    {'method': 'agg',
     'agg_func': {'function': 'avg', 'field': 'gpa'},
     'sorting': None,
     'subq': {'method': 'group_by',
      'group_by': 'course_name',
      'subq': {'method': 'join',
       'tables': ['students', 'enrollments', 'courses'],
       'on': {'students.student_id': 'enrollments.student_id',
        'enrollments.course_id': 'courses.course_id'}}}}



```python
generate_qquery(parsed4)
```


    {'method': 'agg',
     'agg_func': {'function': 'avg', 'field': 'gpa'},
     'sorting': None,
     'subq': {'method': 'group_by',
      'group_by': 'course_name',
      'subq': {'method': 'join',
       'tables': ['students', 'enrollments', 'courses'],
       'on': {'students.student_id': 'enrollments.student_id',
        'enrollments.course_id': 'courses.course_id'}}}}



```python
generate_query(parsed4)
```


    {'Software Engineering': 3.3916274509803923,
     'Introduction to Programming': 3.394664005322688,
     'Scientific Computing and Visualization': 3.384058463630184,
     'Special Topics': 3.407740039190072,
     'Privacy in the World of Big Data': 3.3933125,
     'Senior Project': 3.3886577652846097,
     'Optimization for the Information and Data Sciences': 3.4040390674228105,
     'Introduction to Robotics': 3.3939461588969135,
     'Web Technologies': 3.4026281208935614,
     'Programming Graphical User Interfaces': 3.391156741957563,
     'Search and Planning': 3.40478672985782,
     'Geometric Modeling': 3.3932934131736534,
     'Explorations in Computing': 3.4056466069142126,
     'Introduction to Computer Networks': 3.409338092147956,
     'File and Database Management': 3.415058517555267,
     'Database Systems Interoperability': 3.392032894736842,
     'Digital Geometry Processing': 3.3983025099075297,
     'Introduction to Programming Systems Design': 3.402798194713088,
     'Game Prototyping': 3.388484848484848,
     'Diagnosis and Design of Reliable Digital Systems': 3.4044308943089434,
     'Advanced Natural Language Processing': 3.4046693386773548,
     'Compiler Development': 3.416864973262032,
     'Introduction to Operating Systems': 3.403484549638396,
     'Parallel and Distributed Computation': 3.384815546772069,
     'Natural Language Dialogue Systems': 3.402207792207792,
     'Haptic Interfaces and Virtual Environments': 3.400571428571429,
     'Machine Learning Theory': 3.37599582172702,
     'Quantum Computing and Quantum Cryptography': 3.3996359890109895,
     'Advanced Program Analysis and Verification': 3.3958366013071895,
     'Social Media Analytics': 3.39889400921659,
     'Video Game Programming': 3.4016701316701314,
     'Artificial Intelligence for Sustainable Development': 3.3831297709923667,
     'Introduction to Internetworking': 3.4032992501704156,
     'Advanced Distributed Systems': 3.3935227272727273,
     'Computer Science Research Colloquium': 3.3909053778080325,
     'Computer Systems and Applications Modeling Fundamentals': 3.405497113534317,
     'Computer Graphics': 3.400879566982409,
     'Advanced Information Integration': 3.401489222730242,
     'Advanced Topics in Operating Systems': 3.4039584685269304,
     'Directed Research': 3.389756179024716,
     'Software Engineering for Embedded Systems': 3.407066142763589,
     'Fundamentals of Computation': 3.395050778605281,
     'High Performance Computing and Simulations': 3.3820202702702704,
     'Text as Data': 3.3963682219419926,
     'Professional Writing and Communication for Computer Scientists': 3.40644,
     'Geospatial Information Management': 3.3984680025856497,
     'Computer Systems Organization': 3.387165809768638,
     'Data Structures and Object Oriented Design': 3.3904871794871796,
     'Advanced Topics in Interconnection Network Design and Analysis': 3.3980149346608592,
     'Introduction to Algorithms and Theory of Computing': 3.4089736842105265,
     'Numerical Analysis': 3.397066235864297,
     "Master's Thesis": 3.4003141361256546,
     'Logic and its Applications': 3.3954641211323238,
     'Introduction to Computer Systems': 3.3951523358158426,
     'Mathematical Foundations for System Design: Modeling, Analysis, and Synthesis': 3.4017619680851063,
     'Concepts of Programming Languages': 3.398465211459754,
     'Professional C++': 3.415684348395547,
     'Final Game Project': 3.3905147307822547,
     'Information Retrieval and Web Search Engines': 3.411405750798722,
     'Discrete Methods in Computer Science': 3.410027266530334,
     'Computer Organization and Architecture': 3.401048332198775,
     'Numerical Solutions of Ordinary and Partial Differential Equations': 3.4013220998055735,
     'Multimedia Systems Design': 3.4088287068381855,
     'Computer Vision': 3.412108667529108,
     'Introduction to Computer and Network Security': 3.401806282722513,
     'Native Console Multiplayer Game Development': 3.4044127190136275,
     '3-D Graphics and Rendering': 3.397658438959306,
     'Introduction to Artificial Intelligence': 3.3904524590163936,
     'Translation of Programming Languages': 3.3888984168865433,
     'Analysis of Algorithms': 3.412958904109589,
     'Pipelines for Games and Interactives': 3.404951892238614,
     'Introduction to Online Optimization': 3.3944610169491525,
     'Capstone: Creating Your High-Tech Startup': 3.400497094899936,
     'Operating Systems': 3.4011044176706826,
     'Principles of Software Development': 3.407148337595908,
     'Program Synthesis and Computer-Aided Verification': 3.411141522029372,
     'Introduction to System-on-Chip': 3.396209193870753,
     'Theory of Computation': 3.409633577614924,
     'Mathematics of High-Dimensional Data': 3.385349444807315,
     'Coordinated Mobile Robotics': 3.399974457215837,
     'Probabilistic Reasoning': 3.3925634352635003,
     'Artificial Intelligence for Social Good': 3.404459907223327,
     'Introduction to Computer Science': 3.396340341655716,
     'Networked Systems in Cloud Computing': 3.410325644504749,
     'Database Systems': 3.3869251517194874,
     'Software Architectures': 3.3968754301445285,
     'Advanced Topics in Computer System Architecture': 3.398297595841455,
     'Computer Animation and Simulation': 3.39418945963976,
     'Programming Game Engines': 3.408866666666667,
     'Numerical Methods': 3.3896378830083567,
     'Internet Measurement': 3.382670262980445,
     'Cryptography: Secure Communication and Computation': 3.385424621461488,
     'Advanced Computer Networking': 3.4058097165991903,
     'Introduction to Machine Learning': 3.398111111111111,
     'Numerical Analysis and Computation': 3.393359580052493,
     'Capstone: Design and Construction of Large Software Systems': 3.4094391891891895,
     'Special Problems': 3.399720186542305,
     'Fundamentals of Computer Programming': 3.4051482479784365}

