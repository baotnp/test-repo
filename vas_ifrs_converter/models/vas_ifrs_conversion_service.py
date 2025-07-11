from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class VasIfrsConversionService(models.Model):
    """Service for handling VAS to IFRS conversions"""
    _name = 'vas.ifrs.conversion.service'
    _description = 'VAS to IFRS Conversion Service'

    def convert_move_to_ifrs(self, vas_move):
        """Convert a VAS move to IFRS format"""
        if vas_move.is_ifrs_move:
            return False

        # Get mapping rules
        mappings = self._get_applicable_mappings(vas_move)

        if not mappings:
            _logger.warning(f"No IFRS mappings found for move {vas_move.name}")
            return False

        # Create IFRS move
        ifrs_move_vals = self._prepare_ifrs_move_vals(vas_move)
        ifrs_move = self.env['account.move'].create(ifrs_move_vals)

        # Convert move lines
        ifrs_lines = []
        for line in vas_move.line_ids:
            converted_lines = self._convert_move_line(line, mappings)
            ifrs_lines.extend(converted_lines)

        # Create IFRS move lines
        for line_vals in ifrs_lines:
            line_vals['move_id'] = ifrs_move.id
            self.env['account.move.line'].create(line_vals)

        # Post IFRS move
        ifrs_move.action_post()

        # Link moves
        ifrs_move.vas_move_id = vas_move.id

        return ifrs_move

    def _get_applicable_mappings(self, move):
        """Get applicable mapping rules for a move"""
        domain = [
            ('active', '=', True),
            '|', ('start_date', '<=', move.date), ('start_date', '=', False),
            '|', ('end_date', '>=', move.date), ('end_date', '=', False),
        ]

        return self.env['vas.ifrs.mapping'].search(domain)

    def _prepare_ifrs_move_vals(self, vas_move):
        """Prepare values for IFRS move creation"""
        return {
            'name': f"IFRS-{vas_move.name}",
            'ref': f"IFRS conversion of {vas_move.name}",
            'journal_id': self._get_ifrs_journal().id,
            'date': vas_move.date,
            'is_ifrs_move': True,
            'partner_id': vas_move.partner_id.id,
            'currency_id': vas_move.currency_id.id,
        }

    def _convert_move_line(self, line, mappings):
        """Convert a single move line using mapping rules"""
        # Find applicable mapping
        mapping = mappings.filtered(lambda m: m.vas_account_id == line.account_id)

        if not mapping:
            # No mapping found, create warning
            _logger.warning(f"No IFRS mapping for account {line.account_id.code}")
            return []

        converted_lines = []

        for map_rule in mapping:
            if map_rule.conversion_type == 'direct':
                converted_lines.append(self._create_direct_conversion(line, map_rule))
            elif map_rule.conversion_type == 'split':
                converted_lines.extend(self._create_split_conversion(line, map_rule))
            elif map_rule.conversion_type == 'calculate':
                converted_lines.append(self._create_calculated_conversion(line, map_rule))

        return converted_lines

    def _create_direct_conversion(self, line, mapping):
        """Create direct 1:1 conversion"""
        return {
            'name': line.name,
            'account_id': mapping.ifrs_account_id.id,
            'debit': line.debit * mapping.conversion_factor,
            'credit': line.credit * mapping.conversion_factor,
            'partner_id': line.partner_id.id,
            'currency_id': line.currency_id.id,
            'amount_currency': line.amount_currency * mapping.conversion_factor,
        }

    def _create_split_conversion(self, line, mapping):
        """Create split conversion (for complex mappings)"""
        factor = mapping.split_percentage / 100.0

        return [{
            'name': f"{line.name} (IFRS Split)",
            'account_id': mapping.ifrs_account_id.id,
            'debit': line.debit * factor,
            'credit': line.credit * factor,
            'partner_id': line.partner_id.id,
            'currency_id': line.currency_id.id,
            'amount_currency': line.amount_currency * factor,
        }]

    def _create_calculated_conversion(self, line, mapping):
        """Create calculated conversion with business rules"""
        # This would contain specific IFRS calculation logic
        # For now, using direct conversion as base
        return self._create_direct_conversion(line, mapping)

    def _get_ifrs_journal(self):
        """Get or create IFRS journal"""
        ifrs_journal = self.env['account.journal'].search([
            ('code', '=', 'IFRS'),
            ('type', '=', 'general')
        ], limit=1)

        if not ifrs_journal:
            ifrs_journal = self.env['account.journal'].create({
                'name': 'IFRS Adjustments',
                'code': 'IFRS',
                'type': 'general',
            })

        return ifrs_journal