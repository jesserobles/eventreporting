from flask import render_template, session, redirect, url_for, abort, flash, request, current_app, Response
from flask_login import login_required, current_user
from flask_weasyprint import HTML, render_pdf
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
import io
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, LERForm, AddComponentForm
from .. import db
from ..models import User, Role, Permission, LER, Component, Facility, CFR, ComponentFailure, ComponentCause, \
    EIISComponentType, System
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    pagination = LER.query.filter_by(
        approved=False).order_by(LER.id.desc()).paginate(page,
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
            cur.manufacturer.data = component.component.manufacturer_id
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


@main.route('/delete/<string:lernum>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def delete_ler(lernum):
    return 'Delete LER ' + lernum


@main.route('/unapprove/<string:lernum>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
def unapprove_ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    ler.approved = False
    db.session.add(ler)
    flash('You have unapproved LER ' + lernum)
    return redirect(url_for('.index'))


@main.route('/approve/<string:lernum>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.APPROVE)
def approve_ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    if not ler.approved:
        ler.approved = True
        db.session.add(ler)
        flash('You have approved LER ' + lernum)
    return redirect(url_for('.index'))


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


@main.route('/ler-list')
@login_required
def ler_list():
    page = request.args.get('page', 1, type=int)
    pagination = LER.query.filter_by(
        approved=True).order_by(LER.id.desc()).paginate(page,
                                                        per_page=current_app.config['NRCEVENTS_POSTS_PER_PAGE'],
                                                        error_out=False)
    lers = pagination.items
    return render_template('ler_list.html',
                           lers=lers, name=session.get('name'),
                           pagination=pagination)


@main.route('/ler/<string:lernum>')
@login_required
@permission_required(Permission.READ)
def ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    cfrs = [cfr.cfr for cfr in ler.cfrs]
    return render_template('table.html', ler=ler, cfrs=cfrs)


@main.route('/ler/<string:lernum>.pdf')
@login_required
@permission_required(Permission.READ)
def print_ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    cfrs = [cfr.cfr for cfr in ler.cfrs]
    components = ler.components.all()

    # Hack to get page counts and PDF formatting correct
    page_html = render_template('fullform.html', ler=ler, cfrs=cfrs, components=components)
    page_count = len(HTML(string=page_html).render().pages)
    documents = []
    if len(components) > 2:
        page_count += 1
        components_html = render_template('366b_pdf.html', ler=ler, components=components[2:])
        documents.append(HTML(string=components_html).render())
    first_page_html = render_template('366_pdf.html', ler=ler, cfrs=cfrs, components=components, page_count=page_count)
    narrative_html = render_template('366a_pdf.html', ler=ler)
    documents = [HTML(string=first_page_html).render(), HTML(string=narrative_html).render()] + documents
    all_pages = [p for doc in documents for p in doc.pages]
    pdf = documents[0].copy(all_pages).write_pdf()
    pdf = PyPDF2.PdfFileReader(io.BytesIO(pdf), strict=False)
    output = PyPDF2.PdfFileWriter()
    count = pdf.numPages
    for i in range(count):
        buffer = io.BytesIO()
        pagepdf = canvas.Canvas(buffer, pagesize=letter)
        page = pdf.getPage(i)
        if i == 0:
            output.addPage(page)
            continue
        text = "Page %s of %s" % (i + 1, count)
        pagepdf.drawRightString(195 * mm, 9 * mm, text)
        pagepdf.save()
        buffer.seek(0)
        pagepdf = PyPDF2.PdfFileReader(buffer)
        page.mergePage(pagepdf.getPage(0))
        output.addPage(page)
    outputstream = io.BytesIO()
    output.write(outputstream)
    outputstream.seek(0)
    http_response = Response(outputstream, content_type='application/pdf')
    http_response.headers['Content-Disposition'] = 'filename=LER {}.pdf'.format(ler.ler_number)
    return http_response
