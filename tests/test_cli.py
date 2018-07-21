import subprocess


def test_missing_paths():
    process = subprocess.run(
        ['cloneholio', '-p', 'gitlab', '-t', '123'],
        stderr=subprocess.PIPE
    )
    assert process.returncode == 2
    assert (
        process.stderr.decode().split('\n')[-2] ==
        'cloneholio: error: the following arguments are required: paths'
    )


def test_invalid_provider():
    process = subprocess.run(
        ['cloneholio', '-p', 'microsofthub', '-t', '123'],
        stderr=subprocess.PIPE
    )
    assert process.returncode == 2
    assert (
        process.stderr.decode().split('\n')[-2] ==
        "cloneholio: error: argument -p/--provider: invalid choice: 'microsofthub' (choose from 'github', 'gitlab')"
    )


def test_missing_token():
    process = subprocess.run(
        ['cloneholio', '-p', 'github', 'apath'],
        stderr=subprocess.PIPE
    )
    assert process.returncode == 2
    assert (
        process.stderr.decode().split('\n')[-2] ==
        'cloneholio: error: the following arguments are required: -t/--token'
    )
