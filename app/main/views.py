from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, LERForm, AddComponentForm, CFRSelectForm
from .. import db
from ..models import User, Role, Permission, LER, Component, Facility, CFR, ComponentFailure, ComponentCause, \
    EIISComponentType, System
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    pagination = LER.query.order_by(LER.id.desc()).paginate(page,
                                                            per_page=current_app.config['NRCEVENTS_POSTS_PER_PAGE'],
                                                            error_out=False)
    lers = pagination.items
    return render_template('index.html',
                           lers=lers, name=session.get('name'),
                           pagination=pagination)


@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For Administrators!'


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, user=current_user)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/create-ler', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_ler():
    form = LERForm()
    seq = 1
    if form.validate_on_submit():
        facilities = [Facility.query.filter_by(id=fac).first() for fac in form.facilities.data]
        cfrs = [CFR.query.filter_by(id=cfr).first() for cfr in form.cfrs.data]
        ler_number = facilities[0].docket[5:] + str(form.event_date.data.year) + '001R00'
        ler = LER.query.filter_by(ler_number=ler_number).first()
        if ler:
            while ler is not None:
                seq += 1
                ler_number = (facilities[0].docket[5:] if facilities[0].docket.startswith('0')
            else facilities[0].docket) + str(form.event_date.data)[:4] + '00{}R00'.format(seq)
                ler = LER.query.filter_by(ler_number=ler_number).first()
        ler = LER(facilities=facilities,
                  title=form.title.data,
                  event_date=form.event_date.data,
                  ler_number=ler_number,
                  operating_mode=form.operating_mode.data,
                  power_level=form.power_level.data,
                  cfrs=cfrs,
                  supplement_expected=form.supplement_expected.data,
                  supplement_date=form.supplement_date.data,
                  abstract=form.abstract.data,
                  body=form.body.data,
                  author=current_user._get_current_object())
        for component in form.components:
            if component.system.data == -1 or component.component_type.data == -1 or component.cause.data == -1:
                continue
            if component.inpo_device_id.data != '':
                c = Component.query.filter_by(inpo_device_id=component.inpo_device_id.data).first()
                if c is None:
                    c = Component(system_id=component.system.data, eiiscomponenttype_id=component.component_type.data,
                                  manufacturer_id=component.manufacturer.data, facility_id=ler.facilities[0].id,
                                  inpo_device_id=component.inpo_device_id.data)
                    db.session.add(c)
            else:
                c = Component(system_id=component.system.data,
                              eiiscomponenttype_id=component.component_type.data,
                              manufacturer_id=component.manufacturer.data, facility_id=ler.facilities[0].id)
                db.session.add(c)
            reportable = component.reportable_ices.data
            cf = ComponentFailure(ler=ler,
                                  component=c,
                                  cause_id=component.cause.data,
                                  reportable_ices=reportable)
            ler.components.append(cf)
        db.session.add(ler)
        flash("You have successfully added LER {}.".format(ler_number))
        return redirect(url_for('.index'))
    return render_template('create_ler.html', form=form)


@main.route('/edit/<string:lernum>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    if current_user != ler.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    if ler.approved:
        flash('This LER has already been approved and cannot be edited.')
        return redirect(url_for('main.ler', lernum=lernum))
    form = LERForm()
    if form.validate_on_submit():
        ler.facilities = [Facility.query.filter_by(id=fac).first() for fac in form.facilities.data]
        ler.title = form.title.data
        ler.event_date = form.event_date.data
        ler.operating_mode = form.operating_mode.data
        ler.power_level = form.power_level.data
        ler.cfrs = [CFR.query.filter_by(id=cfr).first() for cfr in form.cfrs.data]
        ler.abstract = form.abstract.data
        ler.body = form.body.data
        ler.supplement_expected = form.supplement_expected.data
        ler.supplement_date = form.supplement_date.data
        ler.components.delete()
        for component in form.components:
            if component.system.data == -1 or component.component_type.data == -1 or component.cause.data == -1:
                continue
            if component.inpo_device_id.data != '':
                c = Component.query.filter_by(inpo_device_id=component.inpo_device_id.data).first()
                if c is None:
                    c = Component(system_id=component.system.data, eiiscomponenttype_id=component.component_type.data,
                                  manufacturer_id=component.manufacturer.data, facility_id=ler.facilities[0].id,
                                  inpo_device_id=component.inpo_device_id.data)
                    db.session.add(c)
            else:
                c = Component(system_id=component.system.data,
                              eiiscomponenttype_id=component.component_type.data,
                              manufacturer_id=component.manufacturer.data, facility_id=ler.facilities[0].id)
                db.session.add(c)
            reportable = component.reportable_ices.data
            cf = ComponentFailure(ler=ler,
                                  component=c,
                                  cause_id=component.cause.data,
                                  reportable_ices=reportable)
            ler.components.append(cf)
        db.session.add(ler)
        flash('LER {} has been updated.'.format(lernum))
        return redirect(url_for('main.ler', lernum=lernum))
    form.facilities.data = [f.id for f in ler.facilities]
    form.title.data = ler.title
    form.event_date.data = ler.event_date
    form.operating_mode.data = ler.operating_mode
    form.power_level.data = ler.power_level
    form.cfrs.data = [cfr.id for cfr in ler.cfrs]
    form.supplement_expected.data = ler.supplement_expected
    if ler.supplement_date:
        form.supplement_date.data = ler.supplement_date
    if ler.components.all():
        has_components = True
        for component in ler.components:
            cur = form.components[-1]
            cur.system.data = component.component.system_id
            cur.component_type.data = component.component.eiiscomponenttype_id
            cur.manufacturer.data = component.component.manufacturer
            cur.cause.data = component.cause_id
            cur.reportable_ices.data = component.reportable_ices
            cur.inpo_device_id.data = component.component.inpo_device_id
            if len(form.components) < len(ler.components.all()):
                form.components.append_entry()
    else:
        has_components = False
    form.abstract.data = ler.abstract
    form.body.data = ler.body
    return render_template('edit_ler.html', form=form, lernum=lernum, has_components=has_components)


@main.route('/add-component', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def add_component():
    form = AddComponentForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        component = Component(facility_id=form.facility.data,
                              system_id=form.system.data,
                              eiiscomponenttype_id=form.component_type.data,
                              manufacturer_id=form.manufacturer.data,
                              inpo_device_id=form.inpo_device_id.data)
        db.session.add(component)
        flash("You have successfully added a new component.")
        return redirect(url_for('.index'))
    return render_template('add_component.html', form=form)


@main.route('/remove-component/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def remove_component(id):
    pass


@main.route('/ler-list')
@login_required
def ler_list():
    lers = LER.query.all()
    return render_template('ler_list.html', lers=lers)


@main.route('/ler/<string:lernum>')
@login_required
@permission_required(Permission.READ)
def ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    return render_template('ler.html', ler=ler)
