from unittest import mock

import cloneholio.github
import github


@mock.patch.object(
    cloneholio.github.github.Github, 'get_repo',
    side_effect=github.UnknownObjectException(None, None)
)
@mock.patch.object(
    cloneholio.github.github.Github, '__init__', return_value=None
)
def test_repo_not_found(*args):
    repos = cloneholio.github.get_repos('fake/repo', mock.sentinel.TOKEN)
    assert [] == list(repos)
