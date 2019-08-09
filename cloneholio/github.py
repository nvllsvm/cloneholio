import logging
import urllib.parse

import github


LOGGER = logging.getLogger('cloneholio')


def get_repos(path, token, insecure=False, base_url=None):
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

    repos = []
    if '/' in path:
        try:
            repo = api.get_repo(path)
            if repo:
                repos.append(repo)
        except github.UnknownObjectException:
            LOGGER.warning('GitHub repo not found: %s', path)
    else:
        repos = api.get_user(path).get_repos()

    for repo in repos:
        yield repo.full_name, repo.ssh_url


def _make_absolute_url(self, url):
    if url.startswith("/"):
        url = self._Requester__prefix + url
    else:
        o = urllib.parse.urlparse(url)
        url = o.path
        if o.query != "":
            url += "?" + o.query
    return url
