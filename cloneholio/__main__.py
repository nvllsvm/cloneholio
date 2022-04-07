import argparse
import concurrent.futures
import itertools
import logging
import os
import pathlib
import shutil
import sys
import urllib3

import git
import pkg_resources
import tqdm

import cloneholio.github
import cloneholio.gitlab


LOGGER = logging.getLogger('cloneholio')


def download_repo(directory, path, url, last_activity_at, default_branch,
                  **kwargs):
    LOGGER.info('Processing %s', path)
    local_path = pathlib.Path(directory, path)
    updated_at = last_activity_at.timestamp() if last_activity_at else None
    try:
        if local_path.exists():
            repo = git.Repo(local_path)
            local_branch = str(repo.active_branch)
            if not updated_at or local_path.stat().st_mtime != updated_at \
                    or local_branch != default_branch:
                for remote in repo.remotes:
                    remote.set_url(url)
                    remote.update()
                    if remote.refs:
                        remote.fetch()
                if repo.branches:
                    if local_branch != default_branch:
                        repo.git.checkout(default_branch)
                    repo.remote().pull()
        else:
            git.Repo.clone_from(url, local_path, **kwargs)
        if updated_at:
            os.utime(local_path,
                     times=(local_path.stat().st_atime, updated_at))
    except git.GitCommandError as e:
        LOGGER.error('Git error %s "%s"', path, ' '.join(e.command))
        return local_path, False
    except Exception as e:
        LOGGER.error('Unhandled error %s "%s"', path, ' '.join(e.command))
        return local_path, False
    return local_path, True


def find_orphans(root, repos):
    """Log unexpected local paths

    An unexpected path may be the result of a repository being deleted at
    origin after at least one cloneholio clone.
    """
    parents = set()
    for path in repos:
        parents.update(path.parents)

    orphans = []

    stack = [root]
    while stack:
        for path in stack.pop().iterdir():
            if path in repos:
                continue

            if path not in parents:
                orphans.append(path)
            elif path.is_dir():
                stack.append(path)

    return orphans


PROVIDER_FUNCTIONS = {
    'github': cloneholio.github.get_repos,
    'gitlab': cloneholio.gitlab.get_repos
}


def main():
    parser = argparse.ArgumentParser(
        'cloneholio',
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
Maintain local backups of all Git repositories belonging to a user or group.

Token creation:
  - GitLab
    Permissions:  api
    URL:  https://gitlab.com/profile/personal_access_tokens

  - GitHub
    Permissions:  repo:status
    URL:  https://github.com/settings/tokens/new
""")

    parser.add_argument(
        '-n', dest='num_processes',
        help='Number of processes to use',
        type=int,
        default=1)

    group_remote = parser.add_argument_group('remote configuration')
    group_remote.add_argument('-t', '--token', required=True)
    group_remote.add_argument(
        '-p', '--provider', choices=PROVIDER_FUNCTIONS.keys()
    )
    group_remote.add_argument(
        '--insecure',
        action='store_true',
        help='Ignore SSL errors'
    )
    group_remote.add_argument('-u', '--base-url')
    group_remote.add_argument(
        '-e', '--exclude',
        action='append',
        default=[],
        help='Paths to exclude from backup'
    )
    group_remote.add_argument(
        '--exclude-archived',
        action='store_true',
        help='exclude archived repositories'
    )
    group_remote.add_argument(
        '--exclude-forks',
        action='store_true',
        help='exclude repositories that are forks'
    )

    group_local = parser.add_argument_group('local configuration')
    group_local.add_argument('-d', '--directory', default='.')
    group_local.add_argument(
        '--remove-orphans',
        action='store_true',
        help='Remove orphaned directories'
    )

    parser.add_argument(
        '--depth',
        type=int,
        default=False,
        help='Corresponds to the git clone --depth option'
    )
    output_mutex = parser.add_mutually_exclusive_group()
    output_mutex.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress informational output'
    )
    output_mutex.add_argument(
        '--progress',
        action='store_true',
        help='Show progress bar'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List remote repositories then exit.'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=pkg_resources.get_distribution('cloneholio').version
    )
    parser.add_argument('--all-groups', action='store_true')
    parser.add_argument('paths', nargs='*')

    args = parser.parse_args()

    if not args.all_groups and not args.paths:
        parser.error('must specifiy at least --all-groups or a path(s)')
        parser.exit(1)

    logging.basicConfig(
        level=logging.WARN if args.quiet or args.progress else logging.INFO,
        format='%(levelname)s %(message)s')

    directory = pathlib.Path(args.directory).absolute()

    LOGGER.info('Begin "%s" processing using "%s"',
                args.provider, directory)

    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    paths = set(args.paths)
    if args.all_groups:
        paths.update(
            path.split('/')[0].lower()
            for path in cloneholio.gitlab.get_groups(
                args.token, args.insecure, args.base_url)
        )

    repos = itertools.chain(*[
        PROVIDER_FUNCTIONS[args.provider](
            path, args.token, args.insecure, args.base_url,
            archived=False if args.exclude_archived else None,
            is_fork=False if args.exclude_forks else None
        )
        for path in paths
    ])

    exclude = set(args.exclude)
    targets = set()
    for path, url, last_activity_at, default_branch in repos:
        split_path = path.split('/')
        parts = {
            '/'.join(split_path[0:i])
            for i in range(1, len(split_path)+1)
        }
        if not exclude.intersection(parts):
            if args.list:
                print(path)
            targets.add((path, url, last_activity_at, default_branch))

    if args.list:
        parser.exit()

    total_repos = len(targets)
    with concurrent.futures.ProcessPoolExecutor(
            args.num_processes) as executor:

        failures = 0
        local_paths = []

        iterable = concurrent.futures.as_completed(
            executor.submit(
                download_repo, directory, *target, depth=args.depth)
            for target in sorted(targets)
        )

        if args.progress and sys.stdout.isatty():
            iterable = tqdm.tqdm(
                iterable,
                dynamic_ncols=True,
                total=total_repos
            )

        for future in iterable:
            local_path, is_success = future.result()
            local_paths.append(local_path)
            if not is_success:
                failures += 1

    orphans = find_orphans(directory, local_paths)
    for path in sorted(orphans):
        log_path = path.relative_to(directory)
        if args.remove_orphans:
            LOGGER.warning('Removing orphan %s', log_path)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        else:
            LOGGER.warning('Orphan %s', log_path)

    LOGGER.info(
        'Finished "%s" processing %d repos with %d failures and %d orphans',
        args.provider, total_repos, failures, len(orphans))
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
