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

from typing import Iterator, Annotated
from bs4 import BeautifulSoup

from dgestypes import *

def __sanitize_html(html: str) -> str:
	"""
		Pieces of a webpage can contain untrimmed whitespace or whitespace characters other
		than space. This method removes those.
	"""
	return ''.join([ c for c in html.strip() if c not in ['\t', '\n'] ])

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

