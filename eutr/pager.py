import math
import json
from urllib import urlencode
from flask import url_for, g

from eutr.core import solr

FILTER_PREFIX = "filter-"

class Pager(object):

    def __init__(self, args, facets=[]):
        self.args = args
        self.page = 1
        try:
            self.page = int(args.get('p'))
        except: pass
        self.limit = 30
        self.facets = facets
        self._results = None

    @property
    def offset(self):
        return (self.page-1)*self.limit
    
    @property
    def pages(self):
        return int(math.ceil(len(self)/float(self.limit)))
    
    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def next_url(self):
        return self.page_url(self.page + 1) if self.has_next \
               else self.page_url(self.page)

    @property
    def prev_url(self):
        return self.page_url(self.page - 1) if self.has_prev \
               else self.page_url(self.page)

    @property
    def params(self):
        return [(k, v.encode('utf-8')) for k, v in self.args.items() \
                if k != 'p']

    def page_url(self, page):
        return url_for('search', p=page, **dict(self.params))

    @property
    def filters(self):
        filters = []
        for k, v in self.params:
            if k.startswith(FILTER_PREFIX):
                filters.append((k, v))
        return filters

    @property
    def fq(self):
        _fq = []
        for k, v in self.filters:
            _fq.append('%s:"%s"' % (k[len(FILTER_PREFIX):], v))
        return _fq

    def filter_url(self, key, value):
        params = self.params
        tp = (FILTER_PREFIX + key, value.encode('utf-8'))
        if tp not in params:
            params.append(tp)
        return url_for('search') + '?' + urlencode(params)

    def unfilter_url(self, key, value):
        p = (FILTER_PREFIX + key, value.encode('utf-8'))
        params = [e for e in self.params if e != p]
        return url_for('search') + '?' + urlencode(params)

    @property
    def q(self): 
        return self.args.get('q', '') 

    @property
    def results(self):
        if self._results is None:
            self._results = self.query()
        return self._results

    def __iter__(self):
        return iter(self.results.get('response', {}).get('docs'))

    def __len__(self):
        return self.results.get('response', {}).get('numFound')

    def facet_values(self, key):
        facets = self.results.get('facet_counts').get('facet_fields')
        _facets = []
        values = facets.get(key + '.s')
        for value in values[::2]:
            count = values[values.index(value)+1]
            _facets.append((value, count))
        return sorted(_facets, key=lambda (a, b): b, reverse=True)

    def query(self, **kwargs):
        data = solr().raw_query(q=self.q or '*:*',
            wt='json', sort='score desc, name desc',
            fq=self.fq,
            facet='true',
            facet_field=[f + '.s' for f in self.facets],
            facet_limit=50,
            rows=self.limit,
            start=self.offset)
        return json.loads(data)


