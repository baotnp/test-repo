from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    """Extended Account Move for VAS-IFRS conversion"""
    _inherit = 'account.move'

    # IFRS related fields
    ifrs_converted = fields.Boolean(string='IFRS Converted', default=False)
    ifrs_move_id = fields.Many2one('account.move', string='Related IFRS Move')
    is_ifrs_move = fields.Boolean(string='Is IFRS Move', default=False)
    vas_move_id = fields.Many2one('account.move', string='Related VAS Move')

    conversion_date = fields.Datetime(string='Conversion Date')
    conversion_method = fields.Selection([
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
        ('batch', 'Batch Processing'),
    ], string='Conversion Method')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger real-time conversion"""
        moves = super().create(vals_list)

        # Trigger real-time conversion for non-IFRS moves
        for move in moves:
            if not move.is_ifrs_move and move.state == 'posted':
                move._trigger_ifrs_conversion()

        return moves

    def write(self, vals):
        """Override write to handle state changes"""
        result = super().write(vals)

        # Trigger conversion when move is posted
        if vals.get('state') == 'posted':
            for move in self:
                if not move.is_ifrs_move and not move.ifrs_converted:
                    move._trigger_ifrs_conversion()

        return result

    def _trigger_ifrs_conversion(self):
        """Trigger real-time IFRS conversion"""
        if self.is_ifrs_move:
            return

        try:
            conversion_service = self.env['vas.ifrs.conversion.service']
            ifrs_move = conversion_service.convert_move_to_ifrs(self)

            if ifrs_move:
                self.write({
                    'ifrs_converted': True,
                    'ifrs_move_id': ifrs_move.id,
                    'conversion_date': fields.Datetime.now(),
                    'conversion_method': 'auto'
                })

                _logger.info(f"Successfully converted move {self.name} to IFRS")

        except Exception as e:
            _logger.error(f"Error converting move {self.name} to IFRS: {str(e)}")
            # Create notification for accounting team
            self._create_conversion_notification(str(e))

    def _create_conversion_notification(self, error_msg):
        """Create notification for conversion errors"""
        self.env['mail.message'].create({
            'subject': f'IFRS Conversion Error - {self.name}',
            'body': f'Error converting journal entry to IFRS: {error_msg}',
            'model': self._name,
            'res_id': self.id,
            'message_type': 'notification',
        })