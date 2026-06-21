from odoo import models


class IncomeStatementReport(models.AbstractModel):
    _name = "primetech.income.statement.report"
    _description = "Compte de Résultat OHADA"


    # =====================================================
    # MAPPING OHADA
    # =====================================================

    OHADA_MAPPING = {

        "TA": ["70"],
        "RA": ["60"],
        "RB": ["603"],

        "TB": ["701"],
        "TC": ["706"],
        "TD": ["707"],

        "TE": ["71"],
        "TF": ["72"],
        "TG": ["74"],
        "TH": ["75"],
        "TI": ["78"],

        "RC": ["601"],
        "RD": ["6031"],
        "RE": ["602"],
        "RF": ["6032"],

        "RG": ["61"],
        "RH": ["62"],
        "RI": ["63"],
        "RJ": ["65"],

        "RK": ["64"],

        "TJ": ["78"],
        "RL": ["68"],

        "TK": ["77"],
        "TL": ["797"],
        "TM": ["79"],

        "RM": ["67"],
        "RN": ["697"],

        "TN": ["84"],
        "TO": ["85"],

        "RO": ["81"],
        "RP": ["83"],

        "RQ": ["87"],
        "RS": ["89"],
    }


    # =====================================================
    # SOLDE PAR PREFIXE
    # =====================================================

    def _get_amount_by_prefixes(
        self,
        prefixes,
        date_from,
        date_to,
        company,
    ):

        domain = [

            ("date", ">=", date_from),
            ("date", "<=", date_to),

            ("parent_state", "=", "posted"),

            ("company_id", "=", company.id),

        ]

        lines = self.env[
            "account.move.line"
        ].search(domain)

        amount = 0.0

        for line in lines:

            code = (
                line.account_id.code
                or ""
            )

            if any(
                code.startswith(prefix)
                for prefix in prefixes
            ):

                amount += (
                    line.credit
                    -
                    line.debit
                )

        return amount


    # =====================================================
    # RUBRIQUE
    # =====================================================

    def _get_rubric_amount(
        self,
        code,
        date_from,
        date_to,
        company,
    ):

        prefixes = self.OHADA_MAPPING.get(
            code,
            []
        )

        return self._get_amount_by_prefixes(

            prefixes,

            date_from,

            date_to,

            company,

        )


    # =====================================================
    # RAPPORT
    # =====================================================

    def get_report_data(
        self,
        date_from,
        date_to,
        company,
    ):

        values = {}

        for code in self.OHADA_MAPPING:

            values[code] = (
                self._get_rubric_amount(
                    code,
                    date_from,
                    date_to,
                    company,
                )
            )

        # ==========================================
        # SOLDES INTERMEDIAIRES
        # ==========================================

        values["XA"] = (

            values["TA"]

            - values["RA"]

            + values["RB"]

        )

        values["XB"] = (

            values["TB"]

            + values["TC"]

            + values["TD"]

        )

        values["XC"] = (

            values["XB"]

            + values["TG"]

            + values["TH"]

            + values["TI"]

            - values["RC"]

            - values["RD"]

            - values["RE"]

            - values["RF"]

            - values["RG"]

            - values["RH"]

            - values["RI"]

            - values["RJ"]

        )

        values["XD"] = (

            values["XC"]

            - values["RK"]

        )

        values["XE"] = (

            values["XD"]

            + values["TJ"]

            - values["RL"]

        )

        values["XF"] = (

            values["TK"]

            + values["TL"]

            + values["TM"]

            - values["RM"]

            - values["RN"]

        )

        values["XG"] = (

            values["XE"]

            + values["XF"]

        )

        values["XH"] = (

            values["TN"]

            + values["TO"]

            - values["RO"]

            - values["RP"]

        )

        values["XI"] = (

            values["XG"]

            + values["XH"]

            - values["RQ"]

            - values["RS"]

        )

        return values