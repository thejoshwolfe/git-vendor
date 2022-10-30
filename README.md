# git-vendor

Manage external git content in your git repo. This is like git submodules, but all the content is integrated into your content as though you copied it into your project and committed it normally. This means that collaborators running `git pull` will always get the content; no need to run any git submodule commands. Beyond initially copying the content, this tool can update the content when new changes are made by the upstream repository.

The main advantage of using `git-vendor` over other solutions (as of writing this), is that you can customize the vendored content via filtering and patching, and these transformations are maintained while updating the vendored content to new versions provided by the third party. This is conceptionally similar to maintaining a fork of a submodule, but it's all part of your main repo; no submodules.

Example use cases:

* You depend on an open source library (or a specific version of it) that isn't available in your system package manager. You opt to simply copy the entire source code at a tagged version into your project. You delete all the examples, unit tests, and CI/CD configuration from that project, since it doesn't matter for your project.
* You're trying to build the above library with CMake, and it requires several modifications to integrate into your build system. Then you find a bug in the above library's code, and you patch that too. The upstream maintainers may or may not merge any of these changes into their code base. Whenever you update the library to a newer tagged version, you want to make sure the patches you've applied persist.
* Your organization maintains code in multiple repositories. An API schema in a server's repo is also needed to build a client in a different repo. Currently the client repo adds the entire server's codebase as a git submodule to just have access to the API schema, but that dependency is slowing down and complicating your CI/CD pipelines as well as straining the Principle of Least Privilege. You decide to copy the API schema alone into your client repo, and you need a way to keep the copy up to date with the server repo's release branch.

TODO: usage examples that demonstrate how this tool solves those problems.

## Status

- [x] Basic initialization and download for a one-time import.
- [x] Following a branch with `--follow-branch`, and checking for and incorporating changes since the last download.
    - [x] Pinning content to a specific tag with `--pin-to-tag`. In this mode, the third-party server is assumed to never update the ref, and is not queried in the typical case.
    - [x] Pinning content to a specific commit with `--pin-to-commit`.
    - [x] Hypothetical untested support for repos using sha256 instead of sha1.
    - [ ] Support for remotes that don't have the `allow-tip-sha1-in-want` capability, such as `https://git.ffmpeg.org/ffmpeg.git`. I can't figure out how to tell if a git remote has this capability before trying and failing a `git fetch`. Somehow `git submodule update` knows how to do it. Maybe it's time to read the source.
- [x] Configuration information stored in a file `.git-vendor-config` in your repo. Automatically gets edited as appropriate while maintaining formatting and comments.
    - [x] Convenient command to support removing vendored content.
    - [x] Convenient command to support renaming/moving local vendored content.
    - [ ] Convenient command to support editing the config file. Validation for a manually edited config file.
    - [ ] Support some kind of quoting/escaping syntax for unusual characters in the config file.
- [x] File name based include/exclude filtering of external content. The syntax is very similar to the gitignore syntax.
- [x] Vendoring a subdirectory instead of the entire project's directory structure. E.g. with `--dir=vendor/foo --subdir=src`, the external file `src/bar.txt` in your project becomes as `vendor/foo/bar.txt` with no `src` component.
- [x] Support maintaining local patches to the external content (in addition to subdir and include/exclude filters) that survive incoming updates to the third-party content.
    - [x] Support viewing the patches in an interface like `git diff`.
    - [ ] Support exporting the patches to an external repository of the third-party content to facilitate submitting the changes upstream.
- [x] Support for also vendoring the submodules of a vendored project while following the proper commit pointers. (They can be omitted with a filename based exclude rule.)
- [ ] Proper documentation for command line interface and config file.
    - [ ] Cleanup argparse CLI so that more options are accepted as positional arguments. E.g. `git-vendor mv --dir a/b/c --new-dir a/z/c` should instead be expressible as `git-vendor mv a/{b,z}/c` (in Bash).
- [ ] Unit tests for corner case error handling. (Code coverage?)
    - [ ] Probably should suppress stack traces on all `CalledProcessError`.
- [ ] Support for non-utf8 file names. (This means proper juggling of bytes vs strings in Python 3; currently the code assumes everything is valid utf8 and converts it all to `str` for convenience. Alas, Python 2's str would have actually worked better; see [utf8everywhere.org](https://utf8everywhere.org/).)
- [ ] Audit local named ref usage and how it relates to objects being orphaned and gc'ed too soon, or perhaps never being gc'ed when they should.
- [ ] Declare 1.0 stable, and move the remaining unfinished items in this list to GitHub Issues.

## git-vendor vs other options

| | `git submodule` | `git subtree` | [ingydotnet/git-subrepo](https://github.com/ingydotnet/git-subrepo) | [brettlangdon/git-vendor](https://github.com/brettlangdon/git-vendor) | thejoshwolfe/git-vendor (this) | manual copy |
| --- | --- | --- | --- | --- | --- | --- |
| just works for collaborators | ❌[1] | ✔️ | ✔️ | ✔️ | ✔️ | ✔️ |
| version-controlled config file | ✔️ | ❌ | ✔️ | ❌[2] | ✔️ | ❌ |
| push as maintainer | ✔️ | ✔️ | ✔️ | ✔️ | ❌ TODO | ❌ |
| fully a git repo | ✔️ | ❌ | ❌ | ❌ | ❌ | ❌ |
| file name based filtering | ❌ | ❌ | ❌ | ❌ | ✔️ | ✔️ |
| non-trivial patches | ❌[3] | ❌[3] | ❌[3] | ❌[3] | ❌[3] TODO | ✔️ |
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

If you were to try to solve the filtering and patching use case with a submodule, it would probably come in the form of a commit that applies the changes you want. This probably means forking the dependency under your own user/organization/server and pushing one or more commits. When new changes are made to the third-party content, you would probably try doing a merge between their changes and your patch. However, if your real intention is to *ignore* the content of the `examples/` directory, for example, then a commit that deletes all the content there is the wrong tool for the job. That commit would cause a merge conflict when anything in the content is changed, and would completely miss new additions to the directory. This is an example of how file name based filtering better expresses intent, and is more suitable to the vendoring use case.

#### `git subtree`

Git subtree solves the collaboration problems by embedding the vendored content in your own repo, but it seems like a low-level command designed to have automation built on top of it. For example, every time you want to pull the latest changes, you have to specify the url again.

Additionally, `git subtree` does not support file name based filtering, which is important for my usecase.

#### [ingydotnet/git-subrepo](https://github.com/ingydotnet/git-subrepo)

That tool solves a slightly different problem. `git-subrepo` is close to a feature-equivalent replacement for git submodules with an emphasis on pushing changes as collaborators. By contrast, `git-vendor` is more designed for a readonly view of someone else's code only upstreaming patches on rare occasions.

It's great that people are trying to patch the design flaws in git submodules. I'm a fan of the idea of `git-subrepo`. I'm a bit surprised it's implemented in Bash, but that's a small complaint. As far as I can tell that project does not support file name based filtering, which is important for my usecase, but I see something in there about `filter-branch`? Maybe it does support file name based filtering; I can't tell.

I haven't researched `git-subrepo` thoroughly; maybe you should use that tool for your usecase depending on what you need.
