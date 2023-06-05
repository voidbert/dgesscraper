""" This module contains data types for representing higher education access contests """

"""
   Copyright 2023 Humberto Gomes

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from enum import Enum
from dataclasses import dataclass
import pickle
from os.path import isfile

@dataclass(eq = True, frozen = True)
class StudentEntry:
	"""
	Information about a candidate to a certain course

	Attributes
	----------

	place:  int
		The place of the student in the list of candidates (ordered by grade)
	gov_id: int
		The first 3 and last 2 digits of the student's government ID, combined into an integer
	name:   str
		The name of the student
	option: int
		The preference of the student for this course (1 to 6)

	grade:       int
		Final average grade of the student (from 0 to 2000 points)
	grade_exams: int
		Average grade of the exams required for this course (from 0 to 2000 points)
	grade_12:    int
		Student's grade in 12th grade (from 0 to 2000 points)
	grade_10_11: int
		Average grade from 10th and 11th grades (from 0 to 2000 points)
	"""

	place:  int
	gov_id: int
	name:   str
	option: int

	grade:       int
	grade_exams: int
	grade_12:    int
	grade_10_11: int

@dataclass(eq = True, frozen = True)
class Course:
	"""
	Information about a course

	Attributes
	----------

	code: str
		An unique identifier for a course within a school
	name: str
		The human-readable name of the course
	"""

	code:       str
	name:       str

class SchoolType(Enum):
	""" The type of an upper education school (university or polytechnical school) """

	UNIVERSITY    = 1
	POLYTECHNICAL = 2

	def to_server_code(self) -> str:
		""" Converts a SchoolType to a string used to identify it in requests' URLs """

		match self:
			case SchoolType.UNIVERSITY:
				return '11'
			case SchoolType.POLYTECHNICAL:
				return '12'

@dataclass(eq = True, frozen = True)
class School:
	"""
	Information about a higher education school

	Attributes
	----------

	school_type: SchoolType
		The type of this school (university or polytechnical school)
	code: str
		A unique school identifier
	name: str
		The human-readable name of the school
	"""

	school_type: SchoolType
	code:        str
	name:        str

class Phase(Enum):
	""" A phase of a higher education access contest """

	FIRST  = 1
	SECOND = 2
	THIRD  = 3

@dataclass(eq = True, frozen = True)
class Contest:
	"""
	Data about a public higher education access contest

	Attributes
	----------

	year: int
		The year of the context
	phase: Phase
		The phase of the context
	"""

	year: int
	phase: Phase

# Due to the small dataset size, databases are stored in memory and only cached to disk after
# all data is collected

CourseStudents = dict[Course, list[StudentEntry]]
SchoolCourses = dict[School, CourseStudents]
Database = dict[Contest, SchoolCourses]

def is_in_database(database: Database, contest: Contest, school: School = None, \
	course: Course = None) -> bool:

	"""
		Checks if something is stored in a database. That can be a contest, a school inside a
		contest, or a course inside a school inside a contest.
	"""

	if contest in database and database[contest] is not None:
		if school is not None:
			if school in database[contest] and database[contest][school] is not None:
				if course is not None:
					if course in database[contest][school] and \
						database[contest][school][course] is not None:
							return True
					else:
						return False
				else:
					return True
			else:
				return False
		else:
			return True
	else:
		return False

def read_database(path: str) -> Database:
	""" Reads a DGES database from a file """

	with open(path, 'rb') as file:
		return pickle.load(file)

def write_database(database: Database, path: str) -> None:
	""" Writes a DGES database to a file """

	with open(path, 'wb') as file:
		pickle.dump(database, file)


def attempt_read_database(database_path: str) -> Database:
	"""
		Tries to read a database from disk. If the file doesn't exist, an empty database is
		returned. If another error happens while loading the database, that error won't be
		caught. If database_path is None, an empty dictionary will be returned (no caching).
	"""

	if database_path is not None and isfile(database_path):
		return read_database(database_path)

	return {}

ATTEMPT_WRITE_DATABASE_BACKUP_PATH = 'dgesdb.pickle' # See attempt_write_database

def attempt_write_database(database: Database, database_path: str) -> None:
	"""
		Tries to save a database to the specified path. If that fails, this method will attempt
		to write the base to ATTEMPT_WRITE_DATABASE_BACKUP_PATH, to avoid loss of data. If
		database_path is None, no file operations will occur (no caching).
	"""

	if database_path is None: # No caching
		return

	try:
		write_database(database, database_path)
	except:
		# Failed to write database. Try to make an emergency backup
		try:
			write_database(database, ATTEMPT_WRITE_DATABASE_BACKUP_PATH)
		except:
			raise RuntimeError(f'Failed to write database to "{database_path}". ' \
				'Attempt to save backup database to ' \
				f'"{ATTEMPT_WRITE_DATABASE_BACKUP_PATH}" also failed.')

		raise RuntimeError(f'Failed to write database to "{database_path}". Able to ' \
			f'save backup database to "{ATTEMPT_WRITE_DATABASE_BACKUP_PATH}".')

