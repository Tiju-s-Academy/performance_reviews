from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class PerformanceRRE(models.Model):
    _name = 'performance.rre'
    _description = 'Roles, Responsibilities and Expectations'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'rre_date desc'

    def _default_employee(self):
        return self.env.user.id

    employee_id = fields.Many2one('res.users', string='Employee', required=True,
                                default=_default_employee, tracking=True)
    rre_date = fields.Date(string='RRE Date', required=True, default=fields.Date.today,
                          tracking=True)
    discussion_date = fields.Date(string='Discussion Date', required=True,
                                tracking=True)
    roles = fields.Text(string='Roles', required=True, tracking=True)
    responsibilities = fields.Text(string='Responsibilities', required=True,
                                 tracking=True)
    expectations = fields.Text(string='Expectations', required=True, tracking=True)
    overall_comment = fields.Text(string='Overall Comment', required=True,
                                tracking=True)
    manager_feedback = fields.Text(string='Manager Feedback', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted_by_employee', 'Submitted by Employee'),
        ('reviewed_by_manager', 'Reviewed by Manager')
    ], string='Status', default='draft', tracking=True)

    @api.constrains('discussion_date')
    def _check_discussion_date(self):
        for record in self:
            if record.discussion_date > fields.Date.today():
                raise ValidationError(_("Discussion date cannot be in the future."))

    @api.constrains('roles', 'responsibilities', 'expectations', 'overall_comment',
                    'manager_feedback')
    def _check_required_fields(self):
        for record in self:
            # Check for empty or whitespace-only content
            if any(not field.strip() if field else True for field in [
                record.roles, record.responsibilities, record.expectations,
                record.overall_comment
            ]):
                raise ValidationError(_("All required text fields must be filled."))

            # Check word count limits
            if len(record.roles.split()) > 300:
                raise ValidationError(_("Roles must not exceed 300 words."))
            
            for field in [record.responsibilities, record.expectations,
                         record.overall_comment]:
                if len(field.split()) > 5000:
                    raise ValidationError(_("Text fields must not exceed 5000 words."))
            
            if record.manager_feedback and len(record.manager_feedback.split()) > 500:
                raise ValidationError(_("Manager feedback must not exceed 500 words."))

            # Check for alphanumeric content (with basic punctuation)
            pattern = r'^[a-zA-Z0-9\s.,!?()-]*$'
            for field, field_name in [
                (record.roles, 'Roles'),
                (record.responsibilities, 'Responsibilities'),
                (record.expectations, 'Expectations')
            ]:
                if not re.match(pattern, field):
                    raise ValidationError(
                        _("%s must contain only alphanumeric characters and basic "
                          "punctuation.") % field_name)

    def action_submit_rre(self):
        """Submit RRE to manager"""
        self.ensure_one()
        if self.env.user != self.employee_id:
            raise ValidationError(_("Only the employee can submit their own RRE."))
        
        self.state = 'submitted_by_employee'
        
        # Send email to manager
        template = self.env.ref('performance_reviews.email_template_rre_submitted')
        template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('RRE has been submitted to your manager.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_submit_review(self):
        """Submit manager's review"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_manager'):
            raise ValidationError(_("Only managers can submit reviews."))
        
        if not self.manager_feedback:
            raise ValidationError(_("Please provide feedback before submitting the review."))
        
        self.state = 'reviewed_by_manager'
        
        # Send email to employee
        template = self.env.ref('performance_reviews.email_template_rre_reviewed')
        template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Review has been submitted successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
