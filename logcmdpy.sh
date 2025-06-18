#!/bin/bash
# Uso: ./logcmd.sh comando [argumentos]

("$@" 2>&1; echo -e "\n---\n") | tee -a logs/consola_terminal_python.log
