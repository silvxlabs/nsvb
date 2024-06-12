import os
import sys

TEST_ENV = os.getenv("TEST_ENV", "local")

if TEST_ENV == "local":
    print("Running tests in local environment")
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

if TEST_ENV == "test_pypi":
    print("Running tests in test_pypi environment")

if TEST_ENV == "pypi":
    print("Running tests in pypi environment")
