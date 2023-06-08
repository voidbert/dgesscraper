""" This module defines a Database class, for storing data for multiple DGES contests """

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

from dgesscraper.dgestypes import *
from dgesscraper.dgesfilter import *

CourseStudents = dict[Course, list[StudentEntry]]
SchoolCourses = dict[School, CourseStudents]
DatabaseDict = dict[Contest, SchoolCourses]

class Database:
	"""
		A database for storing DGES data from multiple contests. It is internally implemented
		using a dictionary, because it's small enough to fully fit in memory.

		The structure of the database is one of a nested dictionary accessed like this:
		database[contest][school][course] returns a list of student entries, the list of
		candidates to that course.

		Any one of the nested dictionaries can have a valid key and a None value. That means
		that part of the database hasn't been cached yet. The key is, however, necessary! For
		example, if a course has a None value, the list of candidates hasn't been scraped yet.
		However, the list of courses in that school (list of keys) is valid.
	"""

	ATTEMPT_WRITE_DATABASE_BACKUP_PATH = 'dgesdb.pickle' # See to_cache

	def __init__(self, dictionary: DatabaseDict):
		""" Creates a database from a dictionary """
		self.dictionary = dictionary

	@staticmethod
	def from_file(path: str) -> 'Database':
		""" Reads a DGES database from a file """
		with open(path, 'rb') as file:
			return Database(pickle.load(file))

	@staticmethod
	def from_cache(path: str) -> 'Database':
		"""
			Similar to from_file, but will return an empty database if the cache file doesn't
			exist or if the path is None (no caching).
		"""

		if path is None or not isfile(path):
			return Database({})
		else:
			return Database.from_file(path)

	def to_file(self, path: str) -> None:
		""" Saves a DGES database to a file """
		with open(path, 'wb') as file:
			pickle.dump(self.dictionary, file)

	def to_cache(self, path: str) -> None:
		"""
			Similar to to_file, but this method will try to save a backup copy to
			ATTEMPT_WRITE_DATABASE_BACKUP_PATH if writing to the specified path fails.
			Also, if path is None, no files are saved (no caching).
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
			Checks if an item is contained in the database. The item can be.

			  - A contest
			  - A (contest, school) pair
			  - A (contest, school, course) tuple
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
			Adds contest information (list of schools) to the database. This will overwrite
			any current data.
		"""

		contest_schools = {}
		for school in school_list:
			contest_schools[school] = None
		self.dictionary[contest] = contest_schools

	def add_school(self, contest: Contest, school: School, course_list: Iterator[Course]):
		"""
			Adds school information (list of courses) to the database. This will overwrite
			any current data.
		"""

		school_courses = {}
		for course in course_list:
			school_courses[course] = None
		self.dictionary[contest][school] = school_courses

	def add_course(self, contest: Contest, school: School, course: Course, \
		    students: Iterator[StudentEntry]):
		"""
			Adds course information (list of candidates) to the database. This will overwrite
			any current data.
		"""
		self.dictionary[contest][school][course] = students

	def iterate_contests(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True)\
		-> Iterator[tuple[Contest, SchoolCourses]]:

		"""
			Iterates through the database, looking for contests accepted by the provided
			filter. If only_cached is True, contests with a None value (corresponding list of
			schools hasn't yet been scraped) won't be returned.
		"""

		for contest in self.dictionary.keys():
			if filter.list_contests() is None or contest in filter.list_contests():
				if not only_cached or self.dictionary[contest] is not None:
					yield (contest, self.dictionary[contest])

	def iterate_schools(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True) \
		-> Iterator[tuple[Contest, School, CourseStudents]]:

		"""
			Iterates through the database, looking for schools accepted by the provided
			filter. If only_cached is True, schools with a None value (correspoding list of
			courses hasn't yet been scraped) won't be returned.
		"""

		for contest, school_courses in self.iterate_contests(filter, True):
			for school in school_courses.keys():
				if filter.filter_schools(contest, school):
					if not only_cached or school_courses[school] is not None:
						yield (contest, school, school_courses[school])

	def iterate_courses(self, filter: DGESFilter = UniversalFilter(), only_cached: bool = True) \
		-> Iterator[tuple[Contest, School, Course, list[StudentEntry]]]:

		"""
			Iterates through the database, looking for courses accepted by the provided
			filter. If only_cached is True, courses with a None value (correspoding list of
			students hasn't yet been scraped) won't be returned.
		"""

		for contest, school, course_students in self.iterate_schools(filter, True):
			for course in course_students.keys():
				if filter.filter_courses(contest, school, course):
					if not only_cached or course_students[course] is not None:
						yield (contest, school, course, course_students[course])

	def iterate_students(self, filter: DGESFilter = UniversalFilter()) \
		-> Iterator[tuple[Contest, School, Course, StudentEntry]]:

		"""
			Iterates through the database, looking for students in courses accepted by the
			provided filter.
		"""

		for contest, school, course, students in self.iterate_courses(filter, True):
			for student in students:
				yield (contest, school, course, student)

