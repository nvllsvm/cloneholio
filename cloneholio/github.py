import functools
import logging
import urllib.parse

import github


LOGGER = logging.getLogger('cloneholio')


@functools.cache
def get_auth_user_private_repos(api):
    """
    The only way to retrieve private repositories is to list
    them from the authenticated user endpoint.
    They are _never_ returned in the non-authenticated user
    endpoints
    """
    user = api.get_user()
    return list(user.get_repos(visibility='private'))


def get_repos(path, token, insecure=False, base_url=None, archived=True,
              is_fork=True):
    kwargs = {'verify': not insecure}
    if base_url:
        kwargs['base_url'] = base_url

    api = github.Github(token, **kwargs)

    if base_url is not None:
        # Fixes bug in upstream PyGithub
        api._Github__requester._Requester__makeAbsoluteUrl = \
            _make_absolute_url.__get__(
                api._Github__requester, github.Requester.Requester
            )

    path_parts = path.split('/')
    path_user = path_parts.pop(0).lower()
    path_name = path_parts.pop(0).lower() if path_parts else None
    if path_parts:
        raise ValueError('Invalid path')

    repos = []
    if path_name:
        try:
            repo = api.get_repo(f'{path_user}/{path_name}')
            if repo:
                repos.append(repo)
        except github.UnknownObjectException:
            LOGGER.warning('GitHub repo not found: %s', path)
    else:
        try:
            repos.extend(api.get_user(path_user).get_repos())
        except github.UnknownObjectException:
            LOGGER.warning('GitHub user not found: %s', path)

    repos.extend(get_auth_user_private_repos(api))

    for repo in repos:
        user, name = repo.full_name.split('/')
        if user.lower() != path_user:
            continue
        if path_name and name.lower() != path_name:
            continue

        if repo.fork and is_fork is False:
            continue
        if repo.archived and archived is False:
            continue
        yield repo.full_name, repo.ssh_url, repo.pushed_at, repo.default_branch


def _make_absolute_url(self, url):
    if url.startswith("/"):
        url = self._Requester__prefix + url
    else:
        o = urllib.parse.urlparse(url)
        url = o.path
        if o.query != "":
            url += "?" + o.query
    return url
