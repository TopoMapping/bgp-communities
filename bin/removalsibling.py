import pickle
import argparse

selected_communities_set = set()
remove_dict = {}


def remove_possible_mistakes(threshold):
    """
    Remove the communities that fault more than threshold times
    :param threshold: limit of times we allow a fault
    """
    local_selected_communities = selected_communities_set.copy()
    for local_comm in local_selected_communities:
        if local_comm in remove_dict:
            if len(remove_dict[local_comm]) >= threshold:
                selected_communities_set.remove(local_comm)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Removal Pickle.", required=True)
    parser.add_argument('-c', '--communities', dest='communities', help="Communities Inferred as Geocomm", required=True)
    parser.add_argument('-m', '--moveout', dest='moveout', help="Threshold limit to remove a sibling", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Name of output file (default: rib-inferred)", required=True)

    args = parser.parse_args()
    input_pickle = args.input
    output_file = args.output
    communities_file = args.communities
    moveout = args.moveout

    # Load inferred communities
    with open(communities_file, "rt") as file_to_process:
        for line in file_to_process:

            # Communities into a SET
            selected_communities_set.add(line.strip())

    # Track for the relations
    with open(input_pickle, "rb") as file_to_process:
        remove_dict = pickle.load(file_to_process)

    # Remove the spurious communities
    remove_possible_mistakes(int(moveout))

    # Output the communities that resist the removal process
    arq = open(output_file, "wt")

    # Save the resulting communities
    for comm in selected_communities_set:
        arq.write("{}\n".format(comm))
    arq.close()
