---
title: Concurrency
nav_order: 12
layout: page
permlink: /functions/general_functions/concurrency/
parent: General Funtions
grand_parent: Documentation
---

---

It is possible to run a function in a separate thread, different from the main one, and get return values from this function. This can be done using the returned_thread module. A minimal example is as follows:

```python
import atomize.general_modules.returned_thread as returnThread

prWait = returnThread.rThread(target = general.wait, args=('150 ms', ), kwargs={})
prWait.start()
# do some other stuff
prWait.join()
# if a function returns something:
# returned_value1 = prWait.join()
```