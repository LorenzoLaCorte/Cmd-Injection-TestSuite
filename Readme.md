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
- if the page is working correctly (e.g., for ping pages, that it pings the correct host)
- if the page is vulnerable to command injection.

The test case should at least take the following attacks (and its variants) into consideration:

- Command Injection (via ";", other command separators, and subshells)
- Argument Injection
- Blind Command Injection [BONUS - not mandatory]

You can inject any command you want. My suggestion is to go with "whoami", which has an easier (and more recognizable) output.

You will notice that some pages (e.g., ping*.php ones) are slow to test. If you want, you can try to make the test more efficient, for example by adding concurrency (e.g., via the asyncio module) *[BONUS - not mandatory]* 

If you want to go above and beyond, fix the vulnerabilities in the attached application, and also hand in your fixed code. *[BONUS 2 - also not mandatory]*


## What to deliver

- The code of your test steps
- Instructions (or a run.sh script) to launch your test suite. *[If you have a complex CLI program (which you really shouldn't have)]*
- A text file with any interesting additional information regarding your tests *[Optional]*
- The updated code for the attached application *[If you implemented BONUS 2]*


Starting from scratch might be harder for some of you, and that's perfectly fine. 
I attached the sample test step that I showed during the lesson to help you with a starting point.

WARNING: the sample test is neither exhaustive, nor entirely correct. 
It will require improvements to be a good test suite (for example, covering all pages and taking additional corner cases into consideration, or cleaning the output).