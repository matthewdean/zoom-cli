# zoom-cli

Command line interface for changing Zoom virtual backgrounds

## Usage

```
$ python zoom.py --help
usage:
  zoom background get             print the current background name
  zoom background set <file>      change the virtual background
  zoom background unset           disable the virtual background

  zoom background import <path>   add virtual background(s) from a given file or directory
  zoom background export <dir>    copy virtual backgrounds to a given directory
  zoom background list            enumerate virtual backgrounds
  zoom background deleteall       delete all custom virtual backgrounds

  zoom app start                  launch zoom app if not running
  zoom app stop                   terminate zoom app if running
  zoom app restart                terminate zoom app if running and then relaunch
```

## Notes
* Requires Python 3
* Zoom must be restarted for virtual background changes to take effect