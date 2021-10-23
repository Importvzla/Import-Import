# -*- coding: utf-8 -*-

from odoo import models, fields, api
import os
import logging

_logger = logging.getLogger(__name__)


class CustomPrintingPrinter(models.Model):
    _inherit = 'printing.printer'
    _description = 'modificar modelo de printing.printer'

    def print_file(self, file_name, report=None, **print_opts):
        """ Print a file """
        # self.ensure_one()
        # connection = self.server_id._open_connection(raise_on_error=True)
        # options = self.print_options(report=report, **print_opts)
        #
        # _logger.debug(
        #     "Sending job to CUPS printer %s on %s with options %s"
        #     % (self.system_name, self.server_id.address, options)
        # )
        # connection.printFile(self.system_name, file_name, file_name, options=options)
        # _logger.info(
        #     "Printing job: '{}' on {}".format(file_name, self.server_id.address)
        # )

        _logger.info(
            'Sending job to CUPS printer %s on %s'
            % (self.system_name, self.server_id.address))
        options = self.print_options(report=report, **print_opts)
        options_str = ""
        for option, value in options.items():
            options_str += "-o %s=%s" % (option, value, )
        _logger.info("Cmd: %s", 'lp -h %s:%s -d %s %s %s' %
                  (self.server_id.address,
                   self.server_id.port,
                   self.system_name,
                   options_str,
                   file_name))
        os.system('lp -h %s:%s -d %s %s %s' %
                  (self.server_id.address,
                   self.server_id.port,
                   self.system_name,
                   options_str,
                   file_name))
        _logger.info("Printing job: '%s' on %s" % (
            file_name,
            self.server_id.address,
        ))

        return True
