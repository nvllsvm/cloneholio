import argparse
import concurrent.futures
import itertools
import logging
import pathlib
import shutil
import urllib3

import git
import pkg_resources

import cloneholio.github
import cloneholio.gitlab


LOGGER = logging.getLogger('cloneholio')


def download_repo(path, url, directory, **kwargs):
    LOGGER.info('Processing %s', path)
    local_path = pathlib.Path(directory, path)
    try:
        if local_path.exists():
            repo = git.Repo(local_path)
            for remote in repo.remotes:
                remote.update()
                if remote.refs:
                    remote.fetch()
            if repo.branches:
                repo.remote().pull()
        else:
            git.Repo.clone_from(url, local_path, **kwargs)
    except git.GitCommandError as e:
        return False
        LOGGER.error('Git error %s "%s"', path, ' '.join(e.command))
    return local_path


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
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress informational output'
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
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARN if args.quiet else logging.INFO,
        format='%(levelname)s %(message)s')

    directory = pathlib.Path(args.directory).absolute()

    LOGGER.info('Begin "%s" processing using "%s"',
                args.provider, directory)

    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    repos = itertools.chain(*[
        PROVIDER_FUNCTIONS[args.provider](
            path, args.token, args.insecure, args.base_url
        )
        for path in args.paths
    ])

    total_repos = 0
    exclude = set(args.exclude)
    with concurrent.futures.ProcessPoolExecutor(
            args.num_processes) as executor:

        futures = []

        for path, url in repos:
            split_path = path.split('/')
            parts = {
                '/'.join(split_path[0:i])
                for i in range(1, len(split_path)+1)
            }
            if not exclude.intersection(parts):
                total_repos += 1
                if args.list:
                    print(path)
                    continue
                futures.append(
                    executor.submit(
                        download_repo,
                        path,
                        url,
                        directory,
                        depth=args.depth
                    )
                )

        if args.list:
            parser.exit()
        failures = 0
        local_paths = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                local_paths.append(result)
            else:
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


if __name__ == '__main__':
    main()
