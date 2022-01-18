import pickle
import os
import argparse

# Dictionary for communities and k-cover result
remove_dict = {}
siblings_relations = {}


def siblings_relationship(file_line):
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    siblings_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        siblings_relations[asn] = first_asn


def remove_as_and_siblings_before(input_dir, file):
    # Remove the announces with AS or its siblings from the file before compute the set
    all_announces = []
    non_impacted_announces = []
    asn, comm = file.split('-')

    if asn in siblings_relations:
        asn = siblings_relations[asn]

    # Read all announcements
    with open(os.path.join(input_dir, file), "rt") as file_to_process:
        for line in file_to_process:
            all_announces.append(line.strip().split(' '))

    # Remove any announcement that the AS or sibbling appear
    for as_path in all_announces:
        status = True
        for asn_in_path in as_path:
            if asn_in_path in siblings_relations:
                asn_in_path = siblings_relations[asn_in_path]

            if asn_in_path == asn:
                status = False
                break
        # If the AS or sibling is not inside the path, add the path
        if status:
            non_impacted_announces.append(as_path)

    # Save it back, removing the old file and creating a new one
    os.remove(os.path.join(input_dir, file))
    with open(os.path.join(input_dir, file), "wt") as file_to_process:
        for line in non_impacted_announces:
            file_to_process.write(f"{' '.join(line)}\n")


def calculate_greedy_hitting_set(input_dir, file):
    all_announces = []
    greedy_strategy = set()

    # Read all announcements
    with open(os.path.join(input_dir, file), "rt") as file_to_process:
        for line in file_to_process:
            all_announces.append(line.strip().split(' '))

    # If the file goes empty because of remove_as_and_siblings_before, the minimum hitting set is 0
    if len(all_announces) == 0:
        return 0

    while len(all_announces):
        counting = {}
        # Count the ocurrences of the ASNs on announcements
        for each_announce in all_announces:
            for asn in each_announce:
                if asn in counting:
                    counting[asn] += 1
                else:
                    counting[asn] = 1

        # Order on reverse order of ocurrence
        counting_desc_list = [value for value in reversed(sorted(counting.items(), key=lambda item: item[1]))]

        # Check if the next ASN have same occurrence and chose the lower ASN
        chosen_asn = 0
        big_occurrence = counting_desc_list[0][1]
        for option in range(len(counting_desc_list)-1):
            if counting_desc_list[option][1] == counting_desc_list[option+1][1]\
                    and counting_desc_list[option][1] == big_occurrence:
                if int(counting_desc_list[option][0]) > int(counting_desc_list[option+1][0]):
                    chosen_asn = option+1

        removed_as = counting_desc_list.pop(chosen_asn)[0]
        greedy_strategy.add(removed_as)

        temp_all_announces = all_announces.copy()
        for each_announce in temp_all_announces:
            for asn in greedy_strategy:
                if asn in each_announce:
                    all_announces.remove(each_announce)

    return greedy_strategy


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_dir', dest='input_dir', help="Input Directory with Announces for Community Files",
                        required=True)
    parser.add_argument('-c', '--community', dest='community',
                        help="Community File",
                        required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output Inferred Pickle with Setcover Calculated",
                        required=True)

    args = parser.parse_args()

    input_dir = args.input_dir
    output_file = args.output
    communities_file = args.community

    # Load Inferred Communities File
    with open(communities_file, "rt") as file_to_process:
        for line in file_to_process:
             remove_dict[line.strip()] = set()

    # Get all directories to walk inside
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if str(file.replace('-', ':')) in remove_dict:
                hitting_set = calculate_greedy_hitting_set(root, file)
                remove_dict[file.replace('-', ':')] = remove_dict[file.replace('-', ':')].union(hitting_set)

    # Save the pickle file
    arq = open(output_file, "wb")
    pickle.dump(remove_dict, arq)
    arq.close()
