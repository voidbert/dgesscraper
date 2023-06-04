"""
	This module contains a class for gracefully exiting the program while a ThreadPoolExecutor
	is active.
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

class GracefulExit:
	"""
		This class sets signal handlers such that, if the program is terminated, all tasks
		currently running on the associated ThreadPoolExecutor will finish, and no more tasks
		will start. After that, the program will be exited.

		It must be used with a with statement from the main thread.
	"""

	__EXIT_SIGNALS = [ signal.SIGINT, signal.SIGTERM, signal.SIGTSTP, signal.SIGQUIT ]

	def __init__(self, executor: ThreadPoolExecutor):
		self.executor            = executor
		self.old_handlers        = {}
		self.must_reset_handlers = True

	def __ignore_signal(self, sig, frame):
		""" After the shutdown process begins, ignore termination signals """

	def __handle_signal(self, sig, frame):
		""" Internal method for handling signals """

		print('\nOrdered to stop. Shutting down.')

		self.executor.shutdown(wait = False, cancel_futures = True)

		for sig in GracefulExit.__EXIT_SIGNALS:
			signal.signal(sig, self.__ignore_signal)
		self.must_reset_handlers = False

		sys.exit(0)

	def __enter__(self):
		"""
			Stores previous signal handlers to restore them if the program is not terminated,
			and then set the new handlers
		"""

		for sig in GracefulExit.__EXIT_SIGNALS:
			self.old_handlers[sig] = signal.getsignal(sig)
			signal.signal(sig, self.__handle_signal)

	def __exit__(self, exc_type, exc_value, traceback):
		""" Restores the previous signal handlers if a signal wasn't captured """

		if self.must_reset_handlers:
			for sig in GracefulExit.__EXIT_SIGNALS:
				signal.signal(sig, self.old_handlers[sig])


