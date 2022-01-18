#!/bin/bash

set -eu

snakemake --cores 2 location --snakefile SnakefileSplit.smk
sleep 10s

snakemake --cores 2 merged_results --snakefile SnakefileMergeResults.smk
sleep 10s

snakemake -cores 2  end --snakefile SnakefileKFilter.smk

