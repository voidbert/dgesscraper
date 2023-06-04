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

from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys

from dgestypes import *
from dgesfilter import DGESFilter
from gracefulexit import GracefulExit

def __thread_work(number: int):
	print(f'Number: {number}')
	sleep(5)

def scrape_website(filter: DGESFilter, workers: int) -> Database:
	""" This method builds a database by scraping all pages requested by the filter """

	with ThreadPoolExecutor(max_workers = workers) as executor:
		with GracefulExit(executor) as graceful:
			futures = [ executor.submit(__thread_work, c) for c in range(6) ]
			for _ in as_completed(futures):
				pass

