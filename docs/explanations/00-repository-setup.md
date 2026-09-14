# 00. Setting up the repository

A repository is a folder whose whole history git remembers. Each time we reach
a point worth keeping we make a commit: a snapshot of the folder plus a one-line
note on what changed. It is like saving a game. If a later change breaks
something, we can load an earlier save and compare the two.

Some files must never enter that history: the virtual environment (a private
copy of Python and its libraries, gigabytes in size), caches, secrets, and
working notes. The .gitignore file lists them, and git never records a file it
is told to ignore. That is why .gitignore was the very first commit. A file
that slips into history stays in every later snapshot, and removing it means
rewriting the past, which is easy to get wrong.

Hooks are small scripts that git runs at fixed moments. The commit-msg hook
removes any co-author trailer a tool tries to append, so the repository owner
is the only author on record, and it rejects subjects over 60 characters. The
pre-push hook refuses to send anything to a server unless ALLOW_PUSH=1 is set
on purpose. Git keeps hooks in a folder it does not track, so a fresh clone has
none. Copies live in scripts/hooks with an install script for that reason.

A common misconception: committing often makes the history messy. Small
commits with clear notes are what make a history readable, and they let you
find the exact change that broke something.

Summary: git records the snapshots we choose to keep, .gitignore decides what
may never enter them, and hooks enforce two house rules automatically: no
attribution lines and no pushing by accident.
