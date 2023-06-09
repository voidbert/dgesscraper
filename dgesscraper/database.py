"""
	@file database.py
	@package dgesscraper.database
	@brief This module defines a `Database` class, for storing data for multiple DGES contests
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

import pickle
from os.path import isfile
from typing import Iterator

from dgesscraper.types import *
from dgesscraper.filter import *

CourseStudents = dict[Course, list[StudentEntry]]
SchoolCourses = dict[School, CourseStudents]
DatabaseDict = dict[Contest, SchoolCourses]

class Database:
	"""
		@brief A database for storing DGES data from multiple contests.
		@details

		### Dictionary structure

		A database is internally implemented using a nested dictionary, because the type of
		data that it stores is small enough to fully fit in memory.

		Any one of the nested dictionaries can have a key with a corresponding `None` value.
		For example, if `dictionary[contest][school]` is `None`, that means that the list of
		courses for that school hasn't yet been scraped. However, the presence of the school as
		a dictionary key is crucial, to store the information that the school is part of the
		list of schools of that contest.

		You can access the database dictionary directly, the following way:

		```
		database.dicitonary[contest][school][course]
		```

		This returns a list of [student entries](@ref dgesscraper.types.StudentEntry), the list
		of candidates to that course.

		For example, if you wish to know the courses provided by a school, you can use:

		```
		database.dictionary[contest][school].keys()
		```

		@anchor dbiter
		### Database iteration

		If you don't wish to access particular contests / schools / courses, you can iterate
		through the whole (or part of the) database, using one of the following methods:

		- [iterate_contests](@ref Database.iterate_contests)
		- [iterate_schools](@ref Database.iterate_schools)
		- [iterate_courses](@ref Database.iterate_courses)
		- [iterate_students](@ref Database.iterate_students)

		The provided [DGESFilter](@ref dgesscraper.filter.DGESFilter) allows you to iterate
		through only a part of part of the database. Keep in mind that, for example, while
		iterating through courses, the filter will also be used to discard contests and
		schools. Therefore, a given contest may meet the condition in
		[DGESFilter.filter_courses](@ref dgesscraper.filter.DGESFilter.filter_courses), but be
		discarded, because either the parent school or contest failed verification by the
		filter. If no filter is provided, the methods iterate through the whole database (see
		[UniversalFilter](@ref dgesscraper.filter.UniversalFilter)).

		When applicable, the `only_cached` parameter, `True` by default, determines whether
		only objects with a non-`None` value should be returned (only already scraped and
		cached contests / school / courses).

		When yielding an item, its parents are also provided, along with the data associated
		with that item. That is indicated by the return type of each function. For example,
		when iterating through schools, the parent contest is returned along with the school.
		The last element of the tuple is the data associated with the school, this is, a
		dictionary that associates courses with lists of candidates.
	"""

	## See @ref Database.to_cache
	ATTEMPT_WRITE_DATABASE_BACKUP_PATH = 'dgesdb.pickle'

	def __init__(self, dictionary: DatabaseDict):
		""" @brief Creates a database from a dictionary """
		self.dictionary = dictionary

	@staticmethod
	def from_file(path: str) -> 'Database':
		"""
			@brief Reads a DGES database from a file
			@details The output is the internal dictionary in a binary format (see
			         [pickle](https://docs.python.org/3/library/pickle.html))
		"""
		with open(path, 'rb') as file:
			return Database(pickle.load(file))

	@staticmethod
	def from_cache(path: str) -> 'Database':
		"""
			@brief Similar to @ref Database.from_file.
			@details Differences from @ref Database.from_file:

			- If @p path is `None` (no caching), no file operations will be performed.
			- If there is no file in @p path, an empty @ref Database will be returned.
		"""

		if path is None or not isfile(path):
			return Database({})
		else:
			return Database.from_file(path)

	def to_file(self, path: str) -> None:
		"""
			@brief Saves a DGES database to a file
			@details The output is the internal dictionary in a binary format (see
			         [pickle](https://docs.python.org/3/library/pickle.html))
		"""
		with open(path, 'wb') as file:
			pickle.dump(self.dictionary, file)

	def to_cache(self, path: str) -> None:
		"""
			@brief Similar to @ref Database.to_file
			@details Differences from @ref Database.to_file:

			- If @p path is `None` (no caching), no file operations will be performed.
			- If writing to @p path fails, this method will attempt to write a backup copy
			  of the database to @ref Database.ATTEMPT_WRITE_DATABASE_BACKUP_PATH.
		"""

		if path is None: # No caching
			return

		try:
			self.to_file(path)
		except:
			# Failed to write database. Try to make an emergency backup
			try:
				self.to_file(Database.ATTEMPT_WRITE_DATABASE_BACKUP_PATH)
			except:
				raise RuntimeError(f'Failed to write database to "{path}". ' \
					'Attempt to save backup database to ' \
					f'"{Database.ATTEMPT_WRITE_DATABASE_BACKUP_PATH}" also failed.')

			raise RuntimeError(f'Failed to write database to "{path}". Able to save ' \
				f'backup database to "{Database.ATTEMPT_WRITE_DATABASE_BACKUP_PATH}".')

	def __contains__(self, item):
		"""
			@brief Checks if an item is present in the database. The item can be.

			- A [Contest](@ref dgesscraper.types.Contest)

			- A ([Contest](@ref dgesscraper.types.Contest),
			     [School](@ref dgesscraper.types.School)) pair

			- A ([Contest](@ref dgesscraper.types.Contest),
			     [School](@ref dgesscraper.types.School),
			     [Course](@ref dgesscraper.types.Course)) tuple
		"""

		dictionary = self.dictionary
		item_tuple = item if isinstance(item, tuple) else (item,)
		while len(item_tuple) > 0:
			key = item_tuple[0]
			if key in dictionary and dictionary[key] is not None:
				dictionary = dictionary[key]
				item_tuple = item_tuple[1:]
			else:
				return False

		return True

	def add_contest(self, contest: Contest, school_list: Iterator[School]):
		"""
			@brief Adds [Contest](@ref dgesscraper.types.Contest) information (list of
			[schools](@ref dgesscraper.types.School)) to the database.

			@details This will overwrite any current data.
		"""

		contest_schools = {}
		for school in school_list:
			contest_schools[school] = None
		self.dictionary[contest] = contest_schools

	def add_school(self, contest: Contest, school: School, course_list: Iterator[Course]):
		"""
			@brief Adds [School](@ref dgesscraper.types.School) information (list of
			[courses](@ref dgesscraper.types.Course)) to the database.

			@details This will overwrite any current data.
		"""

		school_courses = {}
		for course in course_list:
			school_courses[course] = None
		self.dictionary[contest][school] = school_courses

	def add_course(self, contest: Contest, school: School, course: Course, \
		    students: Iterator[StudentEntry]):
		"""
			@brief Adds [Course](@ref dgesscraper.types.Course) information (list of
			candidates) to the database.

			@details This will overwrite any current data.
		"""
		self.dictionary[contest][school][course] = students

	def iterate_contests(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True)\
		-> Iterator[tuple[Contest, SchoolCourses]]:

		""" @brief See [Database iteration](@ref dbiter). """

		for contest in self.dictionary.keys():
			if filter.list_contests() is None or contest in filter.list_contests():
				if not only_cached or self.dictionary[contest] is not None:
					yield (contest, self.dictionary[contest])

	def iterate_schools(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True) \
		-> Iterator[tuple[Contest, School, CourseStudents]]:

		""" @brief See [Database iteration](@ref dbiter). """

		for contest, school_courses in self.iterate_contests(filter, True):
			for school in school_courses.keys():
				if filter.filter_schools(contest, school):
					if not only_cached or school_courses[school] is not None:
						yield (contest, school, school_courses[school])

	def iterate_courses(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True) \
		-> Iterator[tuple[Contest, School, Course, list[StudentEntry]]]:

		""" @brief See [Database iteration](@ref dbiter). """

		for contest, school, course_students in self.iterate_schools(filter, True):
			for course in course_students.keys():
				if filter.filter_courses(contest, school, course):
					if not only_cached or course_students[course] is not None:
						yield (contest, school, course, course_students[course])

	def iterate_students(self, filter: DGESFilter = UniversalFilter()) \
		-> Iterator[tuple[Contest, School, Course, StudentEntry]]:

		""" @brief See [Database iteration](@ref dbiter). """

		for contest, school, course, students in self.iterate_courses(filter, True):
			for student in students:
				yield (contest, school, course, student)

