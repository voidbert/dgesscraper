"""
	@file gracefulexit.py
	@package dgesscraper.gracefulexit
	@brief This module contains a class for gracefully exiting the program while a
	       `ThreadPoolExecutor` is active.
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

from concurrent.futures import ThreadPoolExecutor
import signal
import sys

from dgesscraper.database import Database

class GracefulExit:
	"""
		@brief If the program is terminated, this class will let the currently-running tasks
		on the `ThreadPoolExecutor` terminate, stopping the program after that.

		@anchor classdesc
		@details This class is meant to be used with a `with` statement:

		```
		with ThreadPoolExecutor() as executor:
			with GracefulExit(executor, database, database_path) as graceful:
		```

		It must be used from the main thread, as signal handlers need to be set.

		If the program is terminated, after not letting the executor run any more tasks, a
		provided database can be cached to disk.
	"""

	## All signals that need to be handled as program termination
	__EXIT_SIGNALS = [ signal.SIGINT, signal.SIGTERM, signal.SIGTSTP, signal.SIGQUIT ]

	def __init__(self, executor: ThreadPoolExecutor, database: Database, database_path: str):
		"""
			@brief See [the class description](@ref classdesc)

			@param executor The `ThreadPoolExecutor`
			@param database The [Database](@ref dgesscraper.database.Database) to be saved if
			the program is told to terminate.
			@param database_path Can be `None`, so that the database isn't cached
		"""

		## @brief `ThreadPoolExecutor`
		self.executor            = executor
		## @brief A dictionary that associates signals with their handlers, before this class
		## sets its own
		self.old_handlers        = {}
		## @brief The [Database](@ref dgesscraper.database.Database) to be saved if the program
		## is told to terminate.
		self.database            = database
		## @brief Where to save the database in case of termination
		self.database_path       = database_path
		## @brief Whether the old signal handlers should be restored
		## @details Becomes `False` if the program is terminated.
		self.must_reset_handlers = True

	def __ignore_signal(self, sig, frame):
		"""
			@brief After the shutdown process begins, this internal method is used to ignore
			termination signals
		"""

	def __handle_signal(self, sig, frame):
		""" @brief Internal method for handling signals before the shutdown process begins """

		print('\nOrdered to stop. Shutting down ...')

		self.executor.shutdown(wait = False, cancel_futures = True)

		for sig in GracefulExit.__EXIT_SIGNALS:
			signal.signal(sig, self.__ignore_signal)
		self.must_reset_handlers = False

		print('Saving database ...')
		self.database.to_cache(self.database_path)

		sys.exit(0)

	def __enter__(self):
		"""
			@brief Internal method called in the beginning of the `with` statement.
			@details Stores previous signal handlers to restore them if the program is not
			terminated, and then sets the new handlers.
		"""

		for sig in GracefulExit.__EXIT_SIGNALS:
			self.old_handlers[sig] = signal.getsignal(sig)
			signal.signal(sig, self.__handle_signal)

	def __exit__(self, exc_type, exc_value, traceback):
		"""
			@brief Internal method called in the end of the `with` statement.
			@details Restores the previous signal handlers if a signal wasn't captured.
		"""

		if self.must_reset_handlers:
			for sig in GracefulExit.__EXIT_SIGNALS:
				signal.signal(sig, self.old_handlers[sig])


