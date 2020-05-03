#!/usr/bin/env python3
#
# These are views that display open files in GoodHex.

import curses;
from curses.textpad import Textbox, rectangle;

MODE_COMMAND=0;
MODE_INSERT=1;
MODE_ASCII=2;
MODE_ANNOTATE=3;
MODE_STRINGS=["Command",
              "Insert",
              "ASCII",
              "Annotate"];
class GHVCurses:
    scr=None; #screen
    src=None; #data source
    notes=None;
    notesi=0;
    notesarray=[];
    adr=0; # Current address
    marker=None
    isbytemarking=False
    def __init__(self,screen,source,notesarray):
        """Initializes the curses view.  Be sure to call this in
        curses.wrapper()"""
        self.running=True;
        self.src=source;
        self.scr=screen;
        self.notesarray=notesarray;
        self.notes=self.notesarray[0];
        self.width = 0x10

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK);
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK);
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK);
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK);
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK);
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLUE);
        curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_WHITE);
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN);
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE);
        curses.noecho();
        curses.cbreak();
        self.scr.keypad(True); #Special keys are converted.
    def msgbox(self,message,title="Message Box"):
        """Displays a modal message box.  Let's try not to use this
        much!"""
        self.scr.clear();
        self.scr.addstr(18,0,title,curses.color_pair(9));
        self.scr.addstr(20,0,message);
        self.scr.getch();
        self.scr.clear();
    def inputbox(self,message,title="Message Box"):
        """Displays a modal message box.  Let's try not to use this
        much!"""
        self.scr.clear();
        self.scr.addstr(0,0,
                        "^G to commit.");
        self.scr.addstr(30,0,
                        "----%s----"%title,
                        curses.color_pair(9));
        self.scr.addstr(31,0,message);
        
        editwin = curses.newwin(5,30, 2,1)
        rectangle(self.scr, 1,0, 1+5+1, 1+30+1)
        self.scr.refresh()
        
        box = Textbox(editwin)
        box.edit();
        
        self.scr.clear();
        return box.gather();
    def togglebytemark(self):
        if self.isbytemarking:
            #we were byte marking, so stop it
            self.marker = None
        else:
            #we weren't byte marking, so do it
            self.marker = self.adr

        self.isbytemarking = not self.isbytemarking

    def mainloop(self):
        """Main loop of the curses gui."""
        while self.running:
            self.updateview();
            self.handlekey(self.scr.getch());
    
    def getshortnote(self,adr):
        note=self.notes.getnote(adr);
        if note==None: return None;
        notes=note.split('\n');
        return notes[0];
    def updateview(self):
        """Updates the view from the current location."""
        #First we draw the header and footer.
        self.drawheader()
        self.drawfooter()

        #Then we draw the bytes.
        self.drawbytes();
        self.scr.refresh();

    def drawheader(self):
        mode=MODE_STRINGS[self.mode].strip()
        self.scr.addstr(0,0,
                        "%08x -- width: %x %10s Mode" % (self.adr, self.width, mode),
                        curses.color_pair(1));
        if self.isbytemarking:
            self.scr.addstr(1,0,
                            "Marker @ %08x -- Distance: %08x" %
                            (self.marker,abs(self.marker-self.adr)),
                            curses.color_pair(1));
        else:
            self.scr.addstr(1,0," "*80)


    def drawfooter(self):
        self.scr.addstr(curses.LINES-2,0,
                        "%-20s" % self.notes.getname());
        
        self.scr.addstr(curses.LINES-1,0,
                        "%-80s" % self.getshortnote(self.adr));
    def drawbytes(self):
        """Draws bytes on the screen."""
        start=self.adr&~0xFF;
        for row in range(0,curses.LINES-4):
            self.drawbyteline(row + 2, start + self.width * row);
    def drawbyteline(self,row,adrstart):
        """Draws one line of bytes to the screen."""
        self.scr.addstr(row,0,
                        "%08x" % (adrstart),
);
            
            
        extra_space = 0  # use this to add visual space between blocks

        for adr in range(adrstart, adrstart + self.width):
            b = self.src.getbyte(adr)
            s = "%02x" % b if b != None else " "

            # Fetch the color from the notes.
            color=self.notes.getcolor(adr,b,self.adr);
            if adr==self.adr: color=9;
            if adr==self.marker: color=6;

            offset = adr - adrstart
            extra_space += (offset % 8 == 0) and (offset != 0)

            self.scr.addstr(
                row,
                # 3 -> 3 chars for byte (2 hex + 1 space)
                15 + offset * 3 + extra_space,
                s,
                curses.color_pair(color)
            )
            self.scr.addstr(
                row,
                (20 + (self.width * 3)) + offset,
                self.safechr(b),
                curses.color_pair(color)
            )

    def safechr(self,c):
        """Safely returns a byte for the given string."""
        if c==None: return ' ';
        if c<0x7F and c>=0x20:
            return chr(c);
        else:
            return '.';
    mode=MODE_COMMAND;
    lastkey=0;
    def handlekey(self,key):
        """Handles a keypress."""
        
        #These commands work in any mode.
        if key==curses.KEY_UP:
            self.adr=self.adr - self.width;
        elif key==curses.KEY_DOWN:
            self.adr=self.adr + self.width;
        elif key==curses.KEY_LEFT:
            self.adr=self.adr-1;
        elif key==curses.KEY_RIGHT:
            self.adr=self.adr+1;
        elif key==0x20:
            self.togglebytemark()
        elif key==0x09: #TAB
            self.notesi=(self.notesi+1) % len(self.notesarray);
            self.notes=self.notesarray[self.notesi];
            self.scr.clear();
        elif key==0x1B: # ESCAPE
            if self.lastkey==key:
                self.mode=MODE_COMMAND;
        elif key == ord('+'):
            self.width += 1
            self.scr.clear();
        elif key == ord('-'):
            if self.width != 1:
                self.scr.clear();
                self.width -= 1

        #Next, handle the mode-specific commands.
        elif self.mode==MODE_COMMAND:
            self.handlekeycommand(key);
        elif self.mode==MODE_ASCII:
            self.handlekeyascii(key);
        elif self.mode==MODE_ANNOTATE:
            self.handlekeyannotate(key);
        
        #Finally, fix the address.
        if self.adr<0:
            self.adr=0;
        
        #Save the lastkey.
        self.lastkey=key;

    def handlekeyascii(self,key):
        """Allows for ASCII-style entry."""
        if (key>=0x20 and key<0x7F) or key==0x0a:
            self.src.setbyte(self.adr,key);
            self.adr=self.adr+1;
    def handlekeyannotate(self,key):
        """Handles a keypress in annotation mode."""
        if key>=ord('0') and key<=ord('9'):
            if self.isbytemarking:
                for i in range(min(self.marker, self.adr),
                               max(self.marker,self.adr)+1):
                    self.notes.setcolor(i, key-ord('0'))
            else:
                self.notes.setcolor(self.adr,
                                    key-ord('0'));
        elif key==ord('n'):
            note=self.inputbox("Please add a note for 0x%08x"%self.adr,
                               "Adding Annotation");
            self.notes.setnote(self.adr,note);
    def handlekeycommand(self,key):
        """Handles a key in command mode."""
        if key==ord('q'):
            self.running=False;
        elif key==ord('n'):
            self.adr=self.adr+0x100;
        elif key==ord('p'):
            self.adr=self.adr-0x100;
        elif key==ord('N'):
            self.adr=self.adr+0x1000;
        elif key==ord('P'):
            self.adr=self.adr-0x1000;
        elif key==ord('i'):
            # TODO, actually support insert mode.
            self.mode=MODE_INSERT;
        elif key==ord('a'):
            self.mode=MODE_ANNOTATE;
        elif key==ord('A'):
            self.mode=MODE_ASCII;
        elif key==ord('g'):
            goto=self.inputbox("Where would you like to go?\n(Hex, please.)");
            try:
                self.adr=int(goto,16);
            except: pass;


