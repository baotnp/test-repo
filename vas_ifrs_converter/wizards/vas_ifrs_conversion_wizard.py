from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class VasIfrsConversionWizard(models.TransientModel):
    """Wizard for batch VAS to IFRS conversion"""
    _name = 'vas.ifrs.conversion.wizard'
    _description = 'VAS to IFRS Conversion Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    journal_ids = fields.Many2many('account.journal', string='Journals')
    partner_ids = fields.Many2many('res.partner', string='Partners')

    conversion_mode = fields.Selection([
        ('missing_only', 'Convert Missing Only'),
        ('reconvert_all', 'Reconvert All'),
    ], string='Conversion Mode', default='missing_only')

    def action_convert(self):
        """Execute batch conversion"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('is_ifrs_move', '=', False),
        ]

        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        if self.conversion_mode == 'missing_only':
            domain.append(('ifrs_converted', '=', False))

        moves = self.env['account.move'].search(domain)

        conversion_service = self.env['vas.ifrs.conversion.service']
        converted_count = 0
        errors = []

        for move in moves:
            try:
                ifrs_move = conversion_service.convert_move_to_ifrs(move)
                if ifrs_move:
                    move.write({
                        'ifrs_converted': True,
                        'ifrs_move_id': ifrs_move.id,
                        'conversion_date': fields.Datetime.now(),
                        'conversion_method': 'batch'
                    })
                    converted_count += 1
            except Exception as e:
                errors.append(f"Move {move.name}: {str(e)}")

        # Return results
        print(f"Converted {converted_count} moves with {len(errors)} errors.")
        return
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'vas.ifrs.conversion.result',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {
        #         'default_converted_count': converted_count,
        #         'default_error_count': len(errors),
        #         'default_error_messages': '\n'.join(errors),
        #     }
        # }