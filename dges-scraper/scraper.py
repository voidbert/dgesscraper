""" This module scrapes HTML from DGES websites """

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

from dgestypes import *

def __sanitize_html(html: str) -> str:
	"""
		Pieces of a webpage can contain untrimmed whitespace or whitespace characters other
		than space. This method removes those.
	"""
	return ''.join([ c for c in html.strip() if c not in ['\t', '\n'] ])

# +---------------------------------+
# | SCHOOL AND COURSE LIST SCRAPING |
# +---------------------------------+

def __option_list_remove_code(name: str) -> str:
	"""
		Auxiliary method for __scrape_option_list. In a school / course listing, options are
		preceded by their code. This method removes it, leaving only the human-readable name.
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
		Scrapes pairs of (code, name) from lists where the user chooses what page to visit
		next, namely, lists of schools and lists of courses in a school.
	"""

	# html5lib, though slower, is needed, because the website doesn't close its HTML tags
	soup = BeautifulSoup(html, 'html5lib')

	tag = soup.find('option')
	while tag is not None:
		yield (tag['value'], __option_list_remove_code(tag.get_text()))
		tag = tag.find_next('option')

def scrape_school_list(html: str, school_type: SchoolType) -> Iterator[School]:
	""" Scrapes a webpage containing a list of schools """

	for code, name in __scrape_option_list(html):
		yield School(school_type, code, name)

def scrape_course_list(html: str) -> Iterator[Course]:
	""" Scrapes a webpage containing a list of courses in a school """

	for code, name in __scrape_option_list(html):
		yield Course(code, name)

# +-----------------------+
# | STUDENT LIST SCRAPING |
# +-----------------------+

def __extract_id(id: str) -> int:
	""" Transforms a partial ID ( XXX(...)XX ) from a candidate list into the integer XXXXX """

	try:
		index = id.index('(...)')
		reduced = ''.join([ id[0:index], id[(index + 5):] ])
		return int(reduced)
	except:
		raise RuntimeError(f'Scraping error: Invalid ID number: "{id}"')

def __extract_decimal_grade(g: str) -> int:
	"""
		Extracts a grade in decimal format from the page of student entries
		Used for final and exam grades
	"""

	try:
		# Convert decimal separators from commas to points, and adjust the result to the
		# 0 - 2000 scale
		return int(float(g.replace(',', '.')) * 10)
	except:
		raise RuntimeError(f'Scraping error: Invalid decimal grade: "{g}"')

def __extract_integer_grade(g: str) -> int:
	"""
		Extracts a grade in integer format from the page of student entries
		Used for 12th and 10-11th grade grades
	"""

	try:
		# Multiply by 10 to adjust the result to the 0 - 2000 scale
		return int(g) * 10
	except:
		raise RuntimeError(f'Scraping error: Invalid integer grade: "{g}"')

def __scrape_student_list_row(row: BeautifulSoup) -> StudentEntry:
	""" Extracts student information from a row of a list of candidates """

	tds = row.find_all('td')
	if (len(tds) != 8):
		raise RuntimeError('Invalid student row: wrong number of columns')

	tds_text = list(map(lambda elem: __sanitize_html(elem.get_text()), tds))

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

	return StudentEntry(place, gov_id, name, option, grade, grade_exams, grade_12, grade_10_11)

def scrape_student_list(html: str) -> Iterator[StudentEntry]:
	"""
		Scrape a webpage containing a list of candidates to a course.
		This method may throw exception on invalid pages.
	"""

	# html5lib, though slower, is needed, because the website doesn't close its HTML tags
	soup = BeautifulSoup(html, 'html5lib')
	soup = soup.find_all(class_='caixa').pop().find('tbody') # Table with candidates

	# Search for a 'no candidates' message
	search = soup.find(string = lambda e: 'não teve candidatos' in e.text)
	if search is not None:
		return

	row = soup.find('tr')
	while row is not None:
		yield __scrape_student_list_row(row)
		row = row.find_next_sibling('tr')

