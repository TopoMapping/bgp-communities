import pickle
import argparse

# Global Variables
all_communities = set()
geo_structure = {}
geo_structure_extra = {}
as_relation = {}


def calculate_geo_communities(threshold_limit, minimal_origin=1, phase_two=False, phase_three=False):
    """
    Calculate the correlation of the number of occurrences of each community and the key
    associated with it.
    """
    local_geo_communities = set()

    for key in geo_structure:
        if not len(geo_structure[key][2]) >= minimal_origin:
            continue

        for key_comm in geo_structure[key][1]:
            appeared = geo_structure[key][1][key_comm][0]
            not_appeared = geo_structure[key][1][key_comm][1]

            if appeared > 1:
                if float(appeared) / float((appeared + not_appeared)) >= threshold_limit:
                    local_geo_communities.add(key_comm)

    # Phase 2: T+n near to origin
    if phase_two:
        for key in geo_structure_extra:
            if not len(geo_structure_extra[key][2]) >= minimal_origin:
                continue

            for key_comm in geo_structure_extra[key][1]:
                appeared = geo_structure_extra[key][1][key_comm][0]
                not_appeared = geo_structure_extra[key][1][key_comm][1]

                if appeared > 1:
                    if float(appeared) / float((appeared + not_appeared)) >= threshold_limit:
                        local_geo_communities.add(key_comm)

    # Phase 3: validate the rule customer and peer
    if phase_three:
        local_geo_comm_view = {}

        # Map all keys related to communities
        for key in geo_structure:
            for comm in geo_structure[key][1]:
                if comm in local_geo_communities and comm not in local_geo_comm_view:
                    local_geo_comm_view[comm] = [key]
                elif comm in local_geo_communities:
                    local_geo_comm_view[comm].append(key)

        # Check
        local_valid_communities = set()
        for key in local_geo_comm_view:
            if len(key.split(":")) != 2:  # avoid large communities
                continue
            key_as, key_comm = key.split(":")[0:2]
            relation_client = False
            relation_peer = False

            for keys_comm in local_geo_comm_view[key]:
                relation_test = (key_as, keys_comm[keys_comm.index(key_as) + 1])

                if relation_test in as_relation:
                    if as_relation[relation_test] == 0:
                        relation_peer = True
                    elif as_relation[relation_test] == -1:
                        relation_client = True
                else:
                    # consider as peer
                    relation_peer = True

            if relation_peer and relation_client:
                local_valid_communities.add(key)

        local_geo_communities = local_valid_communities

    return local_geo_communities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Pickle file processed by geocommpickle.py.", required=True)
    parser.add_argument('-d', '--deep', dest='deep', help="How deep search after target ASN. E.g.: -d 1", required=True)
    parser.add_argument('-m', '--minimum-origin', dest='origin', help="Minimal ASN origin number.", required=True)
    parser.add_argument('-o', '--output_dir', dest='output', help="Output Directory.", required=True)
    parser.add_argument('-r', '--relation', dest='relation', help="CAIDA AS Relationship", required=False)
    parser.add_argument('-a', '--approach', dest='approach', help="Approach the origin (phase 2)", action='store_true')

    args = parser.parse_args()
    rib = args.input
    deep = args.deep
    origin = args.origin
    output_dir = args.output
    approach = args.approach
    relation = args.relation

    # Check the minimal number of origin ASNs
    if origin:
        minimum_origin = int(args.origin)
    else:
        minimum_origin = 0

    # Load the pickle file to memory
    with open(rib, "rb") as file_to_process:
        geo_structure = pickle.load(file_to_process)
        if approach:
            geo_structure_extra = pickle.load(file_to_process)

    # Save the Results
    phase_two = False
    phase_three = False

    if approach:
        phase_two = True

    if relation:
        phase_three = True

    # Calc the communities
    for threshold in range(1, 10):
        threshold = float(threshold / 10.0)

        geo_communities = calculate_geo_communities(threshold_limit=threshold, minimal_origin=minimum_origin,
                                                    phase_two=phase_two, phase_three=phase_three)

        rib_name = rib.split('/')[-1]
        rib_name = rib_name.split('-')[0]

        output_name = output_dir + "{}-geocom-{}-c{}".format(rib_name, deep, threshold)
        output_name += "-o{}".format(origin)

        arq = open(output_name, "wt")
        for comm in geo_communities:
            arq.write("{}\n".format(comm))
        arq.close()
