# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

* Static files now work out-of-the-box and `whitenoise` is always used to serve static files, not just in production.

## [0.1.0] - 2020-10-28

### Added

* Swapped out use of `environ.Env` for `environ.FileAwareEnv` to allow for loading environment variables from files in addition to standard environment variables.

## [0.2.0] - 2023-10-17

### Added

* Added `waitress` as default WSGI server on Windows installs.
