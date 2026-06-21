from datetime import timedelta

from odoo import (
    api,
    fields,
    models,
)


class IncomeStatementReportWizard(
    models.TransientModel
):
    _name = (
        "primetech.income.statement.report.wizard"
    )

    _description = (
        "Compte de Résultat OHADA"
    )

    # =====================================================
    # FILTRES
    # =====================================================

    date_from = fields.Date(
        string="Date Début",
        required=True,
    )

    date_to = fields.Date(
        string="Date Fin",
        required=True,
        default=fields.Date.today,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Société",
        required=True,
        default=lambda self:
        self.env.company,
    )

    compare_previous = fields.Boolean(
        string="Comparer N-1",
        default=True,
    )

    # =====================================================
    # DEFAULTS
    # =====================================================

    @api.model
    def default_get(
        self,
        fields_list,
    ):

        res = super().default_get(
            fields_list
        )

        today = fields.Date.today()

        res.update({

            "date_from":
                today.replace(
                    month=1,
                    day=1,
                ),

            "date_to":
                today,

        })

        return res

    # =====================================================
    # DATA
    # =====================================================

    def _get_report_data(self):

        report = self.env[
            "primetech.income.statement.report"
        ]

        return report.get_report_data(

            self.date_from,

            self.date_to,

            self.company_id,

        )

    # =====================================================
    # N-1
    # =====================================================

    def _get_previous_period_data(
        self,
    ):

        report = self.env[
            "primetech.income.statement.report"
        ]

        period_days = (

            self.date_to
            -
            self.date_from

        ).days + 1

        previous_end = (
            self.date_from
            -
            timedelta(days=1)
        )

        previous_start = (
            previous_end
            -
            timedelta(
                days=period_days - 1
            )
        )

        return report.get_report_data(

            previous_start,

            previous_end,

            self.company_id,

        )

    # =====================================================
    # APERCU
    # =====================================================

    def action_preview(self):

        self.ensure_one()

        data = self._get_report_data()

        previous_data = {}

        if self.compare_previous:

            previous_data = (
                self._get_previous_period_data()
            )

        html = self.env[
            "ir.qweb"
        ]._render(

            "primetech_reporting_center.income_statement_preview_template",

            {

                "wizard":
                    self,

                "data":
                    data,

                "previous_data":
                    previous_data,

            }

        )

        preview = self.env[
            "primetech.report.preview.wizard"
        ].create({

            "name":
                "Compte de Résultat OHADA",

            "html_content":
                html,

            "report_xmlid":
                "primetech_reporting_center.action_income_statement_pdf",

            "wizard_id":
                self.id,

        })

        return {

            "type":
                "ir.actions.act_window",

            "res_model":
                "primetech.report.preview.wizard",

            "view_mode":
                "form",

            "target":
                "new",

            "res_id":
                preview.id,

        }

    # =====================================================
    # PDF
    # =====================================================

    def action_print_pdf(self):

        self.ensure_one()

        return self.env.ref(

            "primetech_reporting_center.action_income_statement_pdf"

        ).report_action(self)

    # =====================================================
    # XLSX
    # =====================================================

    def action_export_xlsx(self):

        self.ensure_one()

        return self.env.ref(

            "primetech_reporting_center.action_income_statement_xlsx"

        ).report_action(self)