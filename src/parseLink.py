#!/usr/bin/env python3
import argparse
import re
from bs4 import BeautifulSoup, SoupStrainer


def getopt():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("infile")
    args = parser.parse_args()
    return args


def strip_protocol(link):
    try:
        return link.split('://')[1]
    except:
        return link


def target(data, host, page, table, seen_link):
    soup = BeautifulSoup(data, "lxml")
    ans = list()
    seen_link.add(page)
    table[page] = table.get(page, dict()) 
    for l in soup.findAll('a', href=True):
        if re.match(r'^mailto', l['href']):
            pass
        elif re.match(r'^#', l['href']):
            ans.append(strip_protocol(page))
        elif re.match(r'.*#', l['href']):
            ans.append(strip_protocol(page))
        elif re.match(r'http', l['href']):
            ans.append(strip_protocol(l['href']))
        else:
            ans.append(host + l['href'].strip('/'))
    for i in ans:
        table[page][i] = table[page].get(i, 0)
        table[page][i] += 1
        seen_link.add(i)
    return ans 


def parse(infile):

    table = dict()
    seen_link = set()
    with open(infile, 'r') as fdata:
        data = ''
        host = ''
        page = ''
        for line in fdata:
            tmp = re.match(r'WARC-Target-URI: (.*)', line)
            if tmp:
                page = tmp.groups()[0]
                page = strip_protocol(page.rsplit('#')[0])
                h = re.match(r'(.*/).*', page)
                host = strip_protocol(h.groups()[0])
                linkList = target(data, host, page, table, seen_link)
                
                data = ''
                #print '----' + page
                #print '----' + host 
            else:
                data += line
        linkList = target(data, host, page, table, seen_link)
    
    output(table, seen_link)


def output(table, seen_link):
    length = len(seen_link)
    count = 0
    print length
    span_table = [[0]*length]*length

    with open('./output.csv', 'w') as fout:
        for k in seen_link:
            fout.write(str(count))
            if count != length-1:
                fout.write(',')
            count += 1
        fout.write('\n')
        
        for i in seen_link:
            count = 0 
            for j in seen_link:
                try:
                    fout.write(str(table[i][j]))
                    if count != length-1:
                        fout.write(',')
                except:
                    fout.write('0')
                    if count != length-1:
                        fout.write(',')
                count += 1
            fout.write('\n')

def main():
    args = getopt()
    l = parse(args.infile)


if __name__ == "__main__":
    main()
