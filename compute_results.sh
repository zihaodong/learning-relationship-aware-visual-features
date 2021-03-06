#!/bin/bash

set -e

OPTIND=1

begin=0
end=500
cpus=4
CLEVRDIR=""

usage="\nUsage: $(basename "$0") -d clevr_dir [OPTIONS]\nOPTIONS:\n  -s\tSpecifies start query index [default: $begin]\n  -e\tSpecifies end query index [default: $end]\n  -p\tSpecifies number of processes to use for computing GED [default: $cpus]\n"

while getopts "s:e:p:d:h" opt; do
    case "$opt" in
    s)  begin=$OPTARG
        ;;
    e)  end=$OPTARG
        ;;
    p)  cpus=$OPTARG
        ;;
    d)  CLEVRDIR=$OPTARG
	;;
    h)  printf "$usage"
        exit
        ;;
    esac
done

if [ -z "$CLEVRDIR" ]; then
	echo "CLEVR directory not specified. Please use -d option"
	exit
fi

if [ ! -d "$CLEVRDIR" ]; then
	echo "Specified CLEVR directory does not exist!"
	exit
fi

if [ ! -f .venvok ]; then
	echo "Virtual environment not installed. Have you run setup.sh?"
	exit
fi

source ./retrieval_env/bin/activate

if [ ! -f .statsok ]; then

	echo "Computing all the metrics from index "$begin" to "$end" using "$cpus" cpus"
	#Compute soft-match metrics
	printf "\n\nStep 1/4\n"
	python3 build_stats.py --clevr-dir $CLEVRDIR --query-img-index $begin --until-img-index $end --cpus $cpus
	printf "\n\nStep 2/4\n"
	python3 build_stats.py --clevr-dir $CLEVRDIR --query-img-index $begin --until-img-index $end --normalize --cpus $cpus

	#Compute hard-match metrics
	printf "\n\nStep 3/4\n"
	python3 build_stats.py --clevr-dir $CLEVRDIR --graph-ground-truth atleastone --query-img-index $begin --until-img-index $end --cpus $cpus
	printf "\n\nStep 4/4\n"
	python3 build_stats.py --clevr-dir $CLEVRDIR --graph-ground-truth atleastone --query-img-index $begin --until-img-index $end --normalize --cpus $cpus
fi

touch .statsok

#Emit spearman-rho stats and build pdf
printf "\nSoft-match results\n"
python3 visualize_stats.py --ground-truth graph-approx-proportional --aggregate
printf "\nHard-match results\n"
python3 visualize_stats.py --ground-truth graph-approx-atleastone --aggregate

deactivate
