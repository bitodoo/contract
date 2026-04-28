# Copyright 2020-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from html import escape

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalContract(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "contract_count" in counters:
            contract_model = request.env["contract.contract"]
            contract_count = (
                contract_model.search_count([])
                if contract_model.check_access_rights("read", raise_exception=False)
                else 0
            )
            values["contract_count"] = contract_count
        return values

    def _contract_get_page_view_values(self, contract, access_token, **kwargs):
        values = {
            "page_name": "Contracts",
            "contract": contract,
        }
        return self._get_page_view_values(
            contract, access_token, values, "my_contracts_history", False, **kwargs
        )

    def _get_filter_domain(self, kw):
        return []

    @http.route(
        ["/my/contracts", "/my/contracts/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_contracts(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        contract_obj = request.env["contract.contract"]
        # Avoid error if the user does not have access.
        if not contract_obj.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")
        domain = self._get_filter_domain(kw)
        searchbar_sortings = {
            "date": {"label": _("Date"), "order": "recurring_next_date desc"},
            "name": {"label": _("Name"), "order": "name desc"},
            "code": {"label": _("Reference"), "order": "code desc"},
        }
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]
        # count for pager
        contract_count = contract_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/contracts",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
            },
            total=contract_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        contracts = contract_obj.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_contracts_history"] = contracts.ids[:100]
        values.update(
            {
                "date": date_begin,
                "contracts": contracts,
                "page_name": "Contracts",
                "pager": pager,
                "default_url": "/my/contracts",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("contract.portal_my_contracts", values)

    @http.route(
        ["/my/contracts/<int:contract_contract_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_contract_detail(self, contract_contract_id, access_token=None, **kw):
        try:
            contract_sudo = self._document_check_access(
                "contract.contract", contract_contract_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._contract_get_page_view_values(contract_sudo, access_token, **kw)
        return request.render("contract.portal_contract_page", values)

    @http.route(
        ["/contract/sunat_sol/install"],
        type="http",
        auth="user",
        website=False,
    )
    def sunat_sol_bookmarklet_install(self, **kw):
        bookmarklet = (
            "javascript:(function(){try{"
            "var raw=window.name;"
            "if(!raw){alert('No hay credenciales en window.name. Abre SUNAT desde el botón de Odoo.');return;}"
            "var d=JSON.parse(raw);"
            "if(!d.kaypi_sol){alert('Formato no reconocido en window.name.');return;}"
            "var c=d.kaypi_sol;"
            "var setById=function(id,v){var e=document.getElementById(id);"
            "if(e){e.value=v;"
            "e.dispatchEvent(new Event('input',{bubbles:true}));"
            "e.dispatchEvent(new Event('change',{bubbles:true}));"
            "e.dispatchEvent(new Event('keyup',{bubbles:true}));}};"
            "var btnRuc=document.getElementById('btnPorRuc');"
            "if(btnRuc){try{btnRuc.click();}catch(e){}}"
            "setById('txtRuc',c.ruc);"
            "setById('txtUsuario',c.user);"
            "setById('txtContrasena',c.pass);"
            "window.name='';"
            "setTimeout(function(){"
            "var btn=document.getElementById('btnAceptar');"
            "if(btn){btn.click();}else{alert('No se encontró botón btnAceptar.');}"
            "},150);"
            "}catch(e){alert('Error rellenando: '+e.message);}})();"
        )
        href_attr = escape(bookmarklet, quote=True)
        html = (
            "<!DOCTYPE html>\n"
            "<html lang=\"es\"><head><meta charset=\"utf-8\"/>"
            "<title>Bookmarklet SOL Auto-Login</title>"
            "<style>"
            "body{font-family:-apple-system,system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#2c3e50;line-height:1.5}"
            "h1,h2{color:#1a5fb4}"
            "h2{margin-top:32px;border-bottom:1px solid #e0e0e0;padding-bottom:6px}"
            ".bookmarklet-link{display:inline-block;padding:14px 24px;background:#1a5fb4;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px}"
            ".bookmarklet-link:hover{background:#134a8e}"
            ".step{background:#f6f8fa;padding:16px 20px;border-left:4px solid #1a5fb4;margin:14px 0;border-radius:4px}"
            "code{background:#eee;padding:2px 6px;border-radius:3px;font-size:13px}"
            ".warn{background:#fff8e6;border-left-color:#d9a300}"
            "</style></head><body>"
            "<h1>Bookmarklet SOL Auto-Login</h1>"
            "<p>Esta utilidad permite acceder automáticamente al Menú SOL de SUNAT con las credenciales del cliente. <strong>Solo lo instalas una vez.</strong></p>"
            "<h2>1. Arrastra este botón a tu barra de favoritos</h2>"
            "<p>Asegúrate de tener visible la barra de favoritos (en Chrome: <code>Ctrl+Shift+B</code>).</p>"
            "<p style=\"margin:24px 0\">"
            f"<a class=\"bookmarklet-link\" href=\"{href_attr}\" "
            "onclick=\"alert('No hagas click. Arrastra este botón a tu barra de favoritos.'); return false;\">"
            "SOL Auto-Login</a></p>"
            "<h2>2. Cómo usarlo</h2>"
            "<div class=\"step\"><strong>a.</strong> En Odoo, abre un servicio o contrato y haz click en <strong>Acceder a SOL</strong>.</div>"
            "<div class=\"step\"><strong>b.</strong> Se abrirá el form de login de SUNAT con campos RUC / Usuario / Contraseña.</div>"
            "<div class=\"step\"><strong>c.</strong> Haz click en el favorito <strong>SOL Auto-Login</strong> que guardaste.</div>"
            "<div class=\"step\"><strong>d.</strong> El formulario se rellenará y enviará automáticamente.</div>"
            "<h2>Notas</h2>"
            "<div class=\"step warn\"><ul>"
            "<li>Si la cuenta tiene <strong>captcha</strong> o <strong>MFA</strong>, el form quedará rellenado y solo tendrás que completar el segundo paso.</li>"
            "<li>Las credenciales viajan vía <code>window.name</code> (no quedan en historial). El bookmarklet las borra al usarlas.</li>"
            "<li>Solo funciona si abriste la pestaña SUNAT desde el botón de Odoo.</li>"
            "</ul></div>"
            "</body></html>"
        )
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])
