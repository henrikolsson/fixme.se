title: Saving savegames 
category: unnethack
date: 2014-09-15
tags: unnethack, asm, reverse-engineering, python

**Long post so TL;DR for lazy people:**<br>
Patched 47 binaries to achieve backwards compatibility with old saves

I decided to redo the setup for un.nethack.nu mostly from scratch, to make it easier to support shared state between multiple servers. For historical reasons unnethack ran as uid 5. This uid belongs to the "games" user in debian, which the original server ran. Nowadays I prefer CentOS where uid 5 by default belongs to the username "sync".

So I took the opportunity to use a dedicated user with a non-system uid. This became a pretty big issue since nethack also writes the uid to the save file and if it doesn't match what it's running as when you restore it'll helpfully tell you the save file is not yours and delete it. 

Brainstorming in the unnethack irc channel a few options came up:

1. Move back to uid 5
2. Recompile all the binaries without the check
3. Remove the uid check in the binaries
4. Try to replace the uid inside the save files

The first is the ugly solution, which I see as a last resort. Investigation of the code writing the save files found that the uid was being written to a non-fixed position. This makes it pretty risky to mess with it. Removing the uid check and recompiling was done for the latest binary. Unfortunately there are currently 48 different versions of unnethack with version dependent saves. Even if I had some kind of tag or reference to the point in history where each binary was built I wouldn't rely on being able to get the exact same binary. So investigation began on the fourth option.

Finding the code that does the uid check was easy, just need to look for the string being printed when it happens, "Saved game was not yours.". The uid check and printing seems to be done in "restgamestate" in restore.c:

    :::c
    STATIC_OVL
    boolean
    restgamestate(fd, stuckid, steedid)
    register int fd;
    unsigned int *stuckid, *steedid;        /* STEED */
    {
            /* discover is actually flags.explore */
            boolean remember_discover = discover;
            struct obj *otmp;
            int uid;
    
            mread(fd, (genericptr_t) &uid, sizeof uid);
            if (uid != getuid()) {          /* strange ... */
                /* for wizard mode, issue a reminder; for others, treat it
                   as an attempt to cheat and refuse to restore this file */
                pline("Saved game was not yours.");
    #ifdef WIZARD
                if (!wizard)
    #endif
                    return FALSE;
            }
    // More code...

And restgamestate is being called by dorecover (strange name for a function that restores save files...), also in restore.c:

    :::c,line
    int
    dorecover(fd)
    register int fd;
    {
            unsigned int stuckid = 0, steedid = 0;  /* not a register */
            xchar ltmp;
            int rtmp;
            struct obj *otmp;
    
    #ifdef STORE_PLNAME_IN_FILE
            mread(fd, (genericptr_t) plname, PL_NSIZ);
    #endif
    
            restoring = TRUE;
            getlev(fd, 0, (xchar)0, FALSE);
            if (!restgamestate(fd, &stuckid, &steedid)) {
                    display_nhwindow(WIN_MESSAGE, TRUE);
                    savelev(-1, 0, FREE_SAVE);      /* discard current level */
                    (void) close(fd);
                    (void) delete_savefile();
                    restoring = FALSE;
                    return(0);
            }
            
    // More code...

So if the uid check in "restgamestate" fails it will return FALSE and cause "dorecover" to delete the save file. It seems the easiest solution would be to remove the "return FALSE" in the uid check. Now we need to find this part in the binary. The best and easiest way I found to disassemble in linux is to use objdump:

    $ objdump -D -S -g -t -T unnethack.45 | less -i

I started by searching for calls to getuid and looking at what function they were in. After a number of hits I find a call to it in "dorecover":

    :::objdump
    000000000050cf10 <dorecover>:
      .....
      50cf4f:  e8 fc ef ff ff          callq  50bf50 <mread>
      50cf54:  44 8b 64 24 14          mov    0x14(%rsp),%r12d
      50cf59:  e8 82 14 0f 00          callq  5fe3e0 <__getuid>
      50cf5e:  41 39 c4                cmp    %eax,%r12d
      50cf61:  74 19                   je     50cf7c <dorecover+0x6c>
      50cf63:  31 c0                   xor    %eax,%eax
      50cf65:  bf 06 48 6a 00          mov    $0x6a4806,%edi
      50cf6a:  e8 21 f3 fd ff          callq  4ec290 <pline>
      .....

But getuid isn't called in dorecover. The nearby calls (mread, pline) actually looks like the code from restgamestate. Lets see what's being put in the edi register by the mov instruction before the call to pline by looking at the string data in the binary:

    $ objdump -s -j .rodata unnethack.45 | less -i

Searching for " 6a48" finds the place (6a4800 and then 6 characters in):

    6a4800 74202564 21005361 76656420 67616d65  t %d!.Saved game
    6a4810 20776173 206e6f74 20796f75 72732e00   was not yours..

So it is the code we're looking for, it must have been inlined. Let's analyze what that part actually does:

    000000000050cf10 <dorecover>:
      .....
      50cf4f:  e8 fc ef ff ff          callq  50bf50 <mread>             # read piece of the file
      50cf54:  44 8b 64 24 14          mov    0x14(%rsp),%r12d           # move into %r12d (i think)
      50cf59:  e8 82 14 0f 00          callq  5fe3e0 <__getuid>          # call getuid
      50cf5e:  41 39 c4                cmp    %eax,%r12d                 # compare result to %r12d
      50cf61:  74 19                   je     50cf7c <dorecover+0x6c>    # if the same, jump to 50cf7c -|
      50cf63:  31 c0                   xor    %eax,%eax                  # set %eax to 0                |
      50cf65:  bf 06 48 6a 00          mov    $0x6a4806,%edi             # 6a4806: "Saved game was not yours."
      50cf6a:  e8 21 f3 fd ff          callq  4ec290 <pline>             # print it                     |
      50cf6f:  80 3d 94 4c 42 00 00    cmpb   $0x0,0x424c94(%rip)        # 931c0a <flags+0xa> check if field at flags + 0xA is equal to 0 (most likely WIZARD flag)
      50cf76:  0f 84 66 03 00 00       je     50d2e2 <dorecover+0x3d2>   # if so, jump to 50d2e2 -|     |
      50cf7c:  ba d0 00 00 00          mov    $0xd0,%edx                 #                        |   <-| Here!
      50cf81:  be 00 1c 93 00          mov    $0x931c00,%esi             #                        |
      50cf86:  89 df                   mov    %ebx,%edi                  #                        |
      50cf88:  e8 c3 ef ff ff          callq  50bf50 <mread>             #                        |
                                                                         #                        |
      .....                                                              #                        |
                                                                         #                        |  
      50d2e2:  be 01 00 00 00          mov    $0x1,%esi                  #                      <-| Here! 
      50d2e7:  8b 3d 47 dd 41 00       mov    0x41dd47(%rip),%edi        # 92b034 <WIN_MESSAGE>
      50d2ed:  ff 15 ed 0e 45 00       callq  *0x450eed(%rip)            # 95e1e0 <windowprocs+0x60>
      50d2f3:  ba 04 00 00 00          mov    $0x4,%edx
      50d2f8:  31 f6                   xor    %esi,%esi
      50d2fa:  bf ff ff ff ff          mov    $0xffffffff,%edi
      50d2ff:  e8 3c 40 00 00          callq  511340 <savelev>
      50d304:  89 df                   mov    %ebx,%edi
      50d306:  e8 35 3b 10 00          callq  610e40 <__libc_close>
      50d30b:  e8 e0 cd f5 ff          callq  46a0f0 <delete_savefile>
      50d310:  c6 05 69 01 43 00 00    movb   $0x0,0x430169(%rip)        # 93d480 <restoring>
      50d317:  48 83 c4 20             add    $0x20,%rsp
      50d31b:  31 c0                   xor    %eax,%eax
      50d31d:  5b                      pop    %rbx
      50d31e:  5d                      pop    %rbp
      50d31f:  41 5c                   pop    %r12
      50d321:  c3                      retq

The patch needed turned out to be very simple, change the jump at 50cf61 to an unconditional one.
Looking at an [x86 opcode and instructions reference](http://ref.x86asm.net/coder64.html) we can find that the JMP (unconditional jump) opcode of the same type as the JE (opcode 0x74, rel8, jump <next byte number of bytes> relative to position) is 0xEB. Looking through a few unnethack binaries the disassembled output is very similar, following a pattern for 32-bit and another for 64-bit. So I wrote a fuzzy patcher:

    :::python
    #!/usr/bin/env python
    import sys
    import subprocess
    
    patch_64 = {"needle": [0x44, '*', '*', '*', '*',
                           0xe8, '*', '*', '*', '*',
                           0x41, '*', '*',
                           0x74, 0x19,
                           0x31, 0xc0,
                           0xbf],
                "pos": 13,
                "new": [0xEB]}
    patch_32 = {"needle": [0x8b, '*', '*',
                           0xe8, '*', '*', '*', '*',
                           0x39, 0xc3,
                           0x74, 0x19,
                           0xc7],
                "pos": 10,
                "new": [0xEB]}
    
    def run(cmd):
        return subprocess.Popen(cmd,
                                stdout=subprocess.PIPE).communicate()[0]
        
    def main():
        if len(sys.argv) == 1:
            print("usage: patcher.py <file>")
            return
    
        fn = sys.argv[1]
        print("opening %s" % fn)
    
        output = run(['file', fn])
        if output.find('64-bit') > -1:
            print("64-bit binary")
            patch = patch_64
        elif output.find('32-bit') > -1:
            print("32-bit binary")
            patch = patch_32
        else:
            raise Exception("Unknown binary: %s" % output)
        
            
        f = open(fn, 'r+b')
        b = f.read(1)
        fpos = 1
        npos = 0
        needle = patch["needle"]
        spos = -1
        while not b == "":
            b = ord(b)
            if npos == len(needle):
                print "found it"
                if not spos == -1:
                    raise Exception("Expected to find pattern only once")
                spos = fpos - 1
                npos = 0
            if needle[npos] == '*' or needle[npos] == b:
                npos = npos + 1
            else:
                npos = 0
            b = f.read(1)
            fpos = fpos + 1
    
        if spos == -1:
            raise Exception("Could not find pattern")
    
        f.seek(spos - len(needle) + patch["pos"])
        b = ord(f.read(1))
        assert b == needle[patch["pos"]]
    
        print("writing patch")
        f.seek(spos - len(needle) + patch["pos"])
        for b in patch["new"]:
            f.write(chr(b))
    
        print("done!")
        
    if __name__ == "__main__":
        main()
    
This worked for all but one binary, where the compiler had not inlined the restgamestate call. It was easily patched manually, with the help of emacs wonderful hexl-mode to hexedit the binary.
