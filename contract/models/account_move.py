# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2018 ACSONE SA/NV.
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    # We keep this field for migration purpose
    old_contract_id = fields.Many2one("contract.contract")
    contract_id = fields.Many2one("contract.contract", string="Contrato")
    comission = fields.Monetary(
        string='Comisión',
        tracking=4,
        readonly=True
    )
    utility = fields.Monetary(
        string='Utilidad',
        tracking=4,
        store=True,
        compute='_compute_utility',
    )
    website = fields.Char(related="contract_id.website")
    mobile = fields.Char(related="partner_id.mobile")
    is_nubefact = fields.Boolean(string="Nubefact?",related="contract_id.is_nubefact", store=True)

    @api.depends('amount_total', 'comission')
    def _compute_utility(self):
        for order in self:
            order.update({
                'utility': order.amount_total - order.comission,
            })


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    contract_line_id = fields.Many2one(
        "contract.line", string="Contract Line", index=True
    )
