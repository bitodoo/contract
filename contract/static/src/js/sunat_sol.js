/** @odoo-module **/

import { registry } from "@web/core/registry";

// Handler de la acción cliente "kaypi_sunat_sol_open".
// Abre una nueva pestaña hacia SUNAT colocando las credenciales en window.name
// (sobrevive a las redirecciones OAuth de SUNAT). Un bookmarklet que el operador
// haya guardado en su barra de favoritos lee window.name y rellena el formulario
// loginMenuSol.
function sunatSolOpen(env, action) {
    const params = (action && action.params) || {};
    const sunatUrl = params.sunat_url || "https://www.sunat.gob.pe/sol.html";
    const creds = params.creds || {};
    const payload = JSON.stringify({ kaypi_sol: creds });
    const win = window.open(sunatUrl, payload);
    if (!win) {
        env.services.notification.add(
            "El navegador bloqueó la apertura de la nueva pestaña. Habilita pop-ups para este sitio.",
            { type: "warning", sticky: true }
        );
    }
    return { type: "ir.actions.act_window_close" };
}

registry.category("actions").add("kaypi_sunat_sol_open", sunatSolOpen);
