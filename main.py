import requests
import html
import re
import json
import sys, colorama
from colorama import Fore, Style
from bs4 import BeautifulSoup


colorama.init()
bad = Fore.RED + '[-]' + Style.RESET_ALL
good = Fore.GREEN + '[?]' + Style.RESET_ALL
alert = Fore.YELLOW + '[=]' + Style.RESET_ALL
indi = Fore.CYAN + '[!]' + Style.RESET_ALL


# ----------------------------
def escape_quotes(s):
    return re.sub(r'(=")([^"]+)(")|\[.*?\]', r'=\\"\2\\"', s)

def remove_text_between_tags(s, start_tag, end_tag):
    return re.sub(f'{start_tag}.*?{end_tag}', f'{start_tag}{end_tag}', s)

def remove_non_ascii(s):
    return ''.join(c for c in s if ord(c)<128)

def dnd_getter(s, identifier, tag):
    pattern = r'<{}[^>]+identifier="{}"[^>]+>([^<]+)</{}>'.format(tag, identifier, tag)
    match = re.search(pattern, s)
    if match:
        return match.group(1)
    return None

def dnd_question_getter(s, identifier):
    pattern = r'<simpleAssociableChoice[^>]+identifier="{}"[^>]+><strong>(.*?)</strong>.*?</simpleAssociableChoice>'.format(identifier)
    match = re.search(pattern, s)
    if match:
        return match.group(1)
    return None

def answers_parser(answers):
    values = []
    for i in answers:
        if 'value' in i:
            tmp = re.findall(r'<value>(.*?)</value>', i)
            for j in tmp:
                values.append(j)
        elif i != '':
            values.append(i)
    return values

def dnd_printer(answer,s, identifier, index = 0):
    values = answers_parser(answer)
    for i in values:
        answer = i.split()[index]
        print(f'  {alert} {dnd_getter(s, answer, identifier)}')

def simple_printer(s, tag, identifier, answer, index = 0):
    values = answers_parser(answer)
    for i in values:
        answer = i.split()[index]
        print(f'  {alert} {get_text(s, tag, identifier, answer )}')

def el_finder(s, tag, att, att_value):
    el = s.find(tag, attrs={att: att_value})
    if not el:
        return False
    return el

def get_text(s, tag, att="", att_value=""):
    el = el_finder(s, tag, att, att_value)
    if not el:
        return False

    if el.find('img'):
        return f"Image: {el.find('img').get('alt')}"
    return el.text

# ----------------------------
def main():
    url = sys.argv[1]

    r = requests.get(url)

    if(r.status_code != 200):
        print(f'{bad} Error: {str(r.status_code)} {r.reason}')
        exit()


    # Escape the xml string
    xml_string = r.text.replace('\n','').replace('\\n', '').replace('\\r','').replace('  ', '').encode().decode('unicode_escape').replace('\'', '').replace(u'\xa0', u' ')
    xml_string = remove_non_ascii(xml_string)
    xml_escaped = html.unescape(xml_string)

    # Remove all empty strings (="") and add `\\` to all `"` characters
    xml_quoted = escape_quotes(xml_escaped.replace('""', 'null'))

    # Remove the last character, which is a semicolon and replace the first line with the json key
    xml_quoted = xml_quoted[:-1].replace('ajaxData = ', '')

    try:
        xml_dict = json.loads(xml_quoted)
    except Exception as e:
        print(str(e) + f'\n{bad} The XML is not parsed correctly. Please open an issue here (https://github.com/EverStarck/cambridgeFuck/issues) and add the url you used. Thank you!')
        exit()

    for xml in xml_dict:
        xml = remove_text_between_tags(xml_dict[xml].replace('\\', ''), '<div id="options">', '</div>')
        soup = BeautifulSoup(xml, features="xml")
        isDnD = 'gapMatchInteraction' in xml
        isDnDSimple = 'simpleMatchSet' in xml
        isSimpleInt = 'choiceInteraction' in xml

        # ---------------------------- Indication ----------------------------
        indication = get_text(soup, 'div', 'id', 'rubric')
        if indication:
            print(f'{indi}: {indication}')

        # ---------------------------- Question ----------------------------
        parent = el_finder(soup, 'div', 'id', 'contentblock')
        if parent:
            question = get_text(parent, 'p')
            if question:
                print(f'{good} {question}')

        # ---------------------------- Answers ----------------------------
        answers = re.findall(r'<correctResponse><value>(.*?)</value>(.*?)</correctResponse>', xml, re.DOTALL)

        # simpleMatch question
        if isDnDSimple:
            id = answers[0][0].split()[0]
            question = dnd_question_getter(xml, id)
            print(f'{good} {question}')

        for answer in answers:
            if isDnD:
                dnd_printer(answer, xml, "gapText", 0)
            elif isDnDSimple:
                dnd_printer(answer, xml, "simpleAssociableChoice", 1)
            elif isSimpleInt:
                simple_printer(soup, "simpleChoice", "identifier", answer, 0)
            else:
                print(f'  {alert} {answer[0]}')

        if answers != []:
            print('\n')

print(
    '''
 ▄████▄  ▄▄▄      ███▄ ▄███▓▄▄▄▄   ██▀███  ██▓█████▄  ▄████▓█████  ██████    ██ ▄████▄  ██ ▄█▀
▒██▀ ▀█ ▒████▄   ▓██▒▀█▀ ██▓█████▄▓██ ▒ ██▓██▒██▀ ██▌██▒ ▀█▓█   ▀▓██   ▒██  ▓██▒██▀ ▀█  ██▄█▒ 
▒▓█    ▄▒██  ▀█▄ ▓██    ▓██▒██▒ ▄█▓██ ░▄█ ▒██░██   █▒██░▄▄▄▒███  ▒████ ▓██  ▒██▒▓█    ▄▓███▄░ 
▒▓▓▄ ▄██░██▄▄▄▄██▒██    ▒██▒██░█▀ ▒██▀▀█▄ ░██░▓█▄   ░▓█  ██▒▓█  ▄░▓█▒  ▓▓█  ░██▒▓▓▄ ▄██▓██ █▄ 
▒ ▓███▀ ░▓█   ▓██▒██▒   ░██░▓█  ▀█░██▓ ▒██░██░▒████▓░▒▓███▀░▒████░▒█░  ▒▒█████▓▒ ▓███▀ ▒██▒ █▄
░ ░▒ ▒  ░▒▒   ▓▒█░ ▒░   ░  ░▒▓███▀░ ▒▓ ░▒▓░▓  ▒▒▓  ▒ ░▒   ▒░░ ▒░ ░▒ ░  ░▒▓▒ ▒ ▒░ ░▒ ▒  ▒ ▒▒ ▓▒
  ░  ▒    ▒   ▒▒ ░  ░      ▒░▒   ░  ░▒ ░ ▒░▒ ░░ ▒  ▒  ░   ░ ░ ░  ░░    ░░▒░ ░ ░  ░  ▒  ░ ░▒ ▒░
░         ░   ▒  ░      ░   ░    ░  ░░   ░ ▒ ░░ ░  ░░ ░   ░   ░   ░ ░   ░░░ ░ ░░       ░ ░░ ░ 
░ ░           ░  ░      ░   ░        ░     ░    ░         ░   ░  ░        ░    ░ ░     ░  ░   
░                                ░            ░  ░                                ░
 \n'''
)

main()