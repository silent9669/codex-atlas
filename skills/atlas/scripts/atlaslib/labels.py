"""Automatic document labels and explicit reviewed overrides, stored beside the graph."""
import json
import re
from . import evidence

TOPICS = {
    'ai': r'grounding|citation|llm|openai|lớp ai|kiểm số|prompt',
    'api': r'api/|endpoint|openapi|giao thức',
    'data': r'ingest|dataset|schema|warehouse|dữ liệu|ánh xạ',
    'frontend': r'frontend|giao diện|react|tsx|city chat|ui/ux',
    'security': r'authentication|permission|bảo mật|phân quyền|pii',
    'verification': r'acceptance|kiểm thử|pytest|vitest|regression|nghiệm thu',
    'operations': r'deploy|runbook|triển khai|cloudflare|ci/cd',
}
KINDS = {'decision','plan','runbook','reference','overview','prompt','working-doc','document'}


def automatic(path, text, kind):
    source = path.lower()+'\n'+text[:20000].lower()
    topics = [name for name, pattern in TOPICS.items() if re.search(pattern,source)]
    first_lines='\n'.join(text.splitlines()[:30]).lower()
    status='unclassified'
    for name, pattern in [('superseded',r'(?m)^(?:status|trạng thái)\s*[:|].*(?:superseded|thay thế|deprecated)'),
                          ('approved',r'(?m)^(?:status|trạng thái)\s*[:|].*(?:approved|đã duyệt|accepted)'),
                          ('draft',r'(?m)^(?:status|trạng thái)\s*[:|].*(?:draft|proposed|đề xuất|nháp)')]:
        if re.search(pattern,first_lines): status=name;break
    return {'kind':kind,'topics':topics[:5] or ['general'],'status':status,'origin':'rule-inferred','category':kind.replace('-', ' ').title(),'category_origin':'rule-inferred'}


def apply(root, documents):
    folder=evidence.storage(root)
    path=folder/'document-labels.json'
    previous=json.loads(path.read_text()) if path.exists() and not path.is_symlink() else {}
    labels={}
    for document in documents:
        source=root/document['path']
        label=automatic(document['path'],source.read_text(errors='replace'),document['type'])
        override=previous.get(document['path'],{})
        if override.get('origin')=='human-confirmed':
            label={k:override.get(k,label[k]) for k in label}
            label['freshness']='current' if override.get('content_hash')==document['content_hash'] else 'stale'
        if override.get('category_origin') in {'model-inferred', 'human-confirmed'}:
            for field in ('category', 'category_origin', 'category_hash'):
                if field in override: label[field] = override[field]
            label['category_freshness'] = 'current' if label.get('category_hash') == document['content_hash'] else 'stale'
        label.update(content_hash=override.get('content_hash') if override.get('origin')=='human-confirmed' else document['content_hash'])
        document['labels']=label
        labels[document['path']]=label
    evidence.write_json(path,labels)
    return labels


def set_label(root, graph, path, kind=None, topics=None, status=None, category=None):
    if not isinstance(path,str): raise ValueError('Document path must be a string.')
    if path not in graph['snapshot']['files'] or not path.lower().endswith(('.md','.mdx','.txt')):
        raise ValueError('Only indexed text documents can be labeled.')
    folder=evidence.storage(root);file=folder/'document-labels.json'
    if file.is_symlink(): raise ValueError('Refusing symlinked label store.')
    labels=json.loads(file.read_text()) if file.exists() else {}
    value=labels.get(path,{'kind':'document','topics':['general'],'status':'unclassified'})
    if kind is not None:
        if not isinstance(kind,str) or kind not in KINDS: raise ValueError('Unsupported document kind.')
        value['kind']=kind
    if topics is not None:
        if not isinstance(topics,list) or not 1<=len(topics)<=5 or any(not isinstance(t,str) or not re.fullmatch(r'[a-z0-9-]{1,32}',t) for t in topics):raise ValueError('Use 1–5 short lowercase topic labels.')
        value['topics']=topics
    if status is not None:
        if not isinstance(status,str) or status not in {'unclassified','draft','approved','superseded','needs-review'}:raise ValueError('Unsupported status label.')
        value['status']=status
    if category is not None:
        if not isinstance(category,str) or not re.fullmatch(r'[\w][\w &/\-]{0,47}',category): raise ValueError('Use a category name of 1–48 letters, numbers, spaces or separators.')
        value.update(category=category,category_origin='human-confirmed',category_hash=graph['snapshot']['files'][path],category_freshness='current')
    value.update(origin='human-confirmed',content_hash=graph['snapshot']['files'][path],freshness='current')
    labels[path]=value;evidence.write_json(file,labels)
    return {'kind':'label','path':path,'labels':value}
