# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project starting adhering to [Semantic Versioning](http://semver.org/spec/v2.0.0.html) as of version 0.7.0.

## [Unreleased]

- Add a custom Course Feedback tab.

## [1.0.0] - 2019-05-14

- Merge changes from ISC Ficus specific branch.  No longer Dogwood compatible

## [0.7.1-cmc-dogwood] - 2019-05-14

- Likely final release maintaining CMC Dogwood function.

## [0.7.1] - 2018-05-14
### Changed
- Bug fix: fix local storage dir values in report tasks.

## [0.7.0] - 2018-05-14
### Added
- Started keeping a Changelog
- Allow usage of an additional path prefix for S3 uploads, defined by env token CMC_COURSE_COMPLETION_S3_FOLDER or ISC_COURSE_COMPLETION_S3_FOLDER.
- Improve error handling in running the CMC report task.

### Changed
- Start using semantic versioning.  So, we jumped from ver 0.66, to 0.7.0.  0.66 really should have been 0.6.6. 0.7.0 isn't truly backwards-incompatible, but it is in terms of versioning and makes a cleaner break.  0.7.x will be the last Dogwood-compatible minor version.  

### Removed
- VA microsite report (that microsite is no longer used).
