# Style:

This is small pet project repository,
When introducing or modifying feature, make it simple, do not write tests.
This app will be executed in Raspberry Pi

Back-end:
python, fast api.
Make sure, that python files have less than 200 lines of code.

Front-end:
Make front-end singlepage html, with a minimal set of javascript files.
Make sure, that js files have less than 200 lines of code.

Use port 8001, as developer often run app on this app on port 8000.
If testing requires moving camera and checking objects, kill app server on prot 8000 before staring tests.

Always kill testing server on port after user problem was implemented and tested.
