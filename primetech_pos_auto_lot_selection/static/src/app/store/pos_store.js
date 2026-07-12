/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {

        if (!this.config.enable_auto_lot_selection) {
            return await super.addLineToOrder(vals, order, opts, configure);
        }

        configure = false;

        // ============================================================
        // NORMALISATION DE LA QUANTITE
        // ============================================================

        const requestedQty = Number(vals.qty || 1);

        if (requestedQty <= 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Quantité invalide"),
                body: _t("La quantité doit être supérieure à 0."),
            });
            return;
        }

        // ============================================================
        // RECUPERATION DU PRODUIT
        // ============================================================

        if (typeof vals.product_id === "number") {
            vals.product_id =
                this.data.models["product.product"].get(vals.product_id);
        }

        const product = vals.product_id;

        if (!product) {
            return;
        }

        // ============================================================
        // QUANTITE DEJA PRESENTE DANS LE TICKET
        // ============================================================

        const usedQty = getUsedQty(order, product.id);

        function getUsedQty(order, productId) {

            let used = 0;

            order.get_orderlines().forEach((line) => {
                if (line.product_id.id === productId) {
                    used += line.qty;
                }
            });

            return used;
        }

        // ============================================================
        // PRODUIT SOUMIS AU SUIVI DE STOCK ?
        // ============================================================

        const isStockManaged =
            product.is_storable === true ||
            product.type === "product";

        let availableQty = 0;

        if (isStockManaged) {

            const [res] = await this.env.services.orm.read(
                "product.product",
                [product.id],
                ["qty_available"]
            );

            availableQty = res.qty_available;

            // Blocage uniquement des produits stockables
            if ((availableQty - usedQty) < requestedQty) {

                this.dialog.add(AlertDialog, {
                    title: _t("Stock insuffisant"),
                    body: _t("La quantité demandée dépasse le stock disponible."),
                });

                return;
            }
        }

        // ============================================================
        // PRODUIT AVEC OU SANS TRACKING
        // ============================================================

        const hasTracking =
            product.tracking === "lot" ||
            product.tracking === "serial";

        // Produit sans lot/série
        if (!hasTracking) {

            return await super.addLineToOrder(
                {
                    ...vals,
                    qty: requestedQty,
                },
                order,
                opts,
                configure
            );
        }

        // ============================================================
        // ALLOCATION FEFO
        // ============================================================

        let allocations = [];

        if (product.tracking !== "none") {

            allocations = await this.env.services.orm.call(
                "stock.lot",
                "allocate_fefo_lots",
                [],
                {
                    product_id: product.id,
                    requested_qty: requestedQty,
                }
            ) || [];
        }

        console.log("Produit :", product.display_name);
        console.log("Tracking :", product.tracking);
        console.log("Demandé :", requestedQty);
        console.log("Stock :", availableQty);
        console.log("Lots FEFO :", allocations);

        // ============================================================
        // FALLBACK SI AUCUN LOT RETOURNE
        // ============================================================

        if (
            product.tracking === "lot" &&
            allocations.length === 0
        ) {

            if (isStockManaged && availableQty < requestedQty) {

                this.dialog.add(AlertDialog, {
                    title: _t("Stock insuffisant"),
                    body: _t("Quantité insuffisante pour la vente."),
                });

                return;
            }

            return await super.addLineToOrder(
                {
                    ...vals,
                    qty: requestedQty,
                },
                order,
                opts,
                false
            );
        }

        // ============================================================
        // SERIAL TRACKING
        // ============================================================

        if (product.tracking === "serial") {
                        let existingOrderline = null;
            let allUsedSerials = [];

            order.get_orderlines().forEach((line) => {

                if (line.product_id.id !== product.id) {
                    return;
                }

                existingOrderline = line;

                if (line.pack_lot_ids?.length) {

                    line.pack_lot_ids.forEach((pl) => {
                        allUsedSerials.push(pl.lot_name);
                    });

                }

            });

            // ============================================================
            // RECHERCHE DU PREMIER NUMERO DE SERIE DISPONIBLE
            // ============================================================

            let selectedLot = null;

            for (const lot of allocations) {

                if (
                    !allUsedSerials.includes(lot.name) &&
                    lot.available_qty > 0
                ) {

                    selectedLot = lot;
                    break;

                }

            }

            if (!selectedLot) {

                this.dialog.add(AlertDialog, {
                    title: _t("Numéro de série indisponible"),
                    body: _t("Aucun numéro de série disponible pour ce produit."),
                });

                return;

            }

            // ============================================================
            // LE PRODUIT EXISTE DEJA DANS LE TICKET
            // ============================================================

            if (existingOrderline) {

                const allLots = [];

                if (existingOrderline.pack_lot_ids?.length) {

                    existingOrderline.pack_lot_ids.forEach((pl) => {

                        allLots.push({
                            lot_name: pl.lot_name,
                        });

                    });

                }

                allLots.push({
                    lot_name: selectedLot.name,
                });

                existingOrderline.setPackLotLines({

                    modifiedPackLotLines: [],

                    newPackLotLines: allLots,

                    setQuantity: true,

                });

                return existingOrderline;

            }

            // ============================================================
            // CREATION D'UNE NOUVELLE LIGNE
            // ============================================================

            const orderline = await super.addLineToOrder(
                {
                    ...vals,
                    qty: 1,
                },
                order,
                opts,
                false
            );

            orderline.setPackLotLines({

                modifiedPackLotLines: [],

                newPackLotLines: [
                    {
                        lot_name: selectedLot.name,
                    },
                ],

                setQuantity: true,

            });

            return orderline;
        }

        // ============================================================
        // TRACKING PAR LOT (FEFO)
        // ============================================================

        else if (product.tracking === "lot") {

            let remainingQty = requestedQty;

            const allocatedLots = [];

            for (const lot of allocations) {

                if (remainingQty <= 0) {
                    break;
                }

                let usedLotQty = 0;

                order.get_orderlines().forEach((line) => {

                    if (
                        line.product_id.id === product.id &&
                        line.pack_lot_ids?.length
                    ) {

                        line.pack_lot_ids.forEach((pl) => {

                            if (pl.lot_name === lot.name) {
                                usedLotQty += line.qty;
                            }

                        });

                    }

                });

                const remainingLotQty =
                    lot.available_qty - usedLotQty;

                if (remainingLotQty <= 0) {
                    continue;
                }

                const qtyToTake = Math.min(
                    remainingLotQty,
                    remainingQty
                );

                allocatedLots.push({

                    lot_name: lot.name,

                    qty: qtyToTake,

                });

                remainingQty -= qtyToTake;

            }

            if (remainingQty > 0) {

                this.dialog.add(AlertDialog, {
                    title: _t("Stock insuffisant"),
                    body: _t("La quantité demandée dépasse le stock disponible."),
                });

                return;

            }

            let firstLine = null;
                        // ============================================================
            // CREATION DES LIGNES DE COMMANDE PAR LOT
            // ============================================================

            for (const alloc of allocatedLots) {

                const orderline = await super.addLineToOrder(
                    {
                        ...vals,
                        qty: alloc.qty,
                    },
                    order,
                    opts,
                    false
                );

                orderline.setPackLotLines({
                    modifiedPackLotLines: [],
                    newPackLotLines: [
                        {
                            lot_name: alloc.lot_name,
                        },
                    ],
                    setQuantity: true,
                });

                if (!firstLine) {
                    firstLine = orderline;
                }
            }

            return firstLine;
        }

        // ============================================================
        // SECURITE (CAS NON PREVU)
        // ============================================================

        return await super.addLineToOrder(
            {
                ...vals,
                qty: requestedQty,
            },
            order,
            opts,
            configure
        );
    },
});