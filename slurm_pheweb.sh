#!/bin/bash
#SBATCH --job-name=test
#SBATCH --output=slurm_output/generate-autocomplete-db.%j.out
#SBATCH --error=slurm_output/generate-autocomplete-db.%j.err
#SBATCH --time=08:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8
#SBATCH --account=def-gsarah

module load python/3.12
source ~/.venv/bin/activate

pheweb2 generate-autocomplete-db