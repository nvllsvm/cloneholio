import argparse
import itertools
import logging
import pathlib

import consumers
import git
import github
import gitlab


GITLAB_URL = 'https://gitlab.com'


def get_gitlab_groups(name, api):
    try:
        yield api.users.list(username=name)[0]
    except (gitlab.GitlabGetError, IndexError):
        pass

    try:
        group = api.groups.get(name)
    except gitlab.GitlabGetError:
        return

    yield group

    groups = [group]
    while groups:
        subgroups = []
        for group in groups:
            for subgroup in group.subgroups.list(
                    all_available=True, as_list=False):
                subgroup = api.groups.get(subgroup.id)
                yield subgroup
                subgroups.append(subgroup)
        groups = subgroups


def get_gitlab_project(path, api):
    try:
        return api.projects.get(path)
    except gitlab.GitlabGetError:
        pass


def get_gitlab_projects(path, api):
    project = get_gitlab_project(path, api)
    if project:
        yield project

    for group in get_gitlab_groups(path, api):
        yield from group.projects.list(all_available=True, as_list=False)


def get_gitlab_repos(path, token):
    api = gitlab.Gitlab(GITLAB_URL, private_token=token)

    for project in get_gitlab_projects(path, api):
        project_path = project.path_with_namespace
        # Exclude forks under different groups/users
        if project_path.split('/')[0].lower() == path.lower():
            yield project_path, project.ssh_url_to_repo


def get_github_repos(path, token):
    api = github.Github(token)

    repos = []
    if '/' in path:
        repo = api.get_repo(path)
        if repo:
            repos.append(repo)
    else:
        repos = api.get_user(path).get_repos()

    for repo in repos:
        yield repo.full_name, repo.ssh_url


def download_repos(repos, directory):
    logger = logging.getLogger()

    fail_count = 0

    for path, url in repos:
        logger.info('Processing %s', path)
        local_path = pathlib.Path(directory, path)
        try:
            if local_path.exists():
                repo = git.Repo(local_path)
                for remote in repo.remotes:
                    remote.fetch()
                if repo.branches:
                    repo.remote().pull()
            else:
                git.Repo.clone_from(url, local_path)
        except git.GitCommandError as e:
            fail_count += 1
            logger.error('Git error %s "%s"', path, ' '.join(e.command))

    return fail_count


PROVIDER_FUNCTIONS = {
    'github': get_github_repos,
    'gitlab': get_gitlab_repos
}


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s %(message)s')

    parser = argparse.ArgumentParser(
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
    parser.add_argument('-d', '--directory', default='.')
    parser.add_argument('-t', '--token', required=True)
    parser.add_argument('-p', '--provider', choices=PROVIDER_FUNCTIONS.keys())
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()

    directory = pathlib.Path(args.directory).absolute()

    logging.info('Begin "%s" processing using "%s"',
                 args.provider, directory)

    repos = itertools.chain(*[
        PROVIDER_FUNCTIONS[args.provider](path, args.token)
        for path in args.paths
    ])

    total_repos = 0
    with consumers.Pool(download_repos,
                        args=[directory],
                        quantity=args.num_processes) as pool:
        for path, url in repos:
            total_repos += 1
            pool.put(path, url)

    logging.info('Finished "%s" processing %d repos with %d failures',
                 args.provider, total_repos, sum(pool.results))


if __name__ == '__main__':
    main()
