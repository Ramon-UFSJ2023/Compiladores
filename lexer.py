import re


#O \ no regex é pra falar que quero usar literalmente os significados do simbolo. Ex r'\.', literalmente usar o ponto, enquanto r'.' é qualquer caractere
tokens_provisorios = [
    ('NUM_FLOAT', r'\d+(\.\d+)?' ), #o \d significa numero, o + significa que aceita mais de um numero "(\.\d+)?" fala que é opcional mas aceita ponto flutuante
    ('NUM_INT', r'\d+'), #mesma coisa que o float só que aqui só aceita numeros inteiros, importante para diferenciar int e float quando for compilar o codigo
    ('IDENT', r'[a-zA-Z_]\w*'), # aqui esta dizendo que aceita qualquer letra maiscula ou minusculas, o \w é o simbolo para aceitar letra ou numero
    ('OPER', r'[+\-*/%]'), #Aqui foi necessario usar o \ pra dizer que é literalmente minus e não criar um espaço de um ponto ao outro como a-z
    ('OPER_LOG', r'&&|\|\||!|<=|>=|<|>|=='), #no regex o | sem o literalmente(\) é OU por isso ele veio logo após o &&
    ('OPER_ATRIBUI', r'='), # é o operador de atribuição
    ('SKIP', r'[ \t]+'), # o espaço vazio é realmente que aceita um espaço e o \t é o tab. O + é pra aceitar mais de um espaço ou tab
    ('NEW_LINE', r'\n'), #é só a quebra de linha
]

keywords = {'if', 'while', 'for', 'return', 'main'}

toke_regex_jun = '|'.join(f'(?P<{name}>{pattern})'
                          for name, pattern in tokens_provisorios) #o '|' junta todos os grupos de regex em um unico e depois disso vc só nomeou os grupos e o parten e r'...'


def lexer(code):
    for match in re.finditer(toke_regex_jun, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'IDENT' and value in keywords:
            kind = value.upper() #Se achar uma palavra reservada que sera lida como um token de identificação ele deixa em caixa alta 
        if kind == 'SKIP':
            continue
        yield(kind, value)
