# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import time
import shutil

from cerbero.config import Platform
from cerbero.utils import shell
from cerbero.errors import FatalError


GIT = 'git'


def ensure_user_is_set(git_dir, logfile=None):
    # Set the user configuration for this repository so that Cerbero never warns
    # about it or errors out (it errors out with git-for-windows)
    try:
        shell.call('%s config user.email' % GIT, logfile=logfile)
    except FatalError:
        shell.call('%s config user.email "cerbero@gstreamer.freedesktop.org"' %
                   GIT, git_dir, logfile=logfile)

    try:
        shell.call('%s config user.name' % GIT, logfile=logfile)
    except FatalError:
        shell.call('%s config user.name "Cerbero Build System"' %
                   GIT, git_dir, logfile=logfile)

def init(git_dir, logfile=None):
    '''
    Initialize a git repository with 'git init'

    @param git_dir: path of the git repository
    @type git_dir: str
    '''
    os.makedirs(git_dir, exist_ok=True)
    shell.call('%s init' % GIT, git_dir, logfile=logfile)
    ensure_user_is_set(git_dir, logfile=logfile)


def clean(git_dir, logfile=None):
    '''
    Clean a git respository with clean -dfx

    @param git_dir: path of the git repository
    @type git_dir: str
    '''
    return shell.call('%s clean -dfx' % GIT, git_dir, logfile=logfile)


def list_tags(git_dir, fail=True):
    '''
    List all tags

    @param git_dir: path of the git repository
    @type git_dir: str
    @param fail: raise an error if the command failed
    @type fail: false
    @return: list of tag names (str)
    @rtype: list
    '''
    tags = shell.check_call('%s tag -l' % GIT, git_dir, fail=fail)
    tags = tags.strip()
    if tags:
        tags = tags.split('\n')
    return tags


def create_tag(git_dir, tagname, tagdescription, commit, fail=True, logfile=None):
    '''
    Create a tag using commit

    @param git_dir: path of the git repository
    @type git_dir: str
    @param tagname: name of the tag to create
    @type tagname: str
    @param tagdescription: the tag description
    @type tagdescription: str
    @param commit: the tag commit to use
    @type commit: str
    @param fail: raise an error if the command failed
    @type fail: false
    '''

    shell.call('%s tag -s %s -m "%s" %s' %
               (GIT, tagname, tagdescription, commit), git_dir,
               fail=fail, logfile=logfile)
    return shell.call('%s push origin %s' % (GIT, tagname), git_dir,
                      fail=fail, logfile=logfile)


def delete_tag(git_dir, tagname, fail=True, logfile=None):
    '''
    Delete a tag

    @param git_dir: path of the git repository
    @type git_dir: str
    @param tagname: name of the tag to delete
    @type tagname: str
    @param fail: raise an error if the command failed
    @type fail: false
    '''
    return shell.call('%s tag -d %s' % (GIT, tagname), git_dir, fail=fail, logfile=logfile)


def fetch(git_dir, fail=True, logfile=None):
    '''
    Fetch all refs from all the remotes

    @param git_dir: path of the git repository
    @type git_dir: str
    @param fail: raise an error if the command failed
    @type fail: false
    '''
    return shell.call('%s fetch --all' % GIT, git_dir, fail=fail, logfile=logfile)

def submodules_update(git_dir, src_dir=None, fail=True, offline=False, logfile=None):
    '''
    Update somdules from local directory

    @param git_dir: path of the git repository
    @type git_dir: str
    @param src_dir: path or base URI of the source directory
    @type src_dir: src
    @param fail: raise an error if the command failed
    @type fail: false
    @param offline: don't use the network
    @type offline: false
    '''
    if src_dir:
        config = shell.check_call('%s config --file=.gitmodules --list' % GIT,
                                  git_dir)
        config_array = [s.split('=', 1) for s in config.split('\n')]
        for c in config_array:
            if c[0].startswith('submodule.') and c[0].endswith('.path'):
                submodule = c[0][len('submodule.'):-len('.path')]
                shell.call("%s config --file=.gitmodules submodule.%s.url %s" %
                           (GIT, submodule, os.path.join(src_dir, c[1])),
                           git_dir, logfile=logfile)
    shell.call("%s submodule init" % GIT, git_dir, logfile=logfile)
    if src_dir or not offline:
        shell.call("%s submodule sync" % GIT, git_dir, logfile=logfile)
        shell.call("%s submodule update" % GIT, git_dir, fail=fail, logfile=logfile)
    else:
        shell.call("%s submodule update --no-fetch" % GIT, git_dir, fail=fail, logfile=logfile)
    if src_dir:
        for c in config_array:
            if c[0].startswith('submodule.') and c[0].endswith('.url'):
                shell.call("%s config --file=.gitmodules %s  %s" %
                           (GIT, c[0], c[1]), git_dir, logfile=logfile)
        shell.call("%s submodule sync" % GIT, git_dir, logfile=logfile)

def checkout(git_dir, commit, logfile=None):
    '''
    Reset a git repository to a given commit

    @param git_dir: path of the git repository
    @type git_dir: str
    @param commit: the commit to checkout
    @type commit: str
    '''
    return shell.call('%s reset --hard %s' % (GIT, commit), git_dir, logfile=logfile)


def get_hash(git_dir, commit):
    '''
    Get a commit hash from a valid commit.
    Can be used to check if a commit exists

    @param git_dir: path of the git repository
    @type git_dir: str
    @param commit: the commit to log
    @type commit: str
    '''
    if not os.path.isdir(os.path.join(git_dir, '.git')):
        # If a recipe's source type is switched from tarball to git, then we
        # can get called from built_version() when the directory isn't git.
        # Return a fixed string + unix time to trigger a full fetch.
        return 'not-git-' + str(time.time())
    return shell.check_call('%s rev-parse %s' %
                            (GIT, commit), git_dir).rstrip()


def local_checkout(git_dir, local_git_dir, commit, logfile=None):
    '''
    Clone a repository for a given commit in a different location

    @param git_dir: destination path of the git repository
    @type git_dir: str
    @param local_git_dir: path of the source git repository
    @type local_git_dir: str
    @param commit: the commit to checkout
    @type commit: false
    '''
    # reset to a commit in case it's the first checkout and the masterbranch is
    # missing
    branch_name = 'cerbero_build'
    shell.call('%s reset --hard %s' % (GIT, commit), local_git_dir, logfile=logfile)
    shell.call('%s branch %s' % (GIT, branch_name), local_git_dir, fail=False, logfile=logfile)
    shell.call('%s checkout %s' % (GIT, branch_name), local_git_dir, logfile=logfile)
    shell.call('%s reset --hard %s' % (GIT, commit), local_git_dir, logfile=logfile)
    shell.call('%s clone %s -s -b %s .' % (GIT, local_git_dir, branch_name),
               git_dir, logfile=logfile)
    ensure_user_is_set(local_git_dir, logfile=logfile)
    submodules_update(git_dir, local_git_dir, logfile=logfile)

def add_remote(git_dir, name, url, logfile=None):
    '''
    Add a remote to a git repository

    @param git_dir: destination path of the git repository
    @type git_dir: str
    @param name: name of the remote
    @type name: str
    @param url: url of the remote
    @type url: str
    '''
    try:
        shell.call('%s remote add %s %s' % (GIT, name, url), git_dir, logfile=logfile)
    except:
        shell.call('%s remote set-url %s %s' % (GIT, name, url), git_dir, logfile=logfile)


def check_line_endings(platform):
    '''
    Checks if on windows we don't use the automatic line endings conversion
    as it breaks everything

    @param platform: the host platform
    @type platform: L{cerbero.config.Platform}
    @return: true if git config is core.autorlf=false
    @rtype: bool
    '''
    if platform != Platform.WINDOWS:
        return True
    val = shell.check_call('git config --get core.autocrlf')
    if ('false' in val.lower()):
        return True
    return False


def init_directory(git_dir, logfile=None):
    '''
    Initialize a git repository with the contents
    of a directory

    @param git_dir: path of the git repository
    @type git_dir: str
    '''
    init(git_dir, logfile=logfile)
    try:
        shell.call('%s add --force -A .' % GIT, git_dir, logfile=logfile)
        shell.call('%s commit -m "Initial commit" > /dev/null 2>&1' % GIT,
            git_dir, logfile=logfile)
    except:
        pass


def apply_patch(patch, git_dir, logfile=None):
    '''
    Applies a commit patch usign 'git am'
    of a directory

    @param git_dir: path of the git repository
    @type git_dir: str
    @param patch: path of the patch file
    @type patch: str
    '''
    shell.call('%s am --ignore-whitespace %s' % (GIT, patch), git_dir, logfile=logfile)
