# git-vendor

Manage external git content in your repo.
This is like git submodules, but all the content is integrated into your content as though you copy-pasted it all into a directory.
This means that collaborators running `git pull` will always get the content regardless of any follow-up `git submodule update --init --recrusive` or whatever.

## Status

- [x] Basic initialization and download for a one-time import.
- [x] Following a branch or other named ref, and checking for and incorporating changes since the last download.
- [x] Pinning vendored content to a specific commit instead of following a named ref.
- [x] File name based include/exclude filtering of external content using python's `fnmatch` mechanism.
- [x] Configuration information stored in a file `.git-vendor-config` in your repo. Automatically gets edited as appropriate while maintaining formatting and comments.
- [x] Convenient command to support removing vendored content.
- [x] Convenient command to support renaming/moving local vendored content.
- [x] Vendoring a subdirectory instead of the entire project's directory structure. E.g. with `--dir=vendor/foo --subdir=src`, the external file `src/bar.txt` in your project becomes as `vendor/foo/bar.txt` with no `src` component.
- [ ] Noticing local changes applied to the external content, and facilitating pushing the changes somewhere.
- [ ] Maintaining local changes that are not intended to be pushed (other than the include/exclude filters above), and facilitating pushing without these local edits. This could be patches to file contents or file renames perhaps.
- [ ] Proper documentation for command line interface and config file.
- [ ] Support for also vendoring the submodules of a vendored project while following the proper commit pointers.

## git-vendor vs other options

#### [brettlangdon/git-vendor](https://github.com/brettlangdon/git-vendor)

That project is a great start, but it's limited in functionality and written in a language hostile to complexity. In addition, it uses git commit messages as a source of truth for configuration, which does not play well with GutHub projects that require squash-merging all pull requests. I haven't checked to see if there are any performance issues to be worried about when using `git log --grep` to read configuration information, but it smells like the wrong tool for the job.

The main issue with that project is simply its missing features. I at least want file name based include/exclude filtering, which optimally[1] involves pretty heavy algorithmic use of `git mktree`, and I have no interest in solving that problem in `sh`. I expect other enthusiasts share my distaste for complex Bash software, so a reimplementation in Python should improve collaboration as a bonus.

[1] It's possible to use simple `git add -A` on local file system content instead of fancy `mktree` algorithms, but that involves multiple additional moving parts and opportunities for things to go wrong and be surprising. For example, your global ignore rules might prevent some of the content from getting added, or the file system's case insensitivity or unicode normalization might cause surprises. In terms of what actually happens between these two approaches, `git add` seems simple at first, but `mktree` is more correct.

#### Just submodules

For some reason, the command line user experience of git submodules is seemingly designed to be atrocious. Just to start off the complaining train, `git status` does not warn you about uninitialized submodules someone else has added to your project. (And the default behavior of `git clone` does not initialize submodules.) This simple problem accounts for about 60% of the wasted time debugging why "something's wrong" with a repository in my experience.

The next car in the complaining train is that `git submodule update` does not update submodules. Whenever I tell a colleague at work to "update the submodule to the latest version", I have to remember to clarify that this does not mean `git submodule update`. There doesn't seem to be any first-class mechanism built into git to update a submodule to point to the latest content pointed to by a named ref, such as the `main` branch of the external repo. The simplest command I've found to do this is: `(cd path/to/submodule && git fetch && git checkout origin/main) && git add path/to/submodule`. Is that really the best we can do?

I could go on complaining about how replacing a submodule with a regular directory breaks everyone's `git pull`, or how the hidden content in the `.git/modules` directory will cause subtle errors if you ever try to replace a submodule with another one at the same path, but that's starting to get into niche territory (all of which I have actually run into in a professional environment). The crux of the problem is that git submodules are also functioning git repositories, which introduces tons of complexity unsuitable for a vendoring usecase.

One small advantage of vendoring content over using submodules is the ability to elide unnecessary information: only including the files you want and ignoring the project's history. You might consider this just an optimization, but it's nice to have. This also applies to the vendored content's own git submodules if any; it's common to always include `--recursive` in submodule operations, which means you always get the sub-sub-modules you might not actually need.

#### [ingydotnet/git-subrepo](https://github.com/ingydotnet/git-subrepo)

That tool solves a slightly different problem. `git-subrepo` is close to a feature-equivalent replacement for git submodules with an emphasis on pushing changes as collaborators. By contrast, this tool is more designed for a readonly view of someone else's code only creating patches on rare occasions.

It's great that people are trying to patch the design flaws in git submodules. I'm a fan of the idea of `git-subrepo`. I'm a bit surprised it's implemented in Bash, but that's a small complaint. As far as I can tell that project does not support file name based filtering, which is important for my usecase, but I see something in there about `filter-branch`? Maybe it does support file name based filter; I can't tell.

I haven't researched `git-subrepo` thoroughly; maybe you should use that tool for your usecase depending on what you need.
