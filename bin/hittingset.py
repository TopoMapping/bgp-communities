import os
import argparse
from utils import has_loop, has_as_set, canonical_aspath

siblings_relations = {}
all_communities_set = set()
all_communities_dict = {}
remove_dict = {}


def siblings_relationship(file_line):
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    siblings_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        siblings_relations[asn] = first_asn


def validate_non_agregation(as_path, community_list):
    """
    Validate if a community appears when its AS does not follow the siblings relation.

    :param as_path: the ASN path from the announce
    :param community_list: the Community List from the announce
    :return: nothing, just remove the undesired communities from the global set
    """
    if has_as_set(as_path):
        return

    if has_loop(as_path):  # if has loop, that AS-path does not process
        return

    if not community_list:  # do not evaluate announces without communities
        return

    # Rewrite the AS-path with siblings
    local_as_path = []
    canonical_path = canonical_aspath(as_path)
    for temp_asn in canonical_path:
        if temp_asn in siblings_relations:
            local_as_path.append(f"{siblings_relations[temp_asn]}")
        else:
            local_as_path.append(f"{temp_asn}")

    # Check if the community AS is not in the path and was inferred before (phase 02)
    for local_comm in community_list.split(" "):
        if local_comm.split(':')[0].isdigit() and len(local_comm.split(':')) == 2:
            split_asn, split_comm = local_comm.split(':')[0:2]

            # Change the related ASN to its sibling
            if split_asn in siblings_relations:
                split_asn = siblings_relations[split_asn]

            # If the ASN is not on the local_as_path, it is an indicative
            if split_asn not in local_as_path:
                # we are testing all communities, so the local_comm will be in all_communities_set
                if local_comm in all_communities_set:

                    if local_comm in remove_dict:
                        remove_dict[local_comm].append(canonical_path)

                    else:
                        remove_dict[local_comm] = list()
                        remove_dict[local_comm].append(canonical_path)

        else:
            # not numerical community
            pass


def save_community(limit, output):
    for community in remove_dict:
        if len(remove_dict[community]) >= limit:  # remove the only one line
            community_file = open(os.path.join(output, f"{community.replace(':', '-')}"), "wt")
            for as_path in remove_dict[community]:
                community_file.write(f"{' '.join(as_path)}\n")
            community_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB file processed by bgpscanner.", required=True)
    parser.add_argument('-c', '--communities', dest='communities', help="All Communities Inferred as Geocomm", required=True)
    parser.add_argument('-s', '--siblings', dest='siblings', help="Siblings file", required=True)
    parser.add_argument('-l', '--limit', dest='limit', help="Minimal Limit", required=False)
    parser.add_argument('-d', '--directory', dest='directory', help="Output Directory for Set Cover Process", required=True)

    args = parser.parse_args()
    input_file = args.input
    output_directory = args.directory
    siblings_file = args.siblings
    communities_file = args.communities

    if args.limit:
        limit = int(args.limit)
    else:
        limit = 1

    # Load Siblings File
    with open(siblings_file, "rt") as file_to_process:
        for line in file_to_process:
            siblings_relationship(line)

    # Check if the directory exist
    if not os.path.exists(os.path.join(output_directory)):
        os.makedirs(os.path.join(output_directory))

    # Process all communities
    with open(communities_file, "rt") as file_to_process:
        for line in file_to_process:
            split_community = line.strip().split(":")
            if split_community[0].isdigit() and len(split_community) == 2:
                local_asn, local_comm = split_community
                if int(local_asn) not in range(64512, 65536) and\
                        int(local_asn) not in range(4200000000, 4294967295):  # do not add private ASN communities
                    # https://help.apnic.net/s/article/Autonomous-System-numbers

                    # Communities into a SET
                    all_communities_set.add(line.strip())

                    # Communities into a DICT
                    asn, comm = line.strip()[0:2]
                    if asn in all_communities_dict:
                        all_communities_dict[asn].append(comm)
                    else:
                        all_communities_dict[asn] = [comm]

    # Track for the relations
    with open(input_file, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            as_path = rib_extraction[2]
            comm_list = rib_extraction[7]

            validate_non_agregation(as_path, comm_list)

    # Save Community Files with AS-paths
    save_community(limit, output_directory)
