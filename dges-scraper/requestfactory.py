""" This module allows for generation of web requests to access DGES information """

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

from dgestypes import *
from requests import Request

def create_school_list_request(contest: Contest, school_type: SchoolType) -> Request:
	"""
		Generates a request for the page containing the list of of schools of a certain type in
		a given contest
	"""

	url = 'https://www.dges.gov.pt/coloc/{}/col{}listas.asp?CodR={}&action=2'.format(
		contest.year, contest.phase.value, school_type.to_server_code())
	return Request('GET', url)

def create_course_list_request(contest: Contest, school: School) -> Request:
	"""
		Generates a request for the page containing the list of courses that a given school
		provided during a contest
	"""

	url = 'https://www.dges.gov.pt/coloc/{}/col{}listaredir.asp'.format(
		contest.year, contest.phase.value)
	return Request('POST', url, data = {
		'CodEstab': school.code,
		'CodR': school.school_type.to_server_code(),
		'listagem': 'Lista+Ordenada+de+Candidatos' # Ordered list of candidates
	})

def create_student_list_request(contest: Contest, school: School, course: Course) -> Request:
	"""
		Generates a request for the page containing the list of candidates to a course in a
		school, in a given contest.
	"""

	# Note on fixed-value URL parameters:
	#
	# ids: Likely stands for ID start. The place of the first candidate on the page.
	# ide: Likely stands for ID end.   The place of the last  candidate on the page.
	# Mx:  Likely stands for maximum.  The maximum value of ids, this is, the number of
	#      candidates. It is used to determine if a "Next page" button should exist
	#
	# These parameters are set to show all candidates in the same page
	url = 'https://www.dges.gov.pt/coloc/{}/col{}listaser.asp?CodEstab={}&CodCurso={}&ids=1&ide=9999&Mx=0' \
		.format(contest.year, contest.phase.value, school.code, course.code)
	return Request('GET', url)

