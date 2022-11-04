from odoo import api, fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Payment Mode",
        domain=[("payment_type", "=", "inbound")],
        index=True,
    )
    partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        compute="_compute_partner_bank_id",
        store=True,
        ondelete="restrict",
        readonly=False,
    )

    @api.onchange("partner_id")
    def on_change_partner_id(self):
        self.payment_mode_id = self.partner_id.customer_payment_mode_id.id
    
    @api.depends("partner_id", "payment_mode_id")
    def _compute_partner_bank_id(self):
        for move in self:
            # No bank account assignation is done for out_invoice as this is only
            # needed for printing purposes and it can conflict with
            # SEPA direct debit payments. Current report prints it.
            def get_bank_id():
                return fields.first(
                    move.commercial_partner_id.bank_ids.filtered(
                        lambda b: b.company_id == move.company_id or not b.company_id
                    )
                )

            bank_id = False
            if move.partner_id:
                pay_mode = move.payment_mode_id
                if (
                    pay_mode
                    and pay_mode.payment_type == "outbound"
                    and pay_mode.payment_method_id.bank_account_required
                    and move.commercial_partner_id.bank_ids
                ):
                    bank_id = get_bank_id()
            move.partner_bank_id = bank_id

    def _prepare_invoice(self, date_invoice, journal=None):
        invoice_vals, move_form = super()._prepare_invoice(
            date_invoice=date_invoice, journal=journal
        )
        if self.payment_mode_id:
            invoice_vals["payment_mode_id"] = self.payment_mode_id.id
        if self.partner_bank_id:
            invoice_vals["partner_bank_id"] = self.partner_bank_id.id
        return invoice_vals, move_form
