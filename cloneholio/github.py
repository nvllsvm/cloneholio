import logging
import urllib.parse

import github


LOGGER = logging.getLogger('cloneholio')


class GitHub:

    def __init__(self, token, insecure=False, base_url=None):
        kwargs = {'verify': not insecure}
        if base_url:
            kwargs['base_url'] = base_url

        self.api = github.Github(token, **kwargs)

        if base_url is not None:
            # Fixes bug in upstream PyGithub
            self.api._Github__requester._Requester__makeAbsoluteUrl = \
                _make_absolute_url.__get__(
                    self.api._Github__requester, github.Requester.Requester
                )

    def get_repos(self, path, archived=True, is_fork=True):
        repos = []
        if '/' in path:
            try:
                repo = self.api.get_repo(path)
                if repo:
                    repos.append(repo)
            except github.UnknownObjectException:
                LOGGER.warning('GitHub repo not found: %s', path)
        else:
            repos = self.api.get_user(path).get_repos()

        for repo in repos:
            if repo.fork and not is_fork:
                continue
            if repo.archived and not archived:
                continue
            yield repo.full_name, repo.ssh_url

    def get_gists(self, path):
        for gist in self.api.get_user(path).get_gists():
            yield f'{gist.id}'.strip(), gist.git_pull_url


def _make_absolute_url(self, url):
    if url.startswith("/"):
        url = self._Requester__prefix + url
    else:
        o = urllib.parse.urlparse(url)
        url = o.path
        if o.query != "":
            url += "?" + o.query
    return url
