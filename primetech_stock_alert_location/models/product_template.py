from odoo import api, fields, models
from markupsafe import Markup
from collections import defaultdict

class ProductTemplate(models.Model):
    _inherit = "product.template"

    stock_alert_ids = fields.One2many(
        "stock.location.alert",
        "product_tmpl_id",
        string="Stock par emplacement",
    )

    has_stock_alerts = fields.Boolean(
        compute="_compute_has_stock_alerts",
    )

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

    
    
    # =====================================================
    # FORMATAGE DES NOMBRES
    # =====================================================

   
   
    def _fmt_qty(self, value):

            value = value or 0

            if float(value).is_integer():
                return f"{int(value):,}".replace(",", " ")

            return (
                f"{value:,.2f}"
                .replace(",", " ")
                .replace(".", ",")
            )
        


    @api.depends("stock_alert_ids")
    def _compute_has_stock_alerts(self):
        for product in self:
            product.has_stock_alerts = bool(product.stock_alert_ids)
             

    def action_sync_stock(self):
        self.ensure_one()
        return self.product_variant_id.action_sync_stock()



    # =====================================================
    # STOCK PAR MAGASIN & EMPLACEMENT
    # =====================================================
    @api.depends(
        "qty_available",
        "packaging_ids",
    )
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
                    gap:8px;
                    margin:2px 0;
                ">

                    <span style="
                        min-width:60px;
                        font-size:15px;
                        font-weight:600;
                        color:#147044;
                        font-variant-numeric:tabular-nums;
                    ">
                        {fmt(packaging_count)} {packaging.name}
                    </span>

            
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
                        font-size:13px;
                        font-weight:600;
                        color:#000040;
                        font-variant-numeric:tabular-nums;
                    ">
                        {fmt(remaining)} non conditionnée(s)
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

                {"".join(rows)}

            </div>
            """)




