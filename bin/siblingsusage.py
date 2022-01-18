import argparse
from utils import has_loop, has_as_set, canonical_aspath

siblings_relations = {}
as_sibling_usage = {}


def siblings_relationship(file_line):
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    siblings_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        siblings_relations[asn] = first_asn


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB file processed by bgpscanner.", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Name of output file", required=True)

    args = parser.parse_args()
    rib = args.input
    output_file = args.output

    # Load Siblings File
    with open("bin/geocom/caidasiblings", "rt") as file_to_process:
        for line in file_to_process:
            siblings_relationship(line)

    # Read RIB and track for siblings using the AS community
    with open(rib, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            as_path = rib_extraction[2]
            comm_list = rib_extraction[7]

            if has_as_set(as_path):
                continue

            if has_loop(as_path):  # if has loop, that AS-path does not process
                continue

            # Rewrite the AS-path with siblings
            local_as_path = []
            canonical_path = canonical_aspath(as_path)

            for comm in comm_list.split(' '):
                split_community = comm.strip().split(":")
                if split_community[0].isdigit() and len(split_community) == 2:
                    asn_comm, comm_number = split_community

                    # The ASN of community is in the AS-path
                    if asn_comm in canonical_path:
                        # it's there, no need to check for sibling
                        continue
                    else:
                        # recreate the AS-path with siblings
                        for temp_asn in canonical_path:
                            if temp_asn in siblings_relations:
                                local_as_path.append(f"{siblings_relations[temp_asn]}")
                            else:
                                local_as_path.append(f"{temp_asn}")

                        if asn_comm in local_as_path:
                            if asn_comm in as_sibling_usage:
                                as_sibling_usage[asn_comm] += 1
                            else:
                                as_sibling_usage[asn_comm] = 1

    # Save the output
    arq = open(output_file, "wt")

    for asn_local in as_sibling_usage:
        arq.write(f"{asn_local}:{as_sibling_usage[asn_local]}\n")
    arq.close()
