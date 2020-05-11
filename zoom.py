import argparse
from lib import zoomconfig, zoomapp

parser = argparse.ArgumentParser(
    prog="zoom",
    usage="""
  zoom background get             print the current background name
  zoom background set <file>      change the virtual background
  zoom background unset           disable the virtual background

  zoom background import <path>   add virtual background(s) from a given file or directory
  zoom background export <dir>    copy virtual backgrounds to a given directory
  zoom background list            enumerate virtual backgrounds
  zoom background deleteall       delete all custom virtual backgrounds

  zoom app start                  launch zoom app if not running
  zoom app stop                   terminate zoom app if running
  zoom app restart                terminate zoom app if running and then relaunch"""
)

subparsers = parser.add_subparsers(dest="category", help=argparse.SUPPRESS)
subparsers.add_parser("background")
subparsers.add_parser("app")
args, remaining_args = parser.parse_known_args()

if args.category == "background":
    background_parser = argparse.ArgumentParser()
    subparsers = background_parser.add_subparsers(dest="command")
    get_background_parser = subparsers.add_parser("get")
    set_background_parser = subparsers.add_parser("set")
    set_background_parser.add_argument("path")
    unset_background_parser = subparsers.add_parser("unset")
    deleteall_background_parser = subparsers.add_parser("deleteall")
    list_parser = subparsers.add_parser("list")
    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("path")
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("path")
    args = background_parser.parse_args(remaining_args)
    z = zoomconfig.open()
    if args.command == "get":
        print("current background: " + z.get_background())
    elif args.command == "set":
        z.set_background(args.path)
    elif args.command == "unset":
        z.set_background(None)
    elif args.command == "deleteall":
        z.delete_custom_backgrounds()
    elif args.command == "list":
        backgrounds = z.get_backgrounds()
        print("you have " + str(len(backgrounds)) + " backgrounds:")
        for background in backgrounds:
            print(background.name)
    elif args.command == "import":
        z.import_backgrounds(args.path)
    elif args.command == "export":
        z.export_backgrounds(args.path)
    else:
        background_parser.error("unhandled command: " + args.command)
    z.close()
elif args.category == "app":
    app_parser = argparse.ArgumentParser()
    subparsers = app_parser.add_subparsers(dest="command")
    start_parser = subparsers.add_parser("start")
    stop_parser = subparsers.add_parser("stop")
    restart_parser = subparsers.add_parser("restart")
    args = app_parser.parse_args(remaining_args)
    if args.command == "start":
        zoomapp.start()
    elif args.command == "stop":
        zoomapp.stop()
    elif args.command == "restart":
        zoomapp.restart()
    else:
        app_parser.error("unhandled command: " + args.command)
else:
    parser.error("the following arguments are required: category")