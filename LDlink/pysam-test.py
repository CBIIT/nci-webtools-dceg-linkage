import pysam

tbx = pysam.TabixFile(filename="s3://nci-cbiit-dceg-data-nonprod/ldlink/1000G/GRCh37/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz", index="s3://nci-cbiit-dceg-data-nonprod/ldlink/1000G/GRCh37/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz.tbi")

for row in tbx.fetch("1", 1000000, 1001000):
    print (str(row))