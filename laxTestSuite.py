#!/usr/bin/env python3

# Python script that calls the target application attached to this assignment, and shows a summary of the results. 
# Author: Lorenzo La Corte

from argparse import ArgumentParser, BooleanOptionalAction, Namespace
import subprocess
import time
import uuid
import requests
import os
from pathlib import Path
import asyncio

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


def BeforeAll(args):
    if args.nginx: 
        args.oracle = "www-data"
    else: 
        args.oracle = subprocess.getoutput("whoami")

    # if args.nginx:
    #     cmd = ["docker-compose", "up"]
    #     cwd = os.getcwd() + ('/NginxServer')
    #     subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    # else:
    #     cmd = ["php", "-S", f"localhost:{args.port}"]
    #     cwd = os.getcwd() + ('/Application' if args.fixed_app else '/ApplicationFixed')
    #     # os.system(f"cd Application && php -S localhost:{args.port} &")
    #     # subprocess.run(f"cd Application && php -S localhost:{args.port}", shell=True)
    #     subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

    # time.sleep(2)


def CollectTargets(args):
    if args.fixed_app:
        args.basepath = "ApplicationFixed"
    else:
        args.basepath = "Application"

    targets: dict[str, list[str]] = {}
    basepath = Path(args.basepath)
    subdirs = basepath.iterdir()

    for subdir in subdirs:
        if subdir.is_file(): continue
        targets[subdir.name] = []
        for file in subdir.iterdir():
            if file.is_file():  targets[subdir.name].append(file.name)
    return targets


def AfterEach(rand_num):
    try: os.remove(f"Application/{rand_num}.tmp")
    except: pass

async def functionalStep(target, args):
    if 'echo-' in target:
        vuln_param = 'name'
        test_value = oracle = 'my_message'
    elif 'echo' or 'no-output' in target:
        test_result = True
        print("{} {}".format("\u2705" if test_result else "\u274c", "Functional Verifification"))
        return test_result
    elif 'ping' in target:
        vuln_param = 'host'
        test_value = oracle = '1.1.1.1'
    elif 'find' in target:
        vuln_param = 'input'
        test_value = oracle = target.split("/")[1]
    else:
        raise Exception(f"Error: page not recognized")

    params = {
        vuln_param: test_value
    }

    response = requests.get(f"http://localhost:{args.port}/{target}", params=params)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")

    test_result = oracle in response.text

    print("{} {}".format("\u2705" if test_result else "\u274c", "Functional Verifification"))

    return test_result

async def testStep(attack, target, vuln_param, test_name, test_value, args, withHost=False, isBlind=False):
    rand_num = uuid.uuid4()
    cookies = { }
    headers = { }

    test_value = '1.1.1.1' + test_value if withHost else test_value
    test_value = test_value + f'>../{rand_num}.tmp' if isBlind else test_value

    params = {
        vuln_param: test_value
    }

    response = requests.get(f"http://localhost:{args.port}/{target}", params=params, cookies=cookies, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")

    if isBlind:
        response = requests.get(f"http://localhost:{args.port}/{rand_num}.tmp")

    test_result = not args.oracle in response.text

    if args.verbosity == 1 and not test_result: print(f"\u274c {attack}: {test_name}")
    elif args.verbosity == 2: print("{} {}: {}".format("\u2705" if test_result else "\u274c", attack, test_name))

    AfterEach(rand_num)

    return test_result


# For each page of the tested application, should design and implement a test step
async def testSuite(args):
    print(f"\u2699 Lax TestSuite \u2699")

    targets = CollectTargets(args)

    for subdir, files in targets.items(): 
        for file in files:
            # --- START CONCURRENCY --- #
            tasks = []
            loop = asyncio.get_event_loop()

            target = subdir+'/'+file
            print(f"\nPage under test: {target}")
            
            # --- Functional Step --- #
            tasks.append(loop.create_task(
                    functionalStep(target, args)
            ))

            # --- Command Injection --- #
            vuln_param = 'host'
            args.verify_oracle = 'PING'
            attack = "Command Injection"
            for test_name, test_value in cmd_inj_payloads.items():
                for withHost in [False, True]:
                    for isBlind in [False, True]:
                        test_name_opt = test_name + (', with host' if withHost else '') + (', blind' if isBlind else '')

                        tasks.append(loop.create_task(
                            testStep(attack, target, vuln_param, test_name_opt, test_value, args, withHost, isBlind)
                        ))
            
            # --- Argument Injection --- #
            vuln_param = 'input'
            args.verify_oracle = ''
            attack = "Argument Injection"
            for test_name, test_value in arg_inj_payloads.items():
                tasks.append(loop.create_task(
                            testStep(attack, target, vuln_param, test_name, test_value, args)
                ))

            # --- END CONCURRENCY (SYNC) --- #
            results = await asyncio.gather(*tasks)

            if all(results): print(f"\u2705 All tests have passed")


## TODO: Build per installare ping in php fpm
def main() -> None:
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("--fixed_app", default=False, action=BooleanOptionalAction)
    # 0 doesn't print anything, 1 prints only failure, 2 prints all
    parser.add_argument("--verbosity", type=int, default=1)
    # if I don't have permission to rm a file the program relies on random named files
    parser.add_argument("--port", type=int, default=9050)
    # set --no-nginx if using `php -S localhost:<port>`
    parser.add_argument("--nginx", default=False, action=BooleanOptionalAction)
    args: Namespace = parser.parse_args()
    
    BeforeAll(args)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(testSuite(args))
    loop.close()


if __name__ == "__main__":
    main()
