import os
import csv
import argparse
import sqlite3
from sqlite3 import Error


# Database Connection
def database_connection(dbfile):
    connection = None
    try:
        connection = sqlite3.connect(dbfile)
    except Error as exception:
        print(exception)

    return connection


def fetch_sql(connection, sql_statement):
    cursor = connection.cursor()
    cursor.execute(sql_statement)
    rows = []

    # Return a list
    for row in cursor.fetchall():
        rows.append(row[0])

    return rows


# Global Variables
caida_geo_dict = {}  # key = asn, content = [] list of communities
caida_geo_set = set()
tier_with_comms_set = set()

geolocation_dict = {}
geolocation_set = set()


def statistical_calc(db,
                     tier_to_select,
                     filename,
                     all_comm,
                     all_comox):

    inferred_communities_dict = {}
    inferred_with_known_set = set()
    inferred_but_not_mapped = set()

    # Inferred communities
    inferred_communities_file = open(filename, 'rt')

    # Build dict for inferred communities and add to set
    for line in inferred_communities_file.readlines():
        tmp_comm = line.strip()
        if len(tmp_comm.split(':')) == 2:  # ignore large communities and named communities
            asn, comm = tmp_comm.split(':')[0:2]
        else:
            continue

        if asn not in inferred_communities_dict:
            inferred_communities_dict[asn] = set()
            inferred_communities_dict[asn].add(comm)
        else:
            inferred_communities_dict[asn].add(comm)

    # Inferred & ASN Tier with Geo and are known
    inferred_and_tier_with_geo = 0
    for asn_comm in inferred_communities_dict:
        if asn_comm in tier_with_comms_set:

            known_community_counter = 0
            for tmp_comm in inferred_communities_dict[asn_comm]:
                # Inferred Geo T1 Communities Set and are known
                built_community = f"{asn_comm}:{tmp_comm}"

                if fetch_sql(db, f"select name from community where "
                                 f"name = \"{built_community}\" and "
                                 f"{tier_to_select}"):
                    inferred_with_known_set.add(built_community)
                    known_community_counter += 1
                else:
                    inferred_but_not_mapped.add(built_community)
            inferred_and_tier_with_geo += known_community_counter

    # Read all communities
    all_communities_set = set()
    all_communities_file = open(all_comm, 'rt')

    for line in all_communities_file.readlines():
        if len(line.split(':')) == 2:
            all_communities_set.add(line.strip())

    # Read all communities with origins limit
    all_communities_ox_set = set()
    all_communities_ox_file = open(all_comox, 'rt')

    for line in all_communities_ox_file.readlines():
        if len(line.split(':')) == 2:
            all_communities_ox_set.add(line.strip())

    # AllCom & Tier1 with Geo
    allcom_and_tier_with_com = set()
    for comm in all_communities_set:
        if len(comm.split(':')) == 2:   # avoid large communities
            local_asn, local_comm = comm.split(':')[0:2]
            if local_asn in tier_with_comms_set:
                allcom_and_tier_with_com.add(comm)

    # AllCom & My Geo (Ground Truth)
    allcom_and_mygeo = set()
    for comm in all_communities_set:
        if comm in geolocation_set:
            allcom_and_mygeo.add(comm)

    # AllComOx & Tier1 with Geo
    allcomOx_and_tier_with_com = set()
    for comm in all_communities_ox_set:
        local_asn, local_comm = comm.split(':')[0:2]  # avoid large communities
        if local_asn in tier_with_comms_set:
            allcomOx_and_tier_with_com.add(comm)

    # AllComOx & My Geo (Ground Truth)
    allcomOx_and_mygeo = set()
    for comm in all_communities_ox_set:
        if comm in geolocation_set:
            allcomOx_and_mygeo.add(comm)

    # AllCom & Tier with Geo & Caida
    allcom_and_tier_with_and_caida_com = allcom_and_tier_with_com.intersection(caida_geo_set)

    # AllCom & My Geo Tier & Caida
    allcom_and_mygeo_and_caida = allcom_and_mygeo.intersection(caida_geo_set)

    # AllComOx & Tier & Caida
    allcomOx_and_tier_with_and_caida_com = allcomOx_and_tier_with_com.intersection(caida_geo_set)

    # AllComOx & Geo Tier & Caida
    allcomOx_and_mygeo_and_caida = allcomOx_and_mygeo.intersection(caida_geo_set)

    # AllComOx & Tier with Geo & Inference with known geo community
    allcomOx_and_tier_with_and_inferred_com = allcomOx_and_tier_with_com.intersection(inferred_with_known_set)

    # AllComOx & Geo Tier & Inference with known geo community
    allcomOx_and_mygeo_and_inferred = allcomOx_and_mygeo.intersection(inferred_with_known_set)

    # total = allcom_and_mygeo
    # allcom_and_mygeo_and_caida
    #
    # TP: allcom_and_mygeo_and_caida
    # TN: (all communities from caida are inferred as geo)
    # FN: allcom_and_mygeo - allcom_and_mygeo_and_caida
    # FP: allcom_and_tier_with_caida_com - allcom_and_mygeo_and_caida
    #
    # recall = TP / (TP + FN)
    # precision = TP / (TP + FP)

    # Caida Recall
    if len(allcom_and_mygeo) != 0:
        caida_recall = round(float(len(allcom_and_mygeo_and_caida) / len(allcom_and_mygeo)), 2)
    else:
        caida_recall = 0

    # Caida Precision
    if len(allcom_and_tier_with_and_caida_com) != 0:
        caida_precision = round(float(len(allcom_and_mygeo_and_caida) / len(allcom_and_tier_with_and_caida_com)), 2)
    else:
        caida_precision = 0

    # Caida F1_Score
    if caida_recall == 0 and caida_precision == 0:
        caida_f1 = 0
    else:
        caida_f1 = round(2 * ((caida_precision * caida_recall) / (caida_precision + caida_recall)), 2)

    # CRecallOx
    if len(allcomOx_and_mygeo) != 0:
        caidaOx_recall = round(float(len(allcomOx_and_mygeo_and_caida) / len(allcomOx_and_mygeo)), 2)
    else:
        caidaOx_recall = 0

    # CPrecisionOx
    if len(allcomOx_and_tier_with_and_caida_com) != 0:
        caidaOx_precision = round(float(len(allcomOx_and_mygeo_and_caida) / len(allcomOx_and_tier_with_and_caida_com)), 2)
    else:
        caidaOx_precision = 0

    # CF1_ScoreOx
    if caidaOx_recall == 0 and caidaOx_precision == 0:
        caidaOx_f1 = 0
    else:
        caidaOx_f1 = round(2 * ((caidaOx_precision * caidaOx_recall) / (caidaOx_precision + caidaOx_recall)), 2)

    # total = allcom_and_mygeo
    # allcom_and_mygeo_and_caida
    #
    # TP: allcom_and_mygeo_and_inferred
    # TN:
    # FN: allcom_and_mygeo - allcom_and_mygeo_and_inferred
    # FP: allcom_and_tier_with_and_inferred_com - allcom_and_mygeo_and_inferred
    #
    # recall = TP / (TP + FN)
    # precision = TP / (TP + FP)

    # Inferred Recall
    if len(allcomOx_and_mygeo) != 0:
        inferred_recall = round(float(len(allcomOx_and_mygeo_and_inferred) / len(allcomOx_and_mygeo)), 2)
    else:
        inferred_recall = 0

    # Inferred Precision
    if len(allcomOx_and_tier_with_and_inferred_com) != 0:
        inferred_precision = round(float(len(allcomOx_and_mygeo_and_inferred) / len(allcomOx_and_tier_with_and_inferred_com)), 2)
    else:
        inferred_precision = 0

    # Inferred F1_Score
    if inferred_recall == 0 and inferred_precision == 0:
        inferred_f1 = 0
    else:
        inferred_f1 = round(2 * ((inferred_precision * inferred_recall) / (inferred_precision + inferred_recall)), 2)

    # Unknown
    unknown = len(inferred_but_not_mapped)

    # Baseline Precision
    if len(allcom_and_tier_with_com) != 0:
        baseline_precision = round((float(len(allcom_and_mygeo)) / len(allcom_and_tier_with_com)), 2)
    else:
        baseline_precision = 0.0

    # CSV Output
    return [  # len(all_communities_set),
        len(allcom_and_tier_with_com),
        len(allcom_and_mygeo),
        len(allcomOx_and_tier_with_com),
        len(allcomOx_and_mygeo),
        len(allcom_and_tier_with_and_caida_com),
        len(allcom_and_mygeo_and_caida),
        len(allcomOx_and_tier_with_and_caida_com),
        len(allcomOx_and_mygeo_and_caida),
        len(allcomOx_and_tier_with_and_inferred_com),
        len(allcomOx_and_mygeo_and_inferred),
        caida_recall,
        caida_precision,
        caida_f1,
        caidaOx_recall,
        caidaOx_precision,
        caidaOx_f1,
        inferred_recall,
        inferred_precision,
        inferred_f1,
        unknown,
        baseline_precision]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--comm', dest='comm', help="All Community list.", required=True)
    parser.add_argument('-x', '--allcomox', dest='allcomox', help="All Community list Origin Limited.")
    parser.add_argument('-d', '--directory', dest='directory', help="Directory with files to process.", required=True)
    parser.add_argument('-r', '--reference', dest='reference', help="Consider reference or not", action='store_true')
    parser.add_argument('-o', '--output', dest='output', help="Output Filename.", required=True)
    parser.add_argument('-t', '--tier', dest='tier', help="Set Tier Level: 1, 2, 12 (1 and 2)", required=True)
    args = parser.parse_args()

    output = args.output
    all_comm = args.comm
    tier = int(args.tier)
    reference = args.reference

    # If we have an limited AllCom overview, use it
    if args.allcomox:
        all_comox = args.allcomox
    else:
        all_comox = all_comm

    # Select Tier Level
    if tier == 2:
        tier_to_select = "level = 2"
    elif tier == 12:
        tier_to_select = "(level = 1 or level = 2)"
    else:
        tier_to_select = "level = 1"

    # Check if we will use only geo or reference
    if reference:
        reference_to_select = "(type = 0 or type = 1)"
    else:
        reference_to_select = "type = 0"

    # Database Connection
    db = database_connection("data/communities.sqlite3")

    # Remove Tier ASNs without ground truth communities
    for asn_tier_with_geo in fetch_sql(db, f"select name from asn where {tier_to_select} and with_com = 1"):
        tier_with_comms_set.add(str(asn_tier_with_geo))

    # Get all Caida Geolocation Communities
    caida_geo_sql = fetch_sql(db, "select name from caida where type = 0")
    for community in caida_geo_sql:
        asn, comm = community.split(':')

        caida_geo_set.add(community)
        if asn not in caida_geo_dict:
            caida_geo_dict[asn] = set()
            caida_geo_dict[asn].add(community)
        else:
            caida_geo_dict[asn].add(community)

    # My Tier Geo Comm
    geolocation_sql = fetch_sql(db, f"select name from community where {tier_to_select} and {reference_to_select}")
    for line in geolocation_sql:
        asn, comm = line.split(':')

        geolocation_set.add(line.strip())
        if asn not in geolocation_dict:
            geolocation_dict[asn] = set()
            geolocation_dict[asn].add(comm.strip())
        else:
            geolocation_dict[asn].add(comm.strip())

    files = []
    with open(output, mode='w') as csv_file:
        fieldnames = [  # 'AllCom',
            'Lookahead',
            'Threshold',
            'Origins',
            'AllCom & Tier',  # T1 with geo that I have comm
            'AllCom & Geo Tier',  # My Geo T1 communities
            'AllComOx & Tier',  # T1 with geo that I have comm
            'AllComOx & Geo Tier',  # My Geo T1 communities
            'AllCom & Tier & Caida',
            'AllCom & Geo Tier & Caida',
            'AllComOx & Tier & Caida',
            'AllComOx & Geo Tier & Caida',
            'AllComOx & Tier & Inference',
            'AllComOx & Geo Tier & Inference',
            'CRecall',
            'CPrecision',
            'CF1_Score',
            'CRecallOx',
            'CPrecisionOx',
            'CF1_ScoreOx',
            'IRecall',
            'IPrecision',
            'IF1_Score',
            'Unknown',
            'Baseline']

        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)

        with os.scandir(args.directory) as itr:
            for entry in itr:
                files.append(entry.name)

        for file_process in sorted(files):
            Lookahead = file_process.split('-')[2]
            Threshold = file_process.split('-')[3].split('c')[1]
            Origins = file_process.split('-')[4].split('o')[1]

            # All files generated by Snakemake have the same number of origins
            csv_row = [Lookahead, Threshold, Origins]
            csv_row += statistical_calc(db=db,
                                        tier_to_select=tier_to_select,
                                        filename=os.path.join(args.directory, file_process),
                                        all_comm=all_comm,
                                        all_comox=all_comox)
            writer.writerow(csv_row)
