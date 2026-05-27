import sys
from lexer import lexer #Puxando o lexer q vc já fiz

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0 #Ponteiro pra saber em qual token tá na lista
        
        #Pega o primeiro token se a lista n tiver vazia
        self.current_token = self.tokens[self.pos] if self.tokens else None
        
        #Lista pra guardar os erros e não quebrar o programa
        self.errors = [] 

    def advance(self):
        #Anda uma casa na lista de tokens e pega o proximo
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None #EOF (fim do arquivo)

    def match(self, expected_kind, expected_value=None):
        #Essa função checa se o token atual é oq a gente espera q seja
        if not self.current_token:
            self.reporta_erro(f"Arquivo acabou do nada era pra achar provavelmente um {expected_kind}")
            return False

        kind, value, linha, coluna = self.current_token
        
        #de for o tipo certo e o valor bater, se foi passado como parametro
        if kind == expected_kind and (expected_value is None or value == expected_value):
            self.advance() #Consome o token e vai pro proximo
            return True
        
        #Se n bateu tem problema na sintaxe
        esperado = expected_value if expected_value else expected_kind
        self.reporta_erro(f"Erro de sintaxe: Esperava '{esperado}', mas veio '{value}'", linha, coluna)
        return False

    def reporta_erro(self, message, linha=None, coluna=None):
        #guarda o erro formatado pra printar tudo de uma vez no final
        if linha is None and self.current_token:
            _, _, linha, coluna = self.current_token
        self.errors.append(f"Linha {linha}, Coluna {coluna}: {message}")

    def panic_mode(self):
        #se deu erro de sintaxe ele entra num laço ignorando os proximos tokens até achar um ';' ou '}' pra voltar a analisar isso evita q faltar um simples ';' crie um monte de erro falso dps.
        while self.current_token:
            kind, value, _, _ = self.current_token
            
            #Se achou o fim de um comando consome e para de ignorar
            if value in (';', '}'):
                self.advance()
                return
            
            #Se achou o inicio de um novo comando tbm serve de ancora pra voltar ao normal
            if kind in ('INT', 'FLOAT', 'CHAR', 'IF', 'WHILE', 'FOR', 'RETURN'):
                return
            
            self.advance() #joga fora o token e tenta o proximo

    def parse_program(self):
        #Um programa é basicamente um monte de comandos em sequencia
        statements = []
        while self.current_token:
            stmt = self.parse_direcionamento()
            if stmt:
                statements.append(stmt)
        return statements

    def parse_direcionamento(self):
        #Age como um guarda de transito, olha pro token atual e manda pra função especifica
        if not self.current_token:
            return None

        kind, value, _, _ = self.current_token

        try:
            #direcionamento pelo tipo do token
            if kind in ('INT', 'FLOAT', 'CHAR', 'VOID'):
                return self.parse_declaracao_variavel()
            elif kind == 'IF':
                return self.parse_if()
            elif kind == 'WHILE':
                return self.parse_while()
            elif kind == 'FOR':
                return self.parse_for()
            elif kind == 'IDENT': #se começou com identificador, provavel q seja uma variavel recebendo valor
                return self.parse_atribuicao()
            else:
                self.reporta_erro(f"Comando iniciado com '{value}'")
                self.panic_mode() #chama o panic mode pq n sabe oq é isso
                return None
                
        except Exception:
            #se alguma função em baixo der panic (levantar exceção), cai direto aqui pra sincronizar
            self.panic_mode()
            return None

    def parse_declaracao_variavel(self):
        #espera algo tipo: int x = 5;
        if not self.current_token:
            self.reporta_erro("Deu erro era pra ter declarado variavel.")
            raise Exception("Panic")

        type_token = self.current_token[1]
        self.advance() #Consome o tipo (int, float, char)

        #depois do tipo TEM q vir o nome da variavel
        if not self.current_token or self.current_token[0] != 'IDENT':
            self.reporta_erro("Esqueceu o nome da variável animal")
            raise Exception("Panic")
        
        variavel_nome = self.current_token[1]
        self.advance() #Consome o nome (IDENT)

        expressao = None
        #Se tiver um = logo em seguida, resolve a expressão da direita
        if self.current_token and self.current_token[0] == 'OPER_ATRIBUI':
            self.advance() #Consome o '='
            expressao = self.parse_expression()

        #Independente se recebeu valor ou não TEM q fechar com ;
        if not self.match('DELIM', ';'):
            raise Exception("Panic")

        return {'type': 'VarDecl', 'var_type': type_token, 'name': variavel_nome, 'value': expressao}

    def parse_atribuicao(self):
        #Ex: x = 10;
        if not self.current_token:
            self.reporta_erro("Deu erro era pra ter esperado uma atribuição.")
            raise Exception("Panic")

        variavel_nome = self.current_token[1]
        self.advance() #consome o nome da variavel (IDENT)

        if not self.match('OPER_ATRIBUI', '='):
            raise Exception("Panic")
        
        expr = self.parse_expression()

        if not self.match('DELIM', ';'):
            raise Exception("Panic")

        return {'type': 'Assignment', 'name': variavel_nome, 'value': expr}

    def parse_if(self):
        self.advance() #Consome o 'if'
        
        if not self.match('DELIM', '('): raise Exception("Panic")
        condition = self.parse_expression() #dentro dos parenteses tem q ter expressão
        if not self.match('DELIM', ')'): raise Exception("Panic")

        true_block = self.parse_block() #Conteudo de dentro das chaves {}
        false_block = None

        #O else é opcional, checa se ele existe
        if self.current_token and self.current_token[0] == 'ELSE':
            self.advance() #consome 'else'
            false_block = self.parse_block()

        return {'type': 'If', 'condition': condition, 'true_block': true_block, 'false_block': false_block}

    def parse_while(self):
        #Basicamente o msm esquema do if
        self.advance() #Consome 'while'
        
        if not self.match('DELIM', '('): raise Exception("Panic")
        condition = self.parse_expression()
        if not self.match('DELIM', ')'): raise Exception("Panic")

        block = self.parse_block()
        return {'type': 'While', 'condition': condition, 'body': block}

    def parse_for(self):
        self.advance() #Consome 'for'
        if not self.match('DELIM', '('): raise Exception("Panic")

        if not self.current_token:
            self.reporta_erro("Arquivo acabou no meio do 'for'.")
            raise Exception("Panic")

        #Parte 1: Inicialização (ex: int i = 0;)
        init = None
        if self.current_token[0] in ('INT', 'FLOAT', 'CHAR'):
            init = self.parse_declaracao_variavel() #O parse_var já exige e consome o ';' no final
        elif self.current_token[0] == 'IDENT':
            init = self.parse_atribuicao() #Mesma coisa aqui
        else:
            self.match('DELIM', ';') #Se for vazio, consome só o ';'

        #Parte 2: Condição (ex: i < 10;)
        condition = self.parse_expression()
        if not self.match('DELIM', ';'): raise Exception("Panic")

        #Parte 3: Incremento (ex: i = i + 1) -> n tem ; no final
        increment = None
        if self.current_token and self.current_token[0] == 'IDENT':
            variavel_nome = self.current_token[1]
            self.advance()
            if self.match('OPER_ATRIBUI', '='):
                expr = self.parse_expression()
                increment = {'type': 'Assignment', 'name': variavel_nome, 'value': expr}
        
        if not self.match('DELIM', ')'): raise Exception("Panic")

        block = self.parse_block()
        return {'type': 'For', 'init': init, 'condition': condition, 'increment': increment, 'body': block}

    def parse_block(self):
        #Valida blocos de codigo q ficam entre {}
        if not self.match('DELIM', '{'): raise Exception("Panic")
        
        statements = []
        #Fica lendo comandos ate achar o fecha chaves
        while self.current_token and not (self.current_token[0] == 'DELIM' and self.current_token[1] == '}'):
            stmt = self.parse_direcionamento()
            if stmt:
                statements.append(stmt)
        
        if not self.match('DELIM', '}'): raise Exception("Panic")
        return statements

    def parse_expression(self):
        #Expressões pegando operadores (+ - / * > < ==)
        left = self.parse_termo()

        #Fica num laço juntando a esquerda com a direita enquanto achar operadores
        while self.current_token and self.current_token[0] in ('OPER', 'OPER_LOG'):
            op = self.current_token[1]
            self.advance() #Consome o operador
            right = self.parse_termo()
            left = {'type': 'BinOp', 'left': left, 'op': op, 'right': right}
        
        return left

    def parse_termo(self):
        #Resolve o nivel mais basico da expressão (um numero, variavel, string ou algo entre parenteses)
        if not self.current_token:
            self.reporta_erro("Faltou completar a expressão matemática ou a logica")
            raise Exception("Panic")
            
        kind, value, _, _ = self.current_token
        
        if kind in ('IDENT', 'NUM_INT', 'NUM_FLOAT', 'STR_LIT', 'CHAR_LIT'):
            self.advance()
            return {'type': 'Literal/Var', 'value': value}
        elif kind == 'DELIM' and value == '(': #Se achar parenteses, entra em recursão pra resolver oq tem dentro
            self.advance()
            expr = self.parse_expression()
            if not self.match('DELIM', ')'): raise Exception("Panic")
            return expr
        
        self.reporta_erro(f"Bagulho inválido na expressão: '{value}'")
        raise Exception("Panic")


def main():
    if len(sys.argv) < 2:
        print("Passe o arquivo.txt quando for executar animal.")
        return
    
    code_txt = sys.argv[1]
    
    try:
        with open(code_txt, 'r') as arq:
            code = arq.read()            
        # Pega os tokens limpos do lexer
        tokens = []
        for token in lexer(code):
            if token[0] != 'TOKEN_INEX':
                tokens.append(token)        
        # Inicia o motor do Parser
        parser = Parser(tokens)
        # O parser cria a AST na memória, mas não vamos printar nem salvar
        ast = parser.parse_program() #salvei mas n printei
        
        print(f"\n--- Análise Sintática: {code_txt} ---")
        if parser.errors:
            print(f"O parser achou {len(parser.errors)} erro(s) de sintaxe:")
            for erro in parser.errors:
                print(f" -> {erro}")
        else:
            print("Código analisado sem erros de sintaxe")

    except FileNotFoundError:
        print("Escreveu o nome do arquivo errado animal.")

if __name__ == '__main__':
    main()

