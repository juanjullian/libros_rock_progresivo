#!/bin/bash


# Parte 1
jq 'to_entries | .[0:(length / 3 | floor)] | from_entries' progarchives_albums_full_actualizado.json > parte1.json

# Parte 2
jq 'to_entries | .[(length / 3 | floor):(2 * (length / 3 | floor))] | from_entries' progarchives_albums_full_actualizado.json > parte2.json

# Parte 3
jq 'to_entries | .[(2 * (length / 3 | floor)):] | from_entries' progarchives_albums_full_actualizado.json > parte3.json
