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
    nubefact_start_date = fields.Date(string="F. Inicio", help="Enviado a Nubefact desde")
    nubefact_end_date = fields.Date(string="F. Fin", help="Hasta")
    total_comprobantes = fields.Integer(string="Total Comprobantes", help="Total de comprobantes enviados a Nubefact.")
    message_sent_to_whatsapp = fields.Boolean(
        string="Enviado a Whatsapp", default=False,
        help="Indica si el mensaje fue enviado a whatsapp.")

    @api.depends('amount_total', 'comission')
    def _compute_utility(self):
        for order in self:
            order.update({
                'utility': order.amount_total - order.comission,
            })

    def get_total_documents(self):
        if self.is_nubefact:
            models, db, uid, password = self.contract_id.server_id.ConnectClient()
            total = models.execute_kw(db, uid, password, 'account.move', 'search_count', [[
                ('l10n_pe_edi_date_ose_accepted',  '>=', self.nubefact_start_date),
                ('l10n_pe_edi_date_ose_accepted', '<=', self.nubefact_end_date),
                ('l10n_pe_edi_ose_accepted', '=', True),
            ]])
            self.total_comprobantes = total
    
    @api.model
    def cron_recurring_send_whatsapp_invoice(self):
        print('cron_recurring_send_whatsapp_invoice')
        MessageWizard = self.env['acrux.chat.message.wizard']
        domain = [
            ('partner_id.mobile', '!=', False),
            ('state', '=', 'posted'),
            ('contract_id.send_whatsapp', '=', True),
            ('invoice_date', '<=', fields.Date.context_today(self)),
            ('invoice_date_due', '>=', fields.Date.context_today(self)),
            ('message_sent_to_whatsapp', '=', False )
        ]
        moves = self.search(domain)
        for move in moves:
            vals = {
                'new_number': True,
                'conversation_id': False,
                'connector_id': move.contract_id.connector_id.id,
                'number': move.partner_id.mobile,
                'invisible_top': False,
                'template_id': move.contract_id.template_id.id,
                'text': 'Hola, te enviamos tu factura desde el cron.',
                'attachment_ids': [],
                'model': 'account.move',
                'res_id': move.id,
                'partner_id': move.partner_id.id,
            }
            contact_ids = self.env['res.partner'].browse([move.partner_id.id]).contact_ids
            conversation_id = contact_ids[0].id if contact_ids else False
            if conversation_id:
                vals.update({
                    'new_number': False,
                    'conversation_id': conversation_id,
                    'connector_id': False,
                })
            wizard = MessageWizard.create(vals)
            wizard.onchange_template_id_wrapper()
            # Por alguna razon se borrar el registro de ir.attachment cuando
            # se ejecuta desde el cron por eso se puso el commit
            wizard._cr.commit()
            wizard.send_message_wizard()
            print("Mensaje enviado a whatsapp.")
            move.message_sent_to_whatsapp = True
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    contract_line_id = fields.Many2one(
        "contract.line", string="Contract Line", index=True
    )
