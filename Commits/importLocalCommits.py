#!/usr/bin/env python
import os
import git
import updateLocalDb
import argparse
import subprocess


def getLocalGitRepos(args):
  listOfRepos = []
  for path in args.paths:
    # do some normilazation on the path first
    path = os.path.abspath(os.path.expanduser(path))

    for root, dirs, files in os.walk(os.path.expanduser(path)):
      if '.git' in dirs and root not in listOfRepos:
        listOfRepos.append(root)

      # skip going further down the rabbit hole
      if args.no_recursive:
        break

      # during development we don't want to wait too long
      if args.max_repos > 0 and len(listOfRepos) >= args.max_repos:
        break

  return listOfRepos


def installGitHooks(path):
  gitPath = path+"/.git"
  if os.path.exists(gitPath+"/hooks.old"):
    return False

  p = subprocess.Popen(['git', '--git-dir', gitPath, '--work-tree', path, 'hooks', '--install'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
  out, err = p.communicate()
  if len(err) > 0:
    print err
    return False
  else:
    return True


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Search for existing Git repositories and import commits made by the local user.')
  parser.add_argument('--install-hooks', action='store_true', help="install git-hooks in found directories")
  parser.add_argument('--max-repos', metavar='N', type=int, default=0, help="stop scanning after N repositories")
  parser.add_argument('--no-recursive', action='store_true', help="don't scan recursively")
  parser.add_argument('--paths', nargs='+', type=str, default=["~/"], help="Paths to recursively scan for Git repositories. If not specified, the user's home directory (~/) is scanned.")
  args = parser.parse_args()

  # get all local repositories (this might take a while)
  localGitRepos = getLocalGitRepos(args)

  commitCounter = 0
  for repoPath in localGitRepos:
    # install git-hooks in the directory
    if args.install_hooks:
      installGitHooks(repoPath)

    # get the relevant infos from the repository
    repoInfo = updateLocalDb.extractRepoInfo(git.Repo(repoPath))
    commitCounter += len(repoInfo)

    # fill everything into the database
    updateLocalDb.fillDatabase(repoInfo)

  print "Added {} commits from {} repositories.".format(commitCounter, len(localGitRepos))

