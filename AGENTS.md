# Style:

This is small pet project repository,
When introducing or modifying feature, make it simple, do not write tests.
This app runs on a Mac host and can talk to an ESP32-D0WDQ6 LED light controller.

Back-end:
python, fast api.
Make sure, that python files have less than 200 lines of code.

Front-end:
Make front-end singlepage html, with a minimal set of javascript files.
Make sure, that js files have less than 200 lines of code.

Use port 8001, as developer often run another app on port 8000.
If testing requires moving camera and checking objects, kill app server on prot 8000 before staring tests.

Always kill testing server on port after user problem was implemented and tested.
