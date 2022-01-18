# Specific for paper to generate kcover for comparison
#TODO: remove that and integrate with normal flow
import os

BASE_DEFAULT_DIR = "out/{rib}/output/default/"
OUTPUT_DIR = "out/merged/"
configfile: "config.yaml"
siblings_output = ["", "_siblings"]
origins = list(range(1,10))
deep = list(range(1,4))

# Old Instance
rib_merged_output = [input for input in os.listdir('collector')]
BASE_DIR = "out/{rib}/output/"
tiers = [1, 12]
reference = ['', '-r']
kcover = list(range(1,6))

rule sort_all_communities:
    input:
        all_com = expand(BASE_DIR + "allcom/{rib}-allcom",
                        rib=[input for input in os.listdir('collector/')],
                        allow_missing=True)

    output:
        out_merged=OUTPUT_DIR + "allcom/merged-allcom"

    shell:
        "sort -u {input.all_com} > {output.out_merged}"


rule sort_k_origins:
    input:
        short_comm = expand(BASE_DIR + "allcom/{rib}-allcom-o{origins}",
                            rib=[input for input in os.listdir('collector/')],
                            allow_missing=True)

    output:
        out_merged=OUTPUT_DIR + "allcom/merged-allcom-o{origins}"

    shell:
        "sort -u {input.short_comm} > {output.out_merged}"


rule siblings_kcover_remove:
    input:
        pickle = BASE_DIR + "ribout/{rib}-removal.pkl",
        files = BASE_DEFAULT_DIR + "processed/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}"

    output:
        OUTPUT_DIR + "processed_siblings/{deep}/{origins}/k{kcover}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}"

    shell:
        "pypy3 bin/removalsibling.py -i {input.pickle} -m {wildcards.kcover} -c {input.files} -o {output}"


rule sort_kcover_lookahead_outputs:
    input:
        processed=expand(OUTPUT_DIR + "processed_siblings/{deep}/{origins}/k{kcover}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
                        rib=[input for input in os.listdir('collector/')],
                        allow_missing=True)
    output:
        out_merged = OUTPUT_DIR + "processed_siblings/{deep,[0-9]+}/{origins}/k{kcover}/merged/merged.rib-geocom-{deep}-c{threshold}-o{origins}"

    shell:
        "sort -u {input.processed} > {output.out_merged}"


rule sort_kcover_uniq_outputs:
    input:
        processed=expand(OUTPUT_DIR + "processed_siblings/uniq/{origins}/k{kcover}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
                        rib=[input for input in os.listdir('collector/')],
                        allow_missing=True)
    output:
        out_merged = OUTPUT_DIR + "processed_siblings/uniq/{origins}/k{kcover}/merged/merged.rib-geocom-{deep}-c{threshold}-o{origins}"

    shell:
        "sort -u {input.processed} > {output.out_merged}"


rule statistical:
    input:
        all_com = OUTPUT_DIR + "allcom/merged-allcom",
        short_comm = OUTPUT_DIR + "allcom/merged-allcom-o{origins}",
        entry = expand(OUTPUT_DIR + "processed_siblings/{deep}/{origins}/k{kcover}/merged/merged.rib-geocom-{deep}-c{threshold}-o{origins}",
                    threshold = [f"0.{input}" for input in range(1,10)],
                    allow_missing=True)
    output:
        OUTPUT_DIR + "csv_siblings/k{kcover}/merged-geocom-{deep}-o{origins}-t{tiers,[0-9]+}{reference,.*}.csv"

    params:
        dir_entry= OUTPUT_DIR + "processed_siblings/{deep}/{origins}/k{kcover}/merged",
        tier = "{tiers}",
        ref = "{reference}"

    shell:
        "pypy3 bin/geocomcount.py -d {params.dir_entry} -c {input.all_com} -x {input.short_comm} -t {params.tier} {params.ref} -o {output}"


rule merge_csv:
    input:
        expand(OUTPUT_DIR + "csv_siblings/k{kcover}/merged-geocom-{deep}-o{origins}-t{tiers}{reference}.csv",
            rib=rib_merged_output,
            deep=deep + ["uniq"],
            origins=origins,
            allow_missing=True)
    output:
        OUTPUT_DIR + "csv_siblings-t{tiers,[0-9]+}{reference,.*}/k{kcover}/all-geocom-agregated.csv"
    shell:
        "python3 bin/mergecsv.py {input} {output}"


rule results_kfilter:
    input:
        input = expand(OUTPUT_DIR + "processed_siblings/uniq/{k_origins}/k{k_filter}/merged/merged.rib-geocom-uniq-c{k_prev}-o{k_origins}",
            k_origins=config["k_origins"],
            k_prev=config["k_prev"],
            k_filter=config["k_filter"]
        )
    output:
        output = "results/inferred_communities.txt"
    shell:
        "cp {input} {output}"


rule results_config:
    input:
        input = OUTPUT_DIR + "csv_siblings-t12-r/k{k_filter}/all-geocom-agregated.csv"
    output:
        output = "results/report-k_filter-{k_filter}.csv"
    params:
        k_origins=config["k_origins"],
        k_prev=config["k_prev"]
    shell:
        "echo 'k_prev,k_origin,recall,precision,f1_score,unknown' > {output} &&"
        "grep 'uniq' {input} | grep ',{params.k_origins},' | grep '{params.k_prev},' | cut -d ',' -f 3,4,21-24 >> {output}"


rule end:
    input:
        expand("results/report-k_filter-{k_filter}.csv",
            k_filter=config["k_filter"]
        ),
        "results/inferred_communities.txt"

onsuccess:
    print("Workflow finished, no error")

onerror:
    print("An error occurred")
