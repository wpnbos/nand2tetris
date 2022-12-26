// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Loop that checks keyboard input
(MONITOR)
    // Reset counter
    @8192
    D=A
    @counter
    M=D

    @KBD
    D=M
    // If nonzero, fill screen
    @FILL
    D;JNE
    // Clear screen
    @CLEAR
    0;JMP

(FILL)
    // If (KBD == 0) -> MONITOR
    @KBD
    D=M
    @MONITOR
    D;JEQ

    // If (counter == 0) -> MONITOR
    @counter
    D=M
    @MONITOR
    D;JEQ

    // Fill pixel
    @counter
    D=M-1
    @SCREEN
    D=D+A
    A=D
    M=-1

    // Decrease counter
    @counter
    M=M-1

    // Loop
    @FILL
    0;JMP

(CLEAR)
    // If (KBD == 1) -> MONITOR
    @KBD
    D=M
    @MONITOR
    D;JNE

    // If (counter == 0) -> MONITOR
    @counter
    D=M
    @MONITOR
    D;JEQ

    // Fill pixel
    @counter
    D=M-1
    @SCREEN
    D=D+A
    A=D
    M=0

    // Decrease counter
    @counter
    M=M-1

    // Loop
    @CLEAR
    0;JMP
