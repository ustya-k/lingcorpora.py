from requests import get
from bs4 import BeautifulSoup
import sys
import argparse
from html import unescape
import csv
import unittest


def get_results(query,start,n,lang,mode,n_left,n_right):
    """
    create a query url and get results for one page
    """
    params = {'q': query,
              'start': start,
              'num': n,
              'index':'FullIndex',
              'outputFormat':'HTML',
              'encoding':'UTF-8',
              'maxLeftLength':n_left,
              'maxRightLength':n_right,
              'orderStyle':'score',
              'dir':lang,
              'scopestr':'' # subcorpus: TO DO
              }
    if mode == 'simple':
        r = get('http://ccl.pku.edu.cn:8080/ccl_corpus/search',params)
    if mode == 'pattern':
        r = get('http://ccl.pku.edu.cn:8080/ccl_corpus/pattern',params)
    return unescape(r.text)


def parse_page(page,first=False):
    """
    find results (and total number of results) in the page code
    """
    soup = BeautifulSoup(page, 'lxml')
    res = soup.find('table',align='center')
    if res:
        res = res.find_all('tr')
    else:
        return [],0
    if first:
        num_res = int(soup.find('td',class_='totalright').find('b').text)
        return res, num_res
    return res

    
def parse_results(results):
    """
    find hit and its left and right contexts
    in the extracted row of table
    """
    for i in range(len(results)):
        results[i] = results[i].select('td[align]')
        results[i] = [x.text.strip() for x in results[i]]
    return results
        

def download_all(query,results_wanted,n_left,n_right,lang,mode):
    """
    get information and hits from first page and iterate until
    all hits are collected or maximum set by user is achieved
    """
    per_page = 50
    all_res = []
    first = get_results(query,0,per_page,lang,mode,n_left,n_right)
    first_res,total_res = parse_page(first,True)
    all_res += parse_results(first_res)
    n_results = min(total_res,results_wanted)
    for i in range(per_page,n_results,per_page):
        page = get_results(query,i,per_page,lang,mode,n_left,n_right)
        all_res += parse_results(parse_page(page))
    return all_res


def write_results(query,results,cols):
    """
    write csv
    """
    not_allowed = '/\\?%*:|"<>'
    query = ''.join([x if x not in not_allowed else '_na_' for x in query])
    with open('zho_results_'+query+'.csv','w',encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(cols)
        for i,x in enumerate(results):
            writer.writerow([i]+x)

    
def main(query,corpus='xiandai',mode='simple',n_results=10,
         n_left=30,n_right=30,kwic=True,write=False):
    """
    main function
    
    Args:
        query: a query to search by
        corpus: 'xiandai' (modern Chinese) or 'dugai' (ancient Chinese)
        mode: 'simple' or 'pattern'
              (they differ in syntax, read instructions in the corpus)
        n_results: desired number of results (10 by default)
        n_left: length of left context (in chars, max=40)
        n_right: length of right context (in chars,max=40)
        write: whether to write into csv file or not
        kwic: whether to write into file in kwic format or not

    Return:
        list of row lists and csv file is written if specified
    """
    if not query:
        return 'Empty query'
    results = download_all(query,n_results,n_left,n_right,corpus,mode)[:n_results]
    if not results:
        print ('zho_search: nothing found for "%s"' % (query))
    if kwic:
        cols = ['index','left','center','right']
    else:
        results = [[''.join(x)] for x in results]
        cols = ['index','result']
    if write:
        write_results(query,results,cols)
    return results


class TestMethods(unittest.TestCase):
    def test1(self):
        self.assertTrue(parse_page(get_results(query='古代汉',start=0,n=50,lang='xiandai',
                                               mode='simple',n_left=30,n_right=30)))

    def test2(self):
        self.assertIs(list, type(download_all(query='古代汉',results_wanted=10,n_left=30,
                                              n_right=30,lang='xiandai',mode='simple')))
       

if __name__ == '__main__':
    unittest.main()
    args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str)
    parser.add_argument('corpus', type=str)
    parser.add_argument('mode', type=str)
    parser.add_argument('n_results', type=int)
    parser.add_argument('n_left', type=int)
    parser.add_argument('n_right', type=int)
    parser.add_argument('kwic', type=bool)
    parser.add_argument('write', type=bool)
    args = parser.parse_args(args)
    main(**vars(args))
