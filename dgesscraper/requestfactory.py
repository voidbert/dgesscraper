"""
	@file requestfactory.py
	@package dgesscraper.requestfactory
	@brief This module allows for generation of web requests to access DGES information
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

from dgesscraper.types import *
from requests import Request

def create_school_list_request(contest: Contest, school_type: SchoolType) -> Request:
	"""
		@brief Generates a request for the page containing the list of schools of a certain
		       type in a given contest
	"""

	url = f'https://www.dges.gov.pt/coloc/{contest.year}/col{contest.phase.value}listas.asp?' \
		f'CodR={school_type.to_server_code()}&action=2'
	return Request('GET', url)

def create_course_list_request(contest: Contest, school: School) -> Request:
	"""
		@brief Generates a request for the page containing the list of courses that a given
		       school provided during a contest
	"""

	url = f'https://www.dges.gov.pt/coloc/{contest.year}/col{contest.phase.value}listaredir.asp'
	return Request('POST', url, data = {
		'CodEstab': school.code,
		'CodR': school.school_type.to_server_code(),
		'listagem': 'Lista+Ordenada+de+Candidatos' # Ordered list of candidates
	})

def create_candidate_list_request(contest: Contest, school: School, course: Course) -> Request:
	"""
		@brief Generates a request for the page containing the list of candidates to a course
		       in a school, in a given contest.
	"""

	# Note on fixed-value URL parameters:
	#
	# ids: Likely stands for ID start. The place of the first candidate on the page.
	# ide: Likely stands for ID end.   The place of the last  candidate on the page.
	# Mx:  Likely stands for maximum.  The maximum value of ids, this is, the number of
	#      candidates. It is used to determine if a "Next page" button should exist
	#
	# These parameters are set to show all candidates in the same page
	url = f'https://www.dges.gov.pt/coloc/{contest.year}/col{contest.phase.value}listaser.asp?' \
		f'CodEstab={school.code}&CodCurso={course.code}&ids=1&ide=9999&Mx=0'
	return Request('GET', url)

def create_accepted_list_request(contest: Contest, school: School, course: Course) -> Request:
	"""
		@brief Generates a request for the page containing the list of students accepted into a
		       course in a school, in a given contest.
	"""

	url = f'https://www.dges.gov.pt/coloc/{contest.year}/col{contest.phase.value}listacol.asp'
	return Request('POST', url, data = {
		'CodCurso': course.code,
		'CodEstab': school.code,
		'CodR': school.school_type.to_server_code(),
		'search': 'Continuar'
	})

