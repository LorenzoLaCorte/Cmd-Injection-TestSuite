# Instructions

For this assignment, you will start building a minimal test suite for our environment. 
This assignment will then become a module of a larger testing suite, that we will build and organize in the next assignments.

The ideal test suite should be implemented in Python, and be accessible via a command line.
Remember that, to perform HTTP calls in Python, you can use the requests module.
Also, you can use curl converter to convert cURL commands into Python (or any other language). 
This is particularly useful if you use the "Copy as cURL" functionality from your browser.


## What to do
You should create a Python script that calls the target application attached to this assignment, and shows a summary of the results. 

For each page of the tested application, you should design and implement a test step (which we will integrate in a larger test suite in the upcoming assignments) that checks:
- if the page is working correctly (e.g., for ping pages, that it pings the correct host) **TODO**
- if the page is vulnerable to command injection.

The test case should at least take the following attacks (and its variants) into consideration:

- Command Injection (via ";", other command separators, and subshells)
- Argument Injection
- Blind Command Injection [BONUS - not mandatory]

You can inject any command you want. My suggestion is to go with "whoami", which has an easier (and more recognizable) output.

You will notice that some pages (e.g., ping*.php ones) are slow to test. If you want, you can try to make the test more efficient, for example by adding concurrency (e.g., via the asyncio module) *[BONUS - not mandatory]* **TODO**

If you want to go above and beyond, fix the vulnerabilities in the attached application, and also hand in your fixed code. *[BONUS 2 - also not mandatory]* **TODO**


## What to deliver

- The code of your test steps
- Instructions (or a run.sh script) to launch your test suite. *[If you have a complex CLI program (which you really shouldn't have)]*
- A text file with any interesting additional information regarding your tests *[Optional]*
- The updated code for the attached application *[If you implemented BONUS 2]*


Starting from scratch might be harder for some of you, and that's perfectly fine. 
I attached the sample test step that I showed during the lesson to help you with a starting point.

WARNING: the sample test is neither exhaustive, nor entirely correct. 
It will require improvements to be a good test suite (for example, covering all pages and taking additional corner cases into consideration, or cleaning the output).

## Particular Stuff

### Verbosity Level
0 doesn't print anything, 1 prints only failure (default), 2 prints all
**TODO** set as parameter

### RM Permission Flag
if I don't have permission to rm a file the program relies on random named files
Default behaviour is having permissions.
**TODO** set as parameter


# How to Use
Run the php server (`docker-compose up`)
Run the script (`python3 laxTestSuite.py`)


## Concurrent Version
Image used: https://github.com/richarvey/nginx-php-fpm

To build the infrastructure:
docker build -t rich_fpm_server .
docker run rich_fpm_server

To get the running container IP: 
docker ps 
docker inspect <container_running> | grep IPAddress

IP address will usually be 172.17.0.2, so this is the default in my script, but in the case it is something else, you will have to update it.

Then we can find our application on:
http://<IP>/path_to_file

For example:
http://172.17.0.2/not-vuln/ping-escapeshellcmd.php?host=1.1.1.1