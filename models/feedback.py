from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PerformanceFeedback(models.Model):
    _name = 'performance.feedback'
    _description = '360 Degree Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        return self.env.user.id

    employee_id = fields.Many2one('res.users', string='Employee', required=True,
                                default=_default_employee, tracking=True)
    reviewers = fields.One2many('performance.reviewer', 'feedback_id',
                               string='Reviewers')
    manager_feedback = fields.Text(string='Manager Feedback', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed')
    ], string='Status', default='draft', tracking=True)

    @api.constrains('reviewers')
    def _check_reviewers(self):
        for record in self:
            if len(record.reviewers) < 4:
                raise ValidationError(_("At least 4 reviewers are required."))
            if len(record.reviewers) > 6:
                raise ValidationError(_("Maximum 6 reviewers are allowed."))

            # Check for required relation types
            relation_types = record.reviewers.mapped('relation_type')
            required_types = {'director', 'hod', 'colleagues', 'cross_functional'}
            missing_types = required_types - set(relation_types)
            
            if missing_types:
                raise ValidationError(
                    _("Missing reviewers from the following categories: %s") %
                    ', '.join(missing_types))

    @api.constrains('manager_feedback')
    def _check_manager_feedback(self):
        for record in self:
            if record.state == 'reviewed' and (
                not record.manager_feedback or not record.manager_feedback.strip()):
                raise ValidationError(_("Manager feedback is required."))
            
            if record.manager_feedback and len(record.manager_feedback.split()) > 5000:
                raise ValidationError(_("Manager feedback must not exceed 5000 words."))

    def action_submit_feedback(self):
        """Submit 360° feedback"""
        self.ensure_one()
        if self.env.user != self.employee_id:
            raise ValidationError(_("Only the employee can submit their feedback."))
        
        self.state = 'submitted'
        
        # Send email to manager and employee
        template = self.env.ref('performance_reviews.email_template_feedback_submitted')
        template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('360° feedback has been submitted.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_submit_manager_feedback(self):
        """Submit manager's feedback"""
        self.ensure_one()
        if self.env.user.id != self.manager_id.id:
            raise ValidationError(_("Only the assigned manager can submit feedback."))
        
        if not self.manager_feedback or not self.manager_feedback.strip():
            raise ValidationError(_("Please provide feedback before submitting."))
        
        self.state = 'reviewed'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Manager feedback has been submitted.'),
                'type': 'success',
                'sticky': False,
            }
        }
        
    def action_reset_to_draft(self):
        """Reset 360° Feedback to draft state (HR Manager only)"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_hr_manager'):
            raise ValidationError(_("Only HR Managers can reset feedback to draft."))
        
        self.state = 'draft'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset Successful'),
                'message': _('360° Feedback has been reset to draft state.'),
                'type': 'success',
                'sticky': False,
            }
        }
