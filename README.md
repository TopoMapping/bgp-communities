## Requirements:

You need the tools bellow to generate all the outputs.

* [bgpscanner](https://gitlab.com/Isolario/bgpscanner.git)
* [PyPy3](https://www.pypy.org/)
* [Python3](https://www.python.org/)
* [Snakemake](https://snakemake.github.io)
* [Sort](https://www.oreilly.com/?path=s/sort)

To install the needed Python libraries run:

```
$ pip3 install -r requirements.txt
```

## First Workflow

![Workflow](/img/workflowsplit.png)


Our system executes Python scripts using PyPy3 (for optimization) and other programs to extract location communities. First,
we execute `bgpscanner` on all ribs provided on directory `collector` (don't forget to remove the underline from names), extracting
all communities, communities with a specific number of origins and all keys (better described on paper) to determine
what are the location communities. The `geocommunities` step infers all the communities and also the `hitting_set` for all
communities on RIBs (we compute the `removal_pickle` for brevity and reduce the computation). After that, we have
all location communities. We also apply a removal from the hitting set
to remove non-documented siblings. We compute all statistics and generate a pool of results plus the location communities
for each collector.


## Config File: config.yaml

The configuration file `config.yaml` are used now to collect the information you want (pre-processed on steps bellow). 
The default configuration:

```
k_origins: 2
k_prev: 0.2
k_filter: 1
```

* k_origins: number of minimal origins for each community to be evaluated
* k_prev: number of previous keys that explains a community to be considered
* k_filter: number of post-filter using hitting set strategy


The options defined in `config.yaml` will be in `results` directory output.
You may change the parameters of `k_origins` from 1 to 9, `k_prev` from 0.1 to 0.9, and `k_filter` from 1 to 5.
The actual version does not consider the `config.yaml` to process (it is being planned for the future), for now,
we use the values on config to collect pre-processed data on the steps above. Valid options are:

* k_origins = 1, 2, 3, 4, 5, 6, 7, 8, and 9
* k_prev = 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, and 0.9
* k_filter = 1, 2, 3, 4 and 5


## How it Works:

Download a RIB file from one of projects: RIPE, RouteViews or Isolario. Create the directory `collector`, and copy RIB files inside.
If you just want our manually built database, look for `data/communities.db`.


```
$ mkdir collector
$ cp routeviews.rib.20191201.0000.bz2 ripe.ris.rib20191201.0000.bz2 collector/
```

The number of cores needs to be ajusted to your CPU in the commands below.

We expect that the RIB files that are inside `collector` to not have '-' (dashes) on file names. An easy way to change all of them is using `rename`, for example:

```
$ cd collector
$ rename "s/-/./g" *
```

Use `rename -n` to test before applying the changes. This is a requirement right now but will be automated to download and adjust directly on code.

### SnakefileSplit.smk

To begin, run the command bellow (or run the `run.sh` script, which will run all three steps below) to generate the location community database:


```
$ snakemake --cores 4 location --snakefile SnakefileSplit.smk
```


## Second Workflow

![WorkflowMergeSplit](/img/workflowmergesplit.png)


The second workflow merge the results from each collector into one uniq and sorted output.


### SnakeMergeResults.smk

After processing each collector independently, we take the union across all collectors:

```
$ snakemake --cores 4 merge_results --snakefile SnakefileMergeResults.smk
```

The results will be stored under a directory named `merged`.



## Third Workflow

![WorkflowMergeSplit](/img/workflowkfilter.png)


We compute now all independent results from the siblings removal process from the first workflow using k_filter equal 1 to 5 on the full
inferred data, sort and uniq them and compute the statistics (recall, precision, and F1 score). To finish, we merge and save the output on the `results` directory.



### SnakefileKFilter.smk

The last step is computing the minimum hitting set and discarding incorrect inferences:

```
$ snakemake --cores 4 end --snakefile SnakefileKFilter.smk
```


# The Results

The output will be inside `results`:

```
$ ls results/
inferred_communities.txt
report-k_filter-1.csv
```

Done.
