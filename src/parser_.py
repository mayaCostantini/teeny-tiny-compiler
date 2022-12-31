from lexer import Lexer
from lexer import Token
from lexer import TokenType

import sys


class Parser:
    """Keep track of current token and check if code macthes the grammar."""
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter
        self.symbols = set()
        self.labelsDeclared = set()
        self.labelsGotoed = set()
        self.curToken = None
        self.peekToken = None
        # Intialize current and peek
        self.nextToken()
        self.nextToken()

    def checkToken(self, kind):
        """Return true if current token matches."""
        return kind == self.curToken.kind

    def checkPeek(self, kind):
        """Return true if next token matches."""
        return kind == self.peekToken.kind

    def match(self, kind):
        """Try to match current token."""
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
        self.nextToken()

    def nextToken(self):
        """Advances the current token."""
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()

    def program(self):
        """Parse all the statements in the program."""
        self.emitter.headerLine("#include <stdio.h>")
        self.emitter.headerLine("int main(void){")
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()
        while not self.checkToken(TokenType.EOF):
            self.statement()
        self.emitter.emitLine("return 0;")
        self.emitter.emitLine("}")
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    def statement(self):
        """Parse a statement."""
        if self.checkToken(TokenType.PRINT):
            self.nextToken()
            if self.checkToken(TokenType.STRING):
                self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
                self.nextToken()
            else:
                self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                self.emitter.emitLine("));")

        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if(")
            self.comparison()
            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine("){")
            while not self.checkToken(TokenType.ENDIF):
                self.statement()
            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while(")
            self.comparison()
            self.match(TokenType.REPEAT)
            self.nl()
            self.emitter.emitLine("){")
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()
            self.match(TokenType.ENDWHILE)
            self.emitter.emitLine("}")

        elif self.checkToken(TokenType.LABEL):
            self.nextToken()
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)
            self.emitter.emitLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.emitter.emitLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.LET):
            self.nextToken()
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            self.emitter.emit(self.curToken.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            self.expression()
            self.emitter.emitLine(";")

        elif self.checkToken(TokenType.INPUT):
            self.nextToken()
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")
            self.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
            self.emitter.emitLine(self.curToken.text + " = 0;")
            self.emitter.emit("scanf(\"%")
            self.emitter.emitLine("*s\");")
            self.emitter.emitLine("}")
            self.match(TokenType.IDENT)

        else:
            self.abort("Invalid statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")
        self.nl()

    def comparison(self):
        """Handle comparisons."""
        self.expression()
        if self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()
        else:
            self.abort("Expected comparison operator at" + self.curToken.text)
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    def isComparisonOperator(self):
        """Return true if curren token is a comparison operator."""
        return self.checkToken(TokenType.GT) \
            or self.checkToken(TokenType.GTEQ) \
            or self.checkToken(TokenType.LT) \
            or self.checkToken(TokenType.LTEQ) \
            or self.checkToken(TokenType.EQEQ) \
            or self.checkToken(TokenType.NOTEQ)

    def expression(self):
        """Handle expressions."""
        self.term()
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

    def term(self):
        """Handle terms."""
        self.unary()
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()

    def unary(self):
        """Handle unaries."""
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        self.primary()

    def primary(self):
        """Handle primaries."""
        if self.checkToken(TokenType.NUMBER):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            self.abort("Unexpected token at " + self.curToken.text)

    def nl(self):
        """Handle new lines."""
        self.match(TokenType.NEWLINE)
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    def abort(self, message):
        """Abort if parsing error."""
        sys.exit("Error. " + message)