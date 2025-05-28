# Carolina Braun Prado
# Rafael de Camargo Sampaio
# GRUPO 1

# Dicionário de classes de tokens          
# NUM - Inteiro ou Float
# OP - Operadores aritméticos
# CMP - Comparadores
# MEM - Identificador 'mem'
# RES - Identificador 'res'
# KW - Palavras reservadas (if, for)
# 
# Regras de produção de sintaxe:
# ( NUM/MEM RES ) - NUM
# ( NUM MEM ) - NUM
# ( NUM NUM OP ) - NUM
# ( NUM NUM CMP ) - BOOL
# ( BOOL NUM NUM KW ) - NUM
#

import sys
import re
import time
from graphviz import Digraph

# VARIAVEIS GLOBAIS
MEM = None  # armazena posicao no historico
RES = 0     # contador de expressoes processadas
debug_output = ""  # salva linha e resultado em float

class Node:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children if children else []

    def __repr__(self, level=0):
        ret = "\t"*level + f"{self.type}: {self.value}\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret
    
    def get_type(self):
        return self.type
    def get_value(self):
        return self.value
    def get_children(self):
        return self.children
    def set_type(self, type_):
        self.type = type_
    def set_value(self, value):
        self.value = value
    def add_child(self, child):
        self.children.append(child) 

class SimpleNode:
    def __init__(self, value=None):
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self, level=0, prefix="", is_last=True):
        # Print the node value with tree-like connectors
        lines = []
        connector = ""
        if level > 0:
            connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{self.value}")

        # Prepare prefix for children
        if level > 0:
            child_prefix = prefix + ("    " if is_last else "│   ")
        else:
            child_prefix = ""

        for i, child in enumerate(self.children):
            last = (i == len(self.children) - 1)
            lines.append(child.__repr__(level + 1, child_prefix, last))
        return "\n".join(lines)

def draw_tree(node, graph=None, parent_id=None, counter=[0]):
    if graph is None:
        graph = Digraph()
    node_id = f"{node.type}_{counter[0]}"
    counter[0] += 1
    graph.node(node_id, f"{node.type}\n{node.value}")
    if parent_id:
        graph.edge(parent_id, node_id)
    for child in node.children:
        draw_tree(child, graph, node_id, counter)
    return graph

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


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

        if isinstance(token, list) and token[1]=="res":  # caso (N RES)
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
            

        elif token == "mem":
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

def lexAnalysis(linha,numero_linha=0):
    error_lex_log = ""
    tokens = []
    par_ini = 0
    par_end = 0
    pos = 0
    
    while pos < len(linha):
        char = linha[pos]

        if char.isspace():
            pos += 1
            continue

        elif char.isdigit() or char == '.': # Números (inteiros e floats)
            start = pos
            num = ""
            while pos < len(linha) and (linha[pos]!=" "):
                num += linha[pos]
                pos += 1
            tokens.append(("NUM", num, start))

        elif char in "+-*/|%^": # Operadores aritméticos
            tokens.append(("OP", char, pos))
            pos += 1
        
        elif char == "=": # Comparador ==
            if pos + 1 < len(linha) and linha[pos + 1] == "=":
                tokens.append(("CMP", "==", pos))
                pos += 2
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {pos}: '{char}'\n")
                break

        elif char == "!": # Comparador !=
            if pos + 1 < len(linha) and linha[pos + 1] == "=":
                tokens.append(("CMP", "!=", pos))
                pos += 2
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {pos}: '{char}'\n")
                break

        elif char in "<>": # Comparadores <, >, <=, >=
            if pos + 1 < len(linha) and linha[pos + 1] == "=":
                tokens.append(("CMP", char + "=", pos))
                pos += 2
            elif pos + 1 < len(linha) and linha[pos + 1] == ")" or linha[pos + 1] == " ":
                tokens.append(("CMP", char, pos))
                pos += 1
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {pos}: '{char}'\n")
                break

        elif char in "()": # Parênteses
            if char == '(':
                tokens.append(("PAR_INI", char, pos))
                par_ini += 1
            elif char == ')':
                tokens.append(("PAR_END", char, pos))
                par_end += 1
            pos += 1

        elif linha[pos] == 'm' or linha[pos] == 'M': # Identificador 'mem'
            inside_pos = pos + 1
            if linha[pos+1] == 'e' or linha[pos+1] == 'E':
                inside_pos += 1
                if linha[pos+2] == 'm' or linha[pos+2] == 'M':
                    tokens.append(("MEM", "mem", pos))
                    pos += 3
                else:
                    error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                    break
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                break

        elif linha[pos] == "r" or linha[pos] == "R": # Identificador 'res'
            inside_pos = pos + 1
            if linha[pos+1] == "e" or linha[pos+1] == "E":
                inside_pos += 1
                if linha[pos+2] == "s" or linha[pos+2] == "S":
                    tokens.append(("RES", "res", pos))
                    pos += 3
                else:
                    error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                    break
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                break
        
        elif linha[pos] == "i" or linha[pos] == "I": # Palavra reservada 'if'
            inside_pos = pos + 1
            if linha[pos+1] == "f" or linha[pos+1] == "F":
                tokens.append(("KW", linha[pos:pos+2].lower(), pos))
                pos += 2
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")  
                break

        elif linha[pos] == 'f' or linha[pos] == 'F': # Palavra reservada 'for'
            inside_pos = pos + 1
            if linha[pos+1] == "o" or linha[pos+1] == "O":
                inside_pos += 1
                if linha[pos+2] == "r" or linha[pos+2] == "R":
                    tokens.append(("KW", linha[pos:pos+3].lower(), pos))
                    pos += 3
                else:
                    error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                    break
            else:
                error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {inside_pos}: '{linha[inside_pos]}'\n")
                break
        else:
            error_lex_log += (f"Token inválido na linha {numero_linha}, coluna {pos}: '{char}'\n")
            break

    if par_ini != par_end and error_lex_log == "":
        error_lex_log += (f"Erro de sintaxe: Parênteses desbalanceados na linha {numero_linha}. Nichos iniciados: {par_ini}; Nichos fechados: {par_end}\n")
        return [], error_lex_log
    
    if error_lex_log != "":
        tokens = []

    return tokens, error_lex_log

def sintaxAnalysis(tokens, numero_linha=0):
    error_sintax_log = ""
    nodeStack = []

    pos = 0
    while pos < len(tokens):
        tokenClass = tokens[pos][0]
        
        if tokenClass == "PAR_INI":
            nodeStack.append(Node(tokenClass, tokens[pos]))

        elif tokenClass == "NUM":
            nodeStack.append(Node(tokenClass, tokens[pos]))
            
        elif tokenClass == "OP" or tokenClass == "CMP":
            nodeStack.append(Node(tokenClass, tokens[pos]))

        elif tokenClass == "MEM" or tokenClass == "RES":
            nodeStack.append(Node(tokenClass, tokens[pos]))

        elif tokenClass == "KW":
            nodeStack.append(Node(tokenClass, tokens[pos]))

        elif tokenClass == "PAR_END":
            endNode = nodeStack.pop()
            
            if endNode.get_type() == "RES":
                before = nodeStack.pop()
                if before.get_type() == "NUM" or before.get_type() == "MEM":
                    lastNode = nodeStack.pop()
                    if lastNode.get_type() == "PAR_INI":
                        endNode.add_child(before)
                        endNode.set_type("NUM")
                        nodeStack.append(endNode)
                    else:
                        error_sintax_log += f"Erro na linha {numero_linha}, coluna {lastNode.get_value()[2]}: {lastNode.get_value()[1]}.\n"
                        break
                else:
                    error_sintax_log += f"Erro de sintaxe: 'res' deve ser precedido por um número ou 'mem' na linha {numero_linha}.\n"
                    break
                                    
            elif endNode.get_type() == "MEM":
                before = nodeStack.pop()
                if before.get_type() == "NUM":
                    lastNode = nodeStack.pop()
                    if lastNode.get_type() == "PAR_INI":
                        endNode.add_child(before)
                        endNode.set_type("NUM")
                        nodeStack.append(endNode)
                    else:
                        error_sintax_log += f"Erro na linha {numero_linha}, coluna {lastNode.get_value()[2]}: {lastNode.get_value()[1]}.\n"
                        break
                else:
                    error_sintax_log += f"Erro de sintaxe: 'mem' deve ser precedido por um número na linha {numero_linha}.\n"
                    break

            elif endNode.get_type() == "OP":
                before01 = nodeStack.pop()
                type01 = before01.get_type()
                before02 = nodeStack.pop()
                type02 = before02.get_type()
                if (type01 == "NUM" or type01 == "MEM"):
                    if (type02 == "NUM" or type02 == "MEM"):
                        lastNode = nodeStack.pop()
                        if lastNode.get_type() == "PAR_INI":
                            endNode.add_child(before01)
                            endNode.add_child(before02)
                            endNode.set_type("NUM")
                            nodeStack.append(endNode)
                        else:
                            error_sintax_log += f"Erro na linha {numero_linha}, coluna {lastNode.get_value()[2]}: {lastNode.get_value()[1]}.\n"
                            break
                    else:
                        error_sintax_log += f"Erro de sintaxe: Operações aritméticas devem ser entre números ou 'mem' na linha {numero_linha}, coluna {before02.get_value()[2]}.\n"
                        break
                else:
                    error_sintax_log += f"Erro de sintaxe: Operações aritméticas devem ser entre números ou 'mem' na linha {numero_linha}, coluna {before01.get_value()[2]}.\n"
                    break
            
            elif endNode.get_type() == "CMP":
                before01 = nodeStack.pop()
                type01 = before01.get_type()
                before02 = nodeStack.pop()
                type02 = before02.get_type()
                if (type01 == "NUM" or type01 == "MEM"):
                    if (type02 == "NUM" or type02 == "MEM"):
                        lastNode = nodeStack.pop()
                        if lastNode.get_type() == "PAR_INI":
                            endNode.add_child(before01)
                            endNode.add_child(before02)
                            endNode.set_type("BOOL")
                            nodeStack.append(endNode)
                        else:
                            error_sintax_log += f"Erro na linha {numero_linha}, coluna {lastNode.get_value()[2]}: {lastNode.get_value()[1]}.\n"
                            break
                    else:
                        error_sintax_log += f"Erro de sintaxe: Comparações devem ser entre números ou 'mem' na linha {numero_linha}, coluna {before02.get_value()[2]}.\n"
                        break
                else:
                    error_sintax_log += f"Erro de sintaxe: Comparações aritméticas devem ser entre números ou 'mem' na linha {numero_linha}, coluna {before01.get_value()[2]}.\n"
                    break
            
            elif endNode.get_type() == "KW":
                before01 = nodeStack.pop()
                type01 = before01.get_type()
                before02 = nodeStack.pop()
                type02 = before02.get_type()
                before03 = nodeStack.pop()
                type03 = before03.get_type()
                if type01 == "NUM":
                    if (type02 == "NUM" or type02 == "MEM"):
                        if type03 == "BOOL":
                            lastNode = nodeStack.pop()
                            if lastNode.get_type() == "PAR_INI":
                                endNode.add_child(before01)
                                endNode.add_child(before02)
                                endNode.add_child(before03)
                                endNode.set_type("NUM")
                                nodeStack.append(endNode)
                            else:
                                error_sintax_log += f"Erro na linha {numero_linha}, coluna {lastNode.get_value()[2]}: {lastNode.get_value()[1]}.\n"
                                break
                        else:
                            error_sintax_log += f"Erro de sintaxe: o primeiro item deve ser uma Comparação na linha {numero_linha}, coluna {before03.get_value()[2]}.\n"
                            break
                    else:
                        error_sintax_log += f"Erro de sintaxe: o segundo item deve ser uma Número/Operação na linha {numero_linha}, coluna {before02.get_value()[2]}.\n"
                        break
                else:
                    error_sintax_log += f"Erro de sintaxe: o terceiro item deve ser uma Número/Operação na linha {numero_linha}, coluna {before01.get_value()[2]}.\n"
                    break
            else:
                error_sintax_log += f"Erro de sintaxe: Parênteses fechados sem correspondência na linha {numero_linha}.\n"
                return [], error_sintax_log
        else:
            error_sintax_log += f"Erro de sintaxe: Token desconhecido '{tokens[pos][1]}' na linha {numero_linha}.\n"
            return [], error_sintax_log

        pos += 1

    if len(nodeStack) != 1:
        error_sintax_log += f"Erro de sintaxe: Pilha de nós não está vazia após análise sintática na linha {numero_linha}.\n"
        return [], error_sintax_log

    if error_sintax_log != "":
        return [], error_sintax_log

    return nodeStack[0], error_sintax_log

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
        if is_number(expr[0]) or (isinstance(expr[0], list) and validate_expression(expr[0])[0]) and expr[1] in ['res', 'mem']:
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

def simplify_node(node):
    if node is None:
        return None

    # Extrai o valor do índice 1 do value, se possível
    if isinstance(node.value, (tuple, list)) and len(node.value) > 1:
        valor = node.value[1]
    else:
        valor = node.value

    novo_node = SimpleNode(valor)

    # Mantém os filhos na mesma hierarquia
    for child in node.get_children():
        novo_node.add_child(simplify_node(child))

    return novo_node

# processa o arquivo txt
def processar_arquivo(nome_arquivo):
    global RES
    lineResult = []
    full_log = ""
    error_lex_log = ""
    error_sint_log = ""
    output = ""

    with open(nome_arquivo) as f:
        linhas = f.readlines()

    for idx, linha in enumerate(linhas):
        
        error_lex = False
        error_sint = False

        if linha[-1] == '\n':
            linha = linha[:-1]

        tokens, line_error_log = lexAnalysis(linha,idx+1)

        if tokens == []:
            error_lex = True
            error_lex_log += line_error_log
        else:
            # FULL LOG DE ANALISE LEXICA
            full_log += f"\n\nLinha {idx+1}: {linha}"
            for token in tokens:
                full_log += f"\n{token}"

        if not error_lex:
            node, line_error_log = sintaxAnalysis(tokens, idx+1)
            if node == []:
                error_sint = True
                error_sint_log += line_error_log
            else:
                # FULL LOG DE ANALISE SINTATICA
                full_log += f"\n\nAnálise Sintática:"
                full_log += f"\n{node}"
                full_log += f"\n{simplify_node(node)}"
                
        RES += 1
    
    return lineResult, full_log, error_lex_log, error_sint_log, output

# main executa usando sys.argv ao inves de input
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python programa.py arquivo.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    result, full_log, error_lex_log, error_sint_log, output = processar_arquivo(nome_arquivo)

    print("Resultados do processamento:")
    print(full_log)
    print("Erros Léxico:")
    print(error_lex_log)
    print("Erros Sintático:")
    print(error_sint_log)
    # print(error_lex_log)
    # print(output)
    # for x in result:
    #     print(f"Expr: {x[0]}\nMessage:{x[1]}\nResult:{x[2]}\n")

    # print("Resultados em py:")
    # for expr, val in debug_output:
    #     print(f"{expr} = {val if isinstance(val, str) else f'{val:.4f}'}")

