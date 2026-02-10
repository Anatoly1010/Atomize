import atomize.general_modules.general_functions as general

for i in general.scans(5):
    general.message(i)
    if i > 10:
        break


