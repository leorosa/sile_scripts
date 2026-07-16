#! /usr/bin/python3

# formatting marks, e.g. "*":
#       *enclosed text*
#       ^** formatted line
#       ^*** begin/end formatted block of lines
#  ^####        = section (up to 4 levels)
#                 if there isn't a title in the document, '# ' will assume that it is a title, formatted in a new line
#                 if header has a counter format, then '# ' will be a numbered title
#  ^#:          = force section number
#  ^#-          = ommit section number
#  ^\t          = indent
#  ^%           = comment (ignore)
#  %%%          = begin/end comments (i.e., ignore lines)
#   *text*      = bold
#   _text_      = italic
#   +text+      = underline
#   -text-      = strikeout
#   =text=      = highlight
#   ^sup^       = superscript
#   ~sub~       = subscript
#   `code`      = code
#   #cat:it     = increment a counter in a 'cat' category
#   @cat:it     = print a counter, creating it if needed
#   @cite       = citation
#   [@cite @cite] = grouped citations
#   @meta       = print config
#  ^␣*20        = center line
#  ^>␣          = quote; '>' must be followed by a space (using NBSP will produce a list)
#  ^<␣          = left quote
#  ^|␣          = quote preserving lines
#  ^|...|$      = table
#  ^<<          = include file (text or image)
#  ^<<[opt]     = include file with options: [code] or [quote] to format the text content, or [options] to pass to a figure
#  ^[-+*>§_]␣   = list, with different symbols ('_' for no bullets)
#  ^ *[0-9].    = numbered list
#  ^ *[<[(][0-9][)]>]. = delimited numbered list
#   $...$       = math
#   $$...$$     = displaymath
#   $$:lab...$$ = displaymath, numbered=true, record number to eq:lab
#  ^:key caption = caption, with an optional key for cross-referencing
#             = \vfill ( ia the 'vertical tab' character)
#             = new page ( is the 'form feed' character)
#   ^[note]     = note (footnote or endnote)
#   --          = en-dash, –
#   ---         = em-dash, —
#   ...         = elipsis, …
#   @app:lab    = used to appendix, Alpha number, will print references before if any
# proposed:
#   ^>>>        = raggedleft/flushright
#   ^<<<        = raggedright/flushleft
#   ^<>         = center
#   ^\          = preserve lines
#   \$          = line break


import os, sys, re #, random

config    = {}
counters  = {}
notes     = [''] # dummy text, so the next ones will start from idx=1
unotes    = [''] # for pdf links
references= []
bibrefs   = {}

hasheader = False
curtitle  = 0
numtitle  = 0
toggletitnum = False
inblock   = False   # valid values are: quote, center, math, header, comment
inlist    = []
inenum    = []
initem    = False
intable   = []
innote    = False
infloat   = False   # or use a counter, default to 0?
inslide   = False
label     = ''
lastobj   = ''
seccount  = [0, 0, 0, 0]   # FIXME? the number of header levels is fixed, =4
enditems  = {}
NBSP      = ' '
curcwd    = ''

markers = {}    # when changing marks, see also 'if intable' in l:284
markers['`']   = 'font[monofont]' #autodoc:codeblock' #'raw' #'code'
markers['_']   = 'em'
markers['\\*'] = 'strong'
markers['\\+'] = 'underline'
markers['-']   = 'strikethrough'
markers['=']   = 'highlight' #'color[color=red]' #highlight'
markers['\\^'] = 'superscript'
markers['~']   = 'subscript'
markers['\\$'] = 'math'

inmark = {}
for mark in markers: inmark[mark] = False

languages           = [ 'en'        , 'pt'         , 'es'         , 'de'      , 'fr'            , 'ru']
trans = {}
trans['Appendix']   = [ 'Appendix'  , 'Apêndice'   , 'Apéndice'   , 'Anhang'  , 'Annexe'        , 'Приложение' ]
trans['Figure']     = [ 'Figure'    , 'Figura'     , 'Cifra'      , 'Figur'   , 'Chiffre'       , 'Фигура' ]
trans['Table']      = [ 'Table'     , 'Tabela'     , 'Tabla'      , 'Tabelle' , 'Tableau'       , 'Стол' ]
trans['Figures']    = [ 'Figures'   , 'Figuras'    , 'Cifras'     , 'Figuren' , 'Chiffres'      , 'Фигура' ]
trans['Tables']     = [ 'Tables'    , 'Tabelas'    , 'Tablas'     , 'Tabelles', 'Tableaus'      , 'Стол' ]
trans['Notes']      = [ 'Notes'     , 'Notas'      , 'Notas'      , 'Notizen' , 'Remarques'     , 'Примечания' ]
trans['References'] = [ 'References', 'Referências', 'Referencias', 'Verweise', 'Les Références', 'Рекомендации' ]
trans["'"]          = [ '‘’'        , '‘’'         , '‘’'         , '‚‘'      , '‹›'            , '„“' ]
trans['"']          = [ '“”'        , '“”'         , '“”'         , '„“'      , ['«'+NBSP,NBSP+'»']     , '«»' ]
langidx = 0
squot="''"
dquot='""'

has_bibcite = False
def is_exe(fpath):  # https://stackoverflow.com/posts/377028/
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
for path in os.environ.get("PATH", "").split(os.pathsep):
    exe_file = os.path.join(path, 'bibcite')
    if is_exe(exe_file):
        has_bibcite = True
        break

def escape_chars(line):
    return line.replace('{','\\{').replace('}','\\}').replace(' ',NBSP)

ucounter = 0
def uniqid():
    global ucounter
    ucounter += 1
    return 'unnamed'+str(ucounter)
#   return str(int(1e6*random.random()))

def do_caption():
    global label, lastobj
    key = trans[lastobj][langidx]
    cat = lastobj.lower()[:3]
    line = '\\noindent\\center{\\font[size=0.95em]{\\em '+key+' @'+cat+label+'}}'
    if lastobj.lower()+'s' in enditems:
        enditems[lastobj.lower()+'s'].append(line)
        parse_line(' '*20+'['+lastobj+' @'+cat+':'+label.split(':')[1]+' here]')
    else:
        parse_line(line)
    label = ''
    lastobj = ''

def findid(arg):
    for n in '0123456789IiXxAa*':
        if n in arg: return n
    else: return ''

def id2fmt(arg):
    if   findid(arg)=='0':    return 'bin'
    elif findid(arg).isdigit(): return 'arabic' #arg.isdigit(): return 'arabic'
    elif findid(arg)=='I':    return 'Roman'
    elif findid(arg)=='i':    return 'roman'
    elif findid(arg)=='X':    return 'Hex'
    elif findid(arg)=='x':    return 'hex'
    elif findid(arg)=='A':    return 'Alpha'
    elif findid(arg)=='a':    return 'alpha'
    elif findid(arg)=='*':    return 'symbol'
    else:                     return ''

def alphaid(v, str):
    v -= 1  # index start with 0
    if v<0: return ''
    ret = ''
    while v>=len(str):
        ret += str[int(v/len(str))-1]
        v = v % len(str)
    return ret + str[v]

def alphaval(id, str):  # FIXME: consider id larger than len(str), e.g. 'AA'
    val = 0
    while len(id):
        val *= len(str)-1
        val += str.index(id)
        id = id[1:]
    return val

def id2val(id, fmt):
    if   fmt=='symbol': return alphaval(id, '*†‡§∥¶')
    elif fmt.lower()=='alpha': return alphaval(id.lower(), 'abcdefghijklmnopqrstuvwxyz')
    elif fmt.lower()=='roman':
        d = {'m':1000, 'd':500, 'c':100, 'l':50, 'x':10, 'v':5, 'i':1}
        n = [d[i] for i in id.lower() if i in d]
        return sum([i if i>=n[min(j+1, len(n)-1)] else -i for j,i in enumerate(n)])
    elif fmt: return int(id)
    elif fmt=='bin': return int(id,2)
    elif fmt.lower()=='hex': return int(id,16)
    else: return ''

def val2id(v, arg):
    fmt = id2fmt(arg)
    d = {'m':1000, 'd':500, 'c':100, 'l':50, 'x':10, 'v':5, 'i':1}
    n = []
    if   fmt=='Alpha': return alphaid(v,'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    elif fmt=='alpha': return alphaid(v,'abcdefghijklmnopqrstuvwxyz')
    elif fmt=='symbol': return alphaid(v,'*†‡§∥¶')
    elif fmt.lower()=='roman':
        for i in d: n.append(v-sum(n)-(v-sum(n))%d[i])
        id = ''.join([list(d)[j]*int(i/d[list(d)[j]]) for j,i in enumerate(n)])
        for k in list(d):
            if k not in ['d','l','v']:
                if k!='m':
                    id = id.replace(ok+k+k+k+k,k+ook).replace(k+k+k+k,k+ok)
                ook = k
            else: ok = k
        if fmt=='roman': return id
        else: return id.upper()

    elif fmt=='bin': return bin(v)[2:]
    elif fmt=='Hex': return hex(v)[2:].upper()
    elif fmt=='hex': return hex(v)[2:]
    elif fmt: return str(v)
    else: return ''

def idsec(n):
    if len(config['nsections'])>n:
        return val2id(seccount[n],config['nsections'][n])
    else:
        return val2id(seccount[n], '1')  # for when a number is forced in a section

def fmtid(arg, val):
    return arg.replace(findid(arg), str(val))

def parse_header(line):
    global inblock#, hastitle
    if line=='---':
        if not inblock:
            inblock = 'header'
        else:
            inblock = False
    elif ':' in line:
        key = line.split(':')[0].strip()
        arg = ':'.join(line.split(':')[1:]).strip()
        if key[:2]=='no' and key[2:] in config:
            del config[key[2:]]
        else:
            if 'font' in key: arg = parse_font(arg)
            if arg=='[]':
                config[key] = []    # clear a list
            elif key in config and isinstance(config[key], list):
                config[key].append(arg)
            else:
                config[key] = arg
            if key=='title' and 'sectitle' in config: del config['sectitle']
            if key=='cover' and not os.path.exists(config['cover']):
                config['cover'] = dirname+'/'+config['cover']
            if key=='ornament' and not os.path.exists(config['ornament']):
                config['ornament'] = dirname+'/'+config['ornament']

def parse_list(line):
    global inlist, inenum, initem
    n=0
    pre=''
    if line and len(inlist+inenum):
        n = max(inlist+inenum)
    marks = ''
    if line.strip() and (not inblock or inlist+inenum):
        pre = line.strip().split()[0]
        if pre in ['-','+','*','_'] or (len(pre)>1 and pre[-1] in ['.',')',']','>'] and (pre.strip('<[()]>.').isdigit() or pre.strip('<[()]>.') in 'AaIi')):
            n = len(line) - len(line.lstrip()) + 1
            if '(' in pre: marks += ',before="("'
            if ')' in pre: marks += ',after=")"'
            if '[' in pre: marks += ',before="["'
            if ']' in pre: marks += ',after="]"'
            if '<' in pre: marks += ',before="<"'
            if '>' in pre: marks += ',after=">"'
            line = ' '.join(line.strip().split()[1:])
        elif len(line.strip())>1 and line.strip()[1]==NBSP:
            pre = line.strip()[0]
            n = len(pre)+len(line)-len(line.lstrip())
            line = line.strip()[2:]
        else: pre=''
    for nl in sorted(inlist+inenum,reverse=True):
        if n < nl:
            if initem: print(' '*nl+'\\end{item}')
            initem = False
            if nl in inlist:
                print(' '*(nl-1)+'\\end{itemize}')
                inlist.remove(nl)
            elif nl in inenum:
                print(' '*(nl-1)+'\\end{enumerate}')
                inenum.remove(nl)
    if n:
        if len(pre)>1 and pre[-1] in ['.',')',']','>'] and (pre.strip('<[()]>.').isdigit() or pre.strip('<[()]>.') in 'AaIi'):
            if initem: print(' '*max(inlist+inenum)+'\\end{item}')
            mode = id2fmt(pre.strip('<[()]>.'))
            if mode:
                if n not in inenum:
                    inenum.append(n)
                    lindex = id2val(pre.strip('<[()]>.'), mode)
                    print(' '*(n-1)+'\\begin[display='+mode+marks+',start='+str(lindex)+']{enumerate}')
                print(' '*n+'\\begin{item}')
        else:
            if pre:
                if initem: print(' '*max(inlist+inenum)+'\\end{item}')
                if n not in inlist and n not in inenum:
                    inlist.append(n)
                    print(' '*(n-1)+'\\begin{itemize}')
            if pre=='-': pre='–'
            if pre=='*': pre='•'
            if pre=='o': pre='○'
            if pre=='_':
                print(' '*n+'\\begin[bullet=""]{item}')
            elif pre:
                print(' '*n+'\\begin[bullet='+pre+']{item}')
        initem = True
    parse_line(' '*n+line)

def parse_table(line):
    global intable, lastobj
    def cell(fmt, arg): # TODO: cell alignment
        return(arg)
    if line.strip() and line.strip()[0]=='|' and (line.strip()[-1]=='|' or intable):
        if not intable:
            global twidth #, align
            lastobj = 'Table'
            if label: do_caption()
            intable = []
            for arg in line.strip().strip('|').split('|'):
                intable.append('center')
            twidth = '%dem' % (len(line)/2)
            begintable = '\\begin{center}\n\\hrule[width='+twidth+',height=0.2pt]\n\\begin{table}'
            if 'tables' in enditems:
                enditems['tables'].append(begintable)
            else:
                print(begintable)
        if not line.strip(' |:-'):  # it is a formatting row
            intable = []
            for arg in line.strip(' |').split('|'):
                if arg and arg[0]==':' and arg[-1]==':': intable.append('center')
                elif arg and arg[ 0]==':': intable.append('left')
                elif arg and arg[-1]==':': intable.append('right')
                else: intable.append('center')
            return
    elif intable:
        endtable = '\\end{table}\n\\hrule[width='+twidth+',height=2ex,depth=-2ex]\n\\end{center}'
        if 'tables' in enditems:
            enditems['tables'].append(endtable)
        else:
            print(endtable+'\n')
        intable = []
        parse_line(line)
    if intable:
        tmp = []#'\\tr{'
        for cidx in range(len(line.strip('|_*+').split('|'))):
            col = line.strip('|_*+').split('|')[cidx]
            fmt = intable[cidx]
            tmp.append('\\td{'+cell(fmt,col)+'}')# \\td{|} '%\set[parameter=document.parindent,value=0pt]
        line = ('\\tr{' + (' \\td{'+NBSP+'} ').join(tmp) + '}')
        if 'tables' in enditems:
            enditems['tables'].append(line)
        else: parse_line(line)

def parse_quote(line):
    global inblock
    if (line+' ')[:2] not in ['> ', '< ', '| ']:
        print('\n\\set[parameter=document.lskip,value=0pt]')
        print('\\set[parameter=document.rskip,value=0pt]')
        inblock = ''
    elif not inblock:
        if line[:2]=='< ':
            print('\n\\noindent\\set[parameter=document.rskip,value='+config['quotemargins'].split(',')[0]+']')
        else:
            print('\n\\noindent\\set[parameter=document.lskip,value='+config['quotemargins'].split(',')[0]+']')
            if len(config['quotemargins'].split(','))>1:
                print('\\set[parameter=document.rskip,value='+config['quotemargins'].split(',')[1]+']')
        print('')
        line = line[2:]
        inblock = 'quote'
    elif line[0] == '|' and inblock=='quote':
        line = '\\cr{}'+line[2:]
    else:
        line = line[2:]
    parse_line(line)

def parse_include(line):
    global lastobj, inblock, dirname
    olddir = dirname
    option = ''
    if '[' in line:
        option = line[3:].split(']')[0]
        fname = line.split(']')[-1].strip()
    else:
        fname = line[3:]
    if '/' in fname:
        tmpdir = '/'.join(fname.split('/')[:-1])
        if tmpdir[0] == '/': dirname = tmpdir
        else: dirname += '/'+tmpdir
    elif not os.path.exists(fname): fname = dirname+'/'+fname
    if '!' in option:   # may also be formatted, e.g. as 'code!' or '!quote'
        p      = os.popen(fname)
        output = p.read()
        for line in str(output).rstrip().split('\n'):   # rstrip() needed to remove the trailing \n
            print( parse_replaces(line) )
    elif fname[-4:] in ['.png', '.jpg', '.svg', '.gif', '.bmp', '.dot']:
        lastobj = 'Figure'
        if label: do_caption()
        if fname[-4:] == '.dot':
            oname = '/tmp/'+fname.split('/')[-1]+'.png'
            os.system('dot -Tpng -Gdpi=300 "'+fname+'" -o "'+oname+'"')
            fname = oname
        if 'draft' in config:
            line = '\\noindent\\center{['+fname+']}{}'
        else:
            line = '\\noindent\\center{\\img[src='+fname+','+option+']'+'}{}'
        if 'figures' in enditems:
            enditems['figures'].append(line)
        else: print(line)
    else:
        oconfig = {}
        for op in config: oconfig[op] = config[op]
        inblock=''
        with open(fname,'r') as fileID:
            for lline in fileID.readlines():
                lline = lline.rstrip('\n')
                if fname[-4:] == '.csv':
                    parse('| '+lline.replace(',','|')+' |')
                elif fname[-4:] == '.tsv':
                    parse('| '+lline.replace('	','|')+' |')
                else:
                    parse(option+lline)
        inblock = ''    # close comment block
        for mark in markers:    # close triplets
            if inmark[mark]: parse(mark*3)
        if fname[-4:] == '.txt': # do not discard changes for, e.g., '.hdr', '.yaml' files
            config.clear()
            for op in oconfig: config[op] = oconfig[op]
    dirname = olddir    # restore dirname

def parse_caption(line):
    global label
    id = line.split()[0]
    if id==':': id = ':'+uniqid()
    label = id+':'+' '+' '.join(line.split()[1:])  # turn ':any' into the tag of the label
    if lastobj:
        do_caption()

def parse_section(line):
    global infloat, inslide, dodecor, toggletitnum#, hastitle
    print('\\noindent')
    slevel = line.count('#')
    if config['class']=='poster': slevel -= 1
    if 'sectitle' in config: slevel -= 1
    if not slevel:
        if (line.split()[0]=='#:' and not config['ntitle']) or (line.split()[0]=='#-' and config['ntitle']):
            toggletitnum = True
        config['title'] = line.lstrip('#:-').strip() or ' '  # force a not empty title
        return
    if '@' not in line and ('-' not in line.split()[0]) and ((':' in line.split()[0]) or (config['nsections'] and len(config['nsections'])>=slevel and config['nsections'][slevel-1])):
        item=''
        if ':' in line.strip().split()[0]:
            item = line.strip().split()[0].split(':')[1]
            line = re.sub(':[^ ]*', '', line, count=1)
        if   slevel==1: line = line.strip().split()[0].strip(':') + ' @sec:'+item+NBSP + ' '.join(line.strip().split()[1:])
        elif config['class']=='slides': pass  # do not add counters to slide titles
        elif slevel==2: line = line.strip().split()[0].strip(':') + ' @ssec:'+item+NBSP + ' '.join(line.strip().split()[1:])
        elif slevel==3: line = line.strip().split()[0].strip(':') + ' @sssec:'+item+NBSP + ' '.join(line.strip().split()[1:])
        elif slevel==4: line = line.strip().split()[0].strip(':') + ' @ssssec:'+item+NBSP + ' '.join(line.strip().split()[1:])
    line = parse_counter(line)  # register 'cat' in counters
    if '-' in line.split()[0]:
        line = line.replace('#-', '#')
    pre = line.split()[0].strip('-')
    if '#' in pre and len(pre)==pre.count('#'):
        cat = 's'*slevel+'ec'
        if cat in counters:
            dest = str(curtitle)+cat+counters[cat][list(counters[cat])[-1]]
        else:
            dest = uniqid()
            print('\\pdf:destination[name='+dest+']')
        if config['toc'] == '':
            print('\\pdf:bookmark[title="'+' '.join(line.split()[1:])+'", dest='+dest+', level='+str(slevel+1)+']')
    if config['toc'] != '':
        print('\\tocentry[level='+str(slevel+1)+']{'+' '.join(line.split()[1:])+'}')
    if slevel==1:
        if config['class']=='slides':
            line = '\\section{'+line.lstrip('# ')+'}'
        elif config['class']=='poster':
            print('% \\float')
            if not infloat:
                infloat = True
            else:
                print('\\break')
        else:
                parse_line(config['secstyle'].replace('@', line.lstrip('# ')))
                dodecor = True
    elif slevel==2:
        if config['class']=='slides':
            if inslide: print('\\end{slide}')
            print('\\begin[title="'+parse_marks(line.lstrip('# '))+'"]{slide}')
            inslide = True
        else:
            parse_line(config['ssecstyle'].replace('@', line.lstrip('# ')))
        if 'sectitle' in config:
            dodecor = True
    elif slevel==3:
        if config['class']=='slides':
            parse_line('\\transition{'+line.lstrip('# ')+'}')
        else:
            parse_line(config['sssecstyle'].replace('@', line.lstrip('# ')))
    elif slevel==4:
        parse_line(config['ssssecstyle'].replace('@', line.lstrip('# ')))
    print('\\novbreak')

def do_math(line):
    global inblock
    if line.strip()[:3]!='$$-' and inblock!='math' and 'nequations' in config and (line.strip()[:3]=='$$:' or (line.strip()[:2]=='$$' and 'nequations' in config)):
        if ':' in line: item = line.strip().split()[0].split(':')[1]
        else: item = ''
        if 'eq' not in counters: counters['eq'] = {}
        if not item: item=len(counters['eq'])
        counters['eq'][item] = str(len(list(counters['eq']))+1)
    if inblock!='math' and '$$' in line:
        if '$$-' in line:
            line = line.replace('$$-', '\\begin[mode=display]{math}', 1)
        elif 'nequations' in config and ('$$:' in line or 'nequations' in config):
            print('\\pdf:destination[name='+str(curtitle)+'eq'+counters['eq'][item]+']')
            line = re.sub('\\$\\$:*[^ ]*', '\\\\begin[mode=display,numbered=true]{math}', line, count=1)
        else:
            line = line.replace('$$', '\\begin[mode=display]{math}', 1)
        inblock = 'math'
    if inblock=='math' and '$$' in line:
        line = line.replace('$$', '\\end{math}', 1)
        inblock = ''
    print(line)

def parse_note(line):
    global innote
    repl = ''
    if re.match('.*\\^\\[(.*)\\][^^]*', line):
        note = re.sub('.*\\^\\[(.*)\\].*', '\\1', line)
        if note not in notes:
            notes.append(note)
            unotes.append('\\pdf:destination[name=note'+str(notes.index(note))+']')
            if 'notes' not in enditems:
                parse_line('\\footnote{'+note+'}')
            else:
                repl = '^\\pdf:link[dest=note'+str(notes.index(note))+', borderwidth=0.4pt, bordercolor=red]{'+val2id(notes.index(note), config['notefmt'])+'}^'
                print('\\pdf:destination[name=anote'+str(notes.index(note))+']')
        elif 'notes' not in enditems:
            repl = '^'+str(notes.index(note))+'^'
        else:
            repl = '^\\pdf:link[dest=note'+str(notes.index(note))+', borderwidth=0.4pt, bordercolor=red]{'+val2id(notes.index(note), config['notefmt'])+'}^'
        line = line.replace('^['+note+']', repl)
    elif not innote and re.match('.*\\^\\[(.*)', line): # multi-line notes
        notes.append(re.sub('.*\\^\\[(.*)', '\\1', line))
        line = re.sub('\\^\\['+notes[-1], '', line)
        innote = True
    elif innote:
        if re.match('(.*)\\].*', line):
            notes[-1] += ' '+re.sub('(.*)\\].*', '\\1', line)
            innote = False
            note = notes[-1]
            del notes[-1]
            if note not in notes:
                notes.append(note)
                unotes.append('\\pdf:destination[name=note'+str(notes.index(note))+']')
                if 'notes' not in enditems:
                    line = re.sub('.*\\]', repl, line)
                    parse_line('\\footnote{'+note+'}')
                else:
                    print('\\pdf:destination[name=anote'+str(notes.index(note))+']')
            elif 'notes' not in enditems:
                repl = '^'+str(notes.index(note))+'^'
            if 'notes' in enditems:
                repl = '\\pdf:link[dest=note'+str(notes.index(note))+', borderwidth=0.4pt, bordercolor=red]{'+val2id(notes.index(note), config['notefmt'])+'}^'
            line = re.sub('.*\\]', repl, line)
        else:
            notes[-1] += ' '+line
            line = ''
    if line:
        parse_line(line)

def parse_counter(line):
    for key in re.findall('\\[*[@#][a-zA-Z]+:[a-zA-Z0-9]*\\]*', line):
        cat = key.strip('[]').split(':')[0][1:]
        item = key.strip('[]').split(':')[1]
        if cat not in counters:
            counters[cat] = {}
        if not item: item=len(counters[cat])
        if item=='last': item=list(counters[cat])[-1]
        if item not in counters[cat]:
            if cat=='sec':
                seccount[0] += 1; seccount[1] = 0; seccount[2] = 0; seccount[3] = 0
                counters[cat][item] = idsec(0) #config['snum'])
            elif cat=='ssec':
                seccount[1] += 1; seccount[2] = 0; seccount[3] = 0; #cat='sec'
                counters[cat][item] = idsec(1)
                if 'sec' not in counters: counters['sec'] = {}
                counters['sec'][item] = (idsec(0)+'.'+idsec(1)).strip('.')
            elif cat=='sssec':
                seccount[2] += 1; seccount[3] = 0; #cat='sec'
                counters[cat][item] = idsec(2)
                if 'sec' not in counters: counters['sec'] = {}
                counters['sec'][item] = (idsec(0)+'.'+idsec(1)+'.'+idsec(2)).replace('..','.').strip('.')
            elif cat=='ssssec':
                seccount[3] += 1; #cat='sec'
                counters[cat][item] = idsec(3)
                if 'sec' not in counters: counters['sec'] = {}
                counters['sec'][item] = (idsec(0)+'.'+idsec(1)+'.'+idsec(2)+'.'+idsec(3)).replace('..','.').strip('.')
            elif cat=='app': #appendix
                if references: print_references()
                if 'sectitle' not in config: print('\\eject\n') # only do a page break if sections are not already treated as titles (with its own page break)
                counters['app'][item] = val2id(len(list(counters[cat]))+1,'A')
                line = line.replace(key, ' '+trans['Appendix'][langidx]+' '+counters[cat][item]+'.')
            else:
                counters[cat][item] = str(len(list(counters[cat]))+1)
            if 'sec' in cat:
                if 'nestedsecs' not in config:
                    counters['sec'][item] = counters[cat][item]
                n = cat.count('s')-1
                if n>=len(config['nsections']):
                    line = line.replace(key, fmtid('1', counters['sec'][item]))
                else:
                    line = line.replace(key, fmtid(config['nsections'][n], counters['sec'][item]))
            print('\\pdf:destination[name='+str(curtitle)+cat+counters[cat][list(counters[cat])[-1]]+']')
        if key.strip('[]')[0]=='@':
            line = line.replace(key, '\\pdf:link[dest='+str(curtitle)+cat+counters[cat][list(counters[cat])[-1]]+', borderwidth=0.4pt, bordercolor=red]{'+counters[cat][item]+'}')
        else:
            line = line.replace(key, '')
    return line

def parse_citation(line):
    hasref = False
    for key in re.findall('@[a-zA-Z0-9-]+', line):
        if key.lstrip('@') in bibrefs:
            ref = key.lstrip('@')
            if ref not in references:
                references.append(ref)
        hasref = True
    for key in re.findall('\\[[^\\]]*@[^\\]]+\\]', line):     # each 'arg' may more than one grouped citation
            nkey = key.strip('[]')
            citations = []
            numbers = []
            for ref in re.findall('@[a-zA-Z0-9-]+', key):
                if ref.lstrip('@') in references:
                    nkey = nkey.replace(ref, bibrefs[ref.lstrip('@')].replace(' (',', ').replace(')',''))
                    numbers.append(str(references.index(ref.lstrip('@'))+1))
            if   config['citstyle']=='number':
                line = line.replace(key, '['+','.join(numbers)+']')
            elif config['citstyle']=='super':
                line = line.replace(key, '^'+','.join(numbers)+'^')
            else:   # authoryear
                line = line.replace(key, '('+nkey+')')  # \cite{<keys>}
    for key in re.findall('@[a-zA-Z0-9-]+', line):
        if key.lstrip('@') not in bibrefs: continue
        if   config['citstyle']=='number':
            line = line.replace(key, '\\pdf:link[dest='+key+', borderwidth=0.4pt]{'+bibrefs[key.lstrip('@')].split('(')[0]+'['+str(references.index(key.lstrip('@'))+1)+']}')
        elif config['citstyle']=='super':
            line = line.replace(key, '^\\pdf:link[dest='+key+', borderwidth=0.4pt]{'+str(references.index(key.lstrip('@'))+1)+'}^')
        elif config['citstyle']:  # default
            line = line.replace(key, '\\pdf:link[dest='+key+', borderwidth=0.4pt]{'+bibrefs[key.lstrip('@')]+'}')
    if hasref:
        if config['citstyle']=='number' and ']]' in line:
            for arg in re.findall('\\[(.*\\])\\]', line):   # try to join enclosed authoryear references, removing inner parenthesis
                arg0 = arg.replace('[','\\[').replace(']','\\]')
                arg1 = re.sub('[A-Za-z\\[\\] \\.]*', '', arg)
                line = re.sub(arg0, arg1, line)
        elif config['citstyle']=='super':
            line = re.sub('\\^([,; ]+)\\^', '\\1', line)    # try to join super references
            line = re.sub('([\\(\\[])\\^(.*)\\^([\\)\\]])', '^\\1\\2\\3^', line)    # raise brackets
        elif ')]' in line:
            for arg in re.findall('(\\[.*\\)\\])', line):   # try to join enclosed authoryear references, removing inner parenthesis
                arg0 = arg.replace('(','\\(').replace(')','\\)').replace('[','\\[').replace(']','\\]')
                arg1 = arg.replace(' (',', ').replace(')','').replace('[','(').replace(']',')')
                line = re.sub(arg0, arg1, line)
    return line

def highlight_keys(line):
    for key in re.findall(' @[a-zA-Z0-9-]+', ' '+line):
        line = re.sub(key, ' *'+key[1:]+'[?]*', ' '+line)[1:]
    return line

def parse_dropcaps(line):
    global dodecor
    dodecor=False
    line=line+'-'
    for cdx in range(len(line)):
        if line[cdx] in 'abcdefghijklmnopqrstuvwxyz\n': break
    ini = line[:cdx]
    if ini: print('\\dropcap['+config['decorfont']+',strict=false]{'+ini+'}')
    return line[cdx:-1]

def parse_speech(line):
    skip='1.2em'
    global inblock
    if not line.strip() and inblock:
        inblock=''
        print('\n\\noindent\\set[parameter=document.lskip,value=0pt'+']')
    elif line[:4] in ['--- ', '--- '] and inblock!='speech':
        line = '— '+line[4:]
        inblock='speech'
        print('\n\\noindent\\set[parameter=document.lskip,value='+skip+']') #'+config['quotemargins'].split(',')[0]+']')
#           print('\\hrule[height=0pt,width=-15pt]') #'+config['quotemargins'].split(',')[0]+']')
        print('\\rebox[width=-'+skip+']') #'+config['quotemargins'].split(',')[0]+']')
    parse_line(line)

def parse_marks(line):  # for marks inside a line
    if inmark['`']: return escape_chars(line+'\\cr')
    line = re.sub('^([ 	-]*)-- ','\\1--'+NBSP, line)    # NBSP after ^---
    line = line.replace('---','—').replace('--','–')
    line = ' '+line
    line = re.sub('[  ]``([^ ])', ' '+dquot[0]+'\\1', line)
    line = re.sub("([^ ])''", '\\1'+dquot[1], line)
    line = re.sub('[  ]"([^ "])', ' '+dquot[0]+'\\1', line)
    line = re.sub('([^ "])"', '\\1'+dquot[1], line)
    line = re.sub("[  ]'([^ '])", ' '+squot[0]+'\\1', line)
    line = re.sub("([^ '])'", '\\1'+squot[1], line)
    line = line[1:]
    line = line.replace('\\\\', '\\cr{}')
    line = line.replace('...', '…')
    for mark in markers:
        if '`' in line:
            line = line+'`'
            for arg in re.findall('`[^`]+`', line):
                line = line.replace(arg,escape_chars(arg))
            line = line[:-1]
        if mark in ['\\^', '~']:
            line = re.sub(mark+'([^'+mark+']+)'+mark, '\\\\'+markers[mark]+'{\\1}', ' '+line)[1:]
        else:
            line = re.sub('([^a-zA-Z0-9:\\)\\]}'+mark+'])'+mark+'([^'+mark+']+)'+mark+'([^a-zA-Z0-9])', '\\1\\\\'+markers[mark]+'{\\2}\\3', ' '+line+' ')[1:-1]
        if line[:2]==mark[-1]+mark[-1]:
            line = ' \\'+markers[mark]+'{'+line[2:]+'}'
            if mark=='`': line = line+'\\cr'
        if 'monofont' in line:
            line=line.replace('monofont',config['monofont'])
            return(line)    # FIXME
    line = line.replace('', '\\vfill')
    line = line.replace('', '\\eject')
    return line

def parse_center(line):
    global inblock
    if line.replace('\t',' '*4)[:20]==' '*20:
        if inblock != 'center':
            inblock = 'center'
            print('\\center{')
    elif inblock=='center':
        print('}')
        inblock = ''
    parse_line(line.lstrip())

def parse_replaces(line):
    global infloat
    idx = 0
    for pairs in config['replace']:
        line = line.replace(pairs.split(',')[0], pairs.split(',')[1])
    for key in re.findall('@[A-Za-z0-9]+', line):
        if key[1:] in config:
            line = line.replace(key, config[key[1:]])
    if infloat and ('' in line or '\\eject' in line or '\\break' in line):
        infloat = False
        if   ''      in line: line = line.replace('',      '}}')
        elif '\\eject' in line: line = line.replace('\\eject', '}}')
        elif '\\break' in line: line = line.replace('\\break', '}}')
    return line

def parse_line(line):
    global inblock
    if not inblock and not initem:
        if line.replace('\t','    ')[:4]=='    ':
            print('\\indent')
    if re.match('.*\\[[^\\[]*\\]\\([^\\)]*\\).*', line):    # URL
        line = re.sub('\\[([^\\[]*)\\]\\(([^\\)]*)\\)', '\\\\href[src=\\2, borderwidth=0.4pt, bordercolor=cyan, borderstyle=rectangle]{\\1}', line) # uderline
    elif re.match('.*(https?://[^ ]+).*', line):    # URL
        line = re.sub('(https?://[^ ]+)', '\\\\href[src=\\1, borderwidth=0.4pt, bordercolor=cyan, borderstyle=rectangle]{\\1}', line) # uderline
    line = parse_counter(line)
    line = parse_citation(line)
    if 'highlightids' in config and '@' in line:
        line = highlight_keys(line)
    if dodecor and line.strip() and config['decorfont']:
        line = parse_dropcaps(line)
    line = parse_marks(line)
    print(line)

def parse(line):    # to parse whole lines
    global inblock, inlist, inenum, initem, incenter, intable, innote, lastobj, label, hline, dodecor, infloat#, curtitle, hastitle #, inslide
    if line=='---' or inblock=='header':
        parse_header(line)
        return
    if not hasheader:  # for when a document has no header
        do_header()
    if config['title'] or config['cover']:
        do_title()
    if config['toc']:
        do_toc()
    line = parse_replaces(line)
    if line.strip()=='%%%':
        if not inblock:
            inblock = 'comment'
        else:
            inblock = ''
    if inblock=='comment': return
    if line and line[0]=='%': return
# TRIPLETS
    for mark in markers:
        if line.strip()==mark[-1]*3:
            inmark[mark] = not inmark[mark]
            if inmark[mark]:
                if 'monofont' in markers[mark]:
                    print('\\begin['+markers[mark].split('[')[1].replace('monofont',config['monofont'])+'{'+markers[mark].split('[')[0]+'}')
                else:
                    print('\\begin{'+markers[mark]+'}')
            else:
                if inblock and inblock!='par': parse('')   # allow a more compact writing, but may insert unwanted newlines
                print('\\end{'+markers[mark].split('[')[0]+'}')
            return
####
    if inblock=='math' or ((inblock=='par' or not inblock) and '$$' in line):   # $...$ are parsed in parse_marks()
        do_math(line)
    elif line[:3]=='<< ' or line[:3]=='<<[':
        parse_include(line)
    elif not inblock and line and line[0] == ':':
        parse_caption(line)
    elif innote or re.match('.*\\^\\[(.*)', line):
        parse_note(line)
    elif intable or (not inblock and line.strip() and line.strip()[0]=='|' and line.strip()[-1]=='|'):
        parse_table(line)
    elif inblock=='quote' or (not inblock and (line[:2] in ['> ', '< ', '| '])):
        parse_quote(line)
    elif inblock=='center' or (not inblock and line.replace('\t',' '*4)[:20]==' '*20):
        parse_center(line)
    elif initem or (not inblock and len(line.strip())>2 and (line.strip()[1]==NBSP or (line.strip().split()[0].rstrip('.<[()]>') and line.strip().split()[0].rstrip('.<[()]>') in '-+*_1234567890iIaA'))):
        parse_list(line)
    elif line.strip() and line.strip()[0]=='#':
        parse_section(line)
    elif line[:4] in ['--- ', '--- '] or inblock=='speech':
        parse_speech(line)
    else:
        parse_line(line)
        if line.strip() and not inblock:
            inblock = 'par'
        if not line:
            inblock = ''

def do_header():
    global hasheader#, ntitle
###
    config['titlefont'] = parse_font(config['titlefont'])
    config['monofont']  = parse_font(config['monofont'])
    config['decorfont'] = parse_font(config['decorfont'])
    locale = os.popen('locale -a | grep '+config['lang']+' | head -1', 'r').read().strip()  # use config['lang'] to get localized dates
    config['date'] = os.popen('LC_TIME='+locale+' date +"'+config['datefmt']+'"', 'r').read().strip()
    if '=' in config['margins']:
        tmpm = config['margins'].split(',')
        config['margins'] = ['','','','']
        for margin in tmpm:
            val = margin.split('=')[1].strip()
            if 'left'   in margin: config['margins'][0] = val
            if 'right'  in margin: config['margins'][1] = val
            if 'top'    in margin: config['margins'][2] = val
            if 'bottom' in margin: config['margins'][3] = val
        if not config['margins'][1]: config['margins'][1] = config['margins'][0]
        if not config['margins'][0]: config['margins'][0] = config['margins'][1]
        if not config['margins'][3]: config['margins'][3] = config['margins'][2]
        if not config['margins'][2]: config['margins'][2] = config['margins'][3]
        for idx in range(4):
            if not config['margins'][idx]: config['margins'][idx] = val
    elif config['margins']:
        config['margins'] = config['margins'].split(',')
        if len(config['margins'])==2: config['margins'].insert(0,config['margins'][0])    # horizontal,vertical -> left,right,top,_
        while len(config['margins']) < 4:
            config['margins'].append(config['margins'][-1])
###
    if not hasheader:
        if config['class']=='plain' or config['class'] == 'poster':
            print('\\begin[class=plain,papersize='+config['papersize']+']{document}') # TODO: poster, papersize=a4/a0; alternate between twocolumns and singlecolumn?
            if config['margins']:
                print('\\use[module=packages.masters]   % margins')
                print('\\define-master-template[id=master,first-content-frame=content]{')
                print('    \\frame[id=root, left=0%pw, right=100%pw, top=0%ph, bottom=100%ph]')
                print('    \\frame[id=content, left='+config['margins'][0]+',right=100%pw-'+config['margins'][1]+', top='+config['margins'][2]+', bottom=top(footnotes)]')
                print('    \\frame[id=folio, left=left(content),right=right(content), top=bottom(footnotes)+5mm, bottom=100%ph]')
                print('    \\frame[id=footnotes, left=left(content),right=right(content), height=0cm, bottom=100%ph-'+config['margins'][3]+'] }')
                print('\\switch-master[id=master]')
            if config['columns']:   # i.e., class must be 'plain'
                print('\\use[module=packages.frametricks]')
            print('\\define[command=titlefont]{\\font['+config['titlefont']+']{\\process}}')
            print('\\define[command=title]{'+config['titlestyle'].replace('@','\\process')+'}')
        elif config['class']=='slides':
            print('\\begin[class=slides,papersize='+config['slidesize']+']{document}')
            if 'transitionslides' not in config:
                                        print('\\noTransitionSlides')
            if 'rulefolios' in config:  print('\\ruleFolios')
            if 'vcenter'    in config:  print('\\toggleCenter')
            if 'printnotes' in config:  print('\\printNotes['+config['printnotes']+']')
            if 'background' in config:  print('\\backgroundImage[src='+config['background']+']')
            if 'alternate'  in config:  print('\\alternateImage[src='+config['alternate']+']')
            if 'themecolor' in config:  print('\\themeColor[color='+config['themecolor']+']')
            config['listskip'] = '4pt plus 8pt minus 2pt' # use as default large list spacing
        print('\\set[parameter=document.parskip,value='+config['parskip']+']')
        print('\\set[parameter=document.baselineskip,value='+config['lineskip']+']')
        if len(config['title'])==1 and findid(config['title']):
            confg['ntitle'] = config['title']
            config['title'] = ''
        if 'sectitle' not in config and not config['title']:
            config['sectitle'] = 'true'
        if config['nsections']:
            config['nsections'] = [v.strip() for v in config['nsections'].split(',')]
            while len(config['nsections']) < len(seccount):
                config['nsections'].append( findid(config['nsections'][-1]) )   # try to be 'smart' and reuse the last format to all remaining (sub)sections
 
    if config['packages']:
        for pkg in config['packages'].split():
            print('\\use[module=packages.'+pkg+']')
    print('\\define[command=highlight]{\\color[color=red]{\\process}}') # a yellow background requires to actually draw boxes, which are limited to the same line
    print('\\define[command=superscript]{\\font[size=0.7em]{\\raise[height=4pt]{\\process}}}')
    print('\\define[command=subscript]{\\font[size=0.7em]{\\lower[height=4pt]{\\process}}}')
    print('\\set[parameter=lists.parskip,value='+config['listskip']+']')
    print('\\set[parameter=document.parindent,value='+config['indent']+']')
    if config['decorfont'] and 'dropcaps' not in config['packages']:
        print('\\use[module=packages.dropcaps]')
    if config['lang']:
                                    print('\\language[main='+config['lang']+']')
                                    if config['lang'] in languages:
                                        global langidx, squot, dquot
                                        langidx = languages.index(config['lang'])
                                        if 'curlyquotes' in config:
                                            squot = trans["'"][langidx]
                                            dquot = trans['"'][langidx]
    if config['toc']:
        print('\\use[module=packages.tableofcontents]')
        print('\\define[command=tableofcontents:headerfont]{\\title{\\process}}')
        print('\\define[command=tableofcontents:level1item]{\\font[size=1.2em]{\\process}\\break\\medskip}')
        print('\\define[command=tableofcontents:level2item]{\\font[size=1em]{\\process}\\break\\smallskip}')
        print('\\define[command=tableofcontents:level3item]{\\font[size=1em]{\\em{\\process}}\\break\\smallskip}')
    if config['bibliography'] and has_bibcite: #in config:
                                    refs = []
                                    with open(config['bibliography']) as bibfile:
                                        for line in bibfile:
                                            if '@' in line: refs.append(re.sub('.*@.*{(.*),.*', '\\1', line.strip()))
                                    cits = os.popen('bibcite '+config['bibliography']+' -cite='+','.join(refs), 'r').read().strip().split('\n')   # get all at once
                                    for idx in range(len(refs)): bibrefs[refs[idx]] = cits[idx]
                                    if not config['citstyle']: config['citstyle'] = os.popen('bibcite -style='+config['bibstyle']+' -citstyle', 'r').read().strip()
    if config['font']:              print('\\font['+config['font'][0]+']')
    if len(config['font'])>1:
                                    if 'font-fallback' not in config['packages']:
                                        print('\\use[module=packages.font-fallback]')
                                    for font in config['font'][1:]:
                                        print('\\font:add-fallback['+font.strip()+']')
    if config['columns'] and config['class']=='plain':
        print('\\breakframevertical')
        print('\\makecolumns[columns='+config['columns']+']')
    if config['ornament'] and 'orn' not in config:
        config['orn'] = '\\img[src='+config['ornament']+']'
    if config['enditems']:
        for arg in config['enditems'].split(','):
            if arg=='notes': enditems['notes'] = notes
            else: enditems[arg.strip()] = []
    if 'notes' not in enditems:
        print('\\use[module=packages.footnotes]')
    hasheader = True

def parse_font(arg):
    if '=' in arg: return arg
    font = []
    fname = arg
    fsize = re.findall('[0-9]+[pP][tT]', fname)
    if fsize:
        fname = fname.replace(fsize[0],'').strip()
        font.append('size='+fsize[0])
    if fname:
        font.insert(0,'family='+fname)
    return ','.join(font)

def do_toc():
    print('\\eject')
    print('\\tableofcontents[depth='+config['toc']+']')
    config['toc'] = 0

def do_title():
    global curtitle, numtitle, toggletitnum#, hastitle
    if curtitle:
        print('\\eject\n')
    if config['toc'] != '' and (curtitle or 'sectitle' in config):
        print('\\tocentry[level=1]{'+config['title']+'}')
    if config['cover']:
        print('\\use[module=packages.frametricks]')
        print('\\nofoliothispage')
        print('\\noindent')
        if not curtitle:
            print('\\set-counter[id=folio, value=0]')
        if '=' not in config['cover']:
            print('\\typeset-into[frame=root]{\\img[src='+config['cover']+',height=100%fh,width=100%fw]}')
        else:
            print('\\typeset-into[frame=root]{\\center{\\img[src='+config['cover']+']}}')
        print('\\eject')
    dest = 'tit'+str(curtitle)
    if config['toc'] == '':
        print('\\pdf:destination[name='+dest+']')
        print('\\pdf:bookmark[title="'+config['title']+'", dest='+dest+', level=1]')
    if config['class']=='slides':  print('\\hbox\\vfill\\vfill')
    if config['title']:
        curtitle += 1
        if (config['ntitle'] and not toggletitnum) or (not config['ntitle'] and toggletitnum):
            numtitle += 1
            if config['ntitle']:
                parse_line(parse_replaces('\\title{'+fmtid(config['ntitle'], val2id(numtitle, config['ntitle']))+NBSP+config['title']+'}'))
            else:
                parse_line(parse_replaces('\\title{'+str(numtitle)+NBSP+config['title']+'}'))
        else:
            parse_line(parse_replaces('\\title{'+config['title']+'}'))
    toggletitnum = False
    if config['class']=='slides': print('\\vfill')
    if 'author' in config and 'authtitle' in config:
                                 parse_line(parse_replaces(config['stitlestyle'].replace('@',config['author'])))
    if config['subtitle']:      parse_line(parse_replaces(config['stitlestyle'].replace('@',config['subtitle'])))
    if 'datetitle' in config:
                               parse_line(parse_replaces(config['sstitlestyle'].replace('@',config['date'])))
    if config['subsubtitle']: parse_line(parse_replaces(config['sstitlestyle'].replace('@',config['subsubtitle'])))
    if config['ornament']:   print('\\center{\\img[src='+config['ornament']+']}') #,width=75pt]}')
    config['title'] = ''; config['subtitle'] = '' ; config['subsubtitle'] = ''
    config['cover'] = ''
    seccount[0] = 0; seccount[1] = 0; seccount[2] = 0; seccount[3] = 0
    idx = 0
    for val in config['nini'].split(','):
        if val.lstrip('-').isdigit():
            seccount[idx] += int(val)
        idx += 1
    config['nini'] = ''

nini = 1

def print_notes():
    print('\\begin{itemize}')
    for nidx in range(nini,len(notes)):
        print('\\begin[bullet=""]{item}')
        print(unotes[nidx])
        print('\\pdf:link[dest=anote'+str(nidx)+', borderwidth=0.4pt, bordercolor=red]{'+fmtid(config['notefmt'], nidx)+'}   ')
        parse(notes[nidx])
        print('\\end{item}')
    print('\\end{itemize}')

def print_references():
    global references
    parse('# '+trans['References'][langidx])
    print('')
    ridx=0
    if has_bibcite:
        for line in os.popen('bibcite -style='+config['bibstyle']+' -keys='+','.join(references)+' '+config['bibliography']+' -markup=dj', 'r').read().strip().split('\n'):
            print('\\pdf:destination[name='+references[ridx]+']')
            parse(line)     # parse() because it has a list
            ridx += 1
    parse('')   # a hack to end any open list
    references = []

def print_enditems():
    for key in enditems:
        print('\\eject')
        parse('#-' + trans[key.title()][langidx])
        print('')
        if key=='notes':
            print_notes()
        else:
            for line in enditems[key]:
                parse_line(line)

def end_document():
    global inblock
    if (inblock=='comment'): inblock = ''   # as it is not 'closed' by an empty line
    if inslide: print('\\end{slide}')
    if references: print_references()
    if enditems:   print_enditems()
    print('\\end{document}')


# DEFAULTS
config['class'] = 'plain' #'paper'
config['lang'] = 'en'
config['papersize'] = 'a4'
config['indent'] = '0pt'  # 20pt
config['parskip'] = '8pt plus 2pt'
config['lineskip'] = '1.2em'
config['listskip'] = '0pt plus 1pt'
config['slidesize'] = '128mm x 96mm ' #'5.04in x 3.78in'
config['margins'] = '2cm' # will turn into a list, with values for 'left', 'right', 'top' and 'bottom' margins, respectively
config['quotemargins'] = '1cm,0cm'
config['columns'] = ''
config['font'] = []
config['titlefont'] = 'Liberation Sans'   # config['font'] may define a size; but config['titlefont'] should not
config['monofont'] = 'Liberation Mono 10pt'
config['decorfont'] = ''
# enable some styling in documents; '@' marks the text position
config['title'] = ''
config['subtitle'] = ''
config['subsubtitle'] = ''
config['ornament'] = ''
config['authtitle'] = '' #'on'
config['titlestyle'] = '\\bigskip\\center{\\strong{\\font[size=1.3em]{\\titlefont{@}}}}'
config['stitlestyle'] = '\\center{\\em{@}}'
config['sstitlestyle'] = '\\center{@}'
config['secstyle'] = '\\bigskip\n\\goodbreak\n*\\font[size=1.2em]{\\titlefont{@}}*\n\\medskip\\novbreak'
config['ssecstyle'] = '*\\titlefont{@}*\n\\smallskip\\novbreak'
config['sssecstyle'] = '_\\titlefont{@}_\\novbreak'
config['ssssecstyle'] = '+\\titlefont{@}+\\novbreak'
config['toc'] = ''
config['ntitle'] = ''
config['nini'] = ''
config['nsections'] = ''
config['nequations'] = ''
config['notefmt'] = '1'
config['datefmt'] = '%B %d, %Y' # %F
config['bibliography'] = ''
config['bibstyle'] = ''
config['citstyle'] = ''
config['cover'] = ''
config['enditems'] = ''# None   notes,figures,tables
config['highlightids'] = ''#'true'
config['nestedsecs'] = ''#'true'
config['curlyquotes'] = ''#'on'
config['replace'] = [ \
    '-----,\\noindent\\hrulefill', \
    '=====,\\noindent\\hrulefill[thickness=2.5pt]', \
    '*****,\\noindent\\hrulefill[thickness=5pt]' ]
config['packages'] = 'image rules lists svg raiselower math simpletable url color' # pdf'

dodecor = False
datafile = ''
for arg in list(sys.argv[1:]):
    if arg=='-slides':
        config['class'] = 'slides'
    elif arg=='-poster':
        config['class'] = 'poster'
    elif arg[0]=='-' and ':' in arg:
        config[arg.split(':')[0][1:]] = ':'.join(arg.split(':')[1:]).lstrip()
    elif os.path.exists(arg):
        datafile = arg
        if arg[-4:]=='.sli':
            config['class'] = 'slides'
        elif arg[-4:]=='.pos':
            config['class'] = 'poster'
    elif arg in ['?', '-h', '-help']:
        print(sys.argv[0], '-slides|-poster -key:val')
        print('default values:')
        for key in config:
            print(key.rjust(16)+':', config[key])
        print('switches: authtitle, datetitle, sectitle, nequations, curlyquotes, highlightids, nestedsecs, resetnotes, draft')
        print('slide switches: transitionslides, rulefolios, vcenter, printnotes')
        exit()
    else: print('WARN spurious arg:', arg)

dirname = '.'
if datafile:
    if '/' in datafile:
        dirname = '/'.join(datafile.split('/')[:-1])+'/'
    fileID = open(datafile)
    for line in fileID.readlines():
        parse(line.strip('\n'))
    fileID.close()
else:
    while True:
        try:
            line = input('')
        except: break
        parse(line)

parse('')   # a trick to end any opened block

if 'noheader' in config: exit()
end_document()

