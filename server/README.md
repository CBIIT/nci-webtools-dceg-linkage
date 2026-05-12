in ec2 efs server add the cronjob
# Remove temporary files over 1 hour old
0 * * * * find /local/content/analysistools_efs/ldlink/tmp/ -mindepth 1 -mmin +61 -delete -print > /var/log/ldlink-cron.log 2>&1