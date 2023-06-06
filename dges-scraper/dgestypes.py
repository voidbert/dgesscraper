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

