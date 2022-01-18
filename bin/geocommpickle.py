import lzma
import pickle
import argparse
from utils import has_loop, has_as_set, canonical_aspath, build_relation

# Global Variables
all_communities = set()
geo_structure = {}
geo_structure_extra = {}
as_relation = {}
siblings_relations = {}


def siblings_relationship(file_line):
    """
    Read each line of a sibling file and fullfill the global siblings_relations dict
    """
    # relations for O(constant)
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    siblings_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        siblings_relations[asn] = first_asn


def high_prob_geolocation_communities(as_path, comm_list, router_ip, phase_two, lookahead=1):
    """
    Fullfill the structure geo_code_structure with the information about communities
    on each announcement on the RIB file

    :param as_path: as_path, list of ASN's, from the announce
    :param comm_list: community list from the announce
    :param router_ip:  the IP of the router that share the information with the collector
    :param lookahead: ASN after the target ASN
    """

    if has_as_set(as_path):
        return

    if has_loop(as_path):  # if has loop, that AS-path does not process
        return

    # Rewrite the AS-path with siblings
    # local_as_path = canonical_aspath(as_path)
    local_as_path = []
    canonical_path = canonical_aspath(as_path)
    for temp_asn in canonical_path:
        if temp_asn in siblings_relations:
            local_as_path.append(f"{siblings_relations[temp_asn]}")
        else:
            local_as_path.append(f"{temp_asn}")

    if len(local_as_path) < 2 + lookahead:  # impossible to evaluate short AS-paths
        return

    # Split the community list
    local_comm_list = comm_list.split(' ')

    # First phase: match the advanced key
    for target in local_as_path[0: -1 - lookahead]:  # control the end limit to avoid array explosion
        temporary_list = list(local_as_path[0:local_as_path.index(target) + 1 + lookahead])
        temporary_list.insert(0, router_ip)
        key = tuple(temporary_list)

        if key in geo_structure:
            geo_structure[key][0] += 1  # increment the number of key occurrences
            geo_structure[key][2].add(local_as_path[-1])  # add the origin to the set

            # Update the non occurrences of communities
            for community in geo_structure[key][1]:
                if community not in local_comm_list:  # if the community do not appear, count negatively
                    asn_part = community.split(':')[0]

                    # Change for the sibling to match correctly
                    if asn_part in siblings_relations:
                        asn_part = siblings_relations[asn_part]

                    if target == asn_part:
                        geo_structure[key][1][community][1] += 1  # increment the non occurrence

            # Update the occurrences of communities
            for community in local_comm_list:
                if len(community.split(':')) != 2:  # avoid large communities
                    continue

                asn_part = community.split(':')[0]

                # Change for the sibling to match correctly
                if asn_part in siblings_relations:
                    asn_part = siblings_relations[asn_part]

                if target == asn_part:
                    if community in geo_structure[key][1]:
                        geo_structure[key][1][community][0] += 1  # increment the occurrence
                    else:
                        geo_structure[key][1][community] = [1, geo_structure[key][0] - 1]
        else:
            # the key doesn't exist, need to create the structure
            # counter, community dict, origins
            geo_structure[key] = [1, {}, set()]  # create the reference key with occurrence number
            geo_structure[key][2].add(local_as_path[-1])

            for community in local_comm_list:
                asn_part = community.split(':')[0]

                if target == asn_part:
                    geo_structure[key][1][community] = [1, 0]

    # Phase 2: T+n near to origin
    if phase_two:
        for target in local_as_path[-1 - lookahead: -2]:  # avoid T+0 removing the element
            for i in range(1, len(local_as_path[local_as_path.index(target):]) - 1):
                temporary_list = list(local_as_path[0:-i])
                temporary_list.insert(0, router_ip)
                temporary_list.append(target)  # avoid duplications
                key = tuple(temporary_list)

                if key in geo_structure_extra:
                    geo_structure_extra[key][0] += 1  # increment the number of key occurrences
                    geo_structure_extra[key][2].add(local_as_path[-1])

                    # Update the non occurrences of communities
                    for community in geo_structure_extra[key][1]:
                        if community not in local_comm_list:  # if the community do not appear, count negatively
                            asn_part = community.split(':')[0]

                            # Change for the sibling to match correctly
                            if asn_part in siblings_relations:
                                asn_part = siblings_relations[asn_part]

                            if target == asn_part:
                                geo_structure_extra[key][1][community][1] += 1  # increment the non occurrence

                    for community in local_comm_list:
                        asn_part = community.split(':')[0]

                        # Change for the sibling to match correctly
                        if asn_part in siblings_relations:
                            asn_part = siblings_relations[asn_part]

                        if target == asn_part:
                            if community in geo_structure_extra[key][1]:
                                geo_structure_extra[key][1][community][0] += 1  # increment the occurrence
                            else:
                                geo_structure_extra[key][1][community] = [1, geo_structure_extra[key][0] - 1]
                else:
                    # the key doesn't exist, need to create the structure
                    geo_structure_extra[key] = [1, {}, set()]  # reference key with occur number
                    geo_structure_extra[key][2].add(local_as_path[-1])

                    for community in local_comm_list:
                        asn_part = community.split(':')[0]

                        # Change for the sibling to match correctly
                        if asn_part in siblings_relations:
                            asn_part = siblings_relations[asn_part]

                        if target == asn_part:
                            geo_structure_extra[key][1][community] = [1, 0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB/Pickle file processed by bgpscanner.", required=True)
    parser.add_argument('-d', '--deep', dest='lookahead', help="How deep search after target ASN. E.g.: -d 1", required=True)
    parser.add_argument('-r', '--relation', dest='relation', help="CAIDA AS Relationship", required=False)
    parser.add_argument('-m', '--minimum-origin', dest='origin', help="Minimal ASN origin number. Default=1.")
    parser.add_argument('-z', '--compressed', dest='compress', help="Enabled read XZ files", action='store_true')
    parser.add_argument('-a', '--approach', dest='approach', help="Approach the origin (phase 2)", action='store_true')
    parser.add_argument('-o', '--output', dest='output', help="Name of output file (default: rib-inferred)")

    args = parser.parse_args()
    rib = args.input
    lookahead = args.lookahead
    relation = args.relation
    approach = args.approach
    compressed = args.compress
    output = args.output

    # Check the minimal number of origin ASNs
    if args.origin:
        minimum_origin = int(args.origin)
    else:
        minimum_origin = 0

    # Load Siblings File
    with open("bin/geocom/caidasiblings", "rt") as file_to_process:
        for line in file_to_process:
            siblings_relationship(line)

    if relation:
        # Build the relation structure
        with open(relation, "rt") as file_to_process:
            for relation_line in file_to_process:
                if '#' in relation_line:
                    continue
                else:
                    temp_relation = build_relation(relation_line)

                    for i in temp_relation.keys():  # add one or two relations based on ASN relationship
                        as_relation[i] = temp_relation[i]

    if compressed:
        with lzma.open(rib, "rt") as file_to_process:
            for rib_line in file_to_process:
                rib_line = str(rib_line).strip()
                rib_extraction = rib_line.split('|')

                # Split just prefixes that we are tracking
                as_path = rib_extraction[2]
                comm_list = rib_extraction[7]
                router_ip = rib_extraction[8].split(' ')[0]

                if approach:
                    high_prob_geolocation_communities(as_path, comm_list, router_ip, lookahead=int(lookahead),
                                                      phase_two=True)
                else:
                    high_prob_geolocation_communities(as_path, comm_list, router_ip, lookahead=int(lookahead),
                                                      phase_two=False)
    else:
        with open(rib, "rt") as file_to_process:
            for rib_line in file_to_process:
                rib_extraction = rib_line.split('|')

                # Split just prefixes that we are tracking
                as_path = rib_extraction[2]
                comm_list = rib_extraction[7]
                router_ip = rib_extraction[8].split(' ')[0]

                if approach:
                    high_prob_geolocation_communities(as_path, comm_list, router_ip, phase_two=True,
                                                      lookahead=int(lookahead))
                else:
                    high_prob_geolocation_communities(as_path, comm_list, router_ip, phase_two=False,
                                                      lookahead=int(lookahead))

    # Save the pickle file for the processed file
    if output:
        arq = open(output, "wb")
    else:
        if approach:
            arq = open("{}-{}-a.pkl".format(rib, lookahead), "wb")
        else:
            arq = open("{}-{}.pkl".format(rib, lookahead), "wb")

    # Save the structures
    pickle.dump(geo_structure, arq)
    if approach:
        pickle.dump(geo_structure_extra, arq)  # need to save the extra structure for load later

    arq.close()



