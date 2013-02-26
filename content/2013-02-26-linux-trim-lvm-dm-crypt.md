title: Linux and TRIM with lvm and dm-crypt on SSDs.
category: Linux
date: 2013-02-26
tags: Linux, TRIM

I had made the assumption that [TRIM] [1] was enabled by default
nowadays. Apparently not. To enable it for your filesystems, edit
/etc/fstab and add "discard" as a mount option:

    /dev/mapper/vg_foo-lv_home /home                   ext4    defaults,noatime,discard        1 2
    /dev/mapper/vg_foo-lv_swap swap                    swap    defaults,discard        0 0

Might also want to add noatime, it's not really needed.

To enable it for LVM, edit /etc/lvm/lvm.conf and change

    issue_discards = 0

to

    issue_discards = 1

To enable it for dm-crypt/luks, edit /etc/crypttab and add discard to the option column:

    luks-33ed4f53-a649-b6b5-b871-7de44efdf1aa4 UUID=luks-33ed4f53-a649-b6b5-b871-7de44efdf1aa4 none luks,discard

A word of warning though, enabling TRIM with disk encryption may be
a **security risk**. 

[1]: http://en.wikipedia.org/wiki/TRIM
