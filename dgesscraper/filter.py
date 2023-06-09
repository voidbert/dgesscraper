"""
	@file filter.py
	@package dgestypes.filters
	@brief This module defines an abstract base class for filtering what to scrape in DGES's
	       website or what to look up in a database.
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

from dgesscraper.types import *

class DGESFilter(ABC):
	"""
		@brief An abstract base class used to filter the DGES website or database
		@details A filter can be used to:

		- Restrict what pages are scraped in [sitescraper](@ref dgesscraper.sitescraper);
		- Restrict what parts of a [Database](@ref dgesscraper.database.Database) are iterated
		through.

		Note that you can't filter students per course, as those are all in the same webpage.
	"""

	@abstractmethod
	def list_contests(self) -> Iterator[Contest]:
		"""
			@brief This method returns all the contests accepted by this filter.

			@details For database iteration, returning `None` will cause the whole database
			to be iterated through. However, that's not a possibility when scraping,
			because there's no way of knowing the list of available contests.
		"""

	@abstractmethod
	def filter_schools(self, contest: Contest, school: School) -> bool:
		"""
			@brief Given a contest and a school, this method determines whether the
			corresponding list of courses should be considered.

			@details If `False`, consequently, the lists of candidates to those courses won't
			be considered.
		"""

	@abstractmethod
	def filter_courses(self, contest: Contest, school: School, course: Course) -> bool:
		"""
			@brief Given a contest, a school and a course, this method determines whether the
			correponding list of candidates should be considered.
		"""

class UniversalFilter(DGESFilter):
	"""
		@brief A filter that scrapes all courses and all schools, for a given list of years.
		@details Note that scraping the whole website will be a very lengthy process.
	"""

	def __init__(self, years: list[int] = None):
		"""
			@brief Creates an `UniversalFilter`
			@details

			For website scraping, a list of years must be provided. For example:
			`UniversalFilter(list(range(2018, 2023)))`. However, that is not needed for
			database iteration: `UniversalFilter()`.
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

