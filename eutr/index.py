from pprint import pprint
from eutr import model
from eutr.core import solr

def flatten(data, sep='.'):
    _data = {}
    for k, v in data.items():
        if isinstance(v, dict):
            for ik, iv in flatten(v, sep=sep).items():
                _data[k + sep + ik] = iv
        elif isinstance(v, (list, tuple)):
            for iv in v:
                if isinstance(iv, dict):
                    for lk, lv in flatten(iv, sep=sep).items():
                        key = k + sep + lk
                        if key in _data:
                            if not isinstance(_data[key], set):
                                _data[key] = set([_data[key]])
                            if isinstance(lv, set):
                                _data[key].union(lv)
                            else:
                                _data[key].add(lv)
                        else:
                            _data[key] = lv
                else:
                    _data[k] = v
                    break
        else:
            _data[k] = v
    return _data

def index():
    solr_ = solr()
    buf = []
    for i, org in enumerate(model.db.session.query(model.Organisation)):
        data = flatten(org.as_dict())
        #pprint(data)
        for k, v in data.items():
            #data[k + '.n'] = v
            data[k + '.s'] = v
        data['id'] = org.id
        buf.append(data)
        if i and i % 1000 == 0:
            print "%s ... " % i
            solr_.add_many(buf)
            solr_.commit()
            buf = []
    solr_.add_many(buf)
    solr_.commit()


if __name__ == '__main__':
    index()





