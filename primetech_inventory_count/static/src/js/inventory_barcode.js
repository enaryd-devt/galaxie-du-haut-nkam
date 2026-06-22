/** @odoo-module **/

console.log("PRIMETECH BARCODE LOADED");

setInterval(() => {

    const barcodeInput =
        document.querySelector("#barcode_scan_0");

    const recordInput =
        document.querySelector("#record_id_0");

    if (
        !barcodeInput ||
        !recordInput ||
        barcodeInput.dataset.ready
    ) {
        return;
    }

    barcodeInput.dataset.ready = "1";

    console.log("SCANNER ATTACHE");

    barcodeInput.addEventListener(
        "keydown",
        async function (ev) {

            if (ev.key !== "Enter") {
                return;
            }

            ev.preventDefault();

            const barcode =
                (barcodeInput.value || "").trim();

           const match =
                window.location.href.match(/\/(\d+)(\?|$)/);

            const sheetId =
                match ? parseInt(match[1]) : false;

            console.log("SHEET ID =", sheetId);

            console.log(
                "SHEET ID =",
                sheetId
            );

            console.log(
                "BARCODE =",
                barcode
            );

            if (!sheetId) {

                alert(
                    "Impossible de récupérer l'ID de la feuille."
                );

                return;
            }

            try {

                const currentUrl = window.location.href;

                console.log(currentUrl);

                const match = currentUrl.match(/\/(\d+)(\?|$)/);

                const sheetId = match
                    ? parseInt(match[1])
                    : false;

                console.log("SHEETID =", sheetId);

                console.log(result);

                if (result.success) {

                    barcodeInput.value = "";

                    setTimeout(() => {
                        location.reload();
                    }, 300);

                } else {

                    alert(result.message);

                    barcodeInput.value = "";

                    barcodeInput.focus();
                }

            } catch (error) {

                console.error(error);

                alert(
                    "Erreur lors du scan."
                );
            }
        }
    );
console.log("URL =", window.location.href);

}, 1000);