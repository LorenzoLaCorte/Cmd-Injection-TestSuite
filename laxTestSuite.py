#!/usr/bin/env python3

# Python script that calls the target application attached to this assignment, and shows a summary of the results. 
# Author: Lorenzo La Corte

from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from urllib.parse import urlencode, quote_plus
import logging
import random
import subprocess
import time
import uuid
import os
from pathlib import Path
import asyncio
import aiohttp


logging.basicConfig(filename="requests.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

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
    if args.fixed_app: args.basepath = "ApplicationFixed"
    else: args.basepath = "Application"

    if args.nginx:
        args.oracle = "nginx"
        args.ip = "172.17.0.2"
        args.port = 80
    else:
        args.oracle = subprocess.getoutput("whoami")
        args.ip = "localhost"

        args.processes = []

        for port in args.ports:
            cmd = ["php", "-S", f"localhost:{port}"]
            cwd = os.getcwd() + (f"/{args.basepath}")
            args.processes.append(subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
            
        time.sleep(1) # wait for the server to be running


def CollectTargets(args):
    targets: dict[str, list[str]] = {}
    basepath = Path(args.basepath)
    subdirs = basepath.iterdir()

    for subdir in subdirs:
        if subdir.is_file(): continue
        targets[subdir.name] = []
        for file in subdir.iterdir():
            if file.is_file():  targets[subdir.name].append(file.name)
    return targets


def AfterEach(args, rand_num):
    try: os.remove(f"{args.basepath}/{rand_num}.tmp")
    except: pass

def AfterAll(args):
    try: os.remove(f"{args.basepath}/*.tmp")
    except: pass

    if args.nginx:
        for process in args.processes:
            try: process.terminate()
            except: pass

async def functionalStep(target, args):
    if 'echo' in target or 'no-output' in target:
        print("\u2705 Functional Verifification", flush=True)
        return True
    elif 'echo-' in target:
        vuln_param = 'name'
        test_value = oracle = 'my_message'
    elif 'ping' in target:
        vuln_param = 'host'
        test_value = oracle = 'localhost'
    elif 'find' in target:
        vuln_param = 'input'
        test_value = oracle = target.split("/")[1]
    else:
        raise Exception(f"Error: page not recognized")

    if not args.nginx: args.port = random.choice(args.ports)

    params = urlencode({ vuln_param: test_value }, quote_via=quote_plus)

    async with aiohttp.ClientSession() as client:
        injectionRequest = f"http://{args.ip}:{args.port}/{target}?{params}"
        logging.info(injectionRequest)
        
        async with client.get(injectionRequest) as response:

            if response.status != 200:
                raise Exception(f"Error: {response.status_code}")
            
            response_text = await response.text()

            test_result = oracle in response_text

            print("{} {}".format("\u2705" if test_result else "\u274c", "Functional Verifification"), flush=True)

            return test_result

async def testStep(attack, target, vuln_param, test_name, test_value, args, withHost=False, isBlind=False):
    rand_num = uuid.uuid4()
    if not args.nginx: args.port = random.choice(args.ports)

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

            AfterEach(args, rand_num)

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
    
    AfterAll(args)

def main() -> None:
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("--fixed_app", default=False, action=BooleanOptionalAction, help="Run the TestSuite on the fixed application")
    parser.add_argument("--verbosity", type=int, default=1, help="Verbosity Level - 0: Doesn't print anything, 1: Prints only failure, 2: Prints all")
    parser.add_argument("--ports", type=list[str], default=[i for i in range(9000,9003)], help="Set the ports of your servers")
    parser.add_argument("--nginx", default=False, action=BooleanOptionalAction, help="Test the application on the nginx container")

    args: Namespace = parser.parse_args()
    
    BeforeAll(args)

    asyncio.run(testSuite(args))

if __name__ == "__main__":
    main()
