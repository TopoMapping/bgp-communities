import argparse

# Global Variables
allcomm = {}
all_communities = set()

# Main
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB file processed by bgpscanner.", required=True)
    parser.add_argument('-c', '--comm', dest='comm', help="Community File", required=True)
    args = parser.parse_args()

    rib = args.input
    community = args.comm

    # Read all communities from RIB
    with open(args.comm, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_line = rib_line.strip()
            if rib_line not in allcomm:
                allcomm[rib_line] = [0, set()]

    # Read all communities from RIB
    with open(rib, "rt") as file_to_process:
        for rib_line in file_to_process:

            rib_extraction = rib_line.split('|')

            origin = rib_extraction[2].split(' ')[-1]
            comm_list = rib_extraction[7].split(' ')

            # For number of origins for that community
            for comm in comm_list:
                if comm in allcomm:
                    allcomm[comm][0] += 1
                    allcomm[comm][1].add(origin)

    # Output results
    for i in list(range(1, 10)):
        arq = open("{}-o{}".format(community, i), 'wt')
        for j in allcomm:
            if len(allcomm[j][1]) >= i:
                arq.write("{}\n".format(j))
        arq.close()

