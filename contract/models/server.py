import xmlrpc.client
import time
from ast import literal_eval

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
        ('11', '11.0'),
        ('12', '12.0'),
        ('13', '13.0'),
        ('14', '14.0'),
        ('15', '15.0'),
        ('16', '16.0'),
        ('17', '17.0'),
        ], string="Version", default='15', required=True)
    db = fields.Char(string="Base de datos", required=True)
    username_admin = fields.Char(string="Usuario administrator", required=True)
    password_admin = fields.Char(string="Contraseña administrator", required=True)
    website = fields.Char(string="Website")
    server_active = fields.Boolean(string="Servidor activo", default=True)
    server_user_ids = fields.Text(string="Usuarios no activos")
    server_notification = fields.Text(
        string="Mensaje de notificación",
        default="Su cuenta a sido suspendido. Puede escribir al siguiente correo hola@kaypi.pe",
        help="Mensaje de notificación para el usuario suspendido. Vera al iniciar sesión.")

    @api.model
    def session_logout_background_function(self):
        db = self.db
        username = self.username_admin
        password = self.password_admin

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.website))
        uid = common.authenticate(db, username, password, {})

        # Conexión a la API de objetos
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.website))

        # Obtener todas las sesiones activas
        sessions = models.execute_kw(db, uid, password, 'res.users', 'search_read', [[('active', '=', True)]], {'fields': ['id']})
        print(sessions)
        if self.version in ['15', '16', '17']:
            user_ids = [item['id'] for item in sessions if item['id'] not in [1, 2]]
        else:
            user_ids = [item['id'] for item in sessions if item['id'] not in [1]]
        print(user_ids)
        for user_id in user_ids:
            models.execute_kw(db, uid, password, 'res.users', 'write', [[user_id], {'active': False}])
        # Tiempo suficiente para que se cierre la session de los clientes
        time.sleep(60)
        for user_id in user_ids:
            models.execute_kw(db, uid, password, 'res.users', 'write', [[user_id], {'active': True}])
        print("Todas las sesiones han sido cerradas.")

    def trigger_background_logout(self):
        self.with_delay().session_logout_background_function()

    def action_server_active(self):
        db = self.db
        username = self.username_admin
        password = self.password_admin

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.website))
        uid = common.authenticate(db, username, password, {})

        # Conexión a la API de objetos
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.website))

        if self.server_active:
            # Obtener todas las sesiones activas
            sessions = models.execute_kw(db, uid, password, 'res.users', 'search_read', [[('active', '=', True)]], {'fields': ['id']})
            if self.version in ['15', '16', '17']:
                user_ids = [item['id'] for item in sessions if item['id'] not in [1, 2]]
            else:
                user_ids = [item['id'] for item in sessions if item['id'] not in [1]]

            for user_id in user_ids:
                models.execute_kw(db, uid, password, 'res.users', 'write', [[user_id], {'active': False}])
            self.server_user_ids = user_ids
            self.server_active = False
        else:
            user_ids = literal_eval(self.server_user_ids)
            for user_id in user_ids:
                models.execute_kw(db, uid, password, 'res.users', 'write', [[user_id], {'active': True}])
            self.server_user_ids = False
            self.server_active = True
        print("Todas las sesiones han sido suspendidas.")

    def action_server_test_connect(self):
        db = self.db
        username = self.username_admin
        password = self.password_admin

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.website))
        uid = common.authenticate(db, username, password, {})

        # Conexión a la API de objetos
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.website))

        # Obtener todas las sesiones activas
        sessions = models.execute_kw(db, uid, password, 'res.users', 'search_read', [[('active', '=', True)]], {'fields': ['id']})

        self.env.user.notify_success(message='Test connection successful.')

    def ConnectClient(self):
        db = self.db
        username = self.username_admin
        password = self.password_admin

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.website))
        uid = common.authenticate(db, username, password, {})

        # Conexión a la API de objetos
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.website))

        return models, db, uid, password
