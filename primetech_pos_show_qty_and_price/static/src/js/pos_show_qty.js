import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {

    async afterLoadServerData() {
        await super.afterLoadServerData(...arguments);

        const products = this.models["product.product"].getAll();

        const productIds = products.map(p => p.id);

        const stocks = await this.env.services.orm.read(
            "product.product",
            productIds,
            ["qty_available"]
        );

        const stockMap = new Map(
            stocks.map(s => [s.id, s.qty_available])
        );

        for (const product of products) {
            if (stockMap.has(product.id)) {
                product.qty_available = stockMap.get(product.id);
            }
        }
    },
});