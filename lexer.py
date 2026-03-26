import re
import sys


#O \ no regex é pra falar que quero usar literalmente os significados do simbolo. Ex r'\.', literalmente usar o ponto, enquanto r'.' é qualquer caractere
tokens_provisorios = [
    ('NUM_FLOAT', r'\d+(\.\d+)' ), #o \d significa numero, o + significa que aceita mais de um numero "(\.\d+)" eu tinha deixado como opcional ter numeros dps do ponto, mas ai numeros inteiros n iriam entrar dentro de int
    ('NUM_INT', r'\d+'), #mesma coisa que o float só que aqui só aceita numeros inteiros, importante para diferenciar int e float quando for compilar o codigo
    ('IDENT', r'[a-zA-Z_]\w*'), # aqui esta dizendo que aceita qualquer letra maiscula ou minusculas, o \w é o simbolo para aceitar letra ou numero
    ('OPER', r'[+\-*/%]'), #Aqui foi necessario usar o \ pra dizer que é literalmente minus e não criar um espaço de um ponto ao outro como a-z
    ('OPER_LOG', r'&&|\|\||!=|!|<=|>=|<|>|=='), #no regex o | sem o literalmente(\) é OU por isso ele veio logo após o &&
    ('OPER_ATRIBUI', r'='), # é o operador de atribuição
    ('SKIP', r'[ \t\r]+'), # o espaço vazio é realmente que aceita um espaço e o \t é o tab. O + é pra aceitar mais de um espaço ou tab
    ('NEW_LINE', r'\n'), #é só a quebra de linha
    ('DELIM', r'\(|\)|;|\{|\}'), #aqui eu só criar delimitadores e pode ser qualquer um deles
    ('TOKEN_INEX', r'.'), #Se existir um token que n seja igual os de cima ele entra aqui e sei que é um erro
]

keywords = {'if', 'while', 'for', 'return', 'main', 'int', 'float', 'char'
            }

toke_regex_jun = '|'.join(f'(?P<{name}>{pattern})'
                          for name, pattern in tokens_provisorios) #o '|' junta todos os grupos de regex em um unico e depois disso vc só nomeou os grupos e o parten e r'...'


def lexer(code):
    linha =1
    inicio_linha=0
    for match in re.finditer(toke_regex_jun, code):
        kind = match.lastgroup
        value = match.group()
        if kind == 'NEW_LINE':
            linha+=1
            inicio_linha = match.end() #a proxima linha começa dps do \n, retorna a posição depois do token encontrado e a proxima linha começa no mach.end()
            continue

        if kind == 'IDENT' and value in keywords:
            kind = value.upper() #Se achar uma palavra reservada que sera lida como um token de identificação ele deixa em caixa alta 
        
        if kind == 'SKIP':
            continue
        
        if kind == 'TOKEN_INEX':
            coluna = match.start()-inicio_linha+1 #posição atual do token menos o inicio da linha+1, o match.sart retorna o local onde o token foi encontrado
        
        yield(kind, value, linha, coluna)

def main():
    if len(sys.argv)<2:
        print("Passe o arquivo.txt quando for executar")
        return
    Code_txt = sys.argv[1]

    try: 
        with open(Code_txt, 'r') as arq:
            Code = arq.read() #le o arquivo e guarda todo na variavel
        print(f"Analisando: {Code_txt}\n")
        for token in lexer(Code):
            tipo, valor, linha, coluna = token

            if token[0] == 'TOKEN_INEX':
                print(f"Erro lexico: Caractere inexistente {valor!r} na linha {linha}, coluna {coluna}")
            else:
                print(f"Token: {tipo: <15} | Valor: {valor}")

    except FileNotFoundError:
        print("Escreveu o nome do arquivo errado animal.\n")


if __name__ == '__main__':
    main()