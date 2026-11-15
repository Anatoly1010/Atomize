from importlib.util import find_spec

if find_spec('atomize.main.main'):
    from atomize.main.main import main
else:
    from atomize.main.main_window import main
main()
