# Rafael de Camargo Sampaio
# Carolina Braun Prado
# GRUPO 1
import sys
import re

# VARIAVEIS GLOBAIS
MEM = None  # armazena posicao no historico
RES = 0     # contador de expressoes processadas
debug_output = ""  # salva linha e resultado em float
valid_operators = ["+", "-", "*", "/", "|", "%", "^"]
reserved_words = ["if","then", "else", "while", "for", "range", "in", "res", "mem"]
identif = ["range", "in", "res", "mem"]
comparators = ["==", "!=", "<", ">", "<=", ">="]
valid_for_variables = list(set("abcdefghijklmnopqrstuvwxyz"))
            
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

classes = {
    "ParenIni": "(",
    "ParenEnd": ")",
    "Número": is_float,  # Function to check if the value is a float
    "Operador": valid_operators,
    "Identificador": identif + valid_for_variables,  # Combine identif and valid_for_variables
    "PalavraReservada": reserved_words,
    "Comparador": comparators,
    "NotFound": lambda x: True  # Catch-all for any other token,
}


def is_calculable(tokens, index):
    try: 
        if tokens[index-1] in valid_operators or tokens[index-2] in valid_operators: return True
        else: return False
    except:
        return False
    
# avalia expressao RPN e gera assembly
def evaluate_rpn(tokens, linestack, lineResult):
    global MEM, RES
    
    for i in range(len(tokens)):
        token = tokens[i]

        if isinstance(token, list) and token[1]=="RES":  # caso (N RES)
            line = int(token[0]) - 1
            if line <= RES:
                linestack.append(lineResult[line][2])

            else:
                return None 
            
        elif isinstance(token, list): # caso aninhado
            linestack, r_sub = evaluate_rpn(token,linestack,lineResult)
            linestack.append(str(r_sub))
            

        elif re.match(r'^-?\d+(\.\d+)?$', token):  # numero inteiro
            linestack.append(token)
            

        elif token == "MEM":
            if is_calculable(tokens, i): #recupera valor
                if MEM != None:
                    linestack.append(lineResult[MEM][2])

                else:                           # caso (V MEM)
                    linestack.append(0)
            
            else:
                MEM = RES
                return linestack, float(linestack.pop(-1))

        elif token in "+-*/|%^": # caso operação
            secondary = float(linestack.pop(-1))
            primary = float(linestack.pop(-1))

            if (token == '|' or token == '/') and secondary == 0.0:
                return None
            
            if (token == '^' and secondary < 0) or token == '^' and not (isinstance(secondary, float) and secondary.is_integer()):
                return None

            try:
                if token != '|':
                    if token == '^': r = f"{primary**secondary:.4f}"
                    elif token == '/': r = f"{primary/secondary:.0f}"
                    else: r = eval(f"{primary}{token}{secondary}")
                else:
                    r = f"{primary / secondary:.4f}"
            except:
                r = 0


        else:
            raise ValueError(f"Token invalido: {token}")

    return linestack, r

# separa tokens RPN aninhados, incluindo parenteses
def split_expression_into_tokens(expr: str):
    """
    Splits the input string into a list where each character is an item.
    """
    return list(expr.strip())

def analyze_expression_tokens(chars):
    """
    Analyzes a list of characters and finds items in the expression.
    Returns a structure similar to tokenize_rpn_with_parentheses and the starting position of each item.
    """
    tokens = []
    token = ''
    positions = []
    current_position = None

    for index, char in enumerate(chars):
        if char.isspace():
            if token:
                tokens.append(token)
                positions.append(current_position)
                token = ''
                current_position = None
        elif char in '()':
            if token:
                tokens.append(token)
                positions.append(current_position)
                token = ''
                current_position = None
            tokens.append(char)
            positions.append(index)
        else:
            if token == '':
                current_position = index
            token += char

    if token:
        tokens.append(token)
        positions.append(current_position)

    return tokens, positions

def extract_parentheses_content(tokens):
    """
    Extracts the content inside parentheses, including handling nested cases.
    """
    stack = [[]]  # Stack to manage nested lists
    for token in tokens:
        if token == '(':
            # Start a new list for nested parentheses
            stack.append([])
        elif token == ')':
            # Close the current list and add it to the previous level
            if len(stack) == 1:
                raise ValueError("Unmatched closing parenthesis.")
            completed = stack.pop()
            stack[-1].append(completed)
        else:
            # Add the token to the current list
            stack[-1].append(token)
    
    if len(stack) != 1:
        raise ValueError("Unmatched opening parenthesis.")
    
    return stack[0][0]

def apply_lower_to_tokens(tokens):
    """
    Applies the lower() method to each token in the list.
    """
    return [token.lower() if isinstance(token, str) else token for token in tokens]

def classify_tokens(tokens):
    """
    Classifies each token using the classes dictionary.
    """
    classified_tokens = []
    for token in tokens:
        token_class = "Erro"  # Default to "Erro" if no match is found
        for class_name, class_value in classes.items():
            if callable(class_value):  # If the class value is a function
                if class_value(token):
                    token_class = class_name
                    break
            elif isinstance(class_value, list):  # If the class value is a list
                if token in class_value:
                    token_class = class_name
                    break
            elif token == class_value:  # If the class value is a single value
                token_class = class_name
                break
        classified_tokens.append((token, token_class))
    return classified_tokens

def is_number(x):
    try:
        float(x)
        return True
    except:
        return False

def check_number_type(x):
    """
    Verifica se o número em uma string é um inteiro ou um float.
    Retorna 'int' se for inteiro, 'float' se for float, ou None se não for um número.
    """
    try:
        if '.' in x or 'e' in x.lower():
            float(x)
            return 'float'
        else:
            int(x)
            return 'int'
    except ValueError:
        return None

def validate_condition(condicao):
    """
    Valida a condição de um bloco 'if', incluindo comparações como ['mem', '>=', '3'].
    """
    if not isinstance(condicao, list) or len(condicao) != 3:
        return False, f"Condição inválida: {condicao}. Esperado formato [A operador B]."

    a, operador, b = condicao

    if operador not in comparators:
        return False, f"Operador inválido na condição: {operador}."

    a_valido = is_number(a) or a in valid_for_variables or a == 'mem'
    b_valido = is_number(b) or b in valid_for_variables or b == 'mem'

    if not a_valido:
        return False, f"Operando esquerdo inválido na condição: {a}."
    if not b_valido:
        return False, f"Operando direito inválido na condição: {b}."

    return True, ""

def validate_range_condition(condicao):
    """
    Valida a condição de um range, que deve ser uma lista contendo 'mem' ou um número inteiro.
    """
    if not isinstance(condicao, list) or len(condicao) != 1:
        return False, f"Condição de range inválida: {condicao}. Esperado formato ['valor']."

    valor = condicao[0]

    if valor == 'mem':
        return True, ""
    
    if is_number(valor) and check_number_type(valor) == 'int':
        return True, ""
    
    return False, f"Condição de range inválida: {valor}. Esperado 'mem' ou um número inteiro."

def validate_expression(expr):
    if not isinstance(expr, list):
        return False, "Expressão deve ser uma lista."

    # MEM simples
    if len(expr) == 1 and expr[0] == 'mem':
        return True, ""

    # (N RES) ou (V MEM)
    if len(expr) == 2:
        if is_number(expr[0]) and expr[1] in ['res', 'mem']:
            return True, ""
        return False, f"Expressão inválida: {expr}. Esperado (N RES) ou (V MEM)."

    # Expressão aritmética binária (A B op)
    if len(expr) == 3:
        a, b, op = expr
        if op not in valid_operators:
            return False, f"Operador inválido: {op}."
        if not (is_number(a) or (isinstance(a, list) and validate_expression(a)[0]) or a in valid_for_variables or a == 'mem'):
            return False, f"Operando esquerdo inválido: {a}."
        if not (is_number(b) or (isinstance(b, list) and validate_expression(b)[0]) or b in valid_for_variables or b == 'mem'):
            return False, f"Operando direito inválido: {b}."
        return True, ""

    # Estrutura if-then-(else opcional)
    if len(expr) >= 4 and expr[0] == 'if':
        try:
            condicao = expr[1]
            if expr[2] != 'then':
                return False, f"Palavra-chave 'then' ausente na expressão: {expr}."
            bloco_then = expr[3]
            condicao_valida, condicao_msg = validate_condition(condicao)
            if not condicao_valida:
                return False, condicao_msg
            if isinstance(bloco_then, list):
                if not validate_expression(bloco_then)[0]:
                    return False, f"Bloco 'then' inválido: {bloco_then}."
            else:
                return False, f"Bloco 'then' deve ser uma lista: {bloco_then}."

            # Verifica se existe um bloco 'else' e valida
            if len(expr) > 4 and expr[4] == 'else':
                bloco_else = expr[5]
                if isinstance(bloco_else, list):
                    if not validate_expression(bloco_else)[0]:
                        return False, f"Bloco 'else' inválido: {bloco_else}."
                else:
                    return False, f"Bloco 'else' deve ser uma lista: {bloco_else}."

            return True, ""
        except:
            return False, f"Erro ao validar expressão 'if': {expr}."

    # Estrutura for (i) in range(MEM) then bloco
    if len(expr) >= 7 and expr[0] == 'for' and isinstance(expr[1], list) and len(expr[1]) == 1:
        var = expr[1][0]
        if var not in valid_for_variables:
            return False, f"Variável de loop inválida: {var}."
        if expr[2] != 'in' or expr[3] != 'range':
            return False, f"Palavras-chave 'in range' ausentes ou inválidas na expressão: {expr}."
        
        range_valida, range_msg = validate_range_condition(expr[4])
        if not range_valida:
            return False, range_msg
        
        if expr[5] != 'then':
            return False, f"Palavra-chave 'then' ausente na expressão: {expr}."
        if not validate_expression(expr[6])[0]:
            return False, f"Bloco 'then' inválido: {expr[6]}."
        
        return True, ""

    return False, f"Expressão inválida ou não reconhecida: {expr}."


# processa o arquivo txt
def processar_arquivo(nome_arquivo):
    global RES
    lineResult = []
    full_log = ""
    error_lex_log = ""
    output = ""

    with open(nome_arquivo) as f:
        linhas = f.readlines()

    for idx, linha in enumerate(linhas):
        linestack = []

        lex_error = False

        try:
            splited_line = split_expression_into_tokens(linha.strip())
            item_and_index = analyze_expression_tokens(splited_line)
            
            tokens = item_and_index[0]
            token_index = item_and_index[1]

            tokens = apply_lower_to_tokens(tokens)
            classified_tokens = classify_tokens(tokens)

            tokens = extract_parentheses_content(tokens)
            
            
            full_log += ("\n" + str(linha) + str(tokens) + "\n" + "")
            for i in range(len(classified_tokens)): 
                posText = token_index[i]
                if classified_tokens[i][1] == "NotFound":
                    msg = f"Token '{classified_tokens[i][0]}' invalido na linha {idx+1}, posição {posText}"
                    error_lex_log += "\n" + str(linha)
                    error_lex_log += msg
                    output += "\n" + str(linha)
                    output += msg
                    lineResult.append([tokens,msg,None])
                    lex_error = True
                    break
                full_log += f"Token: '{classified_tokens[i][0]}', Classe: '{classified_tokens[i][1]}, Posição: {posText}\n"
            
            if not lex_error:
                expr_valid, msg = validate_expression(tokens)
                if not expr_valid:
                    error_lex_log += "\n" + str(linha)
                    error_lex_log += f"Erro sintático na linha {idx+1}: {msg}\n"
                    output += "\n" + str(linha)
                    output += f"Erro sintático na linha {idx+1}: {msg}\n"
                    lineResult.append([tokens,msg,None])
                else:
                    output += str(linha)
                    output += "OK\n"
                    linestack, result = evaluate_rpn(tokens, linestack, lineResult)
                    lineResult.append([tokens,"OK",linestack])
        except Exception as e:
            lineResult.append([None, None, None])

        RES += 1
    
    return lineResult, full_log, error_lex_log, output

# main executa usando sys.argv ao inves de input
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python programa.py arquivo.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    result, full_log, error_lex_log, output = processar_arquivo(nome_arquivo)

    # print(full_log)
    # print(error_lex_log)
    # print(output)
    for x in result:
        print(f"Expr: {x[0]}\nMessage:{x[1]}\n")

    # print("Resultados em py:")
    # for expr, val in debug_output:
    #     print(f"{expr} = {val if isinstance(val, str) else f'{val:.4f}'}")

