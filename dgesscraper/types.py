"""
	@file types.py
	@package dgesscraper.types
	@brief This module contains data types for representing higher education access contests
"""

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
	""" @brief Information about a candidate to a certain course """

	## @brief The place of the student in the list of candidates (ordered by grade)
	place: int

	## @brief The first 3 and last 2 digits of the student's government ID, combined into an
	#         integer
	#  @details For more details, see
	#           [pagescraper.__extract_id](@ref dgesscraper.pagescraper.__extract_id)
	gov_id: int

	## @brief Name of the student
	name: str

	## @brief The preference of the student for this course (1 to 6)
	option: int

	## @brief Final average grade of the student (from 0 to 2000 points)
	grade: int
	## @brief Average grade of the exams required for this course (from 0 to 2000 points)
	grade_exams: int
	## @brief Student's grade in 12th grade (from 0 to 2000 points)
	grade_12: int
	## @brief Average grade from 10th and 11th grades (from 0 to 2000 points)
	grade_10_11: int

	## @brief If the student got into the course
	#  @details Note that a student can meet the acceptance criteria (better grades than the
	#           candidate with the worst grades), and this variable can still be `False`, in case
	#           the student got accepted into a course higher up in their list of options.
	accepted: bool

@dataclass(eq = True, frozen = True)
class Course:
	""" @brief Information about a course """

	## @brief An unique course identifier **within its [school](@ref dgesscraper.types.School)**
	code:       str
	## @brief The human-readable name of the course
	name:       str

class SchoolType(Enum):
	""" @brief The type of an upper education school (university or polytechnical school) """

	UNIVERSITY    = 1
	POLYTECHNICAL = 2

	def to_server_code(self) -> str:
		"""
			@brief Converts a [SchoolType](@ref dgesscraper.types.SchoolType) to a string,
			used to identify it in requests' URLs
		"""

		if self == SchoolType.UNIVERSITY:
			return '11'
		else:
			return '12'

@dataclass(eq = True, frozen = True)
class School:
	""" @brief Information about a higher education school """

	## @brief The type of the school (university or polytechnical school)
	school_type: SchoolType
	## @brief A unique school identifier **within its [contest](@ref dgesscraper.types.Contest)**
	code:        str
	## @brief The human-readable name of the school
	name:        str

class Phase(Enum):
	""" @brief A phase of a higher education access contest """

	FIRST  = 1
	SECOND = 2
	THIRD  = 3

@dataclass(eq = True, frozen = True)
class Contest:
	""" @brief Data about a public higher education access contest """

	## @brief The year of the contest
	year: int
	## @brief The name of the contest
	phase: Phase

