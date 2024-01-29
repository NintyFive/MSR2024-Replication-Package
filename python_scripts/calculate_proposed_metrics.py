#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import os
from antlr4 import *
from antlr4.InputStream import InputStream
import sys
sys.path.append('./parsers')

from multiprocessing import Process, Manager
from Java8Lexer import Java8Lexer
from Java8Parser import Java8Parser
from Java8Listener import Java8Listener
import understand
import time
import re
import csv
import math


type_strings = """
file write reader
"""
io_type_list = type_strings.split(' ')
io_type_list = [x.strip() for x in io_type_list if len(x) > 1]

type_strings = """Database Connection Statement"""
database_type_list = type_strings.split(' ')
database_type_list = [x.strip() for x in database_type_list]

type_strings = """collection iterator set list queue dequeue map hash array vector"""
collection_type_list = type_strings.split(' ')
collection_type_list = [x.strip() for x in collection_type_list if len(x) > 1]

type_strings = """semaphore lock"""
synchronization_type_list = type_strings.split(' ')
synchronization_type_list = [x.strip() for x in synchronization_type_list if len(x) > 1]

type_strings = """thread"""
thread_type_list = type_strings.split(' ')
thread_type_list = [x.strip() for x in thread_type_list if len(x) > 1]


# In[3]:


def check_identifier(ent, metrics, loop=0):
    for type_str in io_type_list:
        if type_str.lower() in ent.lower():
            metrics['io'] += 1
            if loop > 0:
                metrics['io_in_loop'] += 1
            break
    for type_str in database_type_list:
        if type_str.lower() in ent.lower():# the type contains database or db
        #if type_str.lower() in type_splits:
            metrics['database'] += 1
            if loop > 0:
                metrics['database_in_loop'] += 1
            break
        elif type_str.lower() in ent.lower():# the variable name contains database or db
            metrics['database'] += 1
            if loop > 0:
                metrics['database_in_loop'] += 1
            break
    for type_str in collection_type_list:
        if type_str.lower() in ent.lower():
            metrics['collection'] += 1
            if loop > 0:
                metrics['collection_in_loop'] += 1
            break
    for type_str in synchronization_type_list:
        if type_str.lower() in ent.lower():
            metrics['synchronization'] += 1
            break
    for type_str in thread_type_list:
        if type_str.lower() in ent.lower():
            metrics['thread'] += 1
            break
        
    return metrics


# In[4]:


# This defines a complete listener for a parse tree produced by CPP14Parser.
class Calculator(Java8Listener):
    def __init__(self, function_name):
        
        self.function_name = function_name
        
        self.metrics = dict()
        self.metrics['io'] = 0
        self.metrics['database'] = 0
        self.metrics['collection'] = 0
        
        self.metrics['io_in_loop'] = 0
        self.metrics['database_in_loop'] = 0
        self.metrics['collection_in_loop'] = 0
        
        self.metrics['synchronization'] = 0
        self.metrics['thread'] = 0
        
        self.metrics['num_if_inloop'] = 0
        self.metrics['num_loop_inif'] = 0
        self.metrics['num_nested_loop'] = 0
        self.metrics['num_nested_loop_incrit'] = 0
        self.metrics['recursive'] = 0
        
        
        self.enterfunction = 0
        self.sif = 0
        self.loop = 0
        self.metrics = check_identifier(function_name, self.metrics, self.loop)
        
    # catch class type, e.g., list, map in statement List<Map<String, Integer>> s;
    # Enter a parse tree produced by Java8Parser#classType_lfno_classOrInterfaceType.
    def enterClassType_lfno_classOrInterfaceType(self, ctx:Java8Parser.ClassType_lfno_classOrInterfaceTypeContext):
        type_name = str(ctx.Identifier())
        #print('enter class1', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)
        
    # Enter a parse tree produced by Java8Parser#classType_lf_classOrInterfaceType.
    def enterClassType_lf_classOrInterfaceType(self, ctx:Java8Parser.ClassType_lf_classOrInterfaceTypeContext):
        type_name = str(ctx.Identifier())
        #print('enter class2', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)

    # Enter a parse tree produced by Java8Parser#typeVariable.
    def enterTypeVariable(self, ctx:Java8Parser.TypeVariableContext):
        type_name = str(ctx.Identifier())
        #print('enter class3', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)

    # extract the type of a varibale declaration, e.g., Connection from Connection conn = ...;
    # Enter a parse tree produced by Java8Parser#unannClassType_lfno_unannClassOrInterfaceType.
    def enterUnannClassType_lfno_unannClassOrInterfaceType(self, ctx:Java8Parser.UnannClassType_lfno_unannClassOrInterfaceTypeContext):
        type_name = str(ctx.Identifier())
        #print('enter unann', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)

    def enterUnannClassType_lf_classOrInterfaceType(self, ctx:Java8Parser.ClassType_lf_classOrInterfaceTypeContext):
        type_name = str(ctx.Identifier())
        #print('enter unann', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)

    def enterUnannTypeVariable(self, ctx:Java8Parser.TypeVariableContext):
        type_name = str(ctx.Identifier())
        #print('enter unann', type_name)
        self.metrics = check_identifier(type_name, self.metrics, self.loop)

    # extract the varibale in its declaration, e.g., conn from Connection conn = ...;
    # Enter a parse tree produced by Java8Parser#variableDeclaratorId.
    def enterVariableDeclaratorId(self, ctx:Java8Parser.VariableDeclaratorIdContext):
        identifier = str(ctx.Identifier())
        #print('variable declare', identifier)
        self.metrics = check_identifier(identifier, self.metrics, self.loop)

    # Enter a parse tree produced by Java8Parser#forStatementNoShortIf.
    def enterForStatementNoShortIf(self, ctx:Java8Parser.ForStatementNoShortIfContext):
        self.enterIterationstatement()

    # Exit a parse tree produced by Java8Parser#forStatementNoShortIf.
    def exitForStatementNoShortIf(self, ctx:Java8Parser.ForStatementNoShortIfContext):
        self.exitIterationstatement()

    # Enter a parse tree produced by Java8Parser#forStatement.
    def enterForStatement(self, ctx:Java8Parser.ForStatementContext):
        self.enterIterationstatement()

    # Exit a parse tree produced by Java8Parser#forStatement.
    def exitForStatement(self, ctx:Java8Parser.ForStatementContext):
        self.exitIterationstatement()

    # Enter a parse tree produced by Java8Parser#whileStatement.
    def enterWhileStatement(self, ctx:Java8Parser.WhileStatementContext):
        self.enterIterationstatement()

    # Exit a parse tree produced by Java8Parser#whileStatement.
    def exitWhileStatement(self, ctx:Java8Parser.WhileStatementContext):
        self.exitIterationstatement()

    # Enter a parse tree produced by Java8Parser#whileStatementNoShortIf.
    def enterWhileStatementNoShortIf(self, ctx:Java8Parser.WhileStatementNoShortIfContext):
        self.enterIterationstatement()

    # Exit a parse tree produced by Java8Parser#whileStatementNoShortIf.
    def exitWhileStatementNoShortIf(self, ctx:Java8Parser.WhileStatementNoShortIfContext):
        self.exitIterationstatement()

    # Enter a parse tree produced by Java8Parser#doStatement.
    def enterDoStatement(self, ctx:Java8Parser.DoStatementContext):
        self.enterIterationstatement()

    # Exit a parse tree produced by Java8Parser#doStatement.
    def exitDoStatement(self, ctx:Java8Parser.DoStatementContext):
        self.exitIterationstatement()

    def enterIterationstatement(self):
        #print('enter iteration')
        self.loop += 1
        if self.sif > 0:
            self.metrics['num_loop_inif'] += 1
        if self.loop > 1:
            self.metrics['num_nested_loop'] += 1
            if self.metrics['synchronization']> 0:
                self.metrics['num_nested_loop_incrit'] += 1

    def exitIterationstatement(self):
        #print('exit iteration')
        self.loop -= 1

    # Enter a parse tree produced by Java8Parser#synchronizedStatement.
    def enterSynchronizedStatement(self, ctx:Java8Parser.SynchronizedStatementContext):
        self.metrics['synchronization'] += 1

    # Enter a parse tree produced by Java8Parser#ifThenElseStatementNoShortIf.
    def enterIfThenElseStatementNoShortIf(self, ctx:Java8Parser.IfThenElseStatementNoShortIfContext):
        self.enterSelectionstatement()

    # Exit a parse tree produced by Java8Parser#ifThenElseStatementNoShortIf.
    def exitIfThenElseStatementNoShortIf(self, ctx:Java8Parser.IfThenElseStatementNoShortIfContext):
        self.exitSelectionstatement()


    # Enter a parse tree produced by Java8Parser#ifThenElseStatement.
    def enterIfThenElseStatement(self, ctx:Java8Parser.IfThenElseStatementContext):
        self.enterSelectionstatement()
        

    # Exit a parse tree produced by Java8Parser#ifThenElseStatement.
    def exitIfThenElseStatement(self, ctx:Java8Parser.IfThenElseStatementContext):
        self.exitSelectionstatement()
        
    # Enter a parse tree produced by Java8Parser#ifThenStatement.
    def enterIfThenStatement(self, ctx:Java8Parser.IfThenStatementContext):
        self.enterSelectionstatement()
        

    # Exit a parse tree produced by Java8Parser#ifThenStatement.
    def exitIfThenStatement(self, ctx:Java8Parser.IfThenStatementContext):
        self.exitSelectionstatement()
        

    def enterSelectionstatement(self):
        #print('enter selection')
        self.sif += 1
        if self.loop > 0:
            self.metrics['num_if_inloop'] += 1
    
    def exitSelectionstatement(self):
        #print('exit selection')
        self.sif -= 1

    # parse read() from reader.read()
    # Enter a parse tree produced by Java8Parser#methodInvocation.
    def enterMethodInvocation(self, ctx:Java8Parser.MethodInvocationContext):
        self.methodInvocation(ctx)

    # Enter a parse tree produced by Java8Parser#methodInvocation_lf_primary.
    def enterMethodInvocation_lf_primary(self, ctx:Java8Parser.MethodInvocation_lf_primaryContext):
        self.methodInvocation(ctx,1)

    # Enter a parse tree produced by Java8Parser#methodInvocation_lfno_primary.
    def enterMethodInvocation_lfno_primary(self, ctx:Java8Parser.MethodInvocation_lfno_primaryContext):
        self.methodInvocation(ctx)

    def methodInvocation(self, ctx, ctx_type=0):
        #Reading the java8.j4 file, find out that the methodInvocation grammer having either methodName or Identifier
        if ctx_type==0 and ctx.methodName() is not None:
            identifier = str(ctx.methodName().Identifier())
            #print('methodName', identifier)
        else:
            identifier = str(ctx.Identifier())
            #print('methodName', identifier)
        self.metrics = check_identifier(identifier, self.metrics, self.loop)
        if self.enterfunction == 1:
            if identifier.strip() == (self.function_name).strip():
                self.metrics['recursive_function'] = 1

    # parse reader from reader.read()
    # Enter a parse tree produced by Java8Parser#typeName.
    def enterTypeName(self, ctx:Java8Parser.TypeNameContext):
        identifier = str(ctx.Identifier())
        #print('type name', identifier)
        self.metrics = check_identifier(identifier, self.metrics, self.loop)

    # extract the class in class instance creation, e.g., Thread in Thread t1 = new ...;
    # Enter a parse tree produced by Java8Parser#classInstanceCreationExpression.
    def enterClassInstanceCreationExpression(self, ctx:Java8Parser.ClassInstanceCreationExpressionContext):
        identifier = str(ctx.Identifier(0))
        #print('class instance', identifier)
        self.metrics = check_identifier(identifier, self.metrics, self.loop)

    # Enter a parse tree produced by Java8Parser#classInstanceCreationExpression_lf_primary.
    def enterClassInstanceCreationExpression_lf_primary(self, ctx:Java8Parser.ClassInstanceCreationExpression_lf_primaryContext):
        identifier = str(ctx.Identifier(0))
        #print('class instance', identifier)
        self.metrics = check_identifier(identifier, self.metrics, self.loop)

    # Enter a parse tree produced by Java8Parser#classInstanceCreationExpression_lfno_primary.
    def enterClassInstanceCreationExpression_lfno_primary(self, ctx:Java8Parser.ClassInstanceCreationExpression_lfno_primaryContext):
        identifier = str(ctx.Identifier(0))
        #print('class instance', identifier)

                
    # Enter a parse tree produced by Java8Parser#methodBody.
    def enterMethodBody(self, ctx:Java8Parser.MethodBodyContext):
        #print('enter function')
        self.enterfunction = 1


def calculate_metrics(ent):
    #with open('test.java') as reader:
    #    content = reader.read()
    metrics = dict()
    content = ent.contents()
    loc_function = len(content.split('\n'))
    print('function loc:', loc_function)
    #print('function content', content)
    function_name = ent.longname()
    #function_name = 'h'
    
    #build the parse tree of the function
    start_time = time.time()
    input_stream = InputStream(content)
    print("---inputstream %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    lexer = Java8Lexer(input_stream)
    print("---lexer %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    token_stream = CommonTokenStream(lexer)
    print("---token stream %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    parser = Java8Parser(token_stream)
    print("---parse stream %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    tree = parser.methodDeclaration()
    #tree = parser.translationunit()
    print("---build ast tree %s seconds ---" % (time.time() - start_time))
    
    #walk through the parse tree using the Calculator listener
    start_time = time.time()
    listener = Calculator(function_name)
    walker = ParseTreeWalker()
    walker.walk(listener, tree)
    metrics['num_if_inloop'] = listener.metrics['num_if_inloop']
    metrics['num_loop_inif'] = listener.metrics['num_loop_inif']
    metrics['num_nested_loop'] = listener.metrics['num_nested_loop']
    metrics['num_nested_loop_incrit'] = listener.metrics['num_nested_loop_incrit']
    metrics['synchronization'] = listener.metrics['synchronization']
    metrics['thread'] = listener.metrics['thread']
    metrics['io_in_loop'] = listener.metrics['io_in_loop']
    metrics['database_in_loop'] = listener.metrics['database_in_loop']
    metrics['collection_in_loop'] = listener.metrics['collection_in_loop']
    metrics['io'] = listener.metrics['io']
    metrics['database'] = listener.metrics['database']
    metrics['collection'] = listener.metrics['collection']
    metrics['recursive'] = listener.metrics['recursive']
    print("---traverse ast tree %s seconds ---" % (time.time() - start_time))
    return metrics



def calculate(subset_ents):
    for ent in subset_ents:
        try:
            function_name = ent.longname() + "("
            first = True
            for param in ent.ents("Define","Parameter"):
                if not first:
                    function_name += ","
                function_name += param.type()
                first = False
            function_name += ")"

            output = os.path.join(data_dir, project, 'metrics', '%s.csv' % (function_name))
                                
            if os.path.exists(output):
                print('already calculated')
                continue
            shape = methods[(methods.Name==function_name)].shape[0]
            if shape == 1:
                metrics = calculate_metrics(ent)
                methodscsv = open(output, 'w', newline='')
                writer = csv.DictWriter(methodscsv, fieldnames=field_names)
                writer.writeheader()
                writer.writerow(metrics)
                methodscsv.close()
                if sum(metrics.values()) > 0:
                    print(metrics)
            else:
                print('shape', shape)
                print('function name', function_name)
        except Exception as e:
            print('Exception', str(e))


if __name__=='__main__':
    data_dir = sys.argv[1]
    project = sys.argv[2]
    # make dir for the metrics
    if not os.path.exists(os.path.join(data_dir, project, 'metrics')):
        os.mkdir(os.path.join(data_dir, project, 'metrics'))
    db = understand.open(os.path.join(data_dir, project, 'myDb.udb'))
    
    
    # In[8]:
    
    
    func_ents = db.ents("function,method,procedure") 
    
    
    # In[9]:
    
    
    methods = pd.read_csv(os.path.join(data_dir, project, 'methods.csv'))
    
    
    # In[10]:
    
    
    field_names = ['num_if_inloop', 'num_loop_inif', 'num_loop_inif', 'num_nested_loop', 'num_nested_loop_incrit',
                  'synchronization', 'thread', 'io_in_loop', 'database_in_loop', 'collection_in_loop',
                  'io', 'database', 'collection', 'recursive', 'num_side_effect', 'num_side_effect_inif',
                  'num_no_side_effect']
    
    chunk = 1000
    num_threads = 15
    start = 0
    for start in range(0, len(func_ents), chunk*num_threads):
        process = []
        for index in range(start, start+chunk*num_threads, chunk):
            p = Process(target=calculate, args=(func_ents[index: index+chunk],))
            process.append(p)
            p.start()
        for p in process:
            print(p)
            p.join(chunk*30)

