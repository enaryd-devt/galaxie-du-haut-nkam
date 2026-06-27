# -*- coding: utf-8 -*-

from odoo import api, fields, models
from markupsafe import Markup
from collections import defaultdict



class ProductProduct(models.Model):
    _inherit = "product.product"


    packaging_summary = fields.Html(
        string="Résumé des conditionnements",
        compute="_compute_packaging_summary",
        sanitize=False,
    )

    warehouse_summary = fields.Html(
        string="Stock par magasin",
        compute="_compute_stock_summary",
        sanitize=False,
    )

    location_summary = fields.Html(
        string="Stock par emplacement",
        compute="_compute_stock_summary",
        sanitize=False,
    )

    # =====================================================
    # TABLEAU DES STOCKS
    # =====================================================

    stock_alert_ids = fields.One2many(
        "stock.location.alert",
        "product_id",
        string="Stock par emplacement",
        copy=False,
    )

    has_stock_alerts = fields.Boolean(
        compute="_compute_has_stock_alerts",
    )


    @api.depends()
    def _compute_stock_summary(self):

        Quant = self.env["stock.quant"]
        Warehouse = self.env["stock.warehouse"]

        for product in self:

            quants = Quant.search([
                ("product_id", "=", product.id),
                ("location_id.usage", "=", "internal"),
            ])

            # =====================================================
            # PAR MAGASIN
            # =====================================================

            warehouse_data = defaultdict(lambda: {
                "qty": 0,
                "reserved": 0,
                "locations": set(),
            })

            # =====================================================
            # PAR EMPLACEMENT
            # =====================================================

            location_rows = ""

            for quant in quants:

                warehouse = Warehouse.search([
                    ("view_location_id", "parent_of", quant.location_id.id)
                ], limit=1)

                if warehouse:

                    warehouse_data[warehouse.name]["qty"] += quant.quantity
                    warehouse_data[warehouse.name]["reserved"] += quant.reserved_quantity
                    warehouse_data[warehouse.name]["locations"].add(
                        quant.location_id.display_name
                    )

                available = quant.quantity - quant.reserved_quantity

                location_rows += f"""
                <tr>

                    <td>{quant.location_id.display_name}</td>

                    <td style="text-align:center;">
                        {quant.lot_id.name if quant.lot_id else '-'}
                    </td>

                    <td style="text-align:center;">
                        {available:.2f}
                    </td>

                    <td style="text-align:center;">
                        {quant.reserved_quantity:.2f}
                    </td>

                </tr>
                """

            # =====================================================
            # TABLEAU MAGASINS
            # =====================================================

            warehouse_rows = ""

            for warehouse, vals in warehouse_data.items():

                available = vals["qty"] - vals["reserved"]

                warehouse_rows += f"""
                <tr>

                    <td>{warehouse}</td>

                    <td style="text-align:center;">
                        {available:.2f}
                    </td>

                    <td style="text-align:center;">
                        {vals["reserved"]:.2f}
                    </td>

                    <td style="text-align:center;">
                        {vals["qty"]:.2f}
                    </td>

                    <td style="text-align:center;">
                        {len(vals["locations"])}
                    </td>

                </tr>
                """

            # =====================================================
            # HTML MAGASINS
            # =====================================================

            product.warehouse_summary = Markup(f"""

            <div style="
                border:1px solid #dee2e6;
                border-radius:10px;
                overflow:hidden;
                margin-bottom:12px;
            ">

                <div style="
                    padding:10px 15px;
                    background:#f8f9fa;
                    font-weight:700;">

                    🏪 Stock par magasin

                </div>

                <table style="
                    width:100%;
                    border-collapse:collapse;">

                    <thead>

                        <tr style="background:#fafafa;">

                            <th>Magasin</th>

                            <th>Disponible</th>

                            <th>Réservé</th>

                            <th>Total</th>

                            <th>Emplacements</th>

                        </tr>

                    </thead>

                    <tbody>

                        {warehouse_rows}

                    </tbody>

                </table>

            </div>

            """)

            # =====================================================
            # HTML EMPLACEMENTS
            # =====================================================

            product.location_summary = Markup(f"""

            <div style="
                border:1px solid #dee2e6;
                border-radius:10px;
                overflow:hidden;
            ">

                <div style="
                    padding:10px 15px;
                    background:#f8f9fa;
                    font-weight:700;">

                    📍 Stock par emplacement

                </div>

                <table style="
                    width:100%;
                    border-collapse:collapse;">

                    <thead>

                        <tr style="background:#fafafa;">

                            <th>Emplacement</th>

                            <th>Lot</th>

                            <th>Disponible</th>

                            <th>Réservé</th>

                        </tr>

                    </thead>

                    <tbody>

                        {location_rows}

                    </tbody>

                </table>

            </div>

            """)

    
    # =====================================================
    # BOUTON ACTUALISER
    # =====================================================

    def action_sync_stock(self):

        self._sync_stock_alerts()

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    # =====================================================
    # SYNCHRONISATION
    # =====================================================

    def _sync_stock_alerts(self):

        Alert = self.env["stock.location.alert"]
        Quant = self.env["stock.quant"]

        for product in self:

            quants = Quant.search([
                ("product_id", "=", product.id),
                ("location_id.usage", "=", "internal"),
                ("quantity", ">", 0),
            ])

            # Toutes les lignes existantes
            existing_alerts = Alert.search([
                ("product_id", "=", product.id),
            ])

            processed = self.env["stock.location.alert"]

            for quant in quants:

                domain = [
                    ("product_id", "=", product.id),
                    ("location_id", "=", quant.location_id.id),
                ]

                if quant.lot_id:
                    domain.append(("lot_id", "=", quant.lot_id.id))
                else:
                    domain.append(("lot_id", "=", False))

                alert = Alert.search(domain, limit=1)

                values = {
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "location_id": quant.location_id.id,
                    "lot_id": quant.lot_id.id or False,
                    "quantity": quant.quantity,
                    "reserved_quantity": quant.reserved_quantity,
                }

                if alert:

                    # On met simplement les quantités à jour.
                    # minimum_qty reste inchangé.
                    alert.write(values)
                    processed |= alert

                else:

                    new_alert = Alert.create({
                        **values,
                        "minimum_qty": 0,
                    })

                    processed |= new_alert

            # Suppression uniquement des lignes devenues inutiles
            (existing_alerts - processed).unlink()

    # =====================================================
    # SYNCHRONISATION AUTOMATIQUE
    # =====================================================

    def read(self, fields=None, load="_classic_read"):

        res = super().read(fields=fields, load=load)

        self._sync_stock_alerts()

        return res
    # =====================================================
    # AFFICHAGE DU TABLEAU
    # =====================================================

    @api.depends("stock_alert_ids")
    def _compute_has_stock_alerts(self):

        Quant = self.env["stock.quant"]

        for product in self:

            product.has_stock_alerts = bool(

                Quant.search_count([

                    ("product_id", "=", product.id),

                    ("location_id.usage", "=", "internal"),

                    ("quantity", ">", 0),

                ])

            )
            
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
    

    # =====================================================
    # STOCK PAR MAGASIN & EMPLACEMENT
    # =====================================================

    @api.depends(
        "product_variant_ids.stock_quant_ids.quantity",
        "product_variant_ids.stock_quant_ids.reserved_quantity",
    )
    def _compute_stock_summary(self):

        Quant = self.env["stock.quant"]
        warehouses = self.env["stock.warehouse"].search([])

        for product in self:

            product.warehouse_summary = False
            product.location_summary = False

            # --------------------------------------------
            # Tous les quants du template
            # --------------------------------------------

            quants = Quant.search([
                ("product_id.product_tmpl_id", "=", product.id),
                ("location_id.usage", "=", "internal"),
                ("quantity", ">", 0),
            ])

            if not quants:
                continue

            warehouse_data = defaultdict(lambda: {
                "available": 0.0,
                "reserved": 0.0,
            })

            location_rows = ""

            # --------------------------------------------
            # Parcours des quants
            # --------------------------------------------

            for quant in quants:

                available = quant.quantity - quant.reserved_quantity

                warehouse = False

                for wh in warehouses:

                    if (
                        quant.location_id.parent_path
                        and wh.view_location_id.parent_path
                        and quant.location_id.parent_path.startswith(
                            wh.view_location_id.parent_path
                        )
                    ):
                        warehouse = wh
                        break

                warehouse_name = (
                    warehouse.display_name
                    if warehouse
                    else "Sans magasin"
                )

                warehouse_data[warehouse_name]["available"] += available
                warehouse_data[warehouse_name]["reserved"] += (
                    quant.reserved_quantity
                )

                location_rows += f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    padding:3px 0;
                    border-bottom:1px solid #F1F3F5;
                ">

                    <span>
                        {quant.location_id.display_name}
                    </span>

                    <span style="
                        font-weight:600;
                        color:#198754;
                    ">
                        {self._fmt_qty(available)}
                        {product.uom_id.display_name}
                    </span>

                </div>
                """

            # --------------------------------------------
            # Résumé magasin
            # --------------------------------------------

            warehouse_rows = ""

            for warehouse_name, vals in sorted(warehouse_data.items()):

                available = vals["available"]

                warehouse_rows += f"""
                <div style="
                    display:flex;
                    align-items:center;
                    margin:5px 0;
                    font-size:14px;
                ">

                    <!-- Nom du magasin -->

                    <span style="
                        color:#2F3B4A;
                        font-weight:500;
                        white-space:nowrap;
                    ">
                        {warehouse_name}
                    </span>

                    <!-- Pointillés -->

                    <div style="
                        flex:1;
                        border-bottom:1px dotted #BFC5CC;
                        margin:0 10px;
                        transform:translateY(-1px);
                    "></div>

                    <!-- Quantité -->

                    <span style="
                        color:#198754;
                        font-weight:700;
                        font-size:15px;
                        font-variant-numeric:tabular-nums;
                        white-space:nowrap;
                    ">
                        {self._fmt_qty(available)}
                    </span>

                    <!-- UDM -->

                    <span style="
                        margin-left:4px;
                        color:#6C757D;
                        font-size:12px;
                        white-space:nowrap;
                    ">
                        {product.uom_id.display_name}
                    </span>

                </div>
                """
            # --------------------------------------------
            # HTML MAGASINS
            # --------------------------------------------

            product.warehouse_summary = Markup(f"""
            <div style="padding:4px 0;">

                <div style="
                    font-size:14px;
                    font-weight:600;
                    color:#495057;
                    margin-bottom:10px;
                ">

                    <i class="fa fa-warehouse"
                    style="color:#0D6EFD;margin-right:6px;"></i>


                </div>

                {warehouse_rows}

            </div>
            """)

            # --------------------------------------------
            # HTML EMPLACEMENTS
            # --------------------------------------------

            product.location_summary = Markup(f"""
            <div style="padding:4px 0;">

                <div style="
                    font-size:14px;
                    font-weight:600;
                    margin-bottom:8px;
                    color:#495057;
                ">

                    <i class="fa fa-location-dot"
                    style="margin-right:6px;color:#0D6EFD;"></i>

                    Stock par emplacement

                </div>

                {location_rows}

            </div>
            """)

    
    
    @api.depends(
        "qty_available",
        "packaging_ids",
    )
    def _compute_packaging_summary(self):

        for product in self:

            product.packaging_summary = False

            stock = product.qty_available or 0

            packagings = product.packaging_ids.filtered(
                lambda p: p.qty > 0
            ).sorted(
                key=lambda p: p.qty,
                reverse=True,
            )

            if not packagings:
                continue

            remaining = stock
            rows = []

            def fmt(value):
                value = value or 0

                if float(value).is_integer():
                    return f"{int(value):,}".replace(",", " ")

                return (
                    f"{value:,.2f}"
                    .replace(",", " ")
                    .replace(".", ",")
                )

            # =====================================================
            # Décomposition du stock
            # =====================================================

            for packaging in packagings:

                qty = packaging.qty or 0

                if qty <= 0:
                    continue

                packaging_count = int(remaining // qty)

                if packaging_count <= 0:
                    continue

                remaining -= packaging_count * qty

            rows.append(f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                padding:10px 0;
                border-bottom:1px solid #F3F4F6;
            ">

                <!-- Icône -->

                <div style="
                    width:34px;
                    height:34px;
                    border-radius:8px;
                    background:#EDF8F0;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    margin-right:12px;
                    flex-shrink:0;
                ">

                    <i class="fa fa-dropbox"
                    style="
                            color:#198754;
                            font-size:15px;
                    "/>

                </div>

                <!-- Conditionnement -->

                <div style="
                    flex:1;
                    min-width:0;
                ">

                    <div style="
                        font-size:13px;
                        font-weight:600;
                        color:#2F3B4A;
                    ">

                        {packaging.name}

                    </div>

                </div>

                <!-- Quantité -->

                <div style="
                    text-align:right;
                    white-space:nowrap;
                ">

                    <div style="
                        font-size:20px;
                        font-weight:700;
                        color:#198754;
                        line-height:18px;
                    ">

                        {fmt(packaging_count)}

                    </div>

                    <div style="
                        font-size:11px;
                        color:#6C757D;
                    ">

                        Conditionnements

                    </div>

                </div>

            </div>
            """)

            # =====================================================
            # Reste non conditionné
            # =====================================================

            if remaining > 0:

                rows.append(f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:8px;
                    margin:2px 0;
                ">

                    <span style="
                        min-width:60px;
                        font-size:17px;
                        font-weight:700;
                        color:#F39C12;
                        font-variant-numeric:tabular-nums;
                    ">
                        {fmt(remaining)}
                    </span>

                    <span style="
                        font-size:14px;
                        color:#6C757D;
                    ">
                        non conditionnées
                    </span>

                </div>
                """)

            # =====================================================
            # Résumé HTML
            # =====================================================

            product.packaging_summary = Markup(f"""
            <div style="
                padding:4px 0;
            ">

                <div style="
                    font-size:14px;
                    font-weight:600;
                    color:#495057;
                    margin-bottom:8px;
                ">

                    <i class="fa fa-boxes-stacked"
                    style="color:#0D6EFD;margin-right:6px;"></i>


                </div>

                {"".join(rows)}

            </div>
            """)      





        