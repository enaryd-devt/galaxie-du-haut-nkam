from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_sourced_by_line_excluded_auto_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse excluded from automatic sale line sourcing",
        config_parameter="sale_sourced_by_line.excluded_auto_warehouse_id",
        help=(
            "This warehouse will never be selected automatically on sale order lines. "
            "Salespeople can still choose it manually."
        ),
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        store=True,
        readonly=False,
    )

    def _get_excluded_auto_warehouse(self):
        warehouse_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_sourced_by_line.excluded_auto_warehouse_id")
        )
        if not warehouse_id or not str(warehouse_id).isdigit():
            return self.env["stock.warehouse"]
        return self.env["stock.warehouse"].browse(int(warehouse_id)).exists()

    def _is_excluded_auto_warehouse(self, warehouse):
        excluded_warehouse = self._get_excluded_auto_warehouse()
        return bool(warehouse and excluded_warehouse and warehouse == excluded_warehouse)

    def _set_best_warehouse_after_product_selection(self):
        warehouse = self._get_best_warehouse() or self._get_fallback_warehouse()
        warehouse_id = warehouse.id if warehouse else False
        self.update({"warehouse_id": warehouse_id})
        return warehouse_id

    def _get_line_company(self):
        self.ensure_one()
        return self.order_id.company_id or self.company_id or self.env.company

    def _get_candidate_auto_warehouses(self):
        self.ensure_one()
        company = self._get_line_company()
        if not company:
            return self.env["stock.warehouse"]

        domain = [("company_id", "in", [company.id, False])]
        excluded_warehouse = self._get_excluded_auto_warehouse()
        if excluded_warehouse:
            domain.append(("id", "!=", excluded_warehouse.id))
        return self.env["stock.warehouse"].search(domain)

    def _get_fallback_warehouse(self):
        self.ensure_one()
        company = self._get_line_company()
        order_warehouse = self.order_id.warehouse_id
        if (
            order_warehouse
            and not self._is_excluded_auto_warehouse(order_warehouse)
            and (
                not order_warehouse.company_id
                or not company
                or order_warehouse.company_id == company
            )
        ):
            return order_warehouse
        return self._get_candidate_auto_warehouses()[:1]

    # =====================================================
    # 🔥 MÉTHODE CENTRALE OPTIMISÉE
    # =====================================================
    def _get_best_warehouse(self):
        self.ensure_one()

        company = self._get_line_company()
        if not self.product_id or not company:
            return False

        warehouses = self._get_candidate_auto_warehouses()
        if not warehouses:
            return False

        # 🔹 Lecture groupée optimisée (1 seule requête SQL)
        grouped_quants = self.env["stock.quant"].read_group(
            domain=[
                ("product_id", "=", self.product_id.id),
                ("location_id.usage", "=", "internal"),
                ("company_id", "in", [company.id, False]),
            ],
            fields=["quantity:sum", "reserved_quantity:sum", "location_id"],
            groupby=["location_id"],
        )

        if not grouped_quants:
            return False

        # 🔹 Stock dispo par location
        location_available = {
            g["location_id"][0]: g["quantity"] - g["reserved_quantity"]
            for g in grouped_quants
            if (g["quantity"] - g["reserved_quantity"]) > 0
        }

        if not location_available:
            return False

        # 🔹 Mapping location → warehouse (optimisé)
        location_obj = self.env["stock.location"]

        best_wh = False
        best_qty = 0

        for wh in warehouses:
            child_locations = set(
                location_obj.search([("id", "child_of", wh.lot_stock_id.id)]).ids
            )

            total = sum(
                qty
                for loc_id, qty in location_available.items()
                if loc_id in child_locations
            )

            if total > best_qty:
                best_qty = total
                best_wh = wh

        return best_wh

    # =====================================================
    # 🔥 ONCHANGE (UI)
    # =====================================================
    @api.onchange("product_id")
    def _onchange_product_set_best_warehouse(self):
        warehouse_id = False
        for line in self:
            if line.product_id:
                warehouse_id = line._set_best_warehouse_after_product_selection()
            elif line._is_excluded_auto_warehouse(line.warehouse_id):
                line.update({"warehouse_id": False})
        if len(self) == 1:
            return {"value": {"warehouse_id": warehouse_id}}
        return {}

    # =====================================================
    # 🔥 CREATE (catalogue inclus)
    # =====================================================
    @api.model
    def create(self, vals):
        line = super().create(vals)

        if line.product_id and (
            not vals.get("warehouse_id")
            or not line._is_excluded_auto_warehouse(line.warehouse_id)
        ):
            line._set_best_warehouse_after_product_selection()

        return line

    # =====================================================
    # 🔥 WRITE (évite reset après modif quantité)
    # =====================================================
    def write(self, vals):
        res = super().write(vals)

        if "product_id" in vals or "product_uom_qty" in vals:
            for line in self:
                if "product_id" in vals:
                    line._set_best_warehouse_after_product_selection()
                elif not line.warehouse_id:
                    line._set_best_warehouse_after_product_selection()

        return res

    # =====================================================
    # 🔥 Neutralise recalcul auto Odoo
    # =====================================================
    @api.depends_context("company")
    def _compute_warehouse_id(self):
        for line in self:
            if (
                not line.warehouse_id
                and not line._is_excluded_auto_warehouse(line.order_id.warehouse_id)
            ):
                line.warehouse_id = line.order_id.warehouse_id

    # =====================================================
    # 🔥 Sécurisation livraison
    # =====================================================
    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)

        if self.warehouse_id:
            values["warehouse_id"] = self.warehouse_id
            values["location_id"] = self.warehouse_id.lot_stock_id.id

        return values
