import argparse, subprocess

import parser, transpiler

LIBFILES = ["clibraries/core.c",]

arg_parser = argparse.ArgumentParser(description="Transpiles XXX code into C code.")
arg_parser.add_argument("input", help = "Path of the code file to read")
arg_parser.add_argument("-o", "--output", help = "Name of output file. Defaults to name of input file with extension switched")
arg_parser.add_argument("-d", "--debug", action = "store_true", help = "Run with debug prints. Also runs GCC with debug flag if relevant")
arg_parser.add_argument("-c", "--compile", action = "store_true", help = "Automatically compile C code (uses GCC)")

args = arg_parser.parse_args()
INPUT_PATH = args.input
if args.output:
    OUTPUT_PATH = args.output
else:
    OUTPUT_PATH = INPUT_PATH[:INPUT_PATH.find(".")]
if args.debug:
    DEBUG = True
else:
    DEBUG = False

p = parser.Parser(debug = DEBUG)
trees = p.parse_file(INPUT_PATH)
t = transpiler.Transpiler(debug = DEBUG)
t.transpile(trees, OUTPUT_PATH+".c")
if args.compile:
    GCCFLAGS = ["gcc", "-std=c11",]
    if DEBUG:
        GCCFLAGS.append("-g")
    subprocess.call(GCCFLAGS + ["-c", OUTPUT_PATH + ".c",])
    for lib in LIBFILES:
        subprocess.call(GCCFLAGS + ["-c", lib,])
    subprocess.call(GCCFLAGS + ["-o", OUTPUT_PATH, OUTPUT_PATH+".o"] + [lib[lib.rfind("/")+1:lib.rfind(".")] + ".o" for lib in LIBFILES])
