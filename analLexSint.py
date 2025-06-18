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
# Regras de inferencia de semantica:
# ( NUM ) - int/float
# ( MEM ) - mem
# ( NUM/MEM RES ) - res
# ( NUM MEM ) - mem
# ( int/float/res/mem int/float/res/mem OP ) - int/float (se for | retorna float; se for / retorna int; se tiver mem ou res retorna float)
# ( int/float/res/mem int/float/res/mem CMP ) - bool
# ( bool int/float/mem/res int/float/mem/res if ) - int/float
# ( bool int/res(round value to int)/mem(round value to int) int/float for ) - int/float
#

import sys
import re
import time
from graphviz import Digraph

# VARIAVEIS GLOBAIS
MEM = 0.0  # armazena valor
RES = 0     # contador de expressoes processadas
debug_output = ""  # salva linha e resultado em float

class Node:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.semType = None  # Tipo semântico, a ser definido na análise semântica
        self.value = value
        self.primary = True 
        self.children = children if children else []

    def __repr__(self, level=0):
        ret = "\t"*level + f"{self.type}: {self.value} - Semantic: {self.semType} - Primary: {self.primary}\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret
    
    def get_type(self):
        return self.type
    def get_value(self):
        return self.value
    def get_children(self):
        return self.children
    def get_semType(self):
        return self.semType
    def is_primary(self):
        return self.primary
    def set_type(self, type_):
        self.type = type_
    def set_primary(self, primary):
        self.primary = primary
    def set_value(self, value):
        self.value = value
    def set_semType(self, value):
        self.semType = value
    def add_child(self, child):
        self.children.append(child) 

class SimpleNode:
    def __init__(self, value=None):
        self.value = value
        self.children = []
    
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

    def add_child(self, child):
        self.children.append(child)

def draw_tree(node, graph=None, parent_id=None, counter=[0]):
    if graph is None:
        graph = Digraph()
    node_id = f"{node.value}_{counter[0]}"
    counter[0] += 1
    graph.node(node_id, f"{node.value}")
    if parent_id:
        graph.edge(parent_id, node_id)
    for child in reversed(node.children):
        draw_tree(child, graph, node_id, counter)
    return graph

# --------------------- CODES USED ---------------------
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

# -------------------- ANALISADORES --------------------

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

        elif char.isdigit() or char == '.' or (char == '-' and (linha[pos+1].isdigit() or ((linha[pos+1] == '.') and linha[pos+2].isdigit()))): # Números (inteiros e floats)
            start = pos
            num = ""
            while pos < len(linha) and linha[pos]!=" ":
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
        # if numero_linha == 1:
        #     print(f"Linha: {numero_linha}; Posição atual: {pos}, Token atual: {tokens[pos]}")
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
                elif before.get_type() == "PAR_INI":
                    endNode.set_type("NUM")
                    nodeStack.append(endNode)
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
                if len(nodeStack) >=4:
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
                    kw_value = endNode.get_value()[1]
                    if kw_value == "if":
                        error_sintax_log += f"Erro de sintaxe: Estrutura '{kw_value}' deve conter pelo menos 3 itens na linha {numero_linha}, ([Condição] [Valor Se Verdade] [Valor Se Falso] {kw_value}).\n"
                        return [], error_sintax_log
                    else:
                        error_sintax_log += f"Erro de sintaxe: Estrutura '{kw_value}' deve conter pelo menos 3 itens na linha {numero_linha}, ([Critério de Parada] [Incremento] [Operação] {kw_value}).\n"
                        return [], error_sintax_log
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

def semanticAnalysis(node, error_sint=False):
    line_error_log = ""
    if error_sint:
        return None, line_error_log, True

    def _sem(node):
        nonlocal line_error_log, error_sint
        if node is None or error_sint:
            return

        for child in node.get_children():
            _sem(child)
            if error_sint:
                return

        children = node.get_children()
        if children and any(child.get_semType() is None for child in children):
            return

        tclass = node.value[0] if isinstance(node.value, (tuple, list)) and len(node.value) > 0 else None
        tval = node.value[1] if isinstance(node.value, (tuple, list)) and len(node.value) > 1 else None

        if tclass == "NUM":
            if "." in tval:
                node.set_semType("float")
            else:
                node.set_semType("int")
        elif tclass == "MEM" and not children:
            node.set_semType("mem")
        elif tclass == "RES":
            if len(children) == 1 and children[0].get_semType() in ("int", "float", "mem"):
                node.set_semType("res")
            else:
                line_error_log += f"Erro semântico: (NUM/MEM RES) esperado, obtido filhos: {[c.get_semType() for c in children]}"
                error_sint = True
        elif tclass == "MEM":
            if len(children) == 1 and children[0].get_semType() in ("int", "float"):
                node.set_semType("mem")
            else:
                line_error_log += f"Erro semântico: (NUM MEM) esperado, obtido filhos: {[c.get_semType() for c in children]}"
                error_sint = True
        elif tclass == "OP":
            if len(children) == 2:
                left, right = children[0], children[1]
                sems = (left.get_semType(), right.get_semType())
                if sems[0] in ("int", "float", "res", "mem") and sems[1] in ("int", "float", "res", "mem"):
                    if tval == "|":
                        node.set_semType("float")
                    elif tval == "/":
                        node.set_semType("int")
                    elif "mem" in sems or "res" in sems:
                        node.set_semType("float")
                    elif sems[0] == "float" or sems[1] == "float":
                        node.set_semType("float")
                    else:
                        node.set_semType("int")
                else:
                    line_error_log += f"Erro semântico: (int/float/res/mem int/float/res/mem OP) esperado, obtido filhos: {sems}"
                    error_sint = True
            else:
                line_error_log += f"Erro semântico: (int/float/res/mem int/float/res/mem OP) esperado, quantidade de filhos: {len(children)}"
                error_sint = True
        elif tclass == "CMP":
            if len(children) == 2:
                left, right = children[0], children[1]
                sems = (left.get_semType(), right.get_semType())
                if sems[0] in ("int", "float", "res", "mem") and sems[1] in ("int", "float", "res", "mem"):
                    node.set_semType("bool")
                else:
                    line_error_log += f"Erro semântico: (int/float/res/mem int/float/res/mem CMP) esperado, obtido filhos: {sems}"
                    error_sint = True
            else:
                line_error_log += f"Erro semântico: (int/float/res/mem int/float/res/mem CMP) esperado, quantidade de filhos: {len(children)}"
                error_sint = True
        elif tclass == "KW":
            if len(children) == 3:
                cond, v1, v2 = children[2], children[1], children[0]
                if tval == "if":
                    if cond.get_semType() == "bool" and v1.get_semType() in ("int", "float", "mem", "res") and v2.get_semType() in ("int", "float", "mem", "res"):
                        if v1.get_semType() == "float" or v2.get_semType() == "float":
                            node.set_semType("float")
                        else:
                            node.set_semType("int")
                    else:
                        line_error_log += f"Erro semântico: (bool int/float/mem/res int/float/mem/res if) esperado, obtido filhos: {[cond.get_semType(), v1.get_semType(), v2.get_semType()]}"
                        error_sint = True
                elif tval == "for":
                    valid_first = cond.get_semType() == "bool"
                    valid_second = v1.get_semType() in ("int", "res", "mem")
                    valid_third = v2.get_semType() in ("int", "float")
                    if valid_first and valid_second and valid_third:
                        if v2.get_semType() == "float":
                            node.set_semType("float")
                        else:
                            node.set_semType("int")
                    else:
                        line_error_log += f"Erro semântico: (bool int/res/mem int/float for) esperado, obtido filhos: {[cond.get_semType(), v1.get_semType(), v2.get_semType()]}"
                        error_sint = True
                else:
                    line_error_log += f"Erro semântico: KW não reconhecido: {tval}\n"
                    error_sint = True
            else:
                line_error_log += f"Erro semântico: (bool int/float/mem/res int/float/mem/res if) ou (bool int/res/mem int/float for) esperado, quantidade de filhos: {len(children)}"
                error_sint = True
        else:
            node.set_semType(None)

    _sem(node)
    if error_sint:
        return None, line_error_log, True
    return node, line_error_log, False

# ------------------- OTHER CODES--------------------

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

def invert_tree(node):
    if node is None:
        return None

    # Inverte os filhos do nó atual
    inverted_children = [invert_tree(child) for child in reversed(node.get_children())]

    # Cria um novo nó com o valor atual e os filhos invertidos
    new_node = Node(node.get_type(), node.get_value(), inverted_children)
    new_node.set_semType(node.get_semType())

    return new_node

def classfyPrimary(node):
    if node is None:
        return

    children = node.get_children()
    if children:
        # Leftmost child is primary
        children[0].set_primary(True)
        # Rightmost child is secondary
        if len(children) > 1:
            children[1].set_primary(False)
        # Recursively classify children
        for child in children:
            classfyPrimary(child)

def writeASMoutput(body, arquivo_base="base.asm"):
    with open(arquivo_base) as base_file:
        codigo_base = base_file.read()

    codigo_base += body

    with open("assembly_out/saida.asm", "w") as out:
        out.write(codigo_base)

# -------------- ASM GENERATION FUNCTIONS --------------
def extractIntRat(number):
    # Extrai a parte inteira e a parte racional de um float como inteiros
    integer_part = int(float(number))
    fractional_part = abs(float(number) - integer_part)
    # Considera até 4 casas decimais para a parte racional como inteiro
    rational_as_int = int(round(fractional_part * 10000))
    return integer_part, rational_as_int

def loadNumberPrimary(value):
    # Extrai a parte inteira e a parte racional de um float como inteiros
    primaryInt, primaryRat = extractIntRat(value)

    if '-' in value:
        sign = "0b00000001"
    else:
        sign = "0b00000000"

    body = f"""
    ldi r19, high({primaryInt})
    ldi r18, low({primaryInt})
    ldi r17, high({primaryRat})
    ldi r16, low({primaryRat})

    ldi r24, {sign}  ; Carrega o sinal

"""
    return body

def loadNumberSecondary(value):
    # Extrai a parte inteira e a parte racional de um float como inteiros
    secondaryInt, secondaryRat = extractIntRat(value)

    
    if '-' in value:
        sign = "0b00000010"
    else:
        sign = "0b00000000"

    body = f"""
    ldi r23, high({secondaryInt})
    ldi r22, low({secondaryInt})
    ldi r21, high({secondaryRat})
    ldi r20, low({secondaryRat})

    ldi r24, {sign}  ; Carrega o sinal

"""
    return body

def loadOperation(op):
    if op == '+':
        return "\n    call add_int_numbers\n"
    elif op == '-':
        return """
    
    call sign_inverter
    call add_int_numbers

"""
    elif op == '*':
        return "\n    call mul_int_numbers\n"
    elif op == '/':
        return "\n    call div_int_int_numbers\n"
    elif op == '|':
        return "\n    call div_real_int_numbers\n"
    elif op == '%':
        return "\n    call rest_numbers\n"
    elif op == '^':
        return "\n    call power_int_numbers\n"
    else:
        raise ValueError(f"Operação desconhecida: {op}")

def pushPrimaryToStack():
    body = """
    
    push r19  ; Parte inteira alta
    push r18  ; Parte inteira baixa
    push r17  ; Parte racional alta
    push r16  ; Parte racional baixa
    push r24  ; Sinal
    
    """
    return body

def popPrimaryFromStack():
    body = """
    
    pop r25  ; Sinal
    pop r16  ; Parte racional baixa
    pop r17  ; Parte racional alta
    pop r18  ; Parte inteira baixa
    pop r19  ; Parte inteira alta

    or r24, r25  ; Combina os sinais dos dois números

    """
    return body

def pushSecondaryToStack():
    body = """
    
    push r23  ; Parte inteira alta
    push r22  ; Parte inteira baixa
    push r21  ; Parte racional alta
    push r20  ; Parte racional baixa
    push r24  ; Sinal
    
    """
    return body

def popSecondaryFromStack():
    body = """
    
    pop r24  ; Sinal
    pop r20  ; Parte racional baixa
    pop r21  ; Parte racional alta
    pop r22  ; Parte inteira baixa
    pop r23  ; Parte inteira alta
    
    """
    return body


def printResult():
    body = popPrimaryFromStack()
    body += """
    
    call send_sign_primary
    call send_full_byte_decimal_primary
    ldi r30, '|'
    call send_char_call_no_Correction
    clr r24

    ; --------------------------
    """
    return body

def endCode():
    body = """
    ldi r30, 13
    call send_char_call_no_Correction
    call delay
    end_of_code_really:
    rjmp end_of_code_really
    """
    return body
# ------ Solver ------

def solveExpression(node, lineResult):
    # Recursively solve the expression tree bottom-up using value[1] for math
    def solveExpressionRec(node, lineResult):
        global MEM, RES
        if node is None:
            return "newBody", None

        children = node.get_children()
        # Leaf node: NUM or MEM or RES
        if not children:
            tval = node.get_value()[1]
            tsem = node.get_semType()
            if tsem == "int":
                body = ""
                if node.is_primary():
                    body = loadNumberPrimary(tval)
                    body += pushPrimaryToStack()
                else:
                    body = loadNumberSecondary(tval)
                    body += pushSecondaryToStack()
                return body, int(tval)
            elif tsem == "float":
                body = ""
                if node.is_primary():
                    body = loadNumberPrimary(tval)
                    body += pushPrimaryToStack()
                else:
                    body = loadNumberSecondary(tval)
                    body += pushSecondaryToStack()
                return body, float(tval)
            elif tsem == "mem":
                body = ""
                if node.is_primary():
                    body = loadNumberPrimary(str(MEM))
                    body += pushPrimaryToStack()
                else:
                    body = loadNumberSecondary(str(MEM))
                    body += pushSecondaryToStack()
                return body, float(MEM)
            else:
                return "", 0.0

        tval = node.get_value()[1]
        tclass = node.get_value()[0]
        tsem = node.get_semType()

        # Unary MEM/RES
        if tsem == "mem" and len(children) == 1:
            body, val = solveExpressionRec(children[0], lineResult)
            MEM = float(val)
            return body, MEM
        if tsem == "res" and len(children) == 1:
            RES = int(children[0].get_value()[2])-1
            return "newBody", float(lineResult[RES][2])

        # Binary OP/CMP
        if tclass == "OP" and len(children) == 2:
            bodyLeft, left = solveExpressionRec(children[0], lineResult)
            bodyRight, right = solveExpressionRec(children[1], lineResult)
            op = tval

            body =  bodyLeft + bodyRight
            
            body += popSecondaryFromStack()
            body += popPrimaryFromStack()
            body += loadOperation(op)
            body += pushPrimaryToStack()

            if op == '+':
                return body, left + right
            elif op == '-':
                return body, left - right
            elif op == '*':
                return body, left * right
            elif op == '/':
                return body, left / right if right != 0 else 0
            elif op == '|':
                return body, left / right if right != 0 else 0
            elif op == '%':
                return body, left % right if right != 0 else 0
            elif op == '^':
                return body, left ** right
            else:
                return body, 0
            
        if tclass == "CMP" and len(children) == 2:
            bodyLeft, left = solveExpressionRec(children[0], lineResult)
            bodyRight, right = solveExpressionRec(children[1], lineResult)
            op = tval

            if op == "==":
                return "", (left == right)
            elif op == "!=":
                return "", (left != right)
            elif op == "<":
                return "", (left < right)
            elif op == "<=":
                return "", (left <= right)
            elif op == ">":
                return "", (left > right)
            elif op == ">=":
                return "", (left >= right)
            else:
                return "", False
        
        # KW (if, for)
        if tclass == "KW" and len(children) == 3:
            _, cond = solveExpressionRec(children[0], lineResult)
            body01, v1 = solveExpressionRec(children[1], lineResult)
            body02, v2 = solveExpressionRec(children[2], lineResult)
            if tval == "if":
                return (body01, v1) if cond else (body02, v2)

            elif tval == "for":
                
                return "newBody", 0
            else:
                return "newBody", 0

        # Fallback
        return "newBody", 0

    newBody, result = solveExpressionRec(node, lineResult)
    newBody += printResult()  # Adiciona a impressão do resultado
    return newBody, result

# processa o arquivo txt
def processar_arquivo(nome_arquivo):
    global RES
    lineResult = []
    full_log = ""
    error_lex_log = ""
    error_sint_log = ""
    error_sem_log = ""
    codASM = ""

    with open(nome_arquivo) as f:
        linhas = f.readlines()

    for idx, linha in enumerate(linhas):
        # print(f"Processando linha {idx+1}: {linha}")
        error_lex = False
        error_sint = False
        error_sem = False

        if linha[-1] == '\n':
            linha = linha[:-1]

        # Análise Léxica
        tokens, line_error_log = lexAnalysis(linha,idx+1)
        # if idx+1 == 1:
        #     print(f"Linha {idx+1}: {linha}")
        #     for token in tokens:
        #         print(f"Linha {idx+1}, Coluna {token[2]}: Token '{token[1]}'; Classe '{token[0]}'")
        #     print(f"Erro Léxico: {line_error_log}")

        if tokens == []:
            error_lex = True
            error_lex_log += line_error_log
        else:
            # FULL LOG DE ANALISE LEXICA
            full_log += f"\n\nLinha {idx+1}: {linha}"
            for token in tokens:
                full_log += f"\nLinha {idx+1}, Coluna {token[2]}: Token '{token[1]}'; Classe '{token[0]}'"

        # Análise Sintática
        if not error_lex:
            node, line_error_log = sintaxAnalysis(tokens, idx+1)
            if node == []:
                error_sint = True
                error_sint_log += line_error_log
            else:
                # FULL LOG DE ANALISE SINTATICA
                full_log += f"\n\nAnálise Sintática:"
                full_log += f"\n{node}"
                # ARVORE SINTATICA
                # simplerNode = simplify_node(node)
                # full_log += f"\n{simplerNode}"
                # graph = draw_tree(simplerNode)
                # graph.render(f"tree_output/line{idx+1}", format="png", cleanup=True)
                
        # Análise Semântica
        if not error_sint and not error_lex:
            node, line_error_log, error_sem = semanticAnalysis(node,error_sem)
            if node == None:
                error_sem_log += line_error_log + " na linha " + str(idx+1) + ".\n"
            else:
                node = invert_tree(node)
                classfyPrimary(node)  # Classifica os nós primários e secundários
                # FULL LOG DE ANALISE SEMANTICA
                full_log += f"\n\nAnálise Semântica:"
                full_log += f"\n{node}"
    
        # Resolução da expressão
        if not error_lex and not error_sint and not error_sem:
            
            body, result = solveExpression(node, lineResult)

            codASM += f"{body}\n\n"
            # Armazena o resultado
            lineResult.append((idx+1, linha, result))
        RES += 1

    codASM += endCode()  # Adiciona o código de finalização
    writeASMoutput(codASM)
    return lineResult, full_log, error_lex_log, error_sint_log, error_sem_log

# main executa usando sys.argv ao inves de input
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python programa.py arquivo.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    result, full_log, error_lex_log, error_sint_log, error_sem_log = processar_arquivo(nome_arquivo)

    print("Resultados do processamento:")
    print(full_log)
    print("Erros Léxico:")
    print(error_lex_log)
    print("Erros Sintático:")
    print(error_sint_log)
    print("Erros Semântico:")
    print(error_sem_log)
    print("Resultados:")
    for x in result:
        print(f"\nLinha:{x[0]}\nExpr: {x[1]}\nResult:{x[2]}\n")

