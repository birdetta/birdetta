#!/bin/sh
rm retux.pot
cp datatext.pot retux.pot
xgettext -j -o retux.pot --msgid-bugs-address="diligentcircle@riseup.net" --add-comments="/" ../../retux.py
