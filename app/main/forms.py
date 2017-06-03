from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, ValidationError, \
    SelectMultipleField, DateField, IntegerField, widgets
from wtforms.validators import DataRequired, Length, Email, Regexp
from ..models import Role, User, Facility, CFR, System, EIISComponentType


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class NameForm(FlaskForm):
    name = StringField('LER Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'Usernames must have only letters, numbers, dots,'
                                                          ' or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class LERForm(FlaskForm):
    docket = SelectField("Docket Number", coerce=int)
    title = StringField('Title', validators=[Length(0, 64), DataRequired()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    ler_number = StringField('LER Number', validators=[DataRequired()])
    operating_mode = SelectField('Operating Mode', coerce=int)
    power_level = IntegerField('Power Level')
    cfr = SelectField("Report Submitted Pursuant to Requirements of 10 CFR: (Select all that apply)", #MultiCheckboxField
                              coerce=int)
    abstract = TextAreaField("Abstract", validators=[DataRequired()])
    body = TextAreaField("LER Text", validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(LERForm, self).__init__(*args, **kwargs)
        self.docket.choices = [(docket.id, '{} - {}'.format(docket.docket, docket.facility_name))
                               for docket in Facility.query.order_by(Facility.facility_name).all()]
        self.cfr.choices = [(cfr.id, cfr.cfr) for cfr in CFR.query.order_by(CFR.cfr).all()]
        self.operating_mode.choices = [(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')]


class AddComponentForm(FlaskForm):
    facility = SelectField("Facility", coerce=int, validators=[DataRequired()])
    system = SelectField("System", coerce=int, validators=[DataRequired()])
    component_type = SelectField("Component Type", coerce=int, validators=[DataRequired()])
    manufacturer = StringField("Manufacturer")

    def __init__(self, *args, **kwargs):
        super(AddComponentForm, self).__init__(*args, **kwargs)
        self.facility.choices = [(docket.id, '{} - {}'.format(docket.docket, docket.facility_name))
                                 for docket in Facility.query.order_by(Facility.facility_name).all()]
        self.system.choices = [(system.id, system.name) for system in System.query.order_by(System.name).all()]
        self.component_type.choices = [(component.id, component.name)
                                       for component in EIISComponent.query.order_by(EIISComponent.name).all()]
