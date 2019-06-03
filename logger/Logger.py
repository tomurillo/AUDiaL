import logging
import logging.handlers
import time
from flask import session
from general_util import truncateString

LOG_DIR = 'logger/logs'  # Log directory
MAX_BYTES = 10485760  # Maximum size of each log file (default: 10 MiB)
SYS_BACKUP_N = 5  # Maximum number of previous system log files to keep
SES_BACKUP_N = 2  # Maximum number of previous individual session log files to keep


class AudialLogger(object):
    """
    Logs user session activity and system status
    """
    def __init__(self):
        """
        Logger constructor
        """
        self.start_time = 0.0
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%d-%m-%Y %H:%M:%S")
        sysh = logging.handlers.RotatingFileHandler("%s/%s.log" % (LOG_DIR, __name__),
                                                    maxBytes=MAX_BYTES,
                                                    backupCount=SYS_BACKUP_N)
        sysh.setLevel(logging.DEBUG)
        sysh.setFormatter(formatter)
        self.system_logger = logging.getLogger(__name__)
        if not self.system_logger.handlers:
            self.system_logger.setLevel(logging.DEBUG)
            self.system_logger.addHandler(sysh)
        self.session_logger = None
        if session:
            sessh = logging.handlers.RotatingFileHandler("%s/session-%s.log" % (LOG_DIR, session.sid),
                                                         maxBytes=MAX_BYTES,
                                                         backupCount=SES_BACKUP_N)
            sessh.setLevel(logging.INFO)
            sessh.setFormatter(formatter)
            self.session_logger = logging.getLogger(session.sid)
            if not self.session_logger.handlers:
                self.session_logger.setLevel(logging.INFO)
                self.session_logger.addHandler(sessh)

    def log_query(self, query, exec_log_start=True):
        """
        Logs that the user has input a query
        :param query: string; raw input query
        :param exec_log_start: boolean; whether to start counting the execution time
        :return:
        """
        if exec_log_start:
            self.start_exec_log()
        msg = "Input query: '%s'" % query
        self.session_logger.info(msg)

    def log_vote(self, uri, exec_log_start=True):
        """
        Logs that the user has voted for a suggestion in a dialog
        :param uri: string; URI of the concept the user has voted for
        :param exec_log_start: boolean; whether to start counting the execution time
        :return:
        """
        if exec_log_start:
            self.start_exec_log()
        if not uri:
            uri = 'None'
        msg = "Vote for '%s' casted." % uri
        self.session_logger.info(msg)

    def log_answer(self, answer):
        """
        Logs that the user has received an answer to their query
        @param answer: string; the answer given to the user
        :return: None; log the answer
        """
        ex_time = self.__exec_time()
        msg = "Answer: %s. " % truncateString(answer)
        msg += "Elapsed: %.2f seconds." % ex_time
        self.session_logger.info(msg)

    def log_command(self, answer):
        """
        Logs that the user has performed a navigational command
        @param answer: string; the answer given to the user
        :return: None; log the command
        """
        ex_time = self.__exec_time()
        msg = "Executed Command: %s. " % truncateString(answer)
        msg += "Elapsed: %.2f seconds." % ex_time
        self.session_logger.info(msg)

    def log_dialog(self, suggestion_pair):
        """
        Logs that a mapping/disambiguation dialogue has been shown to the user
        :param suggestion_pair: dict; JSON serialized SuggestionPair instance
        :return: None; log the dialog
        """
        if 'text' in suggestion_pair and 'votes' in suggestion_pair:
            ex_time = self.__exec_time()
            msg = "Dialog for '%s' shown " % suggestion_pair['text']
            msg += "(%d suggestions). " % len(suggestion_pair['votes'])
            msg += "Elapsed: %.2f seconds." % ex_time
            self.session_logger.info(msg)

    def start_exec_log(self):
        """
        Start logging code execution time in user's session
        :return: None; start internal timer
        """
        self.start_time = time.time()

    def __exec_time(self):
        """
        Return the execution time since the previous call to the logger's methods
        :return: float; execution time, in seconds. May be negative if time cannot be computed.
        """
        end_time = time.time()
        ex_time = -1.0
        if self.start_time > 0.0:
            ex_time = end_time - self.start_time
        self.start_time = 0.0
        return ex_time
