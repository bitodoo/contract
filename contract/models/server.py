from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class KaServer(models.Model):
    _name = "ka.server"
    _description = "Server"
    _order = "name asc"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(
        default=True,
    )
    code = fields.Char(string="Referencia")
    note = fields.Text(string="Notas")
    version = fields.Selection([
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ], string="Version", default='15')
    db = fields.Char(string="Base de datos", required=True)
    username_admin = fields.Char(string="Usuario administrator", required=True)
    password_admin = fields.Char(string="Contraseña administrator", required=True)
