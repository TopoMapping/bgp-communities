def has_loop(path):
    status = False

    local_path = path.split(' ')

    if len(local_path) < 3:
        return False

    for i in range(len(local_path) - 2):
        if local_path[i] in local_path[i + 2:]:
            if local_path[i] != local_path[i + 1]:
                status = True

    return status


def canonical_aspath(path):
    local_path = path.split(' ')
    canonical = []

    for asn in local_path:
        if asn not in canonical:
            canonical.append(asn)

    return canonical


def has_as_set(path):
    status = False

    if '{' in path:
        status = True

    return status


def build_relation(relation):
    asn_rel = {}
    asn1, asn2, value = relation.split('|')[:3]

    if value == '0':
        asn_rel[(asn1, asn2)] = 0
        asn_rel[(asn2, asn1)] = 0
    else:
        asn_rel[(asn1, asn2)] = -1

    return asn_rel
