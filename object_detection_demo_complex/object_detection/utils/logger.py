import multiprocessing


class Logger:
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(multiprocessing.SUBDEBUG)

    @staticmethod
    def info(tag, message):
        Logger.logger.info('{tag}: {message}'.format(
            tag=tag,
            message=message
        ))

    @staticmethod
    def error(tag, message):
        Logger.logger.error('{tag}: {message}'.format(
            tag=tag,
            message=message
        ))
