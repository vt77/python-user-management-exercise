#!/bin/sh
python3 -m unittest tests.test_model.TestModel -vvv
python3 -m unittest tests.test_db_sqlite.TestSqLiteBackend -vvv
python3 -m unittest tests.test_api.TestApi -vvv
