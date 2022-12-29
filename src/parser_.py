from lexer import Lexer
from lexer import Token
from lexer import TokenType

import sys


class Parser:
    """Keep track of current token and check if code macthes the grammar."""
    def __init__(self, lexer):
        self.lexer = lexer
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
        print("PROGRAM")
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()
        while not self.checkToken(TokenType.EOF):
            self.statement()
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    def statement(self):
        """Parse a statement."""
        if self.checkToken(TokenType.PRINT):
            print("STATEMENT-PRINT")
            self.nextToken()
            if self.checkToken(TokenType.STRING):
                self.nextToken()
            else:
                self.expression()

        elif self.checkToken(TokenType.IF):
            print("STATEMENT-IF")
            self.nextToken()
            self.comparison()
            self.match(TokenType.THEN)
            self.nl()
            while not self.checkToken(TokenType.ENDIF):
                self.statement()
            self.match(TokenType.ENDIF)

        elif self.checkToken(TokenType.WHILE):
            print("STATEMENT-WHILE")
            self.nextToken()
            self.comparison()
            self.match(TokenType.REPEAT)
            self.nl()
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()
            self.match(TokenType.ENDWHILE)

        elif self.checkToken(TokenType.LABEL):
            print("STATEMENT-LABEL")
            self.nextToken()
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.GOTO):
            print("STATEMENT-GOTO")
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.LET):
            print("STATEMENT-LET")
            self.nextToken()
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            self.expression()

        elif self.checkToken(TokenType.INPUT):
            print("STATEMENT-INPUT")
            self.nextToken()
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
            self.match(TokenType.IDENT)
            
        else:
            self.abort("Invalid statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")
        self.nl()

    def comparison(self):
        """Handle comparisons."""
        print("COMPARISON")
        self.expression()
        if self.isComparisonOperator():
            self.nextToken()
            self.expression()
        else:
            self.abort("Expected comparison operator at" + self.curToken.text)
        while self.isComparisonOperator():
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
        print("EXPRESSION")
        self.term()
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.nextToken()
            self.term()

    def term(self):
        """Handle terms."""
        print("TERM")
        self.unary()
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.nextToken()
            self.unary()

    def unary(self):
        """Handle unaries."""
        print("UNARY")
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.nextToken()
        self.primary()

    def primary(self):
        """Handle primaries."""
        print(f"PRIMARY({self.curToken.text})")
        if self.checkToken(TokenType.NUMBER):
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)
            self.nextToken()
        else:
            self.abort("Unexpected token at " + self.curToken.text)

    def nl(self):
        """Handle new lines."""
        print("NEWLINE")
        self.match(TokenType.NEWLINE)
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    def abort(self, message):
        """Abort if parsing error."""
        sys.exit("Error. " + message)