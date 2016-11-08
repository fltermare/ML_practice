#!/usr/bin/env python
import argparse
import re
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer


def getopt():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("infile")
    parser.add_argument("types", choices=['matrix', 'inout'])
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


def parse(infile, types):
    '''
    parse WARC
    '''
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
    if types == 'matrix':
        output(table, seen_link)
    elif types == 'inout':
        linkFromTo(table, seen_link)


def linkFromTo(table, seen_link):
    inOut = dict()
    #[0] # of in(from)
    #[1] distinct in(from)
    #[2] # of out(to)
    #[3] distinct out(to)
    #[4] link to self
    for kfrom, v in table.items():
        for kkto, count in v.items():
            inOut[kkto] = inOut.get(kkto, [0, set(), 0, set(), 0])
            inOut[kkto][0] += 1
            inOut[kkto][1].add(kfrom)
            inOut[kfrom] = inOut.get(kfrom, [0, set(), 0, set(), 0])
            inOut[kfrom][2] += count
            inOut[kfrom][3].add(kkto)
            if kkto == kfrom:
                inOut[kkto][4] += 1
    for kfrom, v in inOut.items():
        #if v[0] != len(v[1]) or v[2] != len(v[3]) or v[4] != 0:
        print (v[0], len(v[1]), v[2], len(v[3]), v[4]), kfrom


def output(table, seen_link):
    '''
    output matrix
    '''
    length = len(seen_link)
    d = 0.85
    count = 0
    span_table = list()

    #build span_table
    count_i = 0
    count_j = 0
    for i in seen_link:
        span_table.append([])
        for j in seen_link:
            try:
                ij_content = table[i][j]
            except:
                ij_content = 0

            span_table[count_i].append(ij_content)
            count_j += 1

        count_j = 0
        count_i += 1

    #average span_table
    for i in span_table:
        total = sum(i)
        try:
            i[:] = [(x/float(total))*d for x in i]
        except:
            pass

    #transpose matrix (span_table)
    T_table = list()
    for i in range(length):
        T_table.append([])
        for j in range(length):
            T_table[i].append(span_table[j][i])

    with open('../matrix.csv', 'w') as fout:
        #print columns
        for k in seen_link:
            fout.write('url['+str(count+1)+']')
            if count != length-1:
                fout.write(',')
            count += 1
        fout.write(',damping,result')
        fout.write('\n')
        #print content
        for i in range(length):
            for j in range(length):
                if i == j:
                    fout.write(str(T_table[i][j]))
                    #fout.write(str(T_table[i][j]-1))
                else:
                    fout.write(str(T_table[i][j]))
                fout.write(',')
                if j == length-1:
                    fout.write(str((1-d)/length))
                    fout.write(',url['+str(i+1)+']')
            fout.write('\n')

def main():
    args = getopt()
    l = parse(args.infile, args.types)


if __name__ == "__main__":
    main()
