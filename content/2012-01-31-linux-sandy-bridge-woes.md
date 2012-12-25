title: Linux and Sandy Bridge PCI Woes
category: Linux
date: 2012-01-31
tags: linux, pci, sandy_bridge

I put together a sandy bridged based server a while ago with 2 PCI intel network cards.
However, it didn't turn out to work very well. After putting some load on the network
it would become unbearably slow with error messages like this in the syslog:

    irq 16: nobody cared (try booting with the "irqpoll" option)
    Pid: 0, comm: swapper Not tainted 2.6.35.13-92.fc14.x86_64 #1
    Call Trace:
    <IRQ> [<ffffffff810a74f3>] __report_bad_irq.clone.1+0x3d/0x8b
    [<ffffffff810a765b>] note_interrupt+0x11a/0x17f
    [<ffffffff810a813b>] handle_fasteoi_irq+0xa8/0xce
    [<ffffffff8100c2ea>] handle_irq+0x88/0x90
    [<ffffffff81470b44>] do_IRQ+0x5c/0xb4
    [<ffffffff8146b093>] ret_from_intr+0x0/0x11
    <EOI> [<ffffffff8102b7dd>] ? native_safe_halt+0xb/0xd
    [<ffffffff81290b75>] acpi_safe_halt+0x2a/0x43
    [<ffffffff81290bae>] acpi_idle_do_entry+0x20/0x30
    [<ffffffff81290c27>] acpi_idle_enter_c1+0x69/0xb6
    [<ffffffff8146e01e>] ? notifier_call_chain+0x14/0x63
    [<ffffffff81395d56>] ? menu_select+0x177/0x28c
    [<ffffffff81394d6d>] cpuidle_idle_call+0x8b/0xe9
    [<ffffffff81008325>] cpu_idle+0xaa/0xcc
    [<ffffffff81452876>] rest_init+0x8a/0x8c
    [<ffffffff81ba1c49>] start_kernel+0x40b/0x416
    [<ffffffff81ba12c6>] x86_64_start_reservations+0xb1/0xb5
    [<ffffffff81ba13c2>] x86_64_start_kernel+0xf8/0x107
    handlers:
    [<ffffffff813148a8>] (ata_bmdma_interrupt+0x0/0x1a)
    [<ffffffffa00d8622>] (mpt_interrupt+0x0/0x890 [mptbase])
    controller
    [<ffffffffa00d8622>] (mpt_interrupt+0x0/0x890 [mptbase])
    controller
    [<ffffffffa0132850>] (e1000_intr+0x0/0xe9 [e1000])
    Disabling IRQ #16

After much googling and trying various workarounds like kernel boot options
(including irqpoll, which apparently [is broken in kernels > 2.6.39] [1]),
swapping around the cards, etc, it just wouldn't work. There seems to be
a lot of people having [similar issues] [2] with sandy bridge motherboards and PCI cards,
but it wasn't until i found [this thread] [3] it started to make a bit of sense.

Apparently Sandy Bridge chipsets do not natively support PCI, but most motherboard
manufacturers add some kind of bridge PCI-PCIe bridge chip. One that Asus likes to use
is ASM1083, which doesn't seem to be working quite correctly. Basically, right now the
PCI slots on motherboards with the ASM1083 PCI-PCIe bridge are useless, at least in linux,
so beware!

According to [this message] [4] there's been reports about issues with windows as well, just not
as noticeable.

[1]: https://bugs.launchpad.net/ubuntu/+source/linux/+bug/855199
[2]: https://bugzilla.redhat.com/show_bug.cgi?id=713351
[3]: https://lkml.org/lkml/2011/12/11/44
[4]: https://lkml.org/lkml/2012/1/31/167

