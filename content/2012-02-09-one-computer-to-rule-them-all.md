title: One computer to rule them all
category: Xen
tags: linux, xen
date: 2012-02-09

Loathing using windows but still enjoying the occasional gaming is somewhat 
of a problem. Although wine has improved majorly over the last years, it's 
still somewhat of hit and miss using it for games. After reading success 
stories from people using VGA passthrough with Xen i decided to give that a 
try. 

My Setup
-------------

Hardware:

    ASRock Z68 Extreme4 GEN 3 (known to support VT-d)
    Intel i7 2600 (beware, the K-versions do NOT support VT-d)
    Radeon HD 6950

I decided to settle on Debian Testing (wheezy) as my dom0 (host) os. 
First step is installing Xen:

    # apt-get install xen-hypervisor-4.1-amd64 xen-tools xen-utils
    
Now reboot and you should see a Xen choice in grub. Next step is making the PCI 
devices available for your domU (guest) os. Some documentation points towards using 
the xen-pciback module and hiding it from dom0 via a kernel parameter. I did not 
have any success with this approach, i suspect i would need to either compile 
xen-pciback into the kernel or put it in the initrd manually. Using pci-stub at 
runtime seems to work just as well though. Use lspci to find out the PCI ids: 

    $ lspci -nn|grep ATI
    01:00.0 VGA compatible controller [0300]: ATI Technologies Inc Cayman PRO [Radeon HD 6950] [1002:6719]
    01:00.1 Audio device [0403]: ATI Technologies Inc Device [1002:aa80]
   
In my case the graphics card is actually two PCI devices, and we need to 
passthrough both to the domU. These commands will bind the devices to the 
pci-stub module:

    echo "1002 6719" > /sys/bus/pci/drivers/pci-stub/new_id
    echo "0000:01:00.0" > /sys/bus/pci/devices/0000:01:00.0/driver/unbind
    echo "0000:01:00.0" > /sys/bus/pci/drivers/pci-stub/bind
    echo "1002 aa80" > /sys/bus/pci/drivers/pci-stub/new_id
    echo "0000:01:00.1" > /sys/bus/pci/devices/0000:01:00.1/driver/unbind
    echo "0000:01:00.1" > /sys/bus/pci/drivers/pci-stub/bind
    
"1002 6719" and "1002 aa80" being the vendor/device ids, 
"01:00.0" and "01:00.1" being the PCI ids from the previous lspci command. 
If you get errors about file not found, you probably need to issue "modprobe pci-stub".
Next you need to actually create the virtual machine, this is my configuration: 

    kernel = '/usr/lib/xen-4.1/boot/hvmloader'
    builder = 'hvm'
    memory = '4096'
    vcpus = 4
    disk = [ 'phy:muaddib/derp,ioemu:hda,w', 
             'file:/root/windows.iso,ioemu:hdb:cdrom,r' ]
    name = 'derp'
    vif = ['ip=192.168.70.7, bridge=xen-br0, mac=00:16:3e:60:57:3e']
    boot='d'
    vnc=1
    vncviewer=1
    vncconsole=0
    sdl=0
    pci=['01:00.0', '01:00.1']
    #gfx_passthru=1
    soundhw='es1370'
    device_model = '/usr/lib/xen-4.1/bin/qemu-dm'
    
Use "xm create &lt;file.cfg&gt;" to create the virtual machine, install windows as usual. 
When windows has finished installing, you can download and install the drivers. 
Upon rebooting after that, the ATI card should be active and you should see something 
on any monitor physically connected to it. In my setup, i have the integrated intel 
graphics hooked up to the DisplayPort and my ATI card hooked up to the DVI port of 
my monitor. This allows me to switch between the host and guest by switching the 
monitors active input. I've also set up [synergy] [2] to autostart in windows, which 
seems like the easiest way to use one set of keyboard and mouse for both operating 
systems. This is my synergy config file:

    section: screens
      muaddib:
      derp:
    end
    
    section: links
      muaddib:
        up = derp
      derp:
        down = muaddib
    end
                
    section: options
      screenSaverSync = false
      relativeMouseMoves = true
    end
    
The relativeMouseMoves is necessary to get the mouse working properly in games. It's 
activated when you lock the mouse (toggable by default with the "Scroll Lock" key) 
to one screen.

On my debian system i had issues with getting the emulated sound to work in the guest. 
First issue was that windows could not find a driver for the virtual sound card, this is
apparently an issue of no 64 bit drivers existing for it. Basically solved with installing
Windows 32bit instead. Next up was the inability of actually using it. Turns out the debian 
packages are compiled to only support OSS, which requires exclusive access to the /dev/dsp 
device. I tried using 'padsp' when launching qemu-dm, but that bailed out with something like 
"Failed to set non-blocking mode: Invalid argument". I guess the padsp wrapper does not support 
clients opening the device file in non-blocking mode? Next attempt, use 'aoss'. This gave me 
sound but added a delay of several seconds to it. The easiest way to fix this seemed to be 
compiling xen with pulseaudio or alsa support. Start by installing prerequisites:

    # apt-get build-dep xen-tools xen-utils-4.1 xen-utils-common xen-hypervisor-4.1-amd64
    # apt-get install libpulse-dev build-essential 
    
Get the debian package source:

    $ apt-get source xen-utils-4.1
    $ cd xen-4.1.2/
    
Now we need to make the necessary changes, first edit qemu/configure:

    -        "pa_simple *s = NULL; pa_simple_free(s); return 0;"
    +        "pa_simple *s = 0; pa_simple_free(s); return 0;"
  
And qemu/xen-setup:

    -${QEMU_ROOT:-.}/configure --disable-gfx-check --disable-curses --disable-slirp "$@" --prefix=${PREFIX}
    +${QEMU_ROOT:-.}/configure --audio-drv-list="pa,oss" --disable-gfx-check --disable-curses --disable-slirp "$@" --prefix=${PREFIX}
  
Commit these changes:

    $ dpkg-source --commit
    
Build the debian package:

    $ dpkg-buildpackage
    
If this finishes succesfully, you can now either: 

a) install the package
    
    # cd ../ && dpkg -i xen-*.deb

b) just replace the qemu-dm binary

    # cp ./debian/xen-utils-4.1/usr/lib/xen-4.1/bin/qemu-dm /usr/lib/xen-4.1/bin/qemu-dm
    
The downside of installing the package is you probably should bump the version number 
before so that debian won't overwrite your package, or pin it. The downside of replacing the 
binary is that it will get overwritten if there's an upgrade to that package.

Done!

The gfx_passthru option
-------------
My initial understanding was that this setup required gfx_passthru to be enabled to work. 
This turned out not to be the case, it's only required if your graphics card won't work unless 
it's the primary card in the virtual machine. Basically gfx_passthru will disable the emulated card
and in the virtual machine, but you can still passthru your real graphics card without that option.
From what i've read, ATI/AMD cards work fine as secondary cards. 

[1]: http://www.overclock.net/t/1200725/vt-d-is-your-friend-a-success-in-passthrough-to-xen-hvms
[2]: http://synergy-foss.org/
