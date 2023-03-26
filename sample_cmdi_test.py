#!/usr/bin/env python3

import requests

WHOAMI_ORACLE = "lax"

test_values = {
        'semicolon': ';whoami',
        'ampersand': '&whoami',
        'logical AND': '&&whoami',
        'pipe': '|whoami',
        'logical OR': '||whoami',
        'subshell': '$(whoami)',
        }

def test_step(test_name, test_value):

    cookies = { }
    headers = { }
    params = {
        'host': test_value,
    }

    response = requests.get('http://localhost:9000/cmdi/index.php', params=params, cookies=cookies, headers=headers)

    test_result = not WHOAMI_ORACLE in response.text

    print("{} {}".format("\u2705" if test_result else "\u274c", test_name))

for test_name, test_value in test_values.items():
    test_step(test_name, test_value)

