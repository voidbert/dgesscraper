"""
	This module defines an abstract base class for filtering what to scrape in DGES's website
	or what to look up in a database.
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

from typing import Iterator
from abc import abstractmethod, ABC

from dgestypes import *

class DGESFilter(ABC):
	"""
		An abstract base class that is used to filter what web pages need to scraped (to
		avoid scraping the whole website, when that is not needed). Note that you can't filter
		students per course, as those are all in the same webpage.
	"""

	@abstractmethod
	def list_contests(self) -> Iterator[Contest]:
		"""
			This method returns an iterator of contests to be scraped. When scraping, there
			is no way to know what contest years the server provides. Therefore, an iterator
			of contests is needed (instead of a boolean function to determine whether or not
			to scrape the contest).

			For website scraping, this must return an iterator of contests. However, for
			database iteration, if this method returns None, all contests in the database
			will be processed (as if there were no filter).
		"""

	@abstractmethod
	def filter_schools(self, contest: Contest, school: School) -> bool:
		"""
			Given a contest and a school, this method determines if the list of courses
			that school provides should be scraped. If false, consequently, the lists of
			candidates to those courses won't be scraped.
		"""

	@abstractmethod
	def filter_courses(self, contest: Contest, school: School, course: Course) -> bool:
		"""
			Given a contest, a school and a course, this method determines if the list of
			candidates to that course should be scraped.
		"""

class UniversalFilter(DGESFilter):
	"""
		A filter that scrapes all courses and all schools, for a given list of years (there is
		no way to know all the years stored on the server, so you need to provide it yourself).

		Scraping the whole website will be a very lengthy process.
	"""

	def __init__(self, years: list[int] = None):
		"""
			If this filter is only used for database searching, the list of years can be
			None, and all contests in the database will be considered.
		"""

		self.years = years

	def list_contests(self) -> Iterator[Contest]:
		# Cartesian product of years and set of all phases
		def cartesian():
			for year in self.years:
				for phase in [ Phase.FIRST, Phase.SECOND, Phase.THIRD ]:
					yield Contest(year, phase)


		if self.years is None:
			return None
		else:
			return cartesian()

	def filter_schools(self, contest: Contest, school: School) -> bool:
		return True

	def filter_courses(self, contest: Contest, school: School, course: Course) -> bool:
		return True

