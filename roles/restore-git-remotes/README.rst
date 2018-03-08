Add origin remote to checked-out repositories

Zuul currently does not keep remotes for repositories, but some of our
code depends on them to get diff (list of modified files, etc.).
