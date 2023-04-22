#!/usr/bin/env python3

# Python script that calls the target application attached to this assignment, and shows a summary of the results. 
# Author: Lorenzo La Corte

from argparse import ArgumentParser, BooleanOptionalAction, Namespace
import logging
import random
import subprocess
import time
import uuid
import requests
import os
from pathlib import Path
import asyncio
import aiohttp
from urllib.parse import urlencode, quote_plus


logging.basicConfig(filename="requests.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

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
    args.oracle = subprocess.getoutput("whoami")
    args.ip = "localhost"

    if args.concurrency:
        for port in args.ports:
            cmd = ["php", "-S", f"localhost:{port}"]
            cwd = os.getcwd() + ('/ApplicationFixed' if args.fixed_app else '/Application')
            subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    else:
        cmd = ["php", "-S", f"localhost:{args.port}"]
        cwd = os.getcwd() + ('/ApplicationFixed' if args.fixed_app else '/Application')
        subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(1) # wait for the server to be running


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
        print("{} {}".format("\u2705" if test_result else "\u274c", "Functional Verifification"), flush=True)
        return test_result
    elif 'ping' in target:
        vuln_param = 'host'
        test_value = oracle = 'localhost'
    elif 'find' in target:
        vuln_param = 'input'
        test_value = oracle = target.split("/")[1]
    else:
        raise Exception(f"Error: page not recognized")

    params = {
        vuln_param: test_value
    }

    response = requests.get(f"http://{args.ip}:{args.port}/{target}", params=params)
    logging.info(f"http://{args.ip}:{args.port}/{target}?{vuln_param}={test_value}")

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")

    test_result = oracle in response.text

    print("{} {}".format("\u2705" if test_result else "\u274c", "Functional Verifification"), flush=True)

    return test_result

async def testStep(attack, target, vuln_param, test_name, test_value, args, withHost=False, isBlind=False):
    rand_num = uuid.uuid4()

    if args.concurrency:
        args.port = random.choice(args.ports)

    test_value = 'localhost' + test_value if withHost else test_value
    test_value = test_value + f'>../{rand_num}.tmp' if isBlind else test_value

    params = {
        vuln_param: test_value
    }

    params = urlencode(params, quote_via=quote_plus)

    logging.info(f"http://{args.ip}:{args.port}/{target}?{params}")

    async with aiohttp.ClientSession() as client:
        
        async with client.get(f"http://{args.ip}:{args.port}/{target}?{params}") as response:

            if response.status != 200:
                raise Exception(f"Error: {response.status_code}")

            response_text = ""

            if isBlind:
                async with client.get(f"http://{args.ip}:{args.port}/{rand_num}.tmp") as response:
                    response_text = await response.text()
            else:
                response_text = await response.text()

            test_result = not args.oracle in response_text

            if args.verbosity == 1 and not test_result: print(f"\u274c {attack}: {test_name}", flush=True)
            elif args.verbosity == 2: print("{} {}: {}".format("\u2705" if test_result else "\u274c", attack, test_name), flush=True)

            AfterEach(rand_num)

            return test_result


# For each page of the tested application, should design and implement a test step
async def testSuite(args):
    print(f"\u2699 Lax TestSuite \u2699", flush=True)

    targets = CollectTargets(args)

    for subdir, files in targets.items(): 
        for file in files:
            # --- START CONCURRENCY --- #
            tasks = []

            target = subdir+'/'+file
            print(f"\nPage under test: {target}", flush=True)
            
            # --- Functional Step --- #
            tasks.append(asyncio.create_task(
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

                        tasks.append(asyncio.create_task(
                            testStep(attack, target, vuln_param, test_name_opt, test_value, args, withHost, isBlind)
                        ))
            
            # --- Argument Injection --- #
            vuln_param = 'input'
            args.verify_oracle = ''
            attack = "Argument Injection"
            for test_name, test_value in arg_inj_payloads.items():
                tasks.append(asyncio.create_task(
                            testStep(attack, target, vuln_param, test_name, test_value, args)
                ))

            # --- END CONCURRENCY (SYNC) --- #
            results = await asyncio.gather(*tasks)

            if all(results): print(f"\u2705 All tests have passed", flush=True)

# TODO: Cuncurrent Functional Verification
# TODO: Try it on nginx
# TODO: Clean args
# TODO: Clean everything
def main() -> None:
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("--fixed_app", default=False, action=BooleanOptionalAction, help="Run the TestSuite on the fixed application")
    parser.add_argument("--verbosity", type=int, default=1, help="0 doesn't print anything - 1 prints only failure - 2 prints all")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--concurrency", default=True, action=BooleanOptionalAction)
    parser.add_argument("--ip", type=str, default="172.17.0.2", help="In case the concurrency is enabled, set the IP of your concurrent server")
    parser.add_argument("--ports", type=list[str], default=[i for i in range(8050,8177)], help="In case the concurrency is enabled, set the ports of your servers")

    args: Namespace = parser.parse_args()
    
    BeforeAll(args)

    asyncio.run(testSuite(args))

if __name__ == "__main__":
    main()
