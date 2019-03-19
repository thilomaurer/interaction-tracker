#!/bin/bash
xinput --test-xi2 --root | ./tracker.py | tee tracker.log
