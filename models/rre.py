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
    manager_id = fields.Many2one('res.users', string='Manager', tracking=True)
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
                
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set the manager when employee changes"""
        if self.employee_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.employee_id.id)], limit=1)
            if employee and employee.parent_id and employee.parent_id.user_id:
                self.manager_id = employee.parent_id.user_id.id

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

            # Client requirement specifies all text types should be allowed
            # No character validation needed as all special characters are allowed

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
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'effect',
                    'effects': {
                        'type': 'rainbow_man',
                        'message': _('Well done! Your RRE has been submitted successfully!'),
                    }
                }
            }
        }

    def action_submit_review(self):
        """Submit manager's review"""
        self.ensure_one()
        if not self.manager_id:
            raise ValidationError(_("No manager assigned to this RRE."))
            
        if self.env.user.id != self.manager_id.id:
            raise ValidationError(_("Only the assigned manager can submit reviews."))
        
        if not self.manager_feedback or not self.manager_feedback.strip():
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
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'effect',
                    'effects': {
                        'type': 'rainbow_man',
                        'message': _('Great job! The review has been submitted successfully!'),
                    }
                }
            }
        }
        
    def action_reset_to_draft(self):
        """Reset RRE to draft state (HR Manager only)"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_hr_manager'):
            raise ValidationError(_("Only HR Managers can reset reviews to draft."))
        
        self.state = 'draft'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset Successful'),
                'message': _('RRE has been reset to draft state.'),
                'type': 'success',
                'sticky': False,
            }
        }
