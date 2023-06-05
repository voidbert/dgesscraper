"""
	This module contains methods to go through the whole DGES website, storing collected data
	in a database.
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

from concurrent.futures import ThreadPoolExecutor, as_completed
from requests import Request, Session
from tqdm import tqdm
from sys import stderr

from dgestypes import *
from dgesfilter import DGESFilter
from gracefulexit import GracefulExit
import requestfactory
import scraper

def __perform_request(request: Request):
	""" Performs a web request in a new session, raising a runtime error in case of failure """

	session = Session()
	resp = session.send(session.prepare_request(request))

	if resp.status_code == 200:
		return resp.text
	else:
		raise RuntimeError('Failed to access the following URL: {}'.format(resp.url))

# +------------------+
# | CONTEST SCRAPING |
# +------------------+

def __try_scrape_contest(database: Database, contest: Contest) -> Contest:
	"""
		Scrapes a contest (list of schools, merging universities and polytechnical schools) and
		saves it to the database.

		In case of error, it's printed to stderr and None is returned. Otherwise, the provided
		contest is returned.

		This method should be run on the multiple threads of an executor.
	"""

	try:
		contest_schools = { }

		for t in SchoolType:
			request = requestfactory.create_school_list_request(contest, t)
			html = __perform_request(request)

			for school in scraper.scrape_school_list(html, t):
				contest_schools[school] = None

		database[contest] = contest_schools
		return contest
	except:
		print(f'Failed to scrape contest {contest}', file = stderr)

def __scrape_contests(filter: DGESFilter, executor: ThreadPoolExecutor, database: Database) \
	-> list[Contest]:

	"""
		Scrapes all contests (lists of schools) requested by a filter, merging universities and
		polytechnical schools, and saves those lists to the database. A progress bar is shown
		while that is happening.

		A list of the successfully scraped contests is returned.
	"""

	# Only scrape the uncached contests. Cached contests are considered successfully scraped
	all_contests = filter.list_contests()
	to_scrape, successful = [], []
	for contest in filter.list_contests():
		(to_scrape, successful)[is_in_database(database, contest)].append(contest)

	if not to_scrape:
		print('All needed contests are already cached')
		return successful

	# Scrape all contests (school lists) that aren't cached
	with tqdm(total = len(to_scrape), unit = ' pages') as progress_bar:
		futures = [ executor.submit(__try_scrape_contest, database, c) for c in to_scrape ]
		for future in as_completed(futures):
			progress_bar.update(1)

			if future.result():
				successful.append(future.result()) # Successful scrape

	return successful

# +-----------------+
# | SCHOOL SCRAPING |
# +-----------------+

def __try_scrape_school(database: Database, contest: Contest, school: School) -> (Contest, School):
	"""
		Scrapes a school (list of courses) and saves it to the database.

		In case of error, it's printed to stderr and None is returned. Otherwise, the provided
		contest / school pair is returned.

		This method should be run on the multiple threads of an executor.
	"""

	try:
		school_courses = { }

		request = requestfactory.create_course_list_request(contest, school)
		html = __perform_request(request)

		for course in scraper.scrape_course_list(html):
			school_courses[course] = None

		database[contest][school] = school_courses
		return (contest, school)
	except:
		print(f'Failed to scrape school {contest} / {school}', file = stderr)

def __scrape_schools(filter: DGESFilter, executor: ThreadPoolExecutor, database: Database, \
	successful_contests: list[Contest]) -> list[(Contest, School)]:

	"""
		Scrapes all schools (lists of courses) requested by a filter, and saves those lists
		to the database. A progress bar is shown while that is happening.

		The list of successfully scraped schools (associated with a contest) is returned.
	"""

	# Only scrape the uncached schools. Cached schools are considered successfully scraped
	to_scrape, successful = [], []
	for c in successful_contests:
		for s in database[c]:
			if filter.filter_schools(c, s):
				(to_scrape, successful)[is_in_database(database, c, s)].append((c, s))

	if not to_scrape:
		print('All needed schools are already cached')
		return successful

	# Scrape all schools (course lists) that aren't cached
	with tqdm(total = len(to_scrape), unit = ' pages') as progress_bar:
		futures = [ executor.submit(__try_scrape_school, database, contest, school) \
			for contest, school in to_scrape ]

		for future in as_completed(futures):
			progress_bar.update(1)

			if future.result():
				successful.append(future.result()) # Successful scrape

	return successful

# +-----------------+
# | COURSE SCRAPING |
# +-----------------+

def __try_scrape_course(database: Database, contest: Contest, school: School, course: Course) \
	-> (Contest, School, Course):

	"""
		Scrapes a course (list of candidates) and saves it to the database.

		In case of error, it's printed to stderr and None is returned. Otherwise, the provided
		(contest, school, course) tuple is returned.

		This method should be run on the multiple threads of an executor.
	"""

	try:
		request = requestfactory.create_student_list_request(contest, school, course)
		html = __perform_request(request)
		database[contest][school][course] = list(scraper.scrape_student_list(html))
		return (contest, school, course)
	except:
		print(f'Failed to scrape course {contest} / {school} / {course}', file = stderr)

def __scrape_courses(filter: DGESFilter, executor: ThreadPoolExecutor, database: Database, \
	successful_schools: list[(Contest, School)]) -> list[(Contest, School, Course)]:

	"""
		Scrapes all courses (lists of candidates) requested by a filter, and saves those lists
		to the database. A progress bar is shown while that is happening.

		The list of successfully scraped courses (associated with their schools and contests)
		is returned.
	"""

	# Only scrape the uncached courses. Cached courses are considered successfully scraped
	to_scrape, successful = [], []
	for contest, school in successful_schools:
		for course in database[contest][school]:
			if filter.filter_courses(contest, school, course):
				(to_scrape, successful)[is_in_database(database, contest, school, course)]\
					.append((contest, school, course))

	if not to_scrape:
		print('All needed courses are already cached')
		return successful

	# Scrape all courses (student lists) that aren't cached
	with tqdm(total = len(to_scrape), unit = ' pages') as progress_bar:
		futures = [ executor.submit(__try_scrape_course, database, contest, school, course) \
			for contest, school, course in to_scrape ]

		for future in as_completed(futures):
			progress_bar.update(1)

			if future.result():
				successful.append(future.result()) # Successful scrape

	return successful



def scrape_website(filter: DGESFilter, workers: int, database_path: str = None) -> Database:
	"""
		This method builds a database by scraping all pages requested by the filter

		Parameters
		----------

		filter: DGESFilter
			The filter that will determine which pages will be downloaded and scraped
		workers: int
			The number of parallel workers. If None, the default value in
			ThreadPoolExecutor will be used.
		database_path:
			The path to the database file. If None, the database won't be cached. If the
			file doesn't exist, it'll be created.
	"""

	database = attempt_read_database(database_path)

	with ThreadPoolExecutor(max_workers = workers) as executor:
		with GracefulExit(executor, database, database_path) as graceful:

			print('Getting lists of schools ...')
			successful_contests = __scrape_contests(filter, executor, database)

			print('\nGetting lists of courses ...')
			successful_schools = \
				__scrape_schools(filter, executor, database, successful_contests)

			print('\nGetting lists of students ...')
			__scrape_courses(filter, executor, database, successful_schools)

	print('Saving database ...')
	attempt_write_database(database, database_path)
	return database

