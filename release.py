"""
- https://realpython.com/python-exec/
- https://github.com/m-vdb/pep440-version-utils

- https://gitpython.readthedocs.io/en/stable/tutorial.html#gitpython-tutorial
pip install gitpython
"""

from pathlib import Path
import os
from subprocess import check_call
import sys
from pep440_version_utils import Version
import argparse
import logging
from git import Repo

logger = logging.getLogger(__name__)

ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(ROOT_DIR))

VERSION_FILE_PATH = 'version.py'
RELEASE_BRANCH = 'release'

def parse_args():
    args_parser = argparse.ArgumentParser()
    
    args_parser.add_argument('--release-type', 
                             dest='release_type', 
                             type=str, 
                             default='micro',
                             choices=['micro', 'minor', 'major', 'alpha', 'beta', 'rc']
                             )
    
    args = args_parser.parse_args()
    return args

def get_file_version_path() -> Path:
    _path = os.path.join(str(ROOT_DIR), VERSION_FILE_PATH)
    return Path(_path)

def get_current_version(file_path) -> str:
    
    if not file_path.is_file():
        raise FileNotFoundError(f"Unable to find specified version file from: {Path(file_path).absolute()}")    
    
    d = {}
    with open(file_path) as f:
        exec(f.read(), d)
    
    return d.get('__version__', '')
        
def get_next_version(current_version: str, release_type: str) -> str:
    
    version = Version(current_version)
    
    if release_type == 'micro':
        next_version = version.next_micro()
    elif release_type == 'minor':
        next_version = version.next_minor() 
    elif release_type == 'macro':
        next_version = version.next_major()
    elif version == 'alpha':
        next_version = version.next_alpha() 
    elif release_type == 'beta':
        next_version =  version.next_beta() 
    elif release_type == 'rc': 
        next_version = version.next_release_candidate()
    else:
        raise ValueError(f"Unknown version '{release_type}'")

    return next_version


def update_file_version(file_path: str, new_version: str):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if line.startswith('__version__'):
            lines[i] = f'__version__ = "{new_version}"\n'
            break
        
    with open(file_path, 'w') as f:
        f.writelines(lines)

def set_repo():
    repo = Repo()
    current_branch = repo.active_branch
    logger.info(f'current_branch: {current_branch}')
    # origin = repo.remote()
    # logger.info(f'origin: {origin}')
    return repo
            
def ensure_clean_git(repo: Repo):
    logger.info(f"Ensure that git repo is clean")
    if repo.is_dirty():
        logger.error('Current repository has uncommitted changes')
        changed_files = [item.a_path for item in repo.index.diff(None)]
        print("changed_files: ", changed_files)
        sys.exit(1)
    else:
        print('Git repo is clean')
 
                 
def main(args: argparse.Namespace):
    
    release_type = args.release_type
    logger.info(f'release_type => {release_type}')
    
    git_repo = set_repo()
    
    ensure_clean_git(repo=git_repo)
    
    version_file_path = get_file_version_path()
    logger.info(f'File version path: {version_file_path}')
    
    current_version = get_current_version(file_path=version_file_path)
    logger.info(f'current_version => {current_version}')

    next_version = get_next_version(current_version=current_version, release_type=release_type)
    logger.info(f'next_version => {next_version}')

    logger.info(f"update file version and add it to git")
    update_file_version(file_path=version_file_path, new_version=next_version)
    git_repo.index.add([version_file_path.absolute().resolve()])
    
    logger.info(f"Create release branch and switch on it")
    release_branch = f'{RELEASE_BRANCH}/{next_version}'
    release_branch = git_repo.create_head(release_branch)
    release_branch.checkout()
    
    # repo.checkout("-b", release_branch)
    git_repo.index.commit(f'Preparing release for the version: {next_version}')
    logger.info(f'Push changes to {release_branch.name}')
    git_repo.remote().push(release_branch)
    print('done')


if __name__ == '__main__':
    
    # check_call(["poetry", "update"])

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    
    logging.basicConfig(level=log_level,
                        format='%(asctime)s\t[%(levelname)s] %(name)s: [%(filename)s %(lineno)d]\t%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    _args = parse_args()
    
    main(_args)