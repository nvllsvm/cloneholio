# Changelog

## 0.12.0 (2021-07-15)
- Increase performance by only executing git when the remote reports a change. 
  The local repo's **mtime** is set to the time of the remote's last update.
- Fix GitLab pagination

## 0.11.0 (2019-12-05)
- Add `--all-groups` option to retrieve repos from all available groups (GitLab only)

## 0.10.0 (2019-10-29)
- Add progress bar

## 0.9.1 (2019-10-14)
- Fix Gitlab error when retrieving subgroup

## 0.9.0 (2019-10-10)
- Add `--exclude-forks` option to exclude repositories that are forks

## 0.8.1 (2019-09-13)
- Fix group fork filtering

## 0.8.0 (2019-08-28)
- Add `--exclude-archived` option to exclude archived repositories

## 0.7.2 (2019-08-12)
- Fix typo

## 0.7.1 (2019-08-12)
- Fix insecure HTTPS errors when using --insecure

## 0.7.0 (2019-08-08)
- Add option to list remote repos then exit
- Ignore error when argument GitHub repository is not found
- Refactor into package
- Remove `consumers` dependency
