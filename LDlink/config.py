data_dir="/local/content/ldlink/data/"

data = dict(
    snp_dir = data_dir + "snp142/snp142_annot_2.db",
    pop_dir = data_dir + "1000G/Phase3/samples/",
    vcf_dir = data_dir + "1000G/Phase3/genotypes/ALL.chr",
    reg_dir = data_dir + "regulomedb/regulomedb.db",
    gene_dir = data_dir + "refGene/sorted_refGene.txt.gz",
	gene_c_dir = data_dir + "refGene/sorted_refGene_collapsed.txt.gz",
	gene_dir2 = data_dir + "refGene/gene_names_coords.db",
	recomb_dir = data_dir + "recomb/genetic_map_autosomes_combined_b37.txt.gz",
    array_dir = data_dir + "arrays/snp142_arrays.db"
)