import lzma
import argparse

# Global Variables
all_communities = set()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB file processed by bgpscanner.", required=True)
    parser.add_argument('-z', '--compressed', dest='compress', help="Enabled read XZ files", action='store_true')
    parser.add_argument('-o', '--output', dest='output', help="Name of output file (default: rib-inferred)")

    args = parser.parse_args()
    rib = args.input
    output = args.output

    if args.compress:
        with lzma.open(rib, "rt") as file_to_process:
            for rib_line in file_to_process:
                rib_line = str(rib_line).strip()
                rib_extraction = rib_line.split('|')

                # Split just prefixes that we are tracking
                comm_list = rib_extraction[7]

                # Save all communities on the RIB
                for comm in comm_list.split(' '):
                    if comm.split(':')[0].isdigit():
                        all_communities.add(comm)
    else:
        with open(rib, "rt") as file_to_process:
            for rib_line in file_to_process:
                rib_extraction = rib_line.split('|')

                # Split just prefixes that we are tracking
                comm_list = rib_extraction[7]

                # Save all communities on the RIB
                for comm in comm_list.split(' '):
                    if comm.split(':')[0].isdigit():
                        all_communities.add(comm)

    # Only save all communities when not load from pickled object
    if output:
        arq = open(output, "wt")
    else:
        arq = open("{}-allcom".format(rib), "wt")
    for comm in all_communities:
        arq.write("{}\n".format(comm))
    arq.close()
