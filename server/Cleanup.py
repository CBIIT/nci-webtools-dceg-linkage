import os
import glob
import threading


def schedule_tmp_cleanup(request, logger, delay=60 * 60, tmp_dir="/data/tmp"):
    """
    Schedule deletion of all files in tmp_dir containing the request string after a delay (in seconds).
    """

    def cleanup():
        files = glob.glob(os.path.join(tmp_dir, f"*{request}*"))
        logger.info(f"Starting cleanup for request '{request}'. Found {len(files)} file(s) to delete.")
        for f in files:
            try:
                os.remove(f)
                logger.info(f"Deleted file: {f}")
            except Exception as e:
                logger.error(f"Failed to delete file: {f}. Error: {e}")

    if not request:
        logger.error('Schedule cleanup failed. No request ID provided')
        return "Request id required"
    else:
        logger.info(f"Scheduling cleanup for request '{request}' after {delay} seconds.")
        threading.Timer(delay, cleanup).start()
