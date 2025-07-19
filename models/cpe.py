from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PerformanceCPE(models.Model):
    _name = 'performance.cpe'
    _description = 'Continuous Performance Engagement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'cpe_date desc'

    def _default_employee(self):
        return self.env.user.id

    employee_id = fields.Many2one('res.users', string='Employee', required=True,
                                default=_default_employee, tracking=True)
    manager_id = fields.Many2one('res.users', string='Manager', tracking=True)
    cpe_date = fields.Date(string='CPE Date', required=True,
                          default=fields.Date.today, tracking=True)
    what_went_well = fields.Text(string='What Went Well', required=True, tracking=True)
    what_could_be_improved = fields.Text(string='What Could Be Improved', required=True, tracking=True)
    goals_for_next_period = fields.Text(string='Goals for Next Period', required=True, tracking=True)
    overall_comment = fields.Text(string='Overall Comment', required=True, tracking=True)
    manager_feedback = fields.Text(string='Manager Feedback', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed')
    ], string='Status', default='draft', tracking=True)

    @api.constrains('cpe_date')
    def _check_cpe_date(self):
        for record in self:
            if record.cpe_date > fields.Date.today():
                raise ValidationError(_("CPE date cannot be in the future."))
                
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set the manager when employee changes"""
        if self.employee_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.employee_id.id)], limit=1)
            if employee and employee.parent_id and employee.parent_id.user_id:
                self.manager_id = employee.parent_id.user_id.id

    @api.constrains('what_went_well', 'what_could_be_improved', 'goals_for_next_period', 
                    'overall_comment', 'manager_feedback')
    def _check_text_fields(self):
        for record in self:
            # Check required fields are not empty
            for field, field_name in [
                (record.what_went_well, 'What Went Well'),
                (record.what_could_be_improved, 'What Could Be Improved'),
                (record.goals_for_next_period, 'Goals for Next Period'),
                (record.overall_comment, 'Overall Comment')
            ]:
                if not field or not field.strip():
                    raise ValidationError(_(f"{field_name} cannot be empty."))

            # Check word count limits
            for field in [record.what_went_well, record.what_could_be_improved,
                         record.goals_for_next_period, record.overall_comment]:
                if len(field.split()) > 300:
                    raise ValidationError(_("Text fields must not exceed 300 words."))
            
            if record.manager_feedback and len(record.manager_feedback.split()) > 300:
                raise ValidationError(_("Manager feedback must not exceed 300 words."))

    def action_submit_cpe(self):
        """Submit CPE by employee"""
        self.ensure_one()
        if self.env.user != self.employee_id:
            raise ValidationError(_("Only the employee can submit their own CPE."))
        
        self.state = 'submitted'
        
        # Send email to manager
        template = self.env.ref('performance_reviews.email_template_cpe_reviewed_by_employee')
        template.send_mail(self.id, force_send=True)
        # Return a combined action for both reload and rainbow man
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'performance.cpe',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'mode': 'readonly'},
            'effect': {
                'fadeout': 'fast',
                'message': _('Well done! Your CPE has been submitted successfully!'),
                'type': 'rainbow_man',
            }
        }

    def action_submit_review(self):
        """Manager submits review"""
        self.ensure_one()
        if not self.manager_id:
            raise ValidationError(_("No manager assigned to this CPE."))
            
        if self.env.user.id != self.manager_id.id:
            raise ValidationError(_("Only the assigned manager can submit reviews."))
        
        if not self.manager_feedback or not self.manager_feedback.strip():
            raise ValidationError(_("Please provide feedback before submitting the review."))
        
        self.state = 'reviewed'
        
        # Send email to employee
        template = self.env.ref('performance_reviews.email_template_cpe_reviewed')
        template.send_mail(self.id, force_send=True)

        # Return a combined action for both reload and rainbow man
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'performance.cpe',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'mode': 'readonly'},
            'effect': {
                'fadeout': 'fast',
                'message': _('Great job! The review has been submitted successfully!'),
                'type': 'rainbow_man',
            }
        }
        
    def action_reset_to_draft(self):
        """Reset CPE to draft state (HR Manager only)"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_hr_manager'):
            raise ValidationError(_("Only HR Managers can reset CPEs to draft."))
        
        self.state = 'draft'
        
        # Return a combined action for both reload and rainbow man
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'performance.cpe',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'mode': 'edit'},
            'effect': {
                'fadeout': 'fast',
                'message': _('CPE has been reset to draft state.'),
                'type': 'rainbow_man',
            }
        }
