#!/bin/bash
# EVENT type 0 (Any)
# EVENT type 1 (DeviceChanged)
# EVENT type 2 (KeyPress)
# EVENT type 3 (KeyRelease)
# EVENT type 4 (ButtonPress)
# EVENT type 5 (ButtonRelease)
# EVENT type 6 (Motion)
# EVENT type 8 (Leave)
# EVENT type 9 (FocusIn)
# EVENT type 10 (FocusOut)
# EVENT type 11 (HierarchyChanged)
# EVENT type 12 (PropertyEvent)
# EVENT type 13 (RawKeyPress)
# EVENT type 14 (RawKeyRelease)
# EVENT type 15 (RawButtonPress)
# EVENT type 16 (RawButtonRelease)
# EVENT type 17 (RawMotion)

cd $(readlink -m $(dirname $0))
xinput --test-xi2 --root | ./tracker.py --ignore-event-type 11 12 |& tee tracker.log
