import pickle
import os
import argparse

# Dictionary for communities and k-cover result
remove_dict = {}

def calculate_greedy_hitting_set(input_dir, file):
    all_announces = []
    greedy_strategy = set()

    # Read all announcements
    with open(os.path.join(input_dir, file), "rt") as file_to_process:
        for line in file_to_process:
            all_announces.append(line.strip().split(' '))

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
    parser.add_argument('-i', '--input', dest='input', help="Input Directory with Announces for Community Files", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output Pickle with Setcover Calculated", required=True)

    args = parser.parse_args()
    input_dir = args.input
    output_file = args.output

    for file in os.listdir(input_dir):
        remove_dict[file.replace('-', ':')] = calculate_greedy_hitting_set(input_dir, file)

    # Save the pickle file
    arq = open(output_file, "wb")
    pickle.dump(remove_dict, arq)
    arq.close()
