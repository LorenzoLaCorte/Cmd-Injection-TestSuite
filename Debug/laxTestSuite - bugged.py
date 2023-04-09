#!/usr/bin/env python3

# Python script that calls the target application attached to this assignment, and shows a summary of the results. 
# Author: Lorenzo La Corte

from argparse import ArgumentParser, BooleanOptionalAction, Namespace
import multiprocessing
import subprocess
import requests
import random
import os
from pathlib import Path

MAX_RAND = 10**5

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

def testStep(attack, target, vuln_param, test_name, test_value, args, results, withHost=False, isBlind=False):
    rand_num = random.randrange(MAX_RAND) 
    cookies = { }
    headers = { }

    test_value = '1.1.1.1' + test_value if withHost else test_value

    if args.islocal:
        try: os.remove("Application/my_blind")
        except: pass
        test_value = test_value + f'>../my_blind' if isBlind else test_value
    else:
        test_value = test_value + f'>../{rand_num}' if isBlind else test_value

    params = {
        vuln_param: test_value
    }

    response = requests.get(f"http://localhost:{args.port}/{target}", params=params, cookies=cookies, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")

    if isBlind:
        resource = "my_blind" if args.islocal else rand_num
        response = requests.get(f"http://localhost:{args.port}/{resource}")

    test_result = not args.oracle in response.text

    if args.verbosity == 1 and not test_result: print(f"\u274c {attack}: {test_name}")
    elif args.verbosity == 2: print("{} {}: {}".format("\u2705" if test_result else "\u274c", attack, test_name))

    results[(attack, test_name)] = test_result


# For each page of the tested application, should design and implement a test step
def testSuite(args):
    print(f"\u2699 Lax TestSuite \u2699")

    targets: dict[str, list[str]] = {}
    basepath = Path(args.basepath)
    subdirs = basepath.iterdir()

    for subdir in subdirs:
        if subdir.is_file(): continue
        targets[subdir.name] = []
        for file in subdir.iterdir():
            if file.is_file():  targets[subdir.name].append(file.name)

    manager = multiprocessing.Manager()

    for subdir, files in targets.items(): 
        for file in files:
            # --- START CUNCURRENCY --- #
            processes: list[multiprocessing.Process] = []
            results: DictProxy = manager.dict()  # type: ignore

            target = subdir+'/'+file
            print(f"\nPage under test: {target}")
            
            # --- Command Injection --- #
            vuln_param = 'host'
            attack = "Command Injection"
            for test_name, test_value in cmd_inj_payloads.items():
                for withHost in [False, True]:
                    for isBlind in [False, True]:
                        test_name_opt = test_name + (', with host' if withHost else '') + (', blind' if isBlind else '')

                        if multiprocessing and args.cuncurrency:
                            process = multiprocessing.Process(target=testStep, 
                                                            args=(attack, target, vuln_param, test_name_opt, test_value, args, results, withHost, isBlind))
                            processes.append(process)
                            process.start()
                        else:
                            testStep(attack, target, vuln_param, test_name_opt, test_value, args, results, withHost=withHost, isBlind=isBlind)

            # --- Argument Injection --- #
            vuln_param = 'input'
            attack = "Argument Injection"
            for test_name, test_value in arg_inj_payloads.items():
                if multiprocessing and args.cuncurrency:
                    process = multiprocessing.Process(target=testStep, 
                                                    args=(attack, target, vuln_param, test_name_opt, test_value, args, results))
                    processes.append(process)
                    process.start()
                else:
                    testStep(attack, target, vuln_param, test_name, test_value, args, results)

            # --- END CUNCURRENCY (SYNC) --- #
            for process in processes:
                process.join()

            if all(results.values()): print(f"\u2705 All tests have passed")


def main() -> None:
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("--basepath", type=str, default="Application/")
    # 0 doesn't print anything, 1 prints only failure, 2 prints all
    parser.add_argument("--verbosity", type=int, default=1)
    # if I don't have permission to rm a file the program relies on random named files
    parser.add_argument("--islocal", default=True, action=BooleanOptionalAction)
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--oracle", type=str, default=subprocess.getoutput("whoami"))
    parser.add_argument("--cuncurrency", default=True, action=BooleanOptionalAction)
    args: Namespace = parser.parse_args()

    # subprocess.run(["cd",f"{args.basepath}", ";",  "php", "-S", f"localhost:{args.port}", "&"])
    testSuite(args)

if __name__ == "__main__":
    main()
