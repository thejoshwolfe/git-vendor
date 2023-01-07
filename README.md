# git-vendor

Manage external git content in your git repo. This is like git submodules, but all the content is integrated into your content as though you copied it into your project and committed it normally. This means that collaborators running `git pull` will always get the content; no need to run any git submodule commands. Beyond initially copying the content, this tool can update the content when new changes are made by the upstream repository.

The main advantage of using `git-vendor` over other solutions (as of writing this), is that you can customize the vendored content via file name based filtering, and the filtering is maintained while updating the vendored content to new versions provided by the third party. This is conceptionally similar to maintaining a fork of a submodule, but it's all part of your main repo; no submodules.

Example use cases:

* You depend on an open source library (or a specific version of it) that isn't available in your system package manager. You opt to simply copy the entire source code at a tagged version into your project. You delete all the examples, unit tests, and CI/CD configuration from that project, since it doesn't matter for your project.
* Your organization maintains code in multiple repositories. An API schema in a server's repo is also needed to build a client in a different repo. Currently the client repo adds the entire server's codebase as a git submodule to just have access to the API schema, but that dependency is slowing down and complicating your CI/CD pipelines as well as straining the Principle of Least Privilege. You decide to copy the API schema alone into your client repo, and you need a way to keep the copy up to date with the server repo's release branch.

TODO: usage examples that demonstrate how this tool solves those problems.

<!--GEN_TOC_START-->
* [Status](#status)
* [Reference](#reference)
    * [Config file](#config-file)
    * [Common options](#common-options)
        * [`dir`](#dir)
        * [`url`](#url)
        * [`follow-branch`](#follow-branch)
        * [`pin-to-tag`](#pin-to-tag)
        * [`pin-to-commit`](#pin-to-commit)
        * [`subdir`](#subdir)
        * [`include`](#include)
        * [`exclude`](#exclude)
    * [Command line](#command-line)
* [git-vendor vs other options](#git-vendor-vs-other-options)
    * [brettlangdon/git-vendor](#brettlangdongit-vendor)
    * [`git submoudle`](#git-submoudle)
    * [`git subtree`](#git-subtree)
    * [ingydotnet/git-subrepo](#ingydotnetgit-subrepo)
<!--GEN_TOC_END-->

## Status

- [x] Basic initialization and download for a one-time import.
- [x] Following a branch with `--follow-branch`, and checking for and incorporating changes since the last download.
    - [x] Pinning content to a specific tag with `--pin-to-tag`. In this mode, the third-party server is assumed to never update the ref, and is not queried in the typical case.
    - [x] Pinning content to a specific commit with `--pin-to-commit`.
    - [x] The default is to follow the branch with the name determined via `git ls-remote --symref <url> HEAD`.
    - [x] Rudimentary support for repos using sha256 instead of sha1.
- [x] Configuration information stored in a file `.git-vendor-config` in your repo. Automatically gets edited as appropriate while maintaining formatting and comments.
    - [x] Convenient command to support removing vendored content.
    - [x] Convenient command to support renaming/moving local vendored content.
    - [x] Convenient command to support editing the config file.
    - [x] Validation for a manually edited config file.
    - [x] Quoting unusual characters in the config file uses shell syntax using Python's `shlex` module.
- [x] File name based include/exclude filtering of external content. The syntax is very similar to the gitignore syntax.
- [x] Vendoring a subdirectory instead of the entire project's directory structure. E.g. with `--dir=vendor/foo --subdir=src`, the external file `src/bar.txt` in your project becomes as `vendor/foo/bar.txt` with no `src` component.
- [x] Support for also vendoring the submodules of a vendored project while following the proper commit pointers. (They can be omitted with a file name based exclude rule.)
- [x] Proper documentation for command line interface and config file.
    - [x] Cleanup argparse CLI so that more options are accepted as positional arguments. E.g. `git-vendor mv --dir a/b/c --new-dir a/z/c` should instead be expressible as `git-vendor mv a/{b,z}/c` (in Bash).
- [ ] Unit tests for corner case error handling. (Code coverage?)
    - [ ] Probably should suppress stack traces on all `CalledProcessError`.
    - [ ] Don't show AssertionError stack traces for invalid user input.
- [ ] Audit local named ref usage and how it relates to objects being orphaned and gc'ed too soon, or perhaps never being gc'ed when they should.
- [ ] Declare 1.0 stable, and move the remaining unfinished items in this list to GitHub Issues.

## Reference

Several config file options and command line options are equivalent,
where `<name>=<value>` in the config file is equivalent to `--<name>=<value>` on the command line.
The following is the list of options equivalent between the two:

* `dir`
* `url`
* `follow-branch`
* `pin-to-tag`
* `pin-to-commit`
* `subdir`
* `include`
* `exclude`

The following option appears in config files, but is not intended to be edited directly.
It is used internally by `git-vendor`:

* `commit`

There are several more options that only appear in the command line interface.

### Config file

The config file is comprised of lines delimited by `"\n"` LF UNIX style line endings.
Leading and trailing whitespace of each line are ignored (via Python's
[`str.strip()`](https://docs.python.org/3/library/stdtypes.html#str.strip) method).
Then, if a line is blank or begins with `#`, it is ignored.

If the config file is empty (after ignoring lines), the config file contains no sections,
which is equivalent to the config file not existing.
Otherwise, the config file is split into sections delimited by `---` lines.
Empty sections are not allowed.
(The number of `---` lines is exactly 1 less than the number of sections.)

An option line contains three tokens: a name, an `=`, and a value.
Whitespace surrounding each of these tokens is ignored.
The option name must be one of the recognized config file option names.
The option value is parsed using shell-like quoting rules via Python's
[`shlex.split()`](https://docs.python.org/3/library/shlex.html#shlex.split) function.
Typically, this means that no quoting is necessary, but if the value contains whitespace
or other special shell characters, it must be quoted using `'` characters,
or any other quoting recognized by `shlex.split()`.
If `shlex.split()` finds multiple tokens, it is an error.

If a line is not ignored, not `---`, and not recognized as an option line, it is an error.

Each section must contain a `dir` option which uniquely identifies the section.
In config files, the `dir` option is resolved relative to the repo root (where the config file is),
and must be a *canonicalized relative path*.

A **canonicalized relative path** is a path using `/` for directory separators regardless of platform,
and must begin with a character other than `/`, must not contain `//`, must not contain any `.` or `..` segments,
and on Windows must not contain `\`.

### Common options

These options appear in the config file and the command line API.

#### `dir`

The directory in your repo where the vendored content will be located.
This option is required in every config file section and must be unique in the config file.
In the config file, the path is resolved relative to your repo root
and must be a *canonicalized relative path* (see above).

On the command line, this option is is resolved relative to the cwd
rather than the repo root and is canonicalized internally.
Several commands take this option as either a position argument or a keyword arugment.

<!--GEN_DOCS_START-->
#### `url`

URL of the external git repo. See `git help clone` for acceptable URL formats.
Note that relative paths are sometimes accepted by git,
but git-vendor does not allow local path URLs that are relative paths;
use absolute paths instead (see also issue https://github.com/thejoshwolfe/git-vendor/issues/6 ).

#### `follow-branch`

A branch name identifies the commit of the external repo to use.
This method of identifying a commit communicates with the remote server
whenever updating the local content to check if the branch points to a new commit.
If the branch specified does not begin with `refs/`, then a prefix of `refs/heads/`
is prepended automatically (this is how branches are named in git.).
If the given branch begins with `refs/`, then it will be used as-is,
regardless of whether it really refers to a branch (aka head).

This mode is the default during `git-vendor add` if none of
`--follow-branch`, `--pin-to-tag`, or `--pin-to-commit` are specified.
The branch to follow is determined by getting the 'HEAD' branch name from the remote.
This is typically 'main'.
(It is determined by `git ls-remote --symref <url> HEAD`.)

#### `pin-to-tag`

A tag name identifies the commit of the external repo to use.
This method of identifying a commit only communicates with the remote server
on initial configuration or in any other case where the resolved commit is unknown/uncached locally.
If the given name does not begin with `refs/`, then a prefix of `refs/tags/`
is prepended automatically (this is how tags are named in git.).

#### `pin-to-commit`

Identifies a specific commit to be used from the external repo.
This method of identifying a commit only communicates with the remote server
on initial configuration or in any other case where the object data for the commit is not cached locally.
Note that this option may not work for all git server configurations; see https://github.com/thejoshwolfe/git-vendor/issues/4 .

#### `subdir`

Subdirectory within the external repo that is the root of the content to be vendored.

In the config file, this must be a *canonicalized relative path* (see above).

#### `include`

Indicates that only certain content is to be included from the external repo.
The given patterns identify files by name in a syntax similar to `git help ignore`,
but with some differences (see below).

If this option is unspecified, then all content is implicitly included.
This option can be specified multiple times, and the union of matches will be included.
When this option and `exclude` are both specified, then `exclude` is higher priority;
i.e. anything excluded by `exclude` can never be un-excluded by `include` or any other means.

The following specification for this option and `exclude` is adapted from `git help ignore`:

1) The slash `/` is used as the directory separator.
   Separators may occur at the beginning, middle or end of each pattern.
2) If there is a separator at the beginning or middle (or both) of the pattern,
   then the pattern is relative to the external repo root.
   Otherwise the pattern may also match at any level within the external repo.
3) If there is a separator at the end of the pattern then the pattern will only match directories,
   otherwise the pattern can match both files and directories.
   For example, a pattern `doc/frotz/` matches `doc/frotz` directory, but not `a/doc/frotz` directory;
   however `frotz/` matches `frotz` and `a/frotz` that is a directory
   (all paths are relative from the external repo root).
4) An asterisk `*` matches anything except a slash. The character `?` matches any one character except `/`.
   The range notation, e.g. `[a-zA-Z]`, can be used to match one of the characters in a range.
   See https://docs.python.org/3/library/fnmatch.html for a more detailed description.
5) Two consecutive asterisks `**` in patterns matched against full pathname may have special meaning:
   1)  A leading `**` followed by a slash means match in all directories.
       For example, `**/foo` matches file or directory `foo` anywhere, the same as pattern `foo`.
       `**/foo/bar` matches file or directory `bar` anywhere that is directly under directory `foo`.
   2)  A trailing `/**` is *not allowed*. It is equivalent to omitting it, so please just omit it.
       (This is a deviation from the `git help ignore` specification.)
   3)  A slash followed by two consecutive asterisks then a slash matches zero or more directories.
       For example, `a/**/b` matches `a/b`, `a/x/b`, `a/x/y/b` and so on.
   4)  Other consecutive asterisks are considered regular asterisks and will match according to the previous rules.
6) After splitting the pattern on `/`, if any segment is empty, `.`, or `..`, the pattern is invalid.
   (This is a deviation from the `git help ignore` specification.)
7) Leading, trailing, or internal whitespace is supported by the normal quoting rules
   (your shell, or the .git-vendor-config file syntax, etc.).

#### `exclude`

Indicates that some content is to be excluded from the external repo.
This option can be specified multiple times, and all matches are excluded.
The syntax for this option is identical to `include`.
When this option and `include` are both specified, then this option is higher priority;
i.e. anything excluded by this option can never be un-excluded by `include` or any other means.

Note that if the external repo includes git submodules, those will be recursively fetched and included
unless they are excluded by this option (or not included by `include`).
<!--GEN_DOCS_END-->

### Command line

Much of the above information is duplicated in the command line help,
which is fully accessible via:

```
git-vendor --help
git-vendor [command] --help
```

## git-vendor vs other options

| | `git submodule` | `git subtree` | [git-subrepo (ingydotnet)](https://github.com/ingydotnet/git-subrepo) | [git-vendor (brettlangdon)](https://github.com/brettlangdon/git-vendor) | git-vendor (this repo) | manual copy |
| --- | --- | --- | --- | --- | --- | --- |
| just works for collaborators | ❌[1] | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| version-controlled config file | ✔️ | ❌ | ✔️ | ❌[2] | ✔️ | ❌ |
| push as maintainer | ✔️ | ✔️ | ✔️ | ✔️ | ❌ | ❌ |
| fully a git repo | ✔️ | ❌ | ❌ | ❌ | ❌ | ❌ |
| file name based filtering | ❌ | ❌ | ❌ | ❌ | ✔️ | ✔️ |
| non-trivial patches | ❌[3] | ❌[3] | ❌[3] | ❌[3] | ❌[3] | ✔️ |
| implementation | built-in | built-in | bash | sh | python | manual |
| stars on github | celebrity | celebrity | lots | modest | few | |

* [1] git submodules do not get initialized on clone and do not get updated on pull.
* [2] brettlangdon/git-vendor stores configuration information in git commit messages.
* [3] to maintain non-trivial patches, you'd need to maintain your own fork, then vendor the fork.

#### [brettlangdon/git-vendor](https://github.com/brettlangdon/git-vendor)

That project is a great start, but it's limited in functionality and written in a language hostile to complexity. In addition, it uses git commit messages as a source of truth for configuration, which does not play well with GutHub projects that require squash-merging all pull requests. I haven't checked to see if there are any performance issues to be worried about when using `git log --grep` to read configuration information, but it smells like the wrong tool for the job.

The main issue with that project is simply its missing features. I at least want file name based include/exclude filtering, which optimally[1] involves pretty heavy algorithmic use of `git mktree`, and I have no interest in solving that problem in `sh`. Although the code in that project appears to be very high quality and well maintained software, I expect that a reimplementation in a more popular programming language (in this case Python) will improve collaboration.

I named my project the same as that one with the intent to obviate it for every use case. The main drawback of my project is that it depends on Python 3. (And also my project is unfinished as of writing this.)

[1] It's possible to use simple `git add -A` on local file system content instead of fancy `mktree` algorithms, but that involves multiple additional moving parts and opportunities for things to go wrong and be surprising. For example, your global ignore rules might prevent some of the content from getting added, or the file system's case insensitivity or unicode normalization might cause surprises. In terms of what actually happens between these two approaches, `git add` seems simple at first, but `mktree` is more correct.

#### `git submoudle`

For some reason, the command line user experience of git submodules is seemingly designed to be atrocious. Just to start off the complaining train, `git status` does not warn you about uninitialized submodules someone else has added to your project. (And the default behavior of `git clone` does not initialize submodules.) This simple problem accounts for about 60% of the wasted time debugging why "something's wrong" with a repository in my experience.

The next car in the complaining train is that `git submodule update` does not update submodules. Whenever I tell a colleague at work to "update the submodule to the latest version", I have to remember to clarify that this does not mean `git submodule update`. There doesn't seem to be any first-class mechanism built into git to update a submodule to point to the latest content pointed to by a named ref, such as the `main` branch of the external repo. The simplest command I've found to do this is: `(cd path/to/submodule && git fetch && git checkout origin/main) && git add path/to/submodule`. Is that really the best we can do? *UPDATE*: I've just discovered the `--branch` and `--remote` options in `git help submodule`. I have yet to try them, but they claim to do exactly what I'm asking for here.

I could go on complaining about how replacing a submodule with a regular directory breaks everyone's `git pull`, or how the hidden content in the `.git/modules` directory will cause subtle errors if you ever try to replace a submodule with another one at the same path, but that's starting to get into niche territory (all of which I have actually run into in a professional environment). The crux of the problem is that git submodules are also functioning git repositories, which introduces tons of complexity unsuitable for a vendoring usecase.

If you were to try to solve the filtering use case with a submodule, it would probably come in the form of a commit that applies the changes you want. This probably means forking the dependency under your own user/organization/server and pushing one or more commits. When new changes are made to the third-party content, you would probably try doing a merge between their changes and your patch. However, if your real intention is to *ignore* the content of the `examples/` directory, for example, then a commit that deletes all the content there is the wrong tool for the job. That commit would cause a merge conflict when anything in the content is changed, and would completely miss new additions to the directory. This is an example of how file name based filtering better expresses intent, and is more suitable to the vendoring use case.

#### `git subtree`

Git subtree solves the collaboration problems by embedding the vendored content in your own repo, but it seems like a low-level command designed to have automation built on top of it. For example, every time you want to pull the latest changes, you have to specify the url again.

Additionally, `git subtree` does not support file name based filtering, which is important for my usecase.

#### [ingydotnet/git-subrepo](https://github.com/ingydotnet/git-subrepo)

That tool solves a slightly different problem. `git-subrepo` is close to a feature-equivalent replacement for git submodules with an emphasis on pushing changes as collaborators. By contrast, `git-vendor` is more designed for a readonly view of someone else's code only upstreaming patches on rare occasions.

It's great that people are trying to patch the design flaws in git submodules. I'm a fan of the idea of `git-subrepo`. I'm a bit surprised it's implemented in Bash, but that's a small complaint. As far as I can tell that project does not support file name based filtering, which is important for my usecase, but I see something in there about `filter-branch`? Maybe it does support file name based filtering; I can't tell.

I haven't researched `git-subrepo` thoroughly; maybe you should use that tool for your usecase depending on what you need.
