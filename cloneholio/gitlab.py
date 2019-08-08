import logging

import gitlab


GITLAB_URL = 'https://gitlab.com'

LOGGER = logging.getLogger('cloneholio')


def _get_groups(name, api):
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


def _get_project(path, api):
    try:
        return api.projects.get(path)
    except gitlab.GitlabGetError:
        pass


def _get_projects(path, api):
    project = _get_project(path, api)
    if project:
        yield project

    for group in _get_groups(path, api):
        yield from group.projects.list(all_available=True, as_list=False)


def get_repos(path, token, insecure, base_url=None):
    api = gitlab.Gitlab(
        base_url or GITLAB_URL,
        private_token=token,
        ssl_verify=not insecure
    )

    for project in _get_projects(path, api):
        project_path = project.path_with_namespace
        # Exclude forks under different groups/users
        if project_path.split('/')[0].lower() == path.lower():
            yield project_path, project.ssh_url_to_repo
