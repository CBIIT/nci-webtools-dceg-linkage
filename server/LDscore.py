#!/usr/bin/env python3
import os
import subprocess
import time


# Create LDproxy function
def calculate_ldscore(file, pop, request, genome_build, web, myargs):   
    print("Calculating LD Score:#############",pop)               
    output = exec_command_in_container("cd 1kg_eur && python ../ldsc.py --bfile 22 --l2 --ld-wind-cm 1 --out 22")
    return output

def build_docker_image():
    subprocess.run(["docker", "build", "--platform", "linux/amd64", "-t", "ldsc39", "."], check=True)

def run_docker_container():
    subprocess.run(["docker", "run", "-d", "--name", "ldsc39_container", "-p", "5000:5000", "ldsc39"], check=True)

def exec_command_in_container(command):
    full_command = ["bash", "-c", f"source activate ldsc && {command}"]
    print(full_command)
    result = subprocess.run(["docker", "exec", "-it", "ldsc39_container"] + full_command, capture_output=True, text=True, check=True)
    print(result)
    return result.stdout
	
def main():
    #build_docker_image()
    #run_docker_container()
    output = exec_command_in_container("cd 1kg_eur && python ../ldsc.py --bfile 22 --l2 --ld-wind-cm 1 --out 22")
    print("Running LDSC")
    print(output)

if __name__ == "__main__":
    main()