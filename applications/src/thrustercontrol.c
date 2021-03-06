
#include "seawolf.h"

#include <ctype.h>
#include <stdio.h>
#include <ncurses.h>

#define MIN_SPEED (-1.0)
#define MAX_SPEED (1.0)
#define STEP (0.05)

#define ADJUST(x) Util_inRange(MIN_SPEED, (x), MAX_SPEED)

int main(void) {
    Seawolf_loadConfig("../conf/seawolf.conf");
    Seawolf_init("Thruster Controller");

    initscr();
    cbreak();
    noecho();
    keypad(stdscr, TRUE);

    int c;
    char* display = "   \n\
  Thruster Controller   \n\
                        \n\
         %3.2f          \n\
                        \n\
  %3.2f  %3.2f   %3.2f  \n\
                        \n\
         %3.2f          \n\
";

    float bow=0.0, stern=0.0, port=0.0, star=0.0, strafe=0.0;
    int addsub = 1;
        
    /* Turn off drivers */
    Var_set("Port", 0.0);
    Var_set("Star", 0.0);
    Var_set("Bow", 0.0);
    Var_set("Stern", 0.0);
    Var_set("Strafe", 0.0);
    
    while(true) {
        printw(display, bow, port, strafe, star, stern);
        refresh();

        c = getch();
        clear();

        addsub = -1;
        if(isupper(c)) {
            addsub = 1;
        }
        c = tolower(c);

        switch(c) {
        case 'w':
            bow = ADJUST(bow + (addsub * STEP));
            Var_set("Bow", bow);
            break;

        case 'x':
            stern = ADJUST(stern + (addsub * STEP));
            Var_set("Stern", stern);
            break;

        case 'a':
            port = ADJUST(port + (addsub * STEP));
            Var_set("Port", port);
            break;

        case 'd':
            star = ADJUST(star + (addsub * STEP));
            Var_set("Star", star);
            break;

        case 's':
            strafe = ADJUST(strafe + (addsub * STEP));
            Var_set("Strafe", strafe);
            break;
        }

        if(c == 'q') {
            break;
        }
    }

    endwin();

    /* Turn off drivers */
    Var_set("Port", 0);
    Var_set("Star", 0);
    Var_set("Bow", 0);
    Var_set("Stern", 0);
    Var_set("Strafe", 0);

    Seawolf_close();
    return 0;
}
