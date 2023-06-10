# DGES scraper

`dges-scraper` is a web scraper for extracting information from the Portuguese upper education
access contest results, available in `https://dges.gov.pt/coloc/[year]/`.

It is written in Python and licensed under the [Apache License](./LICENSE). Please be mindful of
other's privacy and excessive server load while using this software.

## Installation

Install the `dgesscraper` package with:

```shell
$ pip install .
```

Documentation can be generated with:

```shell
$ doxygen
```

Doxygen >=1.9.6 is recommended, for correct parsing of class attributes.

## Basic usage

### Website scraping

If you're developing any program using DGES data, know that the website scraping process is **not
meant for the end user**. You, the programmer, should generate the database yourself once, and then
use the generated database file to analyse the data.

Database generation from website data:

```python
from dgesscraper.types import *
from dgesscraper.database import Database
from dgesscraper.filter import UniversalFilter
from dgesscraper.sitescraper import scrape_website

filter = UniversalFilter([2021, 2022]) # Scrape all phases from 2021 and 2022
database = scrape_website(filter, 4, 'database.pickle')
```

This example uses 4 threads and saves the database to `database.pickle`. You can set the database
path to `None`, so that no caching is performed. Also, you can read about custom filters ahead, to
scrape only particular parts of the website.

Be careful with high numbers of threads, because the server will limit the number of requests you
can issue, returning error pages that cannot be scraped, leading to many errors.

### Database manipulation

#### Loading and saving to disk

```python
from dgesscraper.database import Database
database = Database.from_file('database.pickle')
database.to_file('copy.pickle')
```

There are easier and more efficient ways to copy files, but this is just an example.

#### Database structure

A database is internally represented using a nested dictionary, as data is small enough to fit in
memory. It can be accessed the following way:

```python
	database.dictionary[contest][school][course] # Is a list of student entries (candidates)
```

At any point accessing the nested dictionary, you can get a `None` value. That means that page
wasn't yet scraped (for example, the filter used in scraping doesn't allow it).

#### Database iteration

There are many functions for iterating though a database. Generate the project's documentation with
`doxygen` and read about the `database` module. Here's an example on how to iterate through
schools:

```python
for contest, school, course_students in database.iterate_schools():
	print(school)
```

## Advanced usage

### Using filters

Filters are useful tools for limiting what to scrape from DGES's website, or what data to iterate
through in a database.

```python
from dgesscraper.types import *
from dgesscraper.database import Database
from dgesscraper.filter import DGESFilter

# This filter looks for all candidates to an engineering course in Aveiro's University
class CustomFilter(DGESFilter):
	def list_contests(self): # All contests in the database
		return None

	def filter_schools(self, contest, school): # 0300 is UAveiro's code
		return school.code == '0300'

	def filter_courses(self, contest, school, course):
		return 'Engenharia' in course.name

filter = CustomFilter()
database = Database.from_file('database.pickle')
for contest, school, course, student in database.iterate_students(filter):
	print(student.name)
```

For limiting the scope of website scraping, the `list_contests` can't return `None`, as an actual
iterator though contests is expected:

```python
import dgesscraper.sitescraper as sitescraper

class CustomFilter(DGESFIlter):
	def list_contests(self): # Only second and third phases of 2022
		yield Contest(2022, Phase.SECOND)
		yield Contest(2022, Phase.THIRD)

	...

database = sitescraper.scrape_website(CustomFilter(), 8, 'database.pickle')
```

Keep the `UniversalFilter` mentioned above in mind, as it can be very useful.

### Scraping individual pages

Scraping individual pages consists of three steps:

- Getting the page's URL. That can be with the `requestfactory` module.

- Issuing a web request. Use a library of your choice. This project uses
  [`requests`](https://pypi.org/project/requests/).

- Scraping the HTML response from the server. That can be done with the `pagescraper` module.

Generate the project's documentation with `doxygen` and check the docs for those modules.

