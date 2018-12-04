# -*- coding: utf-8 -*-


import io
import re


# Regexes used for parsing
r_empty = re.compile(r'^ *(?:#.*)?(?:\r?\n)?$', re.UNICODE)
r_left = re.compile(r'^(\w+)(?: +(\w+)(?: +(?:"((?:""|[^"])*?)"|([^#"]*?)))?)? *(?:#.*)?(?:\r?\n)?$', re.UNICODE)
r_relationship = re.compile(r'^  (\w+)(?: +(?:"((?:""|[^"])*?)"|([^#"]*?)))? *(?:#.*)?(?:\r?\n)?$', re.UNICODE)
r_right = re.compile(r'^    (?:"((?:""|[^"])*?)"|([^#"]*?)) *(?:#.*)?(?:\r?\n)?$', re.UNICODE)


# Extract triplets from specified file
def iterate(file):
    left = None
    relationship = None
    for line, content in enumerate(file):
        right_quote = None
        right_plain = None
        
        # Try to parse empty line
        match = r_empty.match(content)
        if not match:

            # Try to parse full line
            match = r_left.match(content)
            if match:
                left = match.group(1)
                relationship = match.group(2)
                right_quote = match.group(3)
                right_plain = match.group(4)
            
            # Try to parse headless line
            else:
                match = r_relationship.match(content)
                if match:
                    relationship = match.group(1)
                    right_quote = match.group(2)
                    right_plain = match.group(3)
                
                # Try to parse tail line
                else:
                    match = r_right.match(content)
                    if match:
                        right_quote = match.group(1)
                        right_plain = match.group(2)
        
        # Check for error
        if not match:
            raise IOError('Invalid content at line %d' % line)
        
        # Yield triplet
        if right_quote or right_plain:
            if not left or not relationship:
                raise IOError('Orphan node at line %d' % line)
            right = right_plain or right_quote.replace('""', '"')
            yield left, relationship, right
