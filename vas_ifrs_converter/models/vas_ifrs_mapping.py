from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class VasIfrsMapping(models.Model):
    """Mapping configuration between VAS and IFRS accounts"""
    _name = 'vas.ifrs.mapping'
    _description = 'VAS to IFRS Account Mapping'
    _order = 'vas_account_code'

    name = fields.Char(string='Mapping Name', required=True)
    vas_account_id = fields.Many2one('account.account', string='VAS Account', required=True)
    vas_account_code = fields.Char(related='vas_account_id.code', string='VAS Account Code', store=True)
    ifrs_account_id = fields.Many2one('account.account', string='IFRS Account', required=True)
    ifrs_account_code = fields.Char(related='ifrs_account_id.code', string='IFRS Account Code', store=True)

    # Conversion rules
    conversion_type = fields.Selection([
        ('direct', 'Direct Mapping'),
        ('split', 'Split Mapping'),
        ('merge', 'Merge Mapping'),
        ('calculate', 'Calculated Mapping'),
    ], string='Conversion Type', default='direct', required=True)

    conversion_factor = fields.Float(string='Conversion Factor', default=1.0)
    split_percentage = fields.Float(string='Split Percentage (%)', default=100.0)

    # Conditions
    active = fields.Boolean(string='Active', default=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    # Additional settings
    auto_convert = fields.Boolean(string='Auto Convert', default=True)
    notes = fields.Text(string='Conversion Notes')

    @api.constrains('split_percentage')
    def _check_split_percentage(self):
        for record in self:
            if record.split_percentage <= 0 or record.split_percentage > 100:
                raise ValidationError(_('Split percentage must be between 0 and 100'))

    @api.constrains('vas_account_id', 'ifrs_account_id')
    def _check_account_mapping(self):
        for record in self:
            if record.vas_account_id == record.ifrs_account_id:
                raise ValidationError(_('VAS and IFRS accounts cannot be the same'))
