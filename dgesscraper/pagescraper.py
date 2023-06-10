"""
	@file pagescraper.py
	@package dgesscraper.pagescraper
	@brief This module scrapes individual HTML pages (school lists, course lists and student
	       lists) from DGES's website.

	@details Use the following methods to scrape different types of pages on the DGES website:

	- [scrape_school_list](@ref dgesscraper.pagescraper.scrape_school_list)
	- [scrape_course_list](@ref dgesscraper.pagescraper.scrape_course_list)
	- [scrape_candidate_list](@ref dgesscraper.pagescraper.scrape_candidate_list)
	- [scrape_accepted_list](@ref dgesscraper.pagescraper.scrape_accepted_list)
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
from bs4 import BeautifulSoup

from dgesscraper.types import *

def __sanitize_html(html: str) -> str:
	"""
		@brief Internal method to remove bad spacing from HTML
		@details Pieces of a webpage can contain untrimmed whitespace, or whitespace characters
		         other than space (like tabs, or line feeds). This method removes those.
	"""
	return ''.join([ c for c in html.strip() if c not in ['\t', '\n'] ])

def __detect_too_many_requests(html: str) -> str:
	""" @brief Raises a runtime error if a "too many requests" message is found on @p html """

	if 'número de pedidos' in html: # Translation: number of requests
		raise RuntimeError('Too many requests')

# +---------------------------------+
# | SCHOOL AND COURSE LIST SCRAPING |
# +---------------------------------+

def __option_list_remove_code(name: str) -> str:
	"""
		@brief Internal method that returns the human-readable name of an item in an option
		       list.
		@details Internal auxiliary function for
		         [__scrape_option_list](@ref dgesscraper.pagescraper.__scrape_option_list).
		         Every option name is preceded by a code, that this function removes.
	"""

	try:
		# Remove spacing that causes wrong school / course names
		name = __sanitize_html(name)
		# Remove text before the first dash (the code)
		return name[(name.index('-') + 2) : ]
	except:
		raise ValueError(f'Invalid school / course name: "{str}"')

def __scrape_option_list(html: str) -> Iterator[tuple[str, str]]:
	"""
		@brief Internal method that scrapes pages where the user chooses what page to visit
		       next
		@details This type of page is used to list schools per contest and courses per school
		@returns Iterates through pairs with the structure `(code, name)`
	"""

	__detect_too_many_requests(html)

	# html5lib, though slower, is needed, because the website doesn't close its HTML tags
	soup = BeautifulSoup(html, 'html5lib')

	empty = True
	tag = soup.find('option')
	while tag is not None:
		empty = False
		yield (tag['value'], __option_list_remove_code(tag.get_text()))
		tag = tag.find_next('option')

	if empty:
		raise RuntimeError('Invalid option (school / course) list')

def scrape_school_list(html: str, school_type: SchoolType) -> Iterator[School]:
	"""
		@brief Scrapes a webpage containing a list of schools
		@details The @p school_type won't affect the scraping process, but will be the type of
		         the returned schools, as there is no way to tell the type of schools from the
		         page's HTML.
	"""

	for code, name in __scrape_option_list(html):
		yield School(school_type, code, name)

def scrape_course_list(html: str) -> Iterator[Course]:
	""" @brief Scrapes a webpage containing a list of courses in a school """

	for code, name in __scrape_option_list(html):
		yield Course(code, name)

# +-------------------------+
# | CANDIDATE LIST SCRAPING |
# +-------------------------+

def __extract_id(id: str) -> int:
	"""
		@brief Internal method for transforming a partial ID (`XXX(...)XX`) from a candidate
		       list into the integer `XXXXX`.
	"""

	try:
		index = id.index('(...)')
		reduced = ''.join([ id[0:index], id[(index + 5):] ])
		return int(reduced)
	except:
		raise RuntimeError(f'Scraping error: Invalid ID number: "{id}"')

def __extract_decimal_grade(g: str) -> int:
	"""
		@brief Internal method for extracting a grade in decimal format from the page of
		       student entries.
		@details Used for final and exam grades.
	"""

	try:
		# Convert decimal separators from commas to points, and adjust the result to the
		# 0 - 2000 scale
		return int(float(g.replace(',', '.')) * 10)
	except:
		raise RuntimeError(f'Scraping error: Invalid decimal grade: "{g}"')

def __extract_integer_grade(g: str) -> int:
	"""
		@brief Internal method for extracting a grade in integer format from the page of
		       student entries.
		@details Used for 12th and 10-11th grade grades.
	"""

	try:
		# Multiply by 10 to adjust the result to the 0 - 2000 scale
		return int(g) * 10
	except:
		raise RuntimeError(f'Scraping error: Invalid integer grade: "{g}"')

def __scrape_candidate_list_row(row: BeautifulSoup, accepted: list[tuple[int, str]]) \
	-> StudentEntry:

	"""
		@brief Internal method for extraction of student information from a row in a list of
		       candidates

		@param row      The table row with the candidate information
		@param accepted The list of students accepted into the course
	"""

	tds = row.find_all('td')
	if (len(tds) != 8):
		raise RuntimeError('Invalid candidate row: wrong number of columns')

	tds_text = [ __sanitize_html(elem.get_text()) for elem in tds ]

	place = 0
	try:
		place = int(tds_text[0])
	except:
		raise RuntimeError(f'Scraping error: Invalid candidate number: {tds_text[0]}')

	gov_id = __extract_id(tds_text[1])
	name   = tds_text[2]
	grade  = __extract_decimal_grade(tds_text[3])

	option = 0
	try:
		option = int(tds_text[4])
	except:
		raise RuntimeError(f'Scraping error: Invalid candidate option: {tds_text[4]}')

	grade_exams = __extract_decimal_grade(tds_text[5])
	grade_12    = __extract_integer_grade(tds_text[6])
	grade_10_11 = __extract_integer_grade(tds_text[7])

	return StudentEntry(place, gov_id, name, option, grade, grade_exams, grade_12, grade_10_11, \
		(gov_id, name) in accepted)

def scrape_candidate_list(html: str, accepted: Iterator[tuple[int, str]] = iter(())) \
	-> Iterator[StudentEntry]:
	"""
		@brief Scrapes a webpage containing a list of candidates to a course.
		@details This method may throw exceptions on invalid pages.

		@param html The HTML source of the page
		@param accepted A list of the accepted students is needed to determine if a given
		candidate was or not accepted.
	"""

	__detect_too_many_requests(html)

	accepted = list(accepted)

	# html5lib, though slower, is needed, because the website doesn't close its HTML tags
	soup = BeautifulSoup(html, 'html5lib')
	soup = soup.find_all(class_='caixa').pop().find('tbody') # Table with candidates

	# Search for a 'no candidates' or 'no data' message
	search = soup.find(string = lambda e: 'não teve candidatos' in e.text or \
		'não contém dados' in e.text)
	if search is not None:
		return

	empty = True
	row = soup.find('tr')
	while row is not None:
		empty = False
		yield __scrape_candidate_list_row(row, accepted)
		row = row.find_next_sibling('tr')

	if empty:
		raise RuntimeError('Invalid candidate list')

def __scrape_accepted_list_row(row: BeautifulSoup) -> (int, str):
	"""
		@brief Internal method for extraction of information from a row in a list of accepted
		       students.

		@returns A pair with the student's ID
		         (see [__extract_id](@ref dgesscraper.pagescraper.__extract_id)) and their name.
	"""

	tds = row.find_all('td')
	if (len(tds) != 2):
		raise RuntimeError('Invalid accepted student row: wrong number of columns')

	return (__extract_id(tds[0].get_text()), __sanitize_html(tds[1].get_text()))

def scrape_accepted_list(html: str) -> Iterator[tuple[int, str]]:
	"""
		@brief Scrapes a webpage containing a list of students accepted to a course.
		@details This method may throw exceptions on invalid pages.
		@returns Iterates through pairs with the stucture `(ID, name)`.
	"""

	__detect_too_many_requests(html)

	# html5lib, though slower, is needed, because the website doesn't close its HTML tags
	soup = BeautifulSoup(html, 'html5lib')
	soup = soup.find_all(class_='caixa').pop().find('tbody') # Table with candidates

	# Search for a 'no placed students' or 'no data' message
	search = soup.find(string = lambda e: 'não teve colocados' in e.text or \
		'não contém dados' in e.text)
	if search is not None:
		return

	empty = True
	row = soup.find('tr')
	while row is not None:
		empty = False
		yield __scrape_accepted_list_row(row)
		row = row.find_next_sibling('tr')

	if empty:
		raise RuntimeError('Invalid list of accepted students')

