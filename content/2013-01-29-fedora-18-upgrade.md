title: Fedora 18 upgrade issues
category: Fedora
date: 2013-01-29
tags: Fedora, pulseaudio

Upgrading my fedora installation from 17 to 18 went suprisingly
smooth using [fedup] [1]. The only issue was pulseaudio refusing
to start. Turns out some pulseaudio module hade changed name, but
/etc/pulse/default.pa hadn't been updated. Replacing
"load-module module-cork-music-on-phone" with
"load-module module-role-cork" fixed that.
Maybe i had edited that file manually and it wasn't updated properly?

[1]: http://fedoraproject.org/wiki/FedUp#Network
