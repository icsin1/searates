from os.path import join, dirname


def prepare_group(record, domain, format_dict, fields,  groupby=False, limit=10, offset=0, sort='Count', **kwargs):
    tableData = []
    groupby = groupby or [field.split(':')[0] for field in fields]
    for line in record.with_context(**kwargs.get('context', {})).read_group(domain, fields, groupby, lazy=False):
        value_line = {}
        for key, value in format_dict.items():
            value = value(line) if callable(value) else line.get(value)
            value_line[key] = value
        value_line['__domain'] = line.get('__domain', [])
        tableData.append(value_line)
    tableData.sort(key=lambda x: x[sort], reverse=True)
    if kwargs.get('context') and kwargs.get('context').get('download'):
        return tableData
    return tableData[offset:limit]


def get_version_info():
    values = {}
    exec(open(join(dirname(__file__), 'release.py'), 'rb').read(), globals(), values)
    return values
