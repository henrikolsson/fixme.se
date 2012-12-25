title: Disable automatic ungrab/grab in VMware
category: VMware
date: 2012-12-26
tags: VMware

When you play games in VMware it's quite useful to be able to
lock the mouse inside the vm. Normally when VMware tools are
installed, it automatically ungrabs the mouse when you leave
the window. To change this, edit ~/.vmware/preferences and add:

    pref.motionGrab = "FALSE"
    pref.motionUngrab = "FALSE"

Edit the vmx-file for your virtual machine and add:

    vmmouse.present = FALSE

And that's it. You can switch the grab-state with the keyboard,
by default it's bound to CTRL+ALT.

