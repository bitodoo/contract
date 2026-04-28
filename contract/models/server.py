import re
import xmlrpc.client
import time
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)

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
        ], string="Version", default='17', required=True)
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
        if self.version in ['14', '15', '16', '17']:
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
            if self.version in ['14', '15', '16', '17']:
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

        message='Test connection successful.'
        print(message)

    def ConnectClient(self):
        db = self.db
        username = self.username_admin
        password = self.password_admin
        try:
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.website))
            uid = common.authenticate(db, username, password, {})

            # Conexión a la API de objetos
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.website))
            return models, db, uid, password
        except ConnectionRefusedError as e:
            _logger.error("ConnectionRefusedError occurred: [Errno 111] Conexión rehusada a %s", self.website)

    def _detect_cpe_server_model(self, rmodels, db, uid, password):
        # Detecta el modelo remoto referenciado por res.company.pe_cpe_server_id (v11)
        field_def = rmodels.execute_kw(
            db, uid, password,
            'ir.model.fields', 'search_read',
            [[('model', '=', 'res.company'), ('name', '=', 'pe_cpe_server_id')]],
            {'fields': ['relation'], 'limit': 1},
        )
        if not field_def or not field_def[0].get('relation'):
            raise UserError(_("No se pudo detectar el modelo remoto de pe_cpe_server_id."))
        return field_def[0]['relation']

    def action_open_sunat_sol(self):
        self.ensure_one()
        if self.version not in ('11', '17'):
            raise UserError(_("Auto-login SOL solo está soportado para versiones 11 y 17."))

        conn = self.ConnectClient()
        if not conn:
            raise UserError(_("No se pudo conectar al servidor del cliente."))
        rmodels, db, uid, password = conn

        ruc = sol_user = sol_pass = ''
        try:
            if self.version == '17':
                company = rmodels.execute_kw(
                    db, uid, password,
                    'res.company', 'read',
                    [[1]],
                    {'fields': ['vat', 'pe_ws_user', 'pe_ws_password']},
                )
                if not company:
                    raise UserError(_("No se encontró la compañía 1 en el servidor remoto."))
                ruc = company[0].get('vat') or ''
                sol_user = company[0].get('pe_ws_user') or ''
                sol_pass = company[0].get('pe_ws_password') or ''
            else:  # version == '11'
                company = rmodels.execute_kw(
                    db, uid, password,
                    'res.company', 'read',
                    [[1]],
                    {'fields': ['vat', 'pe_cpe_server_id']},
                )
                if not company:
                    raise UserError(_("No se encontró la compañía 1 en el servidor remoto."))
                ruc = company[0].get('vat') or ''
                cpe_ref = company[0].get('pe_cpe_server_id')
                if not cpe_ref:
                    raise UserError(_("La compañía remota no tiene 'pe_cpe_server_id' configurado."))
                cpe_id = cpe_ref[0] if isinstance(cpe_ref, (list, tuple)) else cpe_ref
                cpe_model = self._detect_cpe_server_model(rmodels, db, uid, password)
                cpe = rmodels.execute_kw(
                    db, uid, password,
                    cpe_model, 'read',
                    [[cpe_id]],
                    {'fields': ['user', 'password']},
                )
                if not cpe:
                    raise UserError(_("No se pudo leer las credenciales del servidor CPE remoto."))
                sol_user = cpe[0].get('user') or ''
                sol_pass = cpe[0].get('password') or ''
        except xmlrpc.client.Fault as e:
            _logger.exception("xmlrpc Fault al leer credenciales SOL: %s", e)
            raise UserError(_("Error XMLRPC al leer credenciales del cliente: %s") % e)

        # Normalizar RUC: extraer los 11 dígitos (en v11 el vat viene como "PER10430268436")
        if ruc:
            m = re.search(r'\d{11}', ruc)
            if m:
                ruc = m.group(0)

        if not (ruc and sol_user and sol_pass):
            raise UserError(_(
                "Faltan credenciales en el cliente remoto.\nRUC: %s\nUsuario: %s\nClave: %s"
            ) % (ruc or '(vacío)', sol_user or '(vacío)', '***' if sol_pass else '(vacío)'))

        return {
            'type': 'ir.actions.client',
            'tag': 'kaypi_sunat_sol_open',
            'params': {
                'sunat_url': 'https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm',
                'creds': {'ruc': ruc, 'user': sol_user, 'pass': sol_pass},
            },
        }

