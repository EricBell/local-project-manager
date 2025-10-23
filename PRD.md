# Product Requirements Document

## Overview
Local Project Manager helps identify projects, manage them, and prune ones you don't want any more.

## Requirements

1. TUI app written in Python and textual.
2. Scans the current directory and subdirectories (or any directory you indicate and subdirectories).
3. Looks for README files (.md, .txt).
4. Shows a list of all the README files and their paths.
5. Show a list of all the project paths without README files.
6. Existing README files can be viewed in a scrolling/paging pane as well as edited and deleted.
7. If README file does not exist in a directory one can be created.
8. Has a configurable list of directories to ignore. Initial list are all node_modules directories.
9. Other directories to ignore are subprojects e.g. if the top level directory is site2pdf and it contains libraries like version/ and todo/ which each have READMEs these subprojects can be ignored if directed to.
