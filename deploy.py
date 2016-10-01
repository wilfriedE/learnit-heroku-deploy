#/usr/bin/python3
import argparse
import random
import string
import datetime
import os
import sys
import subprocess
from git import Repo

LEARN_IT_ENVS = ["APP_DOMAIN","SMTP_ADDRESS","MAILER_PASSWORD","MAILER_USERNAME","DEVISE_SECRET_KEY","MAILER_SENDER","SECRET_KEY_BASE"]
APP_DIR=""
HGEMFILE = None
REPO=None
ACTIVE_BRANCH=None

def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True

def run_cmd(cmd):
    os.system(cmd)

def check_heroku():
    return is_tool("heroku")

def branchout():
    branchname = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    new_branch = REPO.create_head(branchname)
    new_branch.checkout()
    print("Created new branch: %s " % branchname)
    return branchname

def track_bowerfiles():
    run_cmd("git add -f vendor/assets/bower_components/*")

def track_gitchanges():
    run_cmd("git add -A .")
    run_cmd("git commit -m '%s'" % ("heroku-push-on: " + datetime.date.today().strftime("%B %d, %Y")))

def pushtoheroku(branch):
    track_gitchanges()
    print("Pushing %s to heroku master" % branch)
    run_cmd("git push heroku %s:master" % branch)
    run_cmd("heroku run rake db:migrate")

def cleanup(branch):
    print("Cleaning up ... ")
    run_cmd("git checkout %s" % (ACTIVE_BRANCH or "master"))
    run_cmd("git branch -D %s" % branch)
    print("Complete")

def addh_gemfile():
    print("Appending Heroku gems to Gemfile")
    with open("Gemfile", "a") as f:
        for line in HGEMFILE:
            f.write(line.decode("utf-8"))

def set_heroku_configs():
    if not REPO.remotes["heroku"]:
        hremote = input("Enter heroku git remote path:")
        REPO.create_remote("heroku", hremote)
        print("Heroku remote set to "+ hremote)
    print("Please enter the configuration values for the following envs.")
    for env in LEARN_IT_ENVS:
        env_value = input(env + ": ")
        if env_value:
            print("Set %s to %s" % env, env_value)
            run_cmd("heroku config:set %s=%s" % env, env_value)
    addh_gemfile()

def setup_heroku(new_app=False):
    if check_heroku():
        print("Heroku installed, proceeding to configurations")
        if new_app:
            run_cmd("heroku create")
        set_heroku_configs()
    else:
        print("Please install the Heroku toolbelt before proceeding.")

def deploy_to_heroku(branch):
    if is_tool("git"):
        track_bowerfiles()
        pushtoheroku(branch)
        cleanup(branch)
    else:
        print("Git must be installed in order to proceed")

def move_to_app():
    global REPO
    global ACTIVE_BRANCH
    os.chdir(APP_DIR)
    REPO = Repo(".")
    ACTIVE_BRANCH = REPO.active_branch.name

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy to heroku.')
    parser.add_argument('-d', '--dir',help='Location of git repo to deploy')
    parser.add_argument('-c','--create', help='Create new heroku app to push to', action="store_true")
    args = parser.parse_args()
    APP_DIR = args.dir or "."
    with open('h_gemfile','rb') as f:
        HGEMFILE = f.readlines()
    move_to_app()
    branch = branchout()
    setup_heroku(args.create)
    deploy_to_heroku(branch)
