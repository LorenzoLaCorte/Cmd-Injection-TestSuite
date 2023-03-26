#!/usr/bin/env python3

# Python script that calls the target application attached to this assignment, and shows a summary of the results. 
# Author: Lorenzo La Corte

import requests
import random
import os
from pathlib import Path

# 0 doesn't print anything, 1 prints only failure, 2 prints all
VERBOSITY = 1

# if I don't have permission to rm a file the program relies on random named files
RM_PERMISSION = True

WHOAMI_ORACLE = "lax"
MAX_RAND = 10**9
PORT = 9000

targets = ['./cmd-inj/ping.php']

cmd_inj_payloads = {
        'semicolon': ';whoami',
        'ampersand': '&whoami',
        'logical AND': '&&whoami',
        'pipe': '|whoami',
        'logical OR': '||whoami',
        'subshell': '$(whoami)',
}

arg_inj_payloads = {
        'exec flag': 'find-escapeshellcmd.php -exec whoami ;'
}

def testStep(attack, target, vuln_param, test_name, test_value, withHost=False, isBlind=False):
    rand_num = random.randrange(MAX_RAND) 
    cookies = { }
    headers = { }

    test_value = '1.1.1.1' + test_value if withHost else test_value

    if RM_PERMISSION:
        try: os.remove("Application/my_blind")
        except: pass
        test_value = test_value + f'>../my_blind' if isBlind else test_value
    else:
        test_value = test_value + f'>../{rand_num}' if isBlind else test_value

    params = {
        vuln_param: test_value
    }

    response = requests.get(f"http://localhost:{PORT}/{target}", params=params, cookies=cookies, headers=headers)

    if isBlind:
        resource = "my_blind" if RM_PERMISSION else rand_num
        response = requests.get(f"http://localhost:{PORT}/{resource}")

    test_result = not WHOAMI_ORACLE in response.text

    if VERBOSITY == 1 and not test_result: print(f"\u274c {attack}: {test_name}")
    elif VERBOSITY == 2: print("{} {}: {}".format("\u2705" if test_result else "\u274c", attack, test_name))
    return test_result


# For each page of the tested application, should design and implement a test step
def testSuite(targets):
    print(f"\u2699 Lax TestSuite \u2699")
    results = {}

    for subdir, files in targets.items(): 
        for file in files:
            allPassed = True
            target = subdir+'/'+file
            print(f"\nPage under test: {target}")
            
            # --- Command Injection --- #
            vuln_param = 'host'
            attack = "Command Injection"
            for test_name, test_value in cmd_inj_payloads.items():
                for withHost in [False, True]:
                    for isBlind in [False, True]:
                        test_name_opt = test_name + (', with host' if withHost else '') + (', blind' if isBlind else '')
                        testPassed = testStep(attack, target, vuln_param, test_name_opt, test_value, withHost=withHost, isBlind=isBlind)
                        results[(attack, test_name_opt)] = testPassed
                        if not testPassed: allPassed = False

            # --- Argument Injection --- #
            vuln_param = 'input'
            attack = "Argument Injection"
            for test_name, test_value in arg_inj_payloads.items():
                testPassed = testStep(attack, target, vuln_param, test_name, test_value)
                results[(attack, test_name)] = testPassed
                if not testPassed: allPassed = False
            
            if allPassed: print(f"\u2705 All tests have passed")


targets: dict[str, list[str]] = {}

basepath = Path('Application/')
subdirs = basepath.iterdir()

for subdir in subdirs:
    if subdir.is_file(): continue

    targets[subdir.name] = []
    for file in subdir.iterdir():
        if file.is_file():  targets[subdir.name].append(file.name)

# targets = {'cmd-inj':['ping-no-amp.php']}
testSuite(targets)