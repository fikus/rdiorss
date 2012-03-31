import os

from rdio import Rdio

from flask import Flask
from flask import request
from flask import make_response
from flask import Markup

app = Flask(__name__)

key = os.environ['RDIO_CONSUMER_KEY']
secret = os.environ['RDIO_CONSUMER_SECRET']
rdio = Rdio((key, secret))

@app.route('/')
def home():
    return '''
<html>
<form method="GET" action="/search">
  <input type="text" name="q"/>
  <input type="submit" value="Search"/>
</form>
</html>
'''

def rdio_url(url):
    return 'http://www.rdio.com' + url

def item_content(result):
    html = '<img src="%s"/><br/>' % result['icon']
    html = html +'<a href="%s" target="_blank">%s</a>' % (rdio_url(result['url']), result['name'])
    if not result['canStream']:
        if result['canSample']:
            html = html + ' Preview'
        else:
            html = html + ' Not Available'
    html = html + '<br/><a href="%s" target="_blank">%s</a><br/>' % (rdio_url(result['artistUrl']), result['artist'])
    html = html + '<br/><br/>'
    return html

def guid(result):
    guid = result['key']
    if not result['canStream']:
        if result['canSample']:
            guid = guid + '_sample'
        else:
            guid = guid + '_unavailable'
    return guid

def search_rss(query, results):
    text = '''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
'''
    text = text + '<title>%s - Rdio Search Results</title>\n' % query
    text = text + '<description>%s - Rdio Search Results</description>\n' % query
    text = text + '<ttl>10</ttl>\n'

    for result in results:
        text = text + '<item>\n'
        text = text + '<title>%s</title>\n' % result['name']
        text = text + '<description>%s</description>\n' % item_content(result)
        text = text + '<link>%s</link>\n' % rdio_url(result['url'])
        text = text + '<guid>%s</guid>\n' % guid(result)
        text = text + '</item>\n'

    text = text + '''
</channel>
</rss>
'''
    response = make_response(text)
    response.content_type = 'text/xml; charset=utf-8'
    return response

def search_html(query, results):
    s = 'Results for &quot;%s&quot;:<br/><br/>' % query
    s = s + '<img src="http://upload.wikimedia.org/wikipedia/en/thumb/4/43/Feed-icon.svg/16px-Feed-icon.svg.png"/>'
    s = s + ' <a href="/search?q=%s&format=rss">RSS</a><br/><br/>' % query
    for result in results:
        s = s + item_content(result)
    return s

@app.route('/search')
def search():
    query = request.args.get('q', '')
    fmt = request.args.get('format', '')
    types = request.args.get('types', 'Album')
    count = request.args.get('count', 50)
    results = rdio.call('search', {'query': query, 'types': types, 'count': count})['result']['results']
    if fmt == 'rss':
        return search_rss(query, results)
    else:
        return search_html(query, results)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
