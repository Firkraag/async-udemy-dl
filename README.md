
# udemy-dl
## Goals

**A python script using asyncio to speedup downloading for Chinese udemy users who cannot watch video online because of China GFW**
## Thanks
   This project is based on [udemy-dl](https://github.com/r0oth3x49/udemy-dl) and adds asyncio support to it.
   
## ***Features***
- Asynchronously download course videos.
- Resume capability for a course video.
- Download specific chapter in a course (option: `-c / --chapter`).
- Download specific lecture in a chapter (option: `-l / --lecture`).
- Download chapter(s) by providing range in a course (option: `--chapter-start, --chapter-end`).
- Download lecture(s) by providing range in a chapter (option: `--lecture-start, --lecture-end`).
- Download course to user requested path (option: `-o / --output`).

## ***Requirements***

- Python>=3.7

- requests

- aiohttp

## ***Download async-udemy-dl***

You can download the latest version of async-udemy-dl by cloning the GitHub repository.

	git clone https://github.com/Firkraag/async-udemy-dl
	
## ***Usage***
This project uses cookies to authenticate with, so you must specify cookie file on commandline with option `-k cookies_file`. 
Please follow [Extracting Cookies / Request Headers](https://github.com/Firkraag/async-udemy-dl#extracting-cookies--request-headers) to save udemy cookies to files before using this script.

***Download a course***

    python async-udemy-dl.py -k COOKIES_FILE COURSE_URL
  
***Download course to a specific location***

    python async-udemy-dl.py -k COOKIES_FILE COURSE_URL -o "/path/to/directory/"
  
***Download specific chapter from a course***

    python async-udemy-dl.py -k COOKIES_FILE COURSE_URL -c NUMBER

***Download specific lecture from a chapter***

    python async-udemy-dl.py -k COOKIES_FILE COURSE_URL -c NUMBER -l NUMBER

***Download lecture(s) range from a specific chapter***

    python async-udemy-dl.py COURSE_URL -k COOKIES_FILE -c NUMBER --lecture-start NUMBER --lecture-end NUMBER

***Download chapter(s) range from a course***

    python async-udemy-dl.py COURSE_URL -k COOKIES_FILE --chapter-start NUMBER --chapter-end NUMBER

***Download specific lecture from chapter(s) range***

    python async-udemy-dl.py COURSE_URL -k COOKIES_FILE --chapter-start NUMBER --chapter-end NUMBER --lecture NUMBER

***Download lecture(s) range from chapter(s) range***

    python async-udemy-dl.py COURSE_URL -k COOKIES_FILE --chapter-start NUMBER --chapter-end NUMBER --lecture-start NUMBER --lecture-end NUMBER

## ***Extracting Cookies / Request Headers***

 - Login to your udemy account via browser.
 - Once you are logged in right click on page the search for option called **Inspect Element** and click on that.
 - Under that look for **Network Tab** and click on that. Under that **Network Tab** click on Requests type **XHR** .
 - Now click on **My Courses** in the Udemy navbar and refresh the page you will see some requests under **Network Tab**.
 - Right click on request links to **udemy.com/api-2.0/**. Simply copy **Request Headers** and save to text file.
 - The above guide is for ***Firefox*** users. ***Chrome*** Users can follow [guide by @lamlephamngoc](https://github.com/r0oth3x49/udemy-dl/issues/303#issuecomment-441345792).
 
 - Done run the async-udemy-dl against that text file it will start downloading the course.



## **Advanced Usage**

<pre><code>
Author: Firkraag (<a href="https://github.com/Firkraag/">Firkraag</a>)

usage: async-udemy-dl.py [-h] [-v] -k cookie_file [-d] [-o] [-c] [-l]
                   [--chapter-start] [--chapter-end] [--lecture-start]
                   [--lecture-end] course

A cross-platform python based utility to download courses from udemy for
personal offline use.

positional arguments:
  course            Udemy course.

General:
  -h, --help        Shows the help.
  -v, --version     Shows the version.

Authentication:
  -k , --cookies cookies_file    Cookies to authenticate with.

Advance:
  -d, --debug       output debug info to screen
  -o , --output     Download to specific directory, if not specified, download to current directory.
  -c , --chapter    Download specific chapter from course.
  -l , --lecture    Download specific lecture from chapter(s).
  --chapter-start   Download from specific position within course.
  --chapter-end     Download till specific position within course.
  --lecture-start   Download from specific position within chapter(s).
  --lecture-end     Download till specific position within chapter(s).

Example:
  python async-udemy-dl.py  COURSE_URL -k cookies.txt
</code></pre>

