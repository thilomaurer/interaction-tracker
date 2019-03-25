#!/bin/bash
cd $(readlink -m $(dirname $0))
xinput --test-xi2 --root | ./tracker.py
