import os

# Configuration
rib_merged_output = [input for input in os.listdir('collector')]

# Variables
deep = list(range(1,4))
origins = list(range(1,10))
tiers = [1, 12]
reference = ['', '-r']
siblings_output = ["", "_siblings"]
BASE_DIR = "out/{rib}/output/"
AFTER_GEO_OUTDIR = BASE_DIR + "{approach}/"

# Geolocation Communities
# All desired files to be process need to be on 'collector' directory
rule bgpscanner:
    input:
        rib_input = "collector/{rib}"
    output:
        rib_out = BASE_DIR + "ribout/{rib}.rib"
    shell:
        "bgpscanner -L {input} > {output}"


# Geolocation Communities Prune from Inferred Communities
rule geocommpickle:
    input:
        rib_out = BASE_DIR + "ribout/{rib}.rib"
    output:
        AFTER_GEO_OUTDIR + "pickled/{rib}.rib-{deep}.pkl"
    threads:
        # all cores to run this task to avoid memory overload
        workflow.cores * 0.50
    params:
        approach = lambda wildcards: "-a" if wildcards.approach == "approach" else ""
    shell:
        "pypy3 bin/geocommpickle.py -i {input.rib_out} -d {wildcards.deep} {params.approach} -o {output} "


rule geocommunities:
    input:
        pickled = AFTER_GEO_OUTDIR + "pickled/{rib}.rib-{deep}.pkl",
    output:
        expand(AFTER_GEO_OUTDIR + "processed/{{deep,[0-9]+}}/{origins}/{rib}.rib-geocom-{deep}-c0.{num}-o{origins}",
                num=list(range(1,10)),
                allow_missing=True)
    threads:
        # reserve 80% of the given cores for the rule to avoid memory overload
        workflow.cores * 0.50
    params:
        approach = lambda wildcards: "-a" if wildcards.approach == "approach" else "",
        dest_dir= AFTER_GEO_OUTDIR + "processed/{deep}/{origins}/"
    shell:
        # Collector names could only use DOTS as separator of name files
        "pypy3 bin/geocommunities.py -d {wildcards.deep} -m {wildcards.origins} -i {input.pickled} {params.approach} -o {params.dest_dir}"


rule allcommunities:
    input:
        rib = BASE_DIR + "ribout/{rib}.rib"
    output:
        all_com = BASE_DIR + "allcom/{rib}-allcom"
    shell:
        "pypy3 bin/allcommunities.py -i {input.rib} -o {output}"


rule origins_and_comms:
    input:
        rib = BASE_DIR + "ribout/{rib}.rib",
        allcom = BASE_DIR + "allcom/{rib}-allcom"
    output:
        #TODO: arrumar para rodar 1 por 1
        expand(BASE_DIR + "allcom/{rib}-allcom-o{num}",
                num=list(range(1,10)),
                allow_missing=True)
    shell:
        "pypy3 bin/originscom.py -i {input.rib} -c {input.allcom}"

rule sort_data:
    input:
        entry = expand(AFTER_GEO_OUTDIR + "processed{siblings}/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
                    deep=deep,
                    allow_missing=True)
    output:
        AFTER_GEO_OUTDIR + "processed{siblings,.*}/uniq/{origins}/{rib}.rib-geocom-uniq-c{threshold}-o{origins}"
    shell:
        "sort -u {input.entry} > {output}"


rule statistics:
    input:
        all_com = BASE_DIR + "allcom/{rib}-allcom",
        short_comm = BASE_DIR + "allcom/{rib}-allcom-o{origins}",
        entry = expand(AFTER_GEO_OUTDIR + "processed{siblings}/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
                    rib=rib_merged_output,
                    threshold = [f"0.{input}" for input in range(1,10)],
                    allow_missing=True)
    output:
        AFTER_GEO_OUTDIR + "csv{siblings,.*}/{rib}-geocom-{deep}-o{origins}-t{tiers,[0-9]+}{reference,.*}.csv"

    params:
        dir_entry= AFTER_GEO_OUTDIR + "processed{siblings,.*}/{deep}/{origins}/",
        tier = "{tiers}",
        ref = "{reference}"

    shell:
        "pypy3 bin/geocomcount.py -d {params.dir_entry} -c {input.all_com} -x {input.short_comm} -t {params.tier} {params.ref} -o {output}"


rule hitting_set:
    input:
        rib = BASE_DIR + "ribout/{rib}.rib",
        all_com = BASE_DIR + "allcom/{rib}-allcom"
    output:
        directory(BASE_DIR + "hittingset")
    shell:
        "pypy3 bin/hittingset.py -i {input.rib} -s bin/geocom/caidasiblings -c {input.all_com} -d {output}"


rule removal_pickle:
    input:
        BASE_DIR + "hittingset"
    output:
        pickle = BASE_DIR + "ribout/{rib}-removal.pkl"
    shell:
        "bash bin/sortuniq.sh {input} && pypy3 bin/removalpickle.py -i {input} -o {output.pickle}"


rule siblings_remove:
    input:
        pickle = BASE_DIR + "ribout/{rib}-removal.pkl",
        files = AFTER_GEO_OUTDIR + "processed/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}"

    output:
        AFTER_GEO_OUTDIR + "processed_siblings/{deep,[0-9]+}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}"

    shell:
        "pypy3 bin/removalsibling.py -i {input.pickle} -m 2 -c {input.files} -o {output}"


# All Output Files
rule origins_and_comms_all:
    input:
        expand(BASE_DIR + "allcom/{rib}-allcom-o{origins}",
            rib=rib_merged_output,
            origins=origins)


rule geocom_gen_all:
    input:
        expand(AFTER_GEO_OUTDIR + "processed/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
            approach=["default", "approach"],
            rib=rib_merged_output,
            deep=deep,
            threshold = [f"0.{input}" for input in range(1,10)],
            origins=origins,
            allow_missing=True)


rule siblings_all:
    input:
        expand(AFTER_GEO_OUTDIR + "processed{siblings}/{deep}/{origins}/{rib}.rib-geocom-{deep}-c{threshold}-o{origins}",
                approach=["default", "approach"],
                siblings=["", "_siblings"],
                rib=rib_merged_output,
                deep=deep + ["uniq"],
                threshold=[f"0.{input}" for input in range(1,10)],
                origins=origins,
                allow_missing=True)


rule statistical_all:
    input:
        expand(AFTER_GEO_OUTDIR + "csv{siblings}/{rib}-geocom-{deep}-o{origins}-t{tiers}{reference}.csv",
            approach=["default", "approach"],
            rib=rib_merged_output,
            deep=deep+["uniq"],
            origins=origins,
            siblings=siblings_output,
            reference=reference,
            tiers=tiers,
            allow_missing=True),

rule uniq_all:
    input:
        expand(AFTER_GEO_OUTDIR + "processed{siblings}/uniq/{origins}/{rib}.rib-geocom-uniq-c{threshold}-o{origins}",
            approach=["default", "approach"],
            siblings=["", "_siblings"],
            rib=rib_merged_output,
            threshold=[f"0.{input}" for input in range(1,10)],
            origins=origins,)

rule merge_csv:
    input:
        expand(AFTER_GEO_OUTDIR + "csv{siblings}/{rib}-geocom-{deep}-o{origins}-t{tiers}{reference}.csv",
            deep=deep,
            origins=origins,
            allow_missing=True)
    output:
        AFTER_GEO_OUTDIR + "csv{siblings,.*}-t{tiers,[0-9]+}{reference,.*}/all-geocom-agregated.csv"
    shell:
        "python3 bin/mergecsv.py {input} {output}"

rule location:
    input:
        expand(AFTER_GEO_OUTDIR + "csv{siblings}-t{tiers}{reference}/all-geocom-agregated.csv",
            approach=["default", "approach"],
            rib=rib_merged_output,
            siblings=siblings_output,
            tiers=tiers,
            reference=reference,
            ),
        expand(AFTER_GEO_OUTDIR + "csv{siblings}/{rib}-geocom-{deep}-o{origins}-t{tiers}{reference}.csv",
            approach=["default", "approach"],
            rib=rib_merged_output,
            deep=["uniq"],
            origins=origins,
            siblings=siblings_output,
            reference=reference,
            tiers=tiers)


onsuccess:
    print("Workflow finished, no error")

onerror:
    print("An error occurred")


