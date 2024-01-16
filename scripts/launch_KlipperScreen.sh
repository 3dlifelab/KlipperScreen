#!/usr/bin/env bash

# Use display 10 to avoid clashing with local X server, if anyy
Xtigervnc -rfbport 5900 -noreset -AlwaysShared -SecurityTypes none :10&
DISPLAY=:10 $KS_XCLIENT&
wait
