#!/bin/bash
#SBATCH --job-name=matrix
#SBATCH --output=slurm_output/matrix.%j.out
#SBATCH --error=slurm_output/matrix.%j.err
#SBATCH --time=72:00:00
#SBATCH --mem=128G
#SBATCH --cpus-per-task=64
#SBATCH --account=def-gsarah

source /home/jordboul/scratch/PheWeb/PheWeb2-API/.venv/bin/activate

pheweb2 matrix