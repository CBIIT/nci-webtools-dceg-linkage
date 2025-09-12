import os
import glob
import threading


def schedule_tmp_cleanup(request, logger, delay=60 * 1, tmp_dir="/data/tmp"):
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

def schedule_tmp_cleanup_ldscore(request, logger, delay=60 * 1, tmp_dir="/data/tmp/uploads"):
    """
    Schedule deletion of all files in tmp_dir containing the request string after a delay (in seconds).
    """

    def cleanup():
        folder_path = os.path.join(tmp_dir, request)
        if os.path.isdir(folder_path):
            try:
                import shutil
                shutil.rmtree(folder_path)
                logger.info(f"Deleted folder and all contents: {folder_path}")
            except Exception as e:
                logger.error(f"Failed to delete folder: {folder_path}. Error: {e}")
        else:
            logger.info(f"No folder found for request '{request}' at {folder_path}")

    if not request:
        logger.error('Schedule cleanup failed. No request ID provided')
        return "Request id required"
    else:
        logger.info(f"Scheduling cleanup for request '{request}' after {delay} seconds.")
        threading.Timer(delay, cleanup).start()