' ' '
    GSMST Cyber Patriot 2022
' ' '
import json
import subprocess
import functools
import re
import os
import concurrent.futures as future
from typing import Dict


if os.geteuid() != 0:
    exit("You must be root to run this.")


def init() -> None:
    try:
        config = json.loads(open('config.json').read())
        global run
        run = functools.partial(subprocess.run, shell=True,
                                stdout=subprocess.PIPE, encoding='utf-8', timeout=5, check=True)
        config['WHOAMI'] = run('whoami')
        globals().update(config)
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        raise ValueError('Void Config File.')


def load_user() -> Dict[str, list]:
    '''
    This one will smartly load users from readme or according to json
    Although return something, it mainly serve purpose as to utilize side effect of it.
    '''
    if('users' in globals() and len(globals()['users']['admin']) != 0):
        return users

    user_regex = r'(?:(?:([\w:() ]*?)\s)\s+)?'
    users_regex = re.compile(
        rf'Authorized administrators:?\s*{user_regex * MAX_USER}\s*Authorized users:?\s*{user_regex * MAX_USER}', re.MULTILINE)
    user_with_password_regex = re.compile(
        r'(.+?)\s*\(Password:\s*(.+)\)', re.MULTILINE)

    users = {'normal_user': [],
             'admin': []}

    with open(README_PATH) as fp:
        match = users_regex.search(fp.read(), re.MULTILINE)
        key = 'admin'
        if(not match):
            raise ValueError('Unable to parse.')
        for username in match.groups():
            if(username is not None):
                password_match = user_with_password_regex.search(
                    username)
                if(password_match):
                    username = password_match.group(1)
                users[key].append(username)
            else:
                key = 'normal_user'

    globals()['users'] = users
    return users


def safe_users(collection):
    '''
    Final means to secure you from deleted/modified. WHOAMI always return root. It make code more readable.
    '''
    return filter(lambda username: username != WHOAMI and username not in WHITELIST, collection)


def mod_users():
    '''
    TODO: import concurrent.future; optimize it with concurrent pools
    '''
    required_users = set(users['admin'] + users['normal_user'])
    actual_users = set(
        run(r"awk -F: '{if($3>999){print($1)}}' /etc/passwd").stdout.split())

    for to_be_deleted in safe_users(actual_users - required_users):
        print(f'remove {to_be_deleted}')
        run(f'userdel {REMOVE_HOME} -f {to_be_deleted}')

    for to_be_added in safe_users(required_users - actual_users):
        print(f'add user {to_be_added}')
        run(f'useradd "{to_be_added}"')

    for to_be_change_password in safe_users(actual_users):
        print(f'change password {to_be_change_password}')
        run(f'echo "{to_be_change_password}:{PASSWORD}" | chpasswd')


if __name__ == '__main__':
    init()
    load_user()
    mod_users()
