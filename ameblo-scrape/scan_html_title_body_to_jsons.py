import os
import sys
import glob
import gzip
import bs4, lxml
import concurrent.futures
import re
from pathlib import Path
import json
import random
import CONFIG
def pmap(arg):
    key, names = arg
    random.shuffle(names)
    for name in names:
        try:
            sha256 = name.split('/')[-1] 
            if Path(name).exists() is False:
                continue
            if Path(f'jsons_content/{sha256}').exists():
                open(name, 'wb').write(gzip.compress(bytes('finished', 'utf8')))
                #print('already processed', name)
                continue
            html = gzip.decompress(open(name, 'rb').read()).decode()
            soup = bs4.BeautifulSoup(html, 'lxml')
            for script in soup(["script", "style"]):
                script.extract()    # rip it out

            article = soup.find('article')
            if article is None:
                Path(name).unlink()
                continue
            titles = [article.h1, article.h2] 
            if titles == [None, None]:
                continue
            title = [t for t in [t.text for t in titles if t is not None] if t not in ['SNSアカウント']]
            title = ' '.join(title)
            canonical = soup.find('link', {'rel':'canonical'})
            if canonical is None:
                Path(name).unlink()
                continue
            if 'archive-' in canonical.get('href') or \
                    'theme-' in canonical.get('href'):
                Path(name).unlink()
                continue
            print(canonical.get('href'))

            time = soup.time.get('datetime')
            body = soup.find('div', {'id':'entryBody'})
            if body is None:
                Path(name).unlink()
                continue
            body = body.text.replace('\n', ' ')
            body = re.sub(r'\s{1,}', ' ', body)
            record = {'title':title, 'canonical':canonical.get('href'), 'time':time, 'body':body, 'sha256':sha256}
            with open(f'jsons_content/{sha256}', 'w') as fp:
                fp.write(json.dumps(record, indent=2, ensure_ascii=False))
            if random.random() <= 0.05:
                print(record)
            open(name, 'wb').write(gzip.compress(bytes('finished', 'utf8')))
        except Exception as ex:
            #Path(name).unlink()
            print(ex)

def main():
    args = {}
    for index,name in enumerate(glob.glob( CONFIG.HTML_PATH +'/*')):
        key = index % 32
        if args.get(key) is None:
            args[key] = []
        args[key].append(name)
    args = [(key,names) for key, names in args.items()]
    with concurrent.futures.ProcessPoolExecutor(max_workers=32) as exe:
      exe.map(pmap, args)

if __name__ == '__main__':
    if '--loop' in sys.argv:
        while True:
            main()
    else:
        main()
