import sys
from lexer import lexer #Puxando o lexer q vc já fiz

class TabelaDeSimbolos:
    def __init__(self):
        #A tabela de símbolos é uma pilha de dicionários. Cada dicionário representa um escopo.
        self.escopos = [{}] 

    def entrar_escopo(self):
        self.escopos.append({})

    def sair_escopo(self):
        #Varre as variáveis do bloco para ver quais não foram usadas antes de destruí-lo
        variaveis_nao_usadas = []
        
        if not self.escopos: 
            return variaveis_nao_usadas
            
        escopo_atual = self.escopos[-1]
        
        for nome, info in escopo_atual.items():
            if not info['usada']:
                variaveis_nao_usadas.append((nome, info['linha'], info['coluna']))

        #Só sai se não for o global
        if len(self.escopos) > 1:
            self.escopos.pop()
            
        return variaveis_nao_usadas

    def declarar(self, nome, tipo, linha, coluna):
        escopo_atual = self.escopos[-1]
        if nome in escopo_atual:
            return False #Variável já declarada neste escopo exato
        
        #Salva como um dicionário para guardar se ela foi usada
        escopo_atual[nome] = {'tipo': tipo, 'usada': False, 'linha': linha, 'coluna': coluna}
        return True

    def buscar_geral(self, nome):
        #Busca a variável do escopo mais interno (atual) até o mais externo (global)
        for escopo in reversed(self.escopos):
            if nome in escopo:
                escopo[nome]['usada'] = True #Marca que a variável foi utilizada
                return escopo[nome]['tipo']
        return None

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0 #Ponteiro pra saber em qual token tá na lista
        
        #Pega o primeiro token se a lista n tiver vazia
        self.current_token = self.tokens[self.pos] if self.tokens else None
        
        self.errors = [] #Lista pra guardar erros sintáticos
        self.semantic_errors = [] #Lista pra guardar os erros semânticos
        self.warnings = [] #Lista para guardar os warnings
        self.tabela_simbolos = TabelaDeSimbolos() #Instancia o motor semântico

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
            self.advance() 
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

    def reporta_erro_semantico(self, message, linha=None, coluna=None):
        if linha is None and self.current_token:
            _, _, linha, coluna = self.current_token
        self.semantic_errors.append(f"Linha {linha}, Coluna {coluna}: {message}")

    def reporta_warning(self, message, linha, coluna):
        self.warnings.append(f"Linha {linha}, Coluna {coluna}: Aviso - {message}")

    def checar_variaveis_nao_usadas(self, lista_nao_usadas):
        for nome, linha, col in lista_nao_usadas:
            self.reporta_warning(f"A variável '{nome}' foi declarada, mas nunca utilizada.", linha, col)

    #NOVA FUNÇÃO: MOTOR DE REGRAS DE TIPAGEM 
    def checar_tipos_atribuicao(self, tipo_esperado, tipo_recebido, nome_var, linha, coluna):
        if tipo_esperado == 'unknown' or tipo_recebido == 'unknown':
            return
            
        if tipo_esperado == 'int' and tipo_recebido == 'float':
            self.reporta_erro_semantico(f"Incompatibilidade: A variável '{nome_var}' é 'int' e não pode receber um valor 'float' (perda de precisão).", linha, coluna)
        elif tipo_esperado == 'float' and tipo_recebido == 'int':
            #Permite de forma silenciosa. Um float pode receber um int sem problemas e sem warnings.
            pass
        elif tipo_esperado != tipo_recebido:
            self.reporta_erro_semantico(f"Incompatibilidade: A variável '{nome_var}' é do tipo '{tipo_esperado}', mas está recebendo '{tipo_recebido}'.", linha, coluna)

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
            
            self.advance() 

    def parse_program(self):
        #Um programa é basicamente um monte de comandos em sequencia
        statements = []
        while self.current_token:
            stmt = self.parse_direcionamento()
            if stmt:
                statements.append(stmt)
                
        #Checa variáveis não usadas no escopo global ao final do arquivo
        nao_usadas = self.tabela_simbolos.sair_escopo()
        self.checar_variaveis_nao_usadas(nao_usadas)
        
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
            elif kind == 'IDENT': 
                return self.parse_atribuicao()
            else:
                self.reporta_erro(f"Comando iniciado com '{value}'")
                self.panic_mode() 
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
        self.advance() 

        #depois do tipo TEM q vir o nome da variavel
        if not self.current_token or self.current_token[0] != 'IDENT':
            self.reporta_erro("Esqueceu o nome da variável animal")
            raise Exception("Panic")
        
        variavel_nome = self.current_token[1]
        linha_decl, col_decl = self.current_token[2], self.current_token[3]
        self.advance() 

        #INÍCIO CHECAGEM SEMÂNTICA 
        if not self.tabela_simbolos.declarar(variavel_nome, type_token, linha_decl, col_decl):
            self.reporta_erro_semantico(f"A variável '{variavel_nome}' já foi declarada neste escopo.", linha_decl, col_decl)
        #FIM CHECAGEM SEMÂNTICA 

        expressao = None
        #Se tiver um = logo em seguida, resolve a expressão da direita
        if self.current_token and self.current_token[0] == 'OPER_ATRIBUI':
            self.advance() 
            expressao = self.parse_expression()
            
            #CHECAGEM DE TIPO NA DECLARAÇÃO 
            if expressao and expressao.get('eval_type'):
                tipo_recebido = expressao['eval_type']
                self.checar_tipos_atribuicao(type_token, tipo_recebido, variavel_nome, linha_decl, col_decl)

        #Independente se recebeu valor ou não TEM q fechar com ;
        if not self.match('DELIM', ';'):
            raise Exception("Panic")

        return {'type': 'VarDecl', 'var_type': type_token, 'name': variavel_nome, 'value': expressao, 'eval_type': type_token}

    def parse_atribuicao(self):
        #Ex: x = 10;
        if not self.current_token:
            self.reporta_erro("Deu erro era pra ter esperado uma atribuição.")
            raise Exception("Panic")

        variavel_nome = self.current_token[1]
        linha_uso, col_uso = self.current_token[2], self.current_token[3]
        self.advance() 

        #INÍCIO CHECAGEM SEMÂNTICA
        tipo_var = self.tabela_simbolos.buscar_geral(variavel_nome)
        if not tipo_var:
            self.reporta_erro_semantico(f"A variável '{variavel_nome}' está sendo usada mas não foi declarada.", linha_uso, col_uso)
        #FIM CHECAGEM SEMÂNTICA 

        if not self.match('OPER_ATRIBUI', '='):
            raise Exception("Panic")
        
        expr = self.parse_expression()
        
        #CHECAGEM DE TIPO NA ATRIBUIÇÃO 
        tipo_recebido = expr.get('eval_type', 'unknown')
        if tipo_var:
            self.checar_tipos_atribuicao(tipo_var, tipo_recebido, variavel_nome, linha_uso, col_uso)

        if not self.match('DELIM', ';'):
            raise Exception("Panic")

        return {'type': 'Assignment', 'name': variavel_nome, 'value': expr}

    def parse_if(self):
        self.advance() 
        
        if not self.match('DELIM', '('): raise Exception("Panic")
        condition = self.parse_expression() 
        if not self.match('DELIM', ')'): raise Exception("Panic")

        true_block = self.parse_block() 
        false_block = None

        #O else é opcional, checa se ele existe
        if self.current_token and self.current_token[0] == 'ELSE':
            self.advance() 
            false_block = self.parse_block()

        return {'type': 'If', 'condition': condition, 'true_block': true_block, 'false_block': false_block}

    def parse_while(self):
        self.advance() 
        
        if not self.match('DELIM', '('): raise Exception("Panic")
        condition = self.parse_expression()
        if not self.match('DELIM', ')'): raise Exception("Panic")

        block = self.parse_block()
        return {'type': 'While', 'condition': condition, 'body': block}

    def parse_for(self):
        self.advance() 
        if not self.match('DELIM', '('): raise Exception("Panic")

        if not self.current_token:
            self.reporta_erro("Arquivo acabou no meio do 'for'.")
            raise Exception("Panic")

        self.tabela_simbolos.entrar_escopo() 

        init = None
        if self.current_token[0] in ('INT', 'FLOAT', 'CHAR'):
            init = self.parse_declaracao_variavel() 
        elif self.current_token[0] == 'IDENT':
            init = self.parse_atribuicao() 
        else:
            self.match('DELIM', ';') 

        #Parte 2: Condição (ex: i < 10;)
        condition = self.parse_expression()
        if not self.match('DELIM', ';'): raise Exception("Panic")

        #Parte 3: Incremento (ex: i = i + 1) -> n tem ; no final
        increment = None
        if self.current_token and self.current_token[0] == 'IDENT':
            variavel_nome = self.current_token[1]
            linha_inc, col_inc = self.current_token[2], self.current_token[3]
            self.advance()
            
            tipo_var = self.tabela_simbolos.buscar_geral(variavel_nome)
            if not tipo_var:
                self.reporta_erro_semantico(f"A variável '{variavel_nome}' usada no incremento do for não existe.", linha_inc, col_inc)
            
            if self.match('OPER_ATRIBUI', '='):
                expr = self.parse_expression()
                tipo_recebido = expr.get('eval_type', 'unknown')
                
                #CHECAGEM DE TIPO NO INCREMENTO DO FOR 
                if tipo_var:
                    self.checar_tipos_atribuicao(tipo_var, tipo_recebido, variavel_nome, linha_inc, col_inc)
                    
                increment = {'type': 'Assignment', 'name': variavel_nome, 'value': expr}
        
        if not self.match('DELIM', ')'): raise Exception("Panic")

        block = self.parse_block(cria_escopo=False)
        
        #Gera warnings ao sair do escopo do for
        nao_usadas = self.tabela_simbolos.sair_escopo() 
        self.checar_variaveis_nao_usadas(nao_usadas)

        return {'type': 'For', 'init': init, 'condition': condition, 'increment': increment, 'body': block}

    def parse_block(self, cria_escopo=True):
        if not self.match('DELIM', '{'): raise Exception("Panic")
        
        if cria_escopo:
            self.tabela_simbolos.entrar_escopo()
            
        statements = []
        #Fica lendo comandos ate achar o fecha chaves
        while self.current_token and not (self.current_token[0] == 'DELIM' and self.current_token[1] == '}'):
            stmt = self.parse_direcionamento()
            if stmt:
                statements.append(stmt)
        
        if not self.match('DELIM', '}'): raise Exception("Panic")
        
        if cria_escopo:
            #Gera warnings ao fechar chaves de um bloco
            nao_usadas = self.tabela_simbolos.sair_escopo()
            self.checar_variaveis_nao_usadas(nao_usadas) 
            
        return statements

    def parse_expression(self):
        #Expressões pegando operadores (+ - / * > < ==)
        left = self.parse_termo()

        #Fica num laço juntando a esquerda com a direita enquanto achar operadores
        while self.current_token and self.current_token[0] in ('OPER', 'OPER_LOG'):
            op = self.current_token[1]
            linha_op, col_op = self.current_token[2], self.current_token[3]
            self.advance() 
            right = self.parse_termo()
            
            tipo_esq = left.get('eval_type', 'unknown')
            tipo_dir = right.get('eval_type', 'unknown')
            eval_type = 'unknown'

            #A REGRA APLICADA AQUI: Se for matemática e tiver qualquer 'float' no meio, o resultado é 'float'
            if op in ('+', '-', '*', '/', '%'):
                if tipo_esq == 'char' or tipo_dir == 'char':
                    self.reporta_erro_semantico(f"Operação matemática '{op}' não permitida com o tipo 'char'.", linha_op, col_op)
                elif tipo_esq == 'float' or tipo_dir == 'float':
                    eval_type = 'float'
                else:
                    eval_type = 'int'
            elif op in ('&&', '||', '!=', '==', '<=', '>=', '<', '>'):
                if (tipo_esq == 'char' and tipo_dir != 'char') or (tipo_dir == 'char' and tipo_esq != 'char'):
                    self.reporta_erro_semantico(f"Operação lógica '{op}' inválida entre tipos incompátiveis ('{tipo_esq}' e '{tipo_dir}').", linha_op, col_op)
                eval_type = 'int'

            left = {'type': 'BinOp', 'left': left, 'op': op, 'right': right, 'eval_type': eval_type}
            
        return left

    def parse_termo(self):
        #Resolve o nivel mais basico da expressão (um numero, variavel, string ou algo entre parenteses)
        if not self.current_token:
            self.reporta_erro("Faltou completar a expressão matemática ou a logica")
            raise Exception("Panic")
            
        kind, value, linha, coluna = self.current_token
        eval_type = 'unknown'
        
        if kind in ('IDENT', 'NUM_INT', 'NUM_FLOAT', 'STR_LIT', 'CHAR_LIT'):
            self.advance()
            
            if kind == 'IDENT':
                tipo_var = self.tabela_simbolos.buscar_geral(value)
                if not tipo_var:
                    self.reporta_erro_semantico(f"A variável '{value}' usada na expressão não foi declarada.", linha, coluna)
                else:
                    eval_type = tipo_var
            elif kind == 'NUM_INT': eval_type = 'int'
            elif kind == 'NUM_FLOAT': eval_type = 'float'
            elif kind == 'STR_LIT': eval_type = 'char'
            elif kind == 'CHAR_LIT': eval_type = 'char'
            
            return {'type': 'Literal/Var', 'value': value, 'eval_type': eval_type}
            
        elif kind == 'DELIM' and value == '(': 
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
            
        tokens = []
        for token in lexer(code):
            if token[0] != 'TOKEN_INEX':
                tokens.append(token)        
                
        parser = Parser(tokens)
        ast = parser.parse_program() 
        
        print(f"\n Análise Sintática e Semântica: {code_txt} ")
        if parser.errors or parser.semantic_errors or parser.warnings:
            if parser.errors:
                print(f"\nO parser achou {len(parser.errors)} erro(s) de sintaxe:")
                for erro in parser.errors:
                    print(f" -> {erro}")
            
            if parser.semantic_errors:
                print(f"\nO analisador semântico achou {len(parser.semantic_errors)} erro(s) semântico(s):")
                for erro in parser.semantic_errors:
                    print(f" -> {erro}")
                    
            if parser.warnings:
                print(f"\nO analisador gerou {len(parser.warnings)} WARNING(S):")
                for aviso in parser.warnings:
                    print(f" -> {aviso}")
        else:
            print("Código analisado sem erros de sintaxe, regras semânticas válidas e nenhum warning!")

    except FileNotFoundError:
        print("Escreveu o nome do arquivo errado animal.")

if __name__ == '__main__':
    main()